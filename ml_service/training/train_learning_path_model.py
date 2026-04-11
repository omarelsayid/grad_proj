"""
Model 4: Training Recommendation System (GBDT + Knowledge Graph) — Fixed

Bug fixed vs original:
  emp_avg_score target leakage — the original code computed each employee's
  average completion_score globally across ALL their records, then mapped that
  value back as a feature.  When training on row N, this feature already
  included row N's own target score — classic target leakage.

Fix applied:
  emp_avg_score now uses a leave-one-out (LOO) mean: for each row the mean is
  computed over all OTHER records of the same employee, excluding the current
  row.  This exactly mirrors what would be available at inference time.

Output:
  app/models/learning_path_model.pkl   — LGBMRegressor
  app/models/skill_chain_dag.pkl       — DAG + edge-weight lookup dict
"""

# ============================================================================
# IMPORTS
# ============================================================================

import os
import warnings

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

import optuna
from optuna.samplers import TPESampler
optuna.logging.set_verbosity(optuna.logging.WARNING)

import lightgbm as lgb
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, cross_val_score

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("MODEL 4: TRAINING RECOMMENDATION SYSTEM (GBDT + KNOWLEDGE GRAPH) — FIXED")
print("=" * 80)

# ============================================================================
# 1. HELPERS & DATA LOADING
# ============================================================================

def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.replace(r"^\ufeff", "", regex=True).str.strip()
    return df


def get_col(df: pd.DataFrame, candidates: list) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found in columns: {df.columns.tolist()}")


print("\nLoading data...")
training_history   = load_and_clean("training_history.csv")
learning_resources = load_and_clean("learning_resources.csv")
skills_catalog     = load_and_clean("skills_catalog.csv")
skill_chain_dag    = load_and_clean("skill_chain_dag.csv")
job_requirements   = load_and_clean("job_role_requirements.csv")
employee_skills    = load_and_clean("employee_skill_matrix.csv")

# Optional: employees_core for richer employee features
try:
    employees_core = load_and_clean("employees_core.csv")
    core_available = True
    print("  employees_core.csv loaded")
except FileNotFoundError:
    employees_core = pd.DataFrame()
    core_available = False
    print("  employees_core.csv not found — skipping core features")

# ─── Detect columns ──────────────────────────────────────────────────────────
emp_id_col  = get_col(employee_skills, ["employee_id", "Employee_id"])
emp_sk_col  = get_col(employee_skills, ["skill_id",    "Skill_id"])
emp_pr_col  = get_col(employee_skills, ["proficiency", "Proficiency"])

job_role_col = get_col(job_requirements, ["job_role_id",       "Job_role_id"])
job_sk_col   = get_col(job_requirements, ["required_skill_id", "skill_id", "Required_skill_id"])
job_min_col  = get_col(job_requirements, ["min_proficiency",   "Min_proficiency"])
job_wt_col   = get_col(job_requirements, ["importance_weight", "Importance_weight"])

cat_sk_col   = get_col(skills_catalog, ["skill_id",         "Skill_id"])
cat_cplx_col = get_col(skills_catalog, ["complexity_level", "Complexity_level"])

print("Columns detected for all datasets.")

# ============================================================================
# 2. BUILD SKILL CHAIN DAG
# ============================================================================

G = nx.DiGraph()
edge_weight_col = "edge_weight" if "edge_weight" in skill_chain_dag.columns else "weight"
for _, row in skill_chain_dag.iterrows():
    G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
               weight=row[edge_weight_col])

