"""
Model 4: Training Recommendation System (GBDT + Knowledge Graph)
Fixed & improved version:
  - Bug fix: recommend_next_skill no longer breaks after first skill
  - Model persistence: final model saved with joblib
  - Cross-validation added
  - dag_weight precomputed (not queried per skill in the hot path)
  - recommend_next_skill refactored to honour top_k properly
"""

import os
import warnings

import joblib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore")

import optuna
from optuna.samplers import TPESampler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, cross_val_score
import lightgbm as lgb

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("MODEL 4: TRAINING RECOMMENDATION SYSTEM (GBDT + KNOWLEDGE GRAPH)")
print("=" * 80)


# ============================================================================
# 1. LOAD DATA & DETECT COLUMN POSITIONS
# ============================================================================

def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.replace(r"^\ufeff", "", regex=True).str.strip()
    return df


def get_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    print(f"  Available: {df.columns.tolist()}")
    raise KeyError(f"None of {candidates} found")


print("\nLoading data...")
skill_gap         = load_and_clean("skill_gap_dataset.csv")
training_history  = load_and_clean("training_history.csv")
skills_catalog    = load_and_clean("skills_catalog.csv")
learning_resources = load_and_clean("learning_resources.csv")
training_skill_map = load_and_clean("training_skill_map.csv")
skill_chain_dag   = load_and_clean("skill_chain_dag.csv")
job_requirements  = load_and_clean("job_role_requirements.csv")
employee_skills   = load_and_clean("employee_skill_matrix.csv")

# ─── Detect columns ──────────────────────────────────────────────────────────
emp_id_col   = get_col(employee_skills, ["employee_id", "Employee_id"])
emp_sk_col   = get_col(employee_skills, ["skill_id",    "Skill_id"])
emp_pr_col   = get_col(employee_skills, ["proficiency", "Proficiency"])

job_role_col = get_col(job_requirements, ["job_role_id",       "Job_role_id"])
job_sk_col   = get_col(job_requirements, ["required_skill_id", "skill_id", "Required_skill_id"])
job_min_col  = get_col(job_requirements, ["min_proficiency",   "Min_proficiency"])
job_wt_col   = get_col(job_requirements, ["importance_weight", "Importance_weight"])

cat_sk_col   = get_col(skills_catalog, ["skill_id",        "Skill_id"])
cat_cplx_col = get_col(skills_catalog, ["complexity_level","Complexity_level"])

print(f"✅ Columns detected for all datasets")

# ============================================================================
# 2. BUILD DAG
# ============================================================================

G = nx.DiGraph()
for _, row in skill_chain_dag.iterrows():
    G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"], weight=row["weight"])

# Precompute max incoming weight per target skill (used as a feature)
dag_weight_lookup: dict = (
    skill_chain_dag
    .groupby("target_skill_id")["weight"]
    .max()
    .to_dict()
)

