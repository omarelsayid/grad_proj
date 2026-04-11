"""
Model 1: Employee Turnover Prediction (Fixed & Improved)

Bugs fixed vs original:
  1. SMOTE leakage — SMOTE is now wrapped inside an imblearn.Pipeline so it
     only fires on each fold's training split during CV. The old code applied
     SMOTE to the full training set before CV, letting synthetic samples leak
     into validation folds and inflate CV AUC to ~0.94 (true test AUC ~0.75).
  2. Undertuned XGBoost / LightGBM — GridSearchCV is replaced with Optuna
     (50 trials per model) for all four top classifiers.
  3. CV on resampled pool — CV now operates on the raw (pre-SMOTE) training
     data inside the pipeline, not on the already-resampled array.

Output:
  app/models/best_turnover_model.pkl   — ImbPipeline(SMOTE + best classifier)
  app/models/scaler.pkl                — StandardScaler
  app/models/turnover_features.pkl     — ordered feature name list
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
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

import optuna
from optuna.samplers import TPESampler
optuna.logging.set_verbosity(optuna.logging.WARNING)

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from lightgbm import LGBMClassifier
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_and_clean(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.replace(r"^\ufeff", "", regex=True).str.strip()
    return df


def cap_outliers(df: pd.DataFrame, column: str,
                 lower_pct: float = 0.01, upper_pct: float = 0.99) -> int:
    lower = df[column].quantile(lower_pct)
    upper = df[column].quantile(upper_pct)
    n_outliers = int(((df[column] < lower) | (df[column] > upper)).sum())
    df[column] = df[column].clip(lower, upper)
    return n_outliers


def make_pipe(clf):
    """Wrap a classifier in an imblearn Pipeline with SMOTE."""
    return ImbPipeline([
        ("smote", SMOTE(random_state=42)),
        ("clf",   clf),
    ])


print("=" * 80)
print("MODEL 1: EMPLOYEE TURNOVER PREDICTION (SMOTE-Pipeline + Optuna)")
print("=" * 80)

# ============================================================================
# SECTION 1: LOAD DATA
# ============================================================================

print("\nLoading data...")
df = load_and_clean("employee_turnover_dataset.csv")
print(f"Dataset shape: {df.shape}")
print(f"Turnover rate: {df['turnover_label'].mean() * 100:.2f}%")

# ============================================================================
# SECTION 2: CLEANING AND FEATURE ENGINEERING
# ============================================================================

print("\n--- Cleaning & Feature Engineering ---")
df_clean = df.copy()

# Missing values
if "avg_feedback_score" in df_clean.columns:
    df_clean["avg_feedback_score"] = df_clean["avg_feedback_score"].fillna(
        df_clean["avg_feedback_score"].median()
    )
for col in df_clean.select_dtypes(include=[np.number]).columns:
    if col != "employee_id" and df_clean[col].isnull().sum() > 0:
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())

# Infinite values
for col in df_clean.select_dtypes(include=[np.number]).columns:
    if col == "employee_id":
        continue
    n_inf = int(np.isinf(df_clean[col]).sum())
    if n_inf > 0:
        df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan).fillna(
            df_clean[col].median()
        )

# Duplicates
df_clean = df_clean.drop_duplicates(subset=["employee_id"], keep="first")

# Outlier capping
for col in ["salary_egp", "total_overtime_hours", "total_early_leave_min",
            "commute_distance_km", "absence_rate", "late_rate"]:
    if col in df_clean.columns:
        cap_outliers(df_clean, col)

# Feature engineering (9 derived features)
df_clean["tenure_vs_experience"]  = df_clean["tenure_years"] / (df_clean["total_working_years"] + 1e-5)
df_clean["promotion_gap_ratio"]   = df_clean["years_since_last_promotion"] / (df_clean["tenure_years"] + 1e-5)
df_clean["salary_per_year_exp"]   = df_clean["salary_egp"] / (df_clean["total_working_years"] + 1e-5)
df_clean["overtime_intensity"]    = df_clean["total_overtime_hours"] / (df_clean["avg_worked_hours"] + 1e-5)
df_clean["absence_severity"]      = df_clean["absence_rate"] * df_clean["late_rate"]
df_clean["attendance_quality"]    = df_clean["attendance_score"] * df_clean["avg_worked_hours"]
df_clean["performance_score"]     = (df_clean["latest_eval_score"] + df_clean["kpi_score"]) / 2
df_clean["engagement_score"]      = (
    df_clean["courses_completed"] * 10 + df_clean["avg_training_score"]
) / (df_clean["avg_feedback_score"] + 1)
df_clean["work_balance_fit"]      = df_clean["work_life_balance"] * df_clean["role_fit_score"]

# Encode categoricals
for col in [c for c in df_clean.select_dtypes(include=["object"]).columns if c != "employee_id"]:
    df_clean[col] = LabelEncoder().fit_transform(df_clean[col].astype(str))

# ============================================================================
# SECTION 3: PREPARE DATA
# ============================================================================

feature_cols = [c for c in df_clean.columns if c not in ["employee_id", "turnover_label"]]
X = df_clean[feature_cols].values
y = df_clean["turnover_label"].values
print(f"Features: {len(feature_cols)}  |  Samples: {len(X)}")

# FIX: train/test split on RAW data — SMOTE fires inside the pipeline
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s  = scaler.transform(X_te)
print(f"Train: {len(X_tr)}  Test: {len(X_te)}")
print("NOTE: SMOTE is applied inside each Pipeline — no pre-resampling.")

# ============================================================================
# SECTION 4: BASELINE — 7 CLASSIFIERS (SMOTE-PIPELINE + CV)
# ============================================================================

print("\n--- Baseline: 7 classifiers with SMOTE-inside-Pipeline ---")

base_clfs = {
    "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
    "Decision Tree":       DecisionTreeClassifier(random_state=42, max_depth=10),
    "Random Forest":       RandomForestClassifier(random_state=42, n_estimators=100, n_jobs=-1),
    "Gradient Boosting":   GradientBoostingClassifier(random_state=42, n_estimators=100),
    "XGBoost":             XGBClassifier(random_state=42, n_estimators=100, eval_metric="logloss"),
    "LightGBM":            LGBMClassifier(random_state=42, n_estimators=100, verbose=-1),
    "AdaBoost":            AdaBoostClassifier(random_state=42, n_estimators=100),
}

cv1 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results1 = []
trained1: dict = {}

for name, clf in base_clfs.items():
    pipe = make_pipe(clf)
    print(f"  Training {name}...", end=" ")
    pipe.fit(X_tr_s, y_tr)
    y_pred  = pipe.predict(X_te_s)
    y_proba = pipe.predict_proba(X_te_s)[:, 1]

    # CV on raw training data; SMOTE applied per fold inside the pipeline
    cv_f1  = cross_val_score(pipe, X_tr_s, y_tr, cv=cv1, scoring="f1",       n_jobs=-1)
    cv_auc = cross_val_score(pipe, X_tr_s, y_tr, cv=cv1, scoring="roc_auc",  n_jobs=-1)

    row = {
        "Model":     name,
        "Accuracy":  accuracy_score(y_te, y_pred),
        "Precision": precision_score(y_te, y_pred, zero_division=0),
        "Recall":    recall_score(y_te, y_pred),
        "F1-Score":  f1_score(y_te, y_pred),
        "ROC-AUC":   roc_auc_score(y_te, y_proba),
        "CV F1":     cv_f1.mean(),
        "CV AUC":    cv_auc.mean(),
    }
    results1.append(row)
    trained1[name] = {"pipe": pipe, "preds": y_pred, "probas": y_proba}
    print(f"F1={row['F1-Score']:.4f}  AUC={row['ROC-AUC']:.4f}  "
          f"CV_F1={cv_f1.mean():.4f}±{cv_f1.std():.4f}")

res1_df = pd.DataFrame(results1).sort_values("F1-Score", ascending=False)
print("\n--- BASELINE SUMMARY ---")
print(res1_df.to_string(index=False))

# ============================================================================
# SECTION 5: OPTUNA TUNING FOR TOP 4 CLASSIFIERS
# ============================================================================

print("\n--- Optuna tuning (50 trials each) ---")
cv1_opt = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)


def tune(name: str, objective_fn, n_trials: int = 50):
    study = optuna.create_study(direction="maximize", sampler=TPESampler(seed=42))
    study.optimize(objective_fn, n_trials=n_trials, show_progress_bar=False)
    print(f"  {name}: best CV F1={study.best_value:.4f}  params={study.best_params}")
    return study


# Random Forest
def rf_obj(trial):
    clf = RandomForestClassifier(
        n_estimators      = trial.suggest_int("n_estimators", 100, 500),
        max_depth         = trial.suggest_int("max_depth", 5, 30),
        min_samples_split = trial.suggest_int("min_samples_split", 2, 10),
        min_samples_leaf  = trial.suggest_int("min_samples_leaf", 1, 10),
        max_features      = trial.suggest_categorical("max_features", ["sqrt", "log2"]),
        random_state=42, n_jobs=-1,
    )
    return cross_val_score(make_pipe(clf), X_tr_s, y_tr, cv=cv1_opt, scoring="f1", n_jobs=-1).mean()

# XGBoost
def xgb_obj(trial):
    clf = XGBClassifier(
        n_estimators     = trial.suggest_int("n_estimators", 100, 500),
        learning_rate    = trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        max_depth        = trial.suggest_int("max_depth", 3, 10),
        subsample        = trial.suggest_float("subsample", 0.5, 1.0),
        colsample_bytree = trial.suggest_float("colsample_bytree", 0.5, 1.0),
        reg_alpha        = trial.suggest_float("reg_alpha", 1e-8, 5.0, log=True),
        reg_lambda       = trial.suggest_float("reg_lambda", 1e-8, 5.0, log=True),
        eval_metric="logloss", random_state=42,
    )
    return cross_val_score(make_pipe(clf), X_tr_s, y_tr, cv=cv1_opt, scoring="f1", n_jobs=-1).mean()

# LightGBM
def lgbm_obj(trial):
    clf = LGBMClassifier(
        n_estimators     = trial.suggest_int("n_estimators", 100, 500),
        learning_rate    = trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        num_leaves       = trial.suggest_int("num_leaves", 15, 127),
        min_child_samples= trial.suggest_int("min_child_samples", 5, 50),
        subsample        = trial.suggest_float("subsample", 0.5, 1.0),
        colsample_bytree = trial.suggest_float("colsample_bytree", 0.5, 1.0),
        reg_alpha        = trial.suggest_float("reg_alpha", 1e-8, 5.0, log=True),
        reg_lambda       = trial.suggest_float("reg_lambda", 1e-8, 5.0, log=True),
        random_state=42, verbose=-1,
    )
    return cross_val_score(make_pipe(clf), X_tr_s, y_tr, cv=cv1_opt, scoring="f1", n_jobs=-1).mean()

# Gradient Boosting
def gb_obj(trial):
    clf = GradientBoostingClassifier(
        n_estimators      = trial.suggest_int("n_estimators", 100, 400),
        learning_rate     = trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        max_depth         = trial.suggest_int("max_depth", 2, 8),
        subsample         = trial.suggest_float("subsample", 0.5, 1.0),
        min_samples_split = trial.suggest_int("min_samples_split", 2, 10),
        random_state=42,
    )
    return cross_val_score(make_pipe(clf), X_tr_s, y_tr, cv=cv1_opt, scoring="f1", n_jobs=-1).mean()

study_rf   = tune("Random Forest",     rf_obj)
study_xgb  = tune("XGBoost",           xgb_obj)
study_lgbm = tune("LightGBM",          lgbm_obj)
study_gb   = tune("Gradient Boosting", gb_obj)

tuned_models = {
    "Random Forest (Optuna)":     RandomForestClassifier(**study_rf.best_params,   random_state=42, n_jobs=-1),
    "XGBoost (Optuna)":           XGBClassifier(**study_xgb.best_params,           eval_metric="logloss", random_state=42),
    "LightGBM (Optuna)":          LGBMClassifier(**study_lgbm.best_params,         random_state=42, verbose=-1),
    "Gradient Boosting (Optuna)": GradientBoostingClassifier(**study_gb.best_params, random_state=42),
}

tuned_results = []
tuned_trained: dict = {}
for name, clf in tuned_models.items():
    pipe = make_pipe(clf)
    pipe.fit(X_tr_s, y_tr)
    y_pred  = pipe.predict(X_te_s)
    y_proba = pipe.predict_proba(X_te_s)[:, 1]
    row = {
        "Model":     name,
        "Accuracy":  accuracy_score(y_te, y_pred),
        "Precision": precision_score(y_te, y_pred, zero_division=0),
        "Recall":    recall_score(y_te, y_pred),
        "F1-Score":  f1_score(y_te, y_pred),
        "ROC-AUC":   roc_auc_score(y_te, y_proba),
    }
    tuned_results.append(row)
    tuned_trained[name] = {"pipe": pipe, "preds": y_pred, "probas": y_proba}
    print(f"  {name}: F1={row['F1-Score']:.4f}  AUC={row['ROC-AUC']:.4f}")

tuned_df = pd.DataFrame(tuned_results).sort_values("F1-Score", ascending=False)

# ============================================================================
# SECTION 6: SELECT OVERALL BEST MODEL
# ============================================================================

all_results = pd.concat(
    [res1_df[["Model", "Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]], tuned_df],
    ignore_index=True,
).sort_values("F1-Score", ascending=False)

print("\n=== FINAL RANKING ===")
print(all_results.to_string(index=False))

best_name = all_results.iloc[0]["Model"]
all_trained = {**trained1, **tuned_trained}
best_pipe   = all_trained[best_name]["pipe"]
best_preds  = all_trained[best_name]["preds"]
best_probas = all_trained[best_name]["probas"]

print(f"\nOverall Best: {best_name}")
print(classification_report(y_te, best_preds, target_names=["No Turnover", "Turnover"]))

# ============================================================================
# SECTION 7: PLOTS
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
cm = confusion_matrix(y_te, best_preds)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
            xticklabels=["No Turnover", "Turnover"],
            yticklabels=["No Turnover", "Turnover"])
axes[0].set(title=f"Confusion Matrix — {best_name}", xlabel="Predicted", ylabel="Actual")

fpr, tpr, _ = roc_curve(y_te, best_probas)
roc_auc = roc_auc_score(y_te, best_probas)
axes[1].plot(fpr, tpr, color="darkorange", lw=2, label=f"AUC = {roc_auc:.4f}")
axes[1].plot([0, 1], [0, 1], "navy", lw=2, linestyle="--", label="Random")
axes[1].set(xlim=[0, 1], ylim=[0, 1.05], xlabel="FPR", ylabel="TPR",
            title=f"ROC Curve — {best_name}")
axes[1].legend(loc="lower right")
axes[1].grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix_roc.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved confusion_matrix_roc.png")

# Feature importance (from the clf step of the pipeline)
best_clf = best_pipe.named_steps["clf"]
if hasattr(best_clf, "feature_importances_"):
    imps = best_clf.feature_importances_
    idx  = np.argsort(imps)[::-1][:20]
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(idx)), imps[idx], color="steelblue")
    plt.yticks(range(len(idx)), [feature_cols[i] for i in idx])
    plt.xlabel("Importance")
    plt.title(f"Top 20 Features — {best_name}", fontweight="bold")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "feature_importance.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved feature_importance.png")
    print("\nTop 10 features:")
    for i, feat_idx in enumerate(idx[:10], 1):
        print(f"  {i:2d}. {feature_cols[feat_idx]}: {imps[feat_idx]:.4f}")

# ============================================================================
# SECTION 8: SAVE
# ============================================================================

model_path   = os.path.join(OUTPUT_DIR, "best_turnover_model.pkl")
scaler_path  = os.path.join(OUTPUT_DIR, "scaler.pkl")
feature_path = os.path.join(OUTPUT_DIR, "turnover_features.pkl")

joblib.dump(best_pipe,        model_path)
joblib.dump(scaler,           scaler_path)
joblib.dump(list(feature_cols), feature_path)

print(f"\nModel saved  -> {model_path}")
print(f"Scaler saved -> {scaler_path}")
print(f"Feature list -> {feature_path}")
print("\nModel 1 training complete.")
print("NOTE: saved model is an ImbPipeline(SMOTE + classifier).")
print("      Pass StandardScaler-transformed features at inference time.")