dag_weight_lookup: dict = (
    skill_chain_dag
    .groupby("target_skill_id")[edge_weight_col]
    .max()
    .to_dict()
)
print(f"DAG: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# ============================================================================
# 3. BUILD TRAINING DATASET
# ============================================================================

print("\nBuilding training dataset...")

# Join training_history → learning_resources to get resource attributes
res_cols = ["resource_id"]
if "duration_hours" not in learning_resources.columns:
    learning_resources["duration_hours"] = 5.0
if "skill_level" not in learning_resources.columns:
    learning_resources["skill_level"] = "Intermediate"
if "target_skill_id" not in learning_resources.columns:
    learning_resources["target_skill_id"] = None

res_cols += ["duration_hours", "skill_level", "target_skill_id"]
res_attrs = learning_resources[res_cols].copy()

SKILL_LEVEL_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
res_attrs["resource_skill_level"] = res_attrs["skill_level"].map(SKILL_LEVEL_MAP).fillna(2)

t4 = training_history.merge(
    res_attrs[["resource_id", "duration_hours", "resource_skill_level", "target_skill_id"]].rename(
        columns={"duration_hours": "lr_duration_hours"}
    ),
    on="resource_id",
    how="left",
)

# Resolve duration_hours (prefer resource table, fall back to history column)
if "duration_hours" in training_history.columns:
    t4["duration_hours"] = t4["lr_duration_hours"].fillna(training_history["duration_hours"])
else:
    t4["duration_hours"] = t4["lr_duration_hours"].fillna(5.0)

t4 = t4.drop(columns=["lr_duration_hours"], errors="ignore")
print(f"  After resource join: {len(t4)} rows  |  "
      f"missing target_skill: {t4['target_skill_id'].isna().sum()}")

# Employee proficiency on target skill
ep4 = employee_skills[[emp_id_col, emp_sk_col, emp_pr_col]].rename(
    columns={emp_id_col: "employee_id", emp_sk_col: "target_skill_id", emp_pr_col: "emp_proficiency"}
)
t4 = t4.merge(ep4, on=["employee_id", "target_skill_id"], how="left")
t4["emp_proficiency"] = t4["emp_proficiency"].fillna(0)

# Skill complexity
sc_slim = skills_catalog[[cat_sk_col, cat_cplx_col]].rename(
    columns={cat_sk_col: "target_skill_id", cat_cplx_col: "complexity_level"}
)
t4 = t4.merge(sc_slim, on="target_skill_id", how="left")
t4["complexity_level"] = t4["complexity_level"].fillna(2)

# DAG edge weight
t4["dag_edge_weight"] = t4["target_skill_id"].map(dag_weight_lookup).fillna(0)

# Skill gap proxy (how much more advanced the resource is vs employee)
t4["skill_gap_proxy"] = (t4["resource_skill_level"] - t4["emp_proficiency"]).clip(lower=0)

# Employee course count (count only — not a mean of the target)
emp_cnt = training_history.groupby("employee_id").size().to_dict()
t4["emp_courses_done"] = t4["employee_id"].map(emp_cnt).fillna(0)

# ── FIX: Leave-one-out (LOO) mean for emp_avg_score ──────────────────────────
# For each row i, compute mean of completion_score over all OTHER rows for
# the same employee.  The global mean includes row i's own target, which
# causes leakage when that value is used as a feature to predict the same
# target.  LOO exactly matches what's available at real inference time.
global_mean = training_history["completion_score"].mean()

emp_sum  = training_history.groupby("employee_id")["completion_score"].sum().to_dict()
emp_cnt_full = training_history.groupby("employee_id").size().to_dict()

# Bring current row's completion_score into t4 for LOO computation
t4 = t4.merge(
    training_history[["employee_id", "resource_id", "completion_score"]].rename(
        columns={"completion_score": "_cs"}
    ),
    on=["employee_id", "resource_id"],
    how="left",
)

def _loo_mean(row):
    eid = row["employee_id"]
    cur = row["_cs"]
    n   = emp_cnt_full.get(eid, 0)
    s   = emp_sum.get(eid, 0.0)
    if pd.isna(cur) or n <= 1:
        return global_mean
    return (s - cur) / (n - 1)

t4["emp_avg_score"] = t4.apply(_loo_mean, axis=1)
t4 = t4.drop(columns=["_cs"], errors="ignore")
print(f"  emp_avg_score (LOO) mean={t4['emp_avg_score'].mean():.2f}  "
      f"(no target leakage — current row excluded from each employee's average)")

# Attempt number per employee-skill (proxy for retries)
if "attempt_number" not in t4.columns:
    t4["attempt_number"] = (
        t4.groupby(["employee_id", "target_skill_id"]).cumcount() + 1
    )

# Optional: employee core profile features
core_extra: list[str] = []
if core_available and "employee_id" in employees_core.columns:
    available_core = [c for c in ["age", "tenure_years", "total_working_years",
                                   "kpi_score", "latest_eval_score", "role_fit_score"]
                      if c in employees_core.columns]
    if available_core:
        t4 = t4.merge(employees_core[["employee_id"] + available_core],
                      on="employee_id", how="left")
        for c in available_core:
            t4[c] = t4[c].fillna(t4[c].median())
        core_extra = available_core
        print(f"  Core features added: {core_extra}")

# ── Feature set ───────────────────────────────────────────────────────────────
REQUIRED_FEATURES = [
    "emp_proficiency", "resource_skill_level", "skill_gap_proxy",
    "complexity_level", "dag_edge_weight", "duration_hours",
    "emp_avg_score", "emp_courses_done", "attempt_number",
] + core_extra

# Service-compatible feature set (8 features, always available at inference)
# Used by learning_path_service.py — keep in sync
SERVICE_FEATURES = [
    "gap", "importance_weight", "complexity_level", "dag_edge_weight",
    "duration_hours", "resource_skill_level", "employee_avg_score", "employee_courses_done",
]

for col in REQUIRED_FEATURES:
    if col not in t4.columns:
        print(f"  Warning: {col} missing — filling with 0")
        t4[col] = 0

t4_clean = t4.dropna(subset=REQUIRED_FEATURES + ["completion_score"])
X = t4_clean[REQUIRED_FEATURES].apply(pd.to_numeric, errors="coerce").dropna()
y = t4_clean["completion_score"].loc[X.index]

print(f"\nTraining samples: {len(X)}  |  Features: {len(REQUIRED_FEATURES)}")
print(f"Score range: {y.min():.0f}-{y.max():.0f}  std={y.std():.2f}")
if len(X) == 0:
    raise ValueError("No valid training samples — check data joins and employee_id format.")

# ============================================================================
# 4. TRAIN / TEST SPLIT (GROUPED BY EMPLOYEE)
# ============================================================================

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
tr_idx, te_idx = next(gss.split(X, y, groups=t4_clean.loc[X.index, "employee_id"]))
X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]
print(f"Train: {len(X_tr)}  Test: {len(X_te)}")
print(f"Train employees: {t4_clean.iloc[tr_idx]['employee_id'].nunique()}  "
      f"Test employees: {t4_clean.iloc[te_idx]['employee_id'].nunique()}")