print(f"DAG: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


# ============================================================================
# 3. DOMAIN FUNCTIONS (FIXED)
# ============================================================================

def _get_role_requirements(role_id):
    req = job_requirements[job_requirements[job_role_col] == role_id]
    if req.empty:
        return pd.DataFrame()
    rs = req[[req.columns[req.columns.get_loc(job_sk_col)],
               req.columns[req.columns.get_loc(job_min_col)],
               req.columns[req.columns.get_loc(job_wt_col)]]].copy()
    rs.columns = ["skill_id", "min_proficiency", "importance_weight"]
    return rs


def _get_employee_proficiencies(employee_id):
    emp = employee_skills[employee_skills[emp_id_col] == employee_id]
    curr = emp[[emp.columns[emp.columns.get_loc(emp_sk_col)],
                emp.columns[emp.columns.get_loc(emp_pr_col)]]].copy()
    curr.columns = ["skill_id", "proficiency"]
    return curr


def get_learning_path(employee_id, target_role_id) -> list:
    """Return topologically ordered list of skills with gaps for the target role."""
    required_skills = _get_role_requirements(target_role_id)
    if required_skills.empty:
        return []

    current = _get_employee_proficiencies(employee_id)
    merged  = required_skills.merge(current, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"]         = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)

    missing = set(merged[merged["gap"] > 0]["skill_id"])
    ancestors = set()
    for s in missing:
        if s in G.nodes:
            ancestors.update(nx.ancestors(G, s))

    all_needed  = missing | ancestors
    subgraph    = G.subgraph(all_needed).copy()

    try:
        ordered = list(nx.topological_sort(subgraph))
    except nx.NetworkXUnfeasible:
        ordered = list(missing)

    return [s for s in ordered if s in missing]


def compute_readiness_score(employee_id, target_role_id) -> float:
    """Weighted gap-based readiness score in [0, 1]."""
    required_skills = _get_role_requirements(target_role_id)
    if required_skills.empty:
        return 0.0

    current = _get_employee_proficiencies(employee_id)
    merged  = required_skills.merge(current, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"]         = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)

    numerator   = (merged["gap"] * merged["importance_weight"]).sum()
    denominator = (4 * merged["importance_weight"]).sum()

    return 1.0 if denominator == 0 else 1.0 - (numerator / denominator)


# ============================================================================
# 4. PREPARE LIGHTGBM TRAINING DATA
# ============================================================================

print("\nPreparing training data...")

# Primary skill per training item
train_skill = (
    training_skill_map[training_skill_map["is_primary"] == True][["training_id", "skill_id"]]
)
train_history = training_history.merge(train_skill, on="training_id", how="inner")

# Join with skill gap data
train_data = train_history.merge(
    skill_gap[["employee_id", "skill_id", "job_role_id", "gap", "importance_weight"]],
    on=["employee_id", "skill_id"],
    how="inner",
)

# Complexity
train_data = train_data.merge(
    skills_catalog[[cat_sk_col, cat_cplx_col]],
    left_on="skill_id", right_on=cat_sk_col, how="left",
).rename(columns={cat_cplx_col: "complexity_level"})

# Resource attributes
if "duration_hours" not in learning_resources.columns:
    learning_resources["duration_hours"] = 5
if "skill_level" not in learning_resources.columns:
    learning_resources["skill_level"] = "Intermediate"

SKILL_LEVEL_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
res_attrs = learning_resources[["resource_id", "duration_hours", "skill_level"]].copy()
res_attrs["resource_skill_level"] = res_attrs["skill_level"].map(SKILL_LEVEL_MAP).fillna(2)
train_data = train_data.merge(
    res_attrs[["resource_id", "duration_hours", "resource_skill_level"]],
    on="resource_id", how="left",
)

# DAG edge weight (precomputed lookup — no per-row DAG scan)
train_data["dag_edge_weight"] = train_data["skill_id"].map(dag_weight_lookup).fillna(0)

# Employee-level aggregate features
emp_avg_score    = training_history.groupby("employee_id")["completion_score"].mean().rename("employee_avg_score")
emp_courses_done = training_history.groupby("employee_id").size().rename("employee_courses_done")
train_data = (
    train_data
    .merge(emp_avg_score,    on="employee_id", how="left")
    .merge(emp_courses_done, on="employee_id", how="left")
)
train_data["employee_avg_score"]    = train_data["employee_avg_score"].fillna(50.0)
train_data["employee_courses_done"] = train_data["employee_courses_done"].fillna(0)

REQUIRED_FEATURES = [
    "gap", "importance_weight", "complexity_level", "dag_edge_weight",
    "duration_hours", "resource_skill_level", "employee_avg_score", "employee_courses_done",
]

for col in REQUIRED_FEATURES:
    if col not in train_data.columns:
        print(f"  Warning: {col} missing — filling with 0")
        train_data[col] = 0

train_data = train_data.dropna(subset=REQUIRED_FEATURES + ["completion_score"])
X = train_data[REQUIRED_FEATURES].apply(pd.to_numeric, errors="coerce").dropna()
y = train_data["completion_score"].loc[X.index]

print(f"Training samples: {len(X)}")
if len(X) == 0:
    raise ValueError("No valid training samples — check data quality.")

# ============================================================================
# 5. TRAIN LIGHTGBM REGRESSOR WITH OPTUNA
# ============================================================================

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=train_data.loc[X.index, "employee_id"]))
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]


