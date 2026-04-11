"""
Model 2: Role Fit Scoring
Gradient Boosting Regressor trained on (employee, role) pairs.

Target: readiness_score computed from weighted skill gaps — gives the model
real ground-truth to learn from so it generalises to unseen combinations.
"""

import os
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import optuna
from optuna.samplers import TPESampler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("MODEL 2: ROLE FIT SCORING")
print("=" * 80)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.replace(r"^\ufeff", "", regex=True).str.strip()
    return df


def get_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found. Available: {df.columns.tolist()}")


# ─── Load data ───────────────────────────────────────────────────────────────

print("\nLoading data...")
employee_skills = load_and_clean("employee_skill_matrix.csv")
job_requirements = load_and_clean("job_role_requirements.csv")

print(f"Employee skills: {employee_skills.shape}")
print(f"Job requirements: {job_requirements.shape}")

# Detect column names robustly
emp_id_col  = get_col(employee_skills, ["employee_id", "Employee_id", "EMPLOYEE_ID"])
emp_sk_col  = get_col(employee_skills, ["skill_id",    "Skill_id",    "SKILL_ID"])
emp_pr_col  = get_col(employee_skills, ["proficiency", "Proficiency", "PROFICIENCY"])

job_role_col = get_col(job_requirements, ["job_role_id",      "Job_role_id"])
job_sk_col   = get_col(job_requirements, ["required_skill_id","skill_id",   "Required_skill_id"])
job_min_col  = get_col(job_requirements, ["min_proficiency",  "Min_proficiency"])
job_wt_col   = get_col(job_requirements, ["importance_weight","Importance_weight"])

print(f"\nColumns detected:")
print(f"  employee_skills — id:{emp_id_col}, skill:{emp_sk_col}, prof:{emp_pr_col}")
print(f"  job_requirements — role:{job_role_col}, skill:{job_sk_col}, "
      f"min:{job_min_col}, weight:{job_wt_col}")

# ─── Build feature matrix ────────────────────────────────────────────────────

print("\nBuilding (employee × role) feature matrix...")

employee_ids = employee_skills[emp_id_col].unique()
role_ids     = job_requirements[job_role_col].unique()

records = []

for emp_id in employee_ids:
    emp_rows = employee_skills[employee_skills[emp_id_col] == emp_id]
    emp_dict = dict(zip(emp_rows[emp_sk_col], emp_rows[emp_pr_col]))

    for role_id in role_ids:
        req_rows = job_requirements[job_requirements[job_role_col] == role_id]
        if req_rows.empty:
            continue

        n_required   = len(req_rows)
        n_matching   = 0
        n_missing    = 0
        w_gap_sum    = 0.0
        w_sum        = 0.0
        max_gap      = 0.0
        matched_prof = []

        for _, row in req_rows.iterrows():
            skill_id   = row[job_sk_col]
            min_prof   = float(row[job_min_col])
            importance = float(row[job_wt_col])
            current    = float(emp_dict.get(skill_id, 0.0))
            gap        = max(min_prof - current, 0.0)

            w_gap_sum += gap * importance
            w_sum     += 4 * importance      # max gap = 4
            max_gap    = max(max_gap, gap)

            if gap == 0:
                n_matching += 1
                matched_prof.append(current)
            else:
                n_missing += 1

        # Readiness: 1 - weighted_gap_ratio
        readiness = 1.0 - (w_gap_sum / w_sum) if w_sum > 0 else 1.0

        records.append({
            "employee_id":      emp_id,
            "job_role_id":      role_id,
            "n_required":       n_required,
            "n_matching":       n_matching,
            "n_missing":        n_missing,
            "coverage_ratio":   n_matching / n_required if n_required else 0.0,
            "weighted_gap":     (w_gap_sum / w_sum * 4) if w_sum else 0.0,  # 0–4 scale
            "max_gap":          max_gap,
            "avg_matched_prof": float(np.mean(matched_prof)) if matched_prof else 0.0,
            "readiness_score":  readiness,
        })

df = pd.DataFrame(records)
print(f"Feature matrix: {df.shape}")
print(f"\nReadiness score stats:\n{df['readiness_score'].describe()}")

# ─── Train / test split ──────────────────────────────────────────────────────

FEATURE_COLS = [
    "n_required", "n_matching", "n_missing",
    "coverage_ratio", "weighted_gap", "max_gap", "avg_matched_prof",
]
X = df[FEATURE_COLS]
y = df["readiness_score"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")

# ─── Hyperparameter tuning (Optuna) ──────────────────────────────────────────

def objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 100, 500),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth":         trial.suggest_int("max_depth", 2, 8),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
        "random_state":      42,
    }
    model = GradientBoostingRegressor(**params)
    scores = cross_val_score(
        model, X_train, y_train, cv=5, scoring="neg_root_mean_squared_error"
    )
    return -scores.mean()


print("\nHyperparameter tuning with Optuna (30 trials)...")
study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=42))
study.optimize(objective, n_trials=30, show_progress_bar=True)

print(f"\nBest RMSE: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")

# ─── Train final model ────────────────────────────────────────────────────────

final_model = GradientBoostingRegressor(**study.best_params, random_state=42)
final_model.fit(X_train, y_train)

y_pred = final_model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae  = mean_absolute_error(y_test, y_pred)
r2   = r2_score(y_test, y_pred)

print(f"\nFinal Model Performance:")
print(f"  RMSE: {rmse:.4f}")
print(f"  MAE:  {mae:.4f}")
print(f"  R²:   {r2:.4f}")

# Cross-validation
cv_r2 = cross_val_score(final_model, X, y, cv=5, scoring="r2")
print(f"\n5-Fold CV R²: {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")

# ─── Feature importance ───────────────────────────────────────────────────────

importance_df = pd.DataFrame({
    "feature":    FEATURE_COLS,
    "importance": final_model.feature_importances_,
}).sort_values("importance", ascending=False)

print("\nFeature Importance:")
print(importance_df.to_string(index=False))

plt.figure(figsize=(10, 6))
plt.barh(importance_df["feature"], importance_df["importance"], color="steelblue")
plt.xlabel("Importance")
plt.title("Role Fit Model — Feature Importance", fontweight="bold")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("role_fit_feature_importance.png", dpi=150)
plt.close()
print("✓ Saved role_fit_feature_importance.png")

# ─── Example ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("EXAMPLE PREDICTION")
print("=" * 60)
sample = X_test.iloc[:1]
pred   = final_model.predict(sample)[0]
actual = y_test.iloc[0]
print(f"Features:  {dict(zip(FEATURE_COLS, sample.values[0]))}")
print(f"Predicted: {pred:.4f}  ({int(pred*100)}/100)")
print(f"Actual:    {actual:.4f} ({int(actual*100)}/100)")

# ─── Save ────────────────────────────────────────────────────────────────────

model_path = os.path.join(OUTPUT_DIR, "role_fit_model.pkl")
joblib.dump(final_model, model_path)
print(f"\n✓ Model saved → {model_path}")
print("Model 2 training complete.")