# ============================================================================
# 5. LIGHTGBM + OPTUNA TUNING
# ============================================================================

print("\nHyperparameter tuning with Optuna (50 trials)...")


def m4_objective(trial):
    params = {
        "n_estimators":       trial.suggest_int("n_estimators", 100, 500),
        "learning_rate":      trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
        "num_leaves":         trial.suggest_int("num_leaves", 8, 60),
        "min_child_samples":  trial.suggest_int("min_child_samples", 3, 30),
        "subsample":          trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":   trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha":          trial.suggest_float("reg_alpha", 1e-8, 5.0, log=True),
        "reg_lambda":         trial.suggest_float("reg_lambda", 1e-8, 5.0, log=True),
        "random_state": 42, "verbose": -1,
    }
    scores = cross_val_score(
        lgb.LGBMRegressor(**params), X_tr, y_tr.to_numpy(),
        cv=5, scoring="neg_root_mean_squared_error",
    )
    return -scores.mean()


study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=42))
study.optimize(m4_objective, n_trials=50)
print(f"Best CV RMSE: {study.best_value:.4f}")
print(f"Best params:  {study.best_params}")

# ============================================================================
# 6. FINAL MODEL
# ============================================================================

final_model = lgb.LGBMRegressor(
    **study.best_params, objective="regression", metric="rmse",
    random_state=42, verbose=-1,
)
final_model.fit(
    X_tr, y_tr.to_numpy(),
    eval_set=[(X_te, y_te.to_numpy())],
    callbacks=[lgb.early_stopping(20, verbose=False)],
)

y_pred = final_model.predict(X_te)
rmse   = np.sqrt(mean_squared_error(y_te, y_pred))
mae    = mean_absolute_error(y_te, y_pred)
r2     = r2_score(y_te, y_pred)
baseline_rmse = float(y_te.std())

cv_scores = cross_val_score(
    lgb.LGBMRegressor(**study.best_params, random_state=42, verbose=-1),
    X, y.to_numpy(), cv=5, scoring="neg_root_mean_squared_error",
)

print(f"\nFinal Model Performance (LOO emp_avg_score — no leakage):")
print(f"  RMSE:          {rmse:.4f}  (baseline std: {baseline_rmse:.4f})")
print(f"  MAE:           {mae:.4f}")
print(f"  R2:            {r2:.4f}")
print(f"  5-Fold CV RMSE:{-cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")
print(f"  RMSE/baseline: {rmse/baseline_rmse:.3f} (< 1.0 = beats mean predictor)")