def objective(trial):
    params = {
        "objective":        "regression",
        "metric":           "rmse",
        "boosting_type":    "gbdt",
        "num_leaves":       trial.suggest_int("num_leaves", 10, 100),
        "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "n_estimators":     trial.suggest_int("n_estimators", 100, 500),
        "min_child_samples":trial.suggest_int("min_child_samples", 5, 50),
        "subsample":        trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha":        trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda":       trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "random_state":     42,
        "verbose":          -1,
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(20, verbose=False)],
    )
    return np.sqrt(mean_squared_error(y_test, model.predict(X_test)))


print("\nHyperparameter tuning with Optuna (30 trials)...")
study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=42))
study.optimize(objective, n_trials=30, show_progress_bar=True)

print(f"\nBest RMSE: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")

final_model = lgb.LGBMRegressor(
    **study.best_params, objective="regression", metric="rmse", random_state=42, verbose=-1
)
final_model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    callbacks=[lgb.early_stopping(20, verbose=False)],
)

y_pred = final_model.predict(X_test)
rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
r2     = r2_score(y_test, y_pred)
print(f"\nFinal model — RMSE: {rmse:.4f}  R²: {r2:.4f}")

# Cross-validation using sklearn wrapper
cv_model = lgb.LGBMRegressor(**study.best_params, random_state=42, verbose=-1)
cv_rmse = cross_val_score(cv_model, X, y, cv=5, scoring="neg_root_mean_squared_error")
print(f"5-Fold CV RMSE: {-cv_rmse.mean():.4f} ± {cv_rmse.std():.4f}")

# ============================================================================
# 6. SHAP EXPLAINABILITY
# ============================================================================

print("\nComputing SHAP explanations...")
explainer   = shap.TreeExplainer(final_model)
shap_values = explainer.shap_values(X_test)

plt.figure()
shap.summary_plot(shap_values, X_test, show=False)
plt.tight_layout()
plt.savefig("shap_summary.png", dpi=150)
plt.close()
print("✓ Saved shap_summary.png")

# ============================================================================
# 7. RECOMMENDATION FUNCTION (FIXED — honours top_k)
# ============================================================================