# ─── Plots ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(y_te, y_pred, alpha=0.5, color="steelblue")
mn, mx = float(y_te.min()), float(y_te.max())
axes[0].plot([mn, mx], [mn, mx], "r--", lw=2, label="Perfect")
axes[0].set(xlabel="Actual Score", ylabel="Predicted Score",
            title=f"Predicted vs Actual (R2={r2:.4f}, RMSE={rmse:.2f})")
axes[0].legend()

residuals = y_pred - y_te.to_numpy()
axes[1].scatter(y_pred, residuals, alpha=0.5, color="steelblue")
axes[1].axhline(0, color="red", linestyle="--", lw=2)
axes[1].set(xlabel="Predicted Score", ylabel="Residual",
            title="Residual Plot (should be random around 0)")
axes[1].grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "learning_path_predictions.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved learning_path_predictions.png")

# SHAP
try:
    print("Computing SHAP values...")
    explainer   = shap.TreeExplainer(final_model)
    shap_values = explainer.shap_values(X_te)
    plt.figure()
    shap.summary_plot(shap_values, X_te, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "shap_summary.png"), dpi=150)
    plt.close()
    print("Saved shap_summary.png")
except Exception as exc:
    print(f"SHAP skipped: {exc}")

# ============================================================================
# 7. DOMAIN FUNCTIONS
# ============================================================================

def _get_role_requirements(role_id):
    req = job_requirements[job_requirements[job_role_col] == role_id]
    if req.empty:
        return pd.DataFrame(columns=["skill_id", "min_proficiency", "importance_weight"])
    return req[[job_sk_col, job_min_col, job_wt_col]].rename(
        columns={job_sk_col: "skill_id", job_min_col: "min_proficiency", job_wt_col: "importance_weight"}
    ).copy()


def _get_employee_proficiencies(employee_id):
    emp = employee_skills[employee_skills[emp_id_col] == employee_id]
    return emp[[emp_sk_col, emp_pr_col]].rename(
        columns={emp_sk_col: "skill_id", emp_pr_col: "proficiency"}
    ).copy()


def get_learning_path(employee_id, target_role_id) -> list:
    required = _get_role_requirements(target_role_id)
    if required.empty:
        return []
    current = _get_employee_proficiencies(employee_id)
    merged  = required.merge(current, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"]         = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)
    missing   = set(merged[merged["gap"] > 0]["skill_id"])
    ancestors = set()
    for s in missing:
        if s in G.nodes:
            ancestors.update(nx.ancestors(G, s))
    subgraph = G.subgraph(missing | ancestors).copy()
    try:
        ordered = list(nx.topological_sort(subgraph))
    except nx.NetworkXUnfeasible:
        ordered = list(missing)
    return [s for s in ordered if s in missing]


def compute_readiness_score(employee_id, target_role_id) -> float:
    required = _get_role_requirements(target_role_id)
    if required.empty:
        return 0.0
    current = _get_employee_proficiencies(employee_id)
    merged  = required.merge(current, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"]         = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)
    num = (merged["gap"] * merged["importance_weight"]).sum()
    den = (4 * merged["importance_weight"]).sum()
    return 1.0 if den == 0 else 1.0 - (num / den)


# Quick demo
emp_demo  = employee_skills[emp_id_col].iloc[0]
role_demo = job_requirements[job_role_col].iloc[0]
path_demo = get_learning_path(emp_demo, role_demo)
rdy_demo  = compute_readiness_score(emp_demo, role_demo)
print(f"\nDemo: {emp_demo} -> Role {role_demo}")
print(f"  Readiness: {rdy_demo:.4f}  |  Skills in path: {len(path_demo)}")
if path_demo:
    print(f"  First 5: {path_demo[:5]}")

# ============================================================================
# 8. SAVE
# ============================================================================

model_path = os.path.join(OUTPUT_DIR, "learning_path_model.pkl")
dag_path   = os.path.join(OUTPUT_DIR, "skill_chain_dag.pkl")

joblib.dump(final_model, model_path)
joblib.dump({"dag": G, "dag_weight_lookup": dag_weight_lookup}, dag_path)
# Also save the feature list so the service can verify alignment
joblib.dump(REQUIRED_FEATURES, os.path.join(OUTPUT_DIR, "learning_path_features.pkl"))

print(f"\nModel saved  -> {model_path}")
print(f"DAG saved    -> {dag_path}")
print("Model 4 training complete.")
print("NOTE: emp_avg_score uses LOO mean — no target leakage.")
print(f"      Model trained on {len(REQUIRED_FEATURES)} features: {REQUIRED_FEATURES}")