def recommend_next_skills(employee_id, target_role_id, top_k: int = 3) -> tuple[list, float]:
    """
    Returns (recommendations, readiness_score).
    recommendations is a list of dicts, one per skill in the learning path (up to top_k).
    FIX: removed the erroneous `break` so all skills are processed.
    """
    path      = get_learning_path(employee_id, target_role_id)
    readiness = compute_readiness_score(employee_id, target_role_id)

    if not path:
        return [], readiness

    required_skills = _get_role_requirements(target_role_id)
    current         = _get_employee_proficiencies(employee_id)
    merged          = required_skills.merge(current, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"]         = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)

    emp_avg    = float(emp_avg_score.get(employee_id, 50.0))
    emp_done   = int(emp_courses_done.get(employee_id, 0))

    recommendations = []

    for skill in path:
        if "target_skill_id" not in learning_resources.columns:
            print("ERROR: learning_resources missing 'target_skill_id'")
            break

        resources = learning_resources[learning_resources["target_skill_id"] == skill]
        if resources.empty:
            continue

        skill_info = merged[merged["skill_id"] == skill]
        if skill_info.empty:
            continue

        gap        = float(skill_info["gap"].iloc[0])
        importance = float(skill_info["importance_weight"].iloc[0])

        cplx_row = skills_catalog[skills_catalog[cat_sk_col] == skill]
        complexity = int(cplx_row.iloc[0][cat_cplx_col]) if not cplx_row.empty else 2

        dag_weight = dag_weight_lookup.get(skill, 0)

        results = []
        for _, res in resources.iterrows():
            features = pd.DataFrame([{
                "gap":                  gap,
                "importance_weight":    importance,
                "complexity_level":     complexity,
                "dag_edge_weight":      dag_weight,
                "duration_hours":       res.get("duration_hours", 5),
                "resource_skill_level": SKILL_LEVEL_MAP.get(res.get("skill_level", "Intermediate"), 2),
                "employee_avg_score":   emp_avg,
                "employee_courses_done":emp_done,
            }])[REQUIRED_FEATURES]
            pred_score = float(final_model.predict(features)[0])
            results.append((res["resource_id"], pred_score))

        results.sort(key=lambda x: x[1], reverse=True)

        recommendations.append({
            "skill_id":                skill,
            "recommended_resources":   [r[0] for r in results[:top_k]],
            "predicted_completion_score": results[0][1] if results else None,
        })
        # NOTE: No `break` here — all skills in the path are processed

    return recommendations, readiness


# ============================================================================
# 8. TEST CASE
# ============================================================================

print("\n" + "=" * 60)
print("TEST CASE: EMP-0001 → Role 5 (Tech Lead)")
print("=" * 60)

emp_id      = "EMP-0001"
target_role = 5

path      = get_learning_path(emp_id, target_role)
readiness = compute_readiness_score(emp_id, target_role)

print(f"Employee:        {emp_id}")
print(f"Readiness Score: {readiness:.4f}")
print(f"Status:          {'✅ READY' if readiness >= 0.75 else '❌ NEEDS TRAINING'}")
print(f"Skills to close: {len(path)}")
if path:
    print(f"First 5:         {path[:5]}")

# Detailed gap table
print("\n📊 Skill Gap Detail (top 10 by importance):")
print("-" * 70)
req  = _get_role_requirements(target_role)
curr = _get_employee_proficiencies(emp_id)
mg   = req.merge(curr, on="skill_id", how="left")
mg["proficiency"] = mg["proficiency"].fillna(0)
mg["gap"]         = np.maximum(mg["min_proficiency"] - mg["proficiency"], 0)
gaps = mg[mg["gap"] > 0].sort_values("importance_weight", ascending=False)

print(f"{'Skill':<12} {'Required':<10} {'Current':<10} {'Gap':<8} {'Importance':<12}")
print("-" * 70)
for _, row in gaps.head(10).iterrows():
    print(f"{row['skill_id']:<12} {row['min_proficiency']:<10.0f} "
          f"{row['proficiency']:<10.0f} {row['gap']:<8.0f} {row['importance_weight']:<12.2f}")

# ============================================================================
# 9. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    emp_id      = "EMP-0018"
    target_role = 4
    print(f"\n--- Recommendation: {emp_id} → Role {target_role} ---")
    recs, rdy = recommend_next_skills(emp_id, target_role, top_k=2)
    print(f"Readiness: {rdy:.4f}")
    for rec in recs:
        print(f"  Skill: {rec['skill_id']}")
        print(f"  Resources: {rec['recommended_resources']}")
        if rec["predicted_completion_score"]:
            print(f"  Predicted score: {rec['predicted_completion_score']:.2f}")

    lp = get_learning_path(emp_id, target_role)
    print(f"\nFull learning path ({len(lp)} skills): {lp}")

# ============================================================================
# 10. SAVE MODEL
# ============================================================================

model_path = os.path.join(OUTPUT_DIR, "learning_path_model.pkl")
dag_path   = os.path.join(OUTPUT_DIR, "skill_chain_dag.pkl")

joblib.dump(final_model, model_path)
joblib.dump({"dag": G, "dag_weight_lookup": dag_weight_lookup}, dag_path)

print(f"\n✓ Model saved → {model_path}")
print(f"✓ DAG saved   → {dag_path}")
print("Model 4 training complete.")
