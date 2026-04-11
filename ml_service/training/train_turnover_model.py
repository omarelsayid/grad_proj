"""
Model 1: Employee Turnover Prediction
Multi-classifier comparison with SMOTE, GridSearchCV, cross-validation,
and full model persistence.
"""

# ============================================================================
# SECTION 1: IMPORTS AND DATA LOADING
# ============================================================================

import os
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

from imblearn.over_sampling import SMOTE
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
    GridSearchCV,
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


print("=" * 80)
print("MODEL 1: EMPLOYEE TURNOVER PREDICTION")
print("=" * 80)

print("\nLoading data...")
df = load_and_clean("employee_turnover_dataset.csv")

print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nBasic statistics:\n{df.describe()}")
print(f"\nTarget distribution:\n{df['turnover_label'].value_counts()}")
print(f"Turnover rate: {df['turnover_label'].mean() * 100:.2f}%")

# ============================================================================
# SECTION 2: DATA CLEANING AND PREPROCESSING
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 2: DATA CLEANING AND PREPROCESSING")
print("=" * 80)

df_clean = df.copy()

# ─── 2.1 Missing values ──────────────────────────────────────────────────────
print("\n--- 2.1 HANDLE MISSING VALUES ---")

if "avg_feedback_score" in df_clean.columns:
    n_missing = df_clean["avg_feedback_score"].isnull().sum()
    print(f"Missing avg_feedback_score: {n_missing} ({n_missing/len(df_clean)*100:.2f}%)")
    median_fb = df_clean["avg_feedback_score"].median()
    df_clean["avg_feedback_score"] = df_clean["avg_feedback_score"].fillna(median_fb)
    print(f"Filled with median: {median_fb:.2f}")

for col in df_clean.columns:
    if df_clean[col].dtype in ["float64", "int64"] and col != "employee_id":
        if df_clean[col].isnull().sum() > 0:
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())

print(f"Total missing after cleaning: {df_clean.isnull().sum().sum()}")

# ─── 2.2 Infinite values ─────────────────────────────────────────────────────
print("\n--- 2.2 HANDLE INFINITE VALUES ---")
for col in df_clean.select_dtypes(include=[np.number]).columns:
    if col == "employee_id":
        continue
    n_inf = int(np.isinf(df_clean[col]).sum())
    if n_inf > 0:
        print(f"  Replacing {n_inf} infinite values in {col}")
        df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())

# ─── 2.3 Duplicates ──────────────────────────────────────────────────────────
print("\n--- 2.3 REMOVE DUPLICATES ---")
initial_rows = len(df_clean)
df_clean = df_clean.drop_duplicates(subset=["employee_id"], keep="first")
print(f"Removed {initial_rows - len(df_clean)} duplicate rows")

# ─── 2.4 Outlier treatment ───────────────────────────────────────────────────
print("\n--- 2.4 OUTLIER TREATMENT ---")
outlier_cols = [
    "salary_egp", "total_overtime_hours", "total_early_leave_min",
    "commute_distance_km", "absence_rate", "late_rate",
]
for col in outlier_cols:
    if col in df_clean.columns:
        n = cap_outliers(df_clean, col)
        print(f"  {col}: capped {n} outliers")

# ─── 2.5 Feature engineering ─────────────────────────────────────────────────
print("\n--- 2.5 FEATURE ENGINEERING ---")
df_clean["tenure_vs_experience"] = (
    df_clean["tenure_years"] / (df_clean["total_working_years"] + 1e-5)
)
df_clean["promotion_gap_ratio"] = (
    df_clean["years_since_last_promotion"] / (df_clean["tenure_years"] + 1e-5)
)
df_clean["salary_per_year_exp"] = (
    df_clean["salary_egp"] / (df_clean["total_working_years"] + 1e-5)
)
df_clean["overtime_intensity"] = (
    df_clean["total_overtime_hours"] / (df_clean["avg_worked_hours"] + 1e-5)
)
df_clean["absence_severity"] = df_clean["absence_rate"] * df_clean["late_rate"]
df_clean["attendance_quality"] = (
    df_clean["attendance_score"] * df_clean["avg_worked_hours"]
)
df_clean["performance_score"] = (
    df_clean["latest_eval_score"] + df_clean["kpi_score"]
) / 2
df_clean["engagement_score"] = (
    df_clean["courses_completed"] * 10 + df_clean["avg_training_score"]
) / (df_clean["avg_feedback_score"] + 1)
df_clean["work_balance_fit"] = (
    df_clean["work_life_balance"] * df_clean["role_fit_score"]
)
print(f"Added 9 engineered features — total columns now: {len(df_clean.columns)}")

# ─── 2.6 Encode categoricals ─────────────────────────────────────────────────
print("\n--- 2.6 ENCODE CATEGORICAL VARIABLES ---")
categorical_cols = [
    c for c in df_clean.select_dtypes(include=["object"]).columns
    if c != "employee_id"
]
print(f"Categorical columns: {categorical_cols}")
for col in categorical_cols:
    le = LabelEncoder()
    df_clean[col] = le.fit_transform(df_clean[col].astype(str))
    print(f"  Encoded '{col}'")

# ============================================================================
# SECTION 3: PREPARE DATA FOR MODELING
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 3: PREPARE DATA FOR MODELING")
print("=" * 80)

feature_cols = [c for c in df_clean.columns if c not in ["employee_id", "turnover_label"]]
X = df_clean[feature_cols]
y = df_clean["turnover_label"]

print(f"Feature matrix: {X.shape}  |  Target: {y.shape}")
print(f"\nFeature list:")
for i, col in enumerate(X.columns, 1):
    print(f"  {i:2d}. {col}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {X_train.shape[0]}  |  Test: {X_test.shape[0]}")
print(f"Train turnover rate: {y_train.mean()*100:.2f}%")
print(f"Test  turnover rate: {y_test.mean()*100:.2f}%")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_train.columns)
X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=X_test.columns)
print("\n✓ Features scaled with StandardScaler")

smote = SMOTE(random_state=42)
X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
print(f"\nAfter SMOTE:")
print(f"  Train size: {X_train_res.shape[0]}  |  Turnover rate: {y_train_res.mean()*100:.2f}%")

# ============================================================================
# SECTION 4: MODEL TRAINING AND EVALUATION
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 4: MODEL TRAINING AND EVALUATION")
print("=" * 80)

models = {
    "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
    "Decision Tree":        DecisionTreeClassifier(random_state=42, max_depth=10),
    "Random Forest":        RandomForestClassifier(random_state=42, n_estimators=100, n_jobs=-1),
    "Gradient Boosting":    GradientBoostingClassifier(random_state=42, n_estimators=100),
    "XGBoost":              XGBClassifier(random_state=42, n_estimators=100,
                                          use_label_encoder=False, eval_metric="logloss"),
    "LightGBM":             LGBMClassifier(random_state=42, n_estimators=100, verbose=-1),
    "AdaBoost":             AdaBoostClassifier(random_state=42, n_estimators=100),
}


def evaluate_model(model, X_tr, X_te, y_tr, y_te, name):
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    y_proba = model.predict_proba(X_te)[:, 1]
    return {
        "Model":     name,
        "Accuracy":  accuracy_score(y_te, y_pred),
        "Precision": precision_score(y_te, y_pred),
        "Recall":    recall_score(y_te, y_pred),
        "F1-Score":  f1_score(y_te, y_pred),
        "ROC-AUC":   roc_auc_score(y_te, y_proba),
    }, model, y_pred, y_proba


results_list = []
trained_models: dict = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    res, trained, y_pred, y_proba = evaluate_model(
        model, X_train_res, X_test_scaled, y_train_res, y_test, name
    )
    results_list.append(res)
    trained_models[name] = {"model": trained, "predictions": y_pred, "probabilities": y_proba}
    print(f"  Accuracy={res['Accuracy']:.4f}  Precision={res['Precision']:.4f}"
          f"  Recall={res['Recall']:.4f}  F1={res['F1-Score']:.4f}  AUC={res['ROC-AUC']:.4f}")

results_df = pd.DataFrame(results_list).sort_values("F1-Score", ascending=False)
print("\n--- MODEL PERFORMANCE SUMMARY (sorted by F1) ---")
print(results_df.to_string(index=False))

best_name = results_df.iloc[0]["Model"]
best_model = trained_models[best_name]["model"]
best_preds = trained_models[best_name]["predictions"]
best_probas = trained_models[best_name]["probabilities"]

print(f"\n{'='*60}")
print(f"BEST MODEL: {best_name}")
print(f"{'='*60}")
for metric in ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]:
    print(f"  {metric}: {results_df.iloc[0][metric]:.4f}")

# ─── Cross-validation on best model ─────────────────────────────────────────
print(f"\n5-Fold Stratified Cross-Validation ({best_name}):")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1 = cross_val_score(best_model, X_train_res, y_train_res, cv=cv, scoring="f1", n_jobs=-1)
cv_auc = cross_val_score(best_model, X_train_res, y_train_res, cv=cv, scoring="roc_auc", n_jobs=-1)
print(f"  F1:      {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")
print(f"  ROC-AUC: {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

# ============================================================================
# SECTION 5: FEATURE IMPORTANCE
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 5: FEATURE IMPORTANCE ANALYSIS")
print("=" * 80)


def plot_feature_importance(model, feature_names, model_name: str, top_n: int = 20):
    if not hasattr(model, "feature_importances_"):
        print(f"  {model_name} has no feature_importances_")
        return []
    importances = model.feature_importances_
    idx = np.argsort(importances)[::-1][:top_n]
    plt.figure(figsize=(12, 8))
    plt.barh(range(len(idx)), importances[idx], color="steelblue")
    plt.yticks(range(len(idx)), [feature_names[i] for i in idx])
    plt.xlabel("Feature Importance")
    plt.title(f"Top {top_n} Features — {model_name}", fontweight="bold")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    safe_name = model_name.replace(" ", "_")
    plt.savefig(f"feature_importance_{safe_name}.png", dpi=150, bbox_inches="tight")
    plt.close()
    return [(feature_names[i], importances[i]) for i in idx]


top_features = plot_feature_importance(best_model, list(X.columns), best_name)
if top_features:
    print(f"\nTop 10 features ({best_name}):")
    for i, (feat, imp) in enumerate(top_features[:10], 1):
        print(f"  {i:2d}. {feat}: {imp:.4f}")

# ============================================================================
# SECTION 6: HYPERPARAMETER TUNING
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 6: HYPERPARAMETER TUNING")
print("=" * 80)

param_grids = {
    "Random Forest": {
        "base": RandomForestClassifier(random_state=42, n_jobs=-1),
        "grid": {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5],
        },
    },
    "Gradient Boosting": {
        "base": GradientBoostingClassifier(random_state=42),
        "grid": {
            "n_estimators": [100, 200],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5],
        },
    },
    "XGBoost": {
        "base": XGBClassifier(random_state=42, use_label_encoder=False, eval_metric="logloss"),
        "grid": {
            "n_estimators": [100, 200],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5],
        },
    },
    "LightGBM": {
        "base": LGBMClassifier(random_state=42, verbose=-1),
        "grid": {
            "n_estimators": [100, 200],
            "learning_rate": [0.05, 0.1],
            "num_leaves": [31, 63],
        },
    },
}

best_final_model = best_model
if best_name in param_grids:
    print(f"\nTuning {best_name} with GridSearchCV (cv=5)...")
    entry = param_grids[best_name]
    gs = GridSearchCV(entry["base"], entry["grid"], cv=5, scoring="f1", n_jobs=-1, verbose=1)
    gs.fit(X_train_res, y_train_res)

    print(f"Best params: {gs.best_params_}")
    print(f"Best CV F1:  {gs.best_score_:.4f}")

    tuned_model = gs.best_estimator_
    y_pred_tuned = tuned_model.predict(X_test_scaled)
    y_proba_tuned = tuned_model.predict_proba(X_test_scaled)[:, 1]

    f1_before = results_df.iloc[0]["F1-Score"]
    f1_after = f1_score(y_test, y_pred_tuned)
    print(f"\nF1 improvement: {f1_before:.4f} → {f1_after:.4f} ({f1_after - f1_before:+.4f})")

    best_final_model = tuned_model
    best_preds = y_pred_tuned
    best_probas = y_proba_tuned
else:
    print(f"Skipping tuning for {best_name}")

# ============================================================================
# SECTION 7: CONFUSION MATRIX AND ROC CURVE
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 7: CONFUSION MATRIX AND ROC CURVE")
print("=" * 80)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

cm = confusion_matrix(y_test, best_preds)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
            xticklabels=["No Turnover", "Turnover"],
            yticklabels=["No Turnover", "Turnover"])
axes[0].set_title(f"Confusion Matrix — {best_name}", fontweight="bold")
axes[0].set_xlabel("Predicted")
axes[0].set_ylabel("Actual")

fpr, tpr, _ = roc_curve(y_test, best_probas)
roc_auc = roc_auc_score(y_test, best_probas)
axes[1].plot(fpr, tpr, color="darkorange", lw=2, label=f"AUC = {roc_auc:.4f}")
axes[1].plot([0, 1], [0, 1], "navy", lw=2, linestyle="--", label="Random")
axes[1].set(xlim=[0, 1], ylim=[0, 1.05], xlabel="FPR", ylabel="TPR",
            title=f"ROC Curve — {best_name}")
axes[1].legend(loc="lower right")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig("confusion_matrix_roc.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ Saved confusion_matrix_roc.png")

# ============================================================================
# SECTION 8: CLASSIFICATION REPORT
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 8: CLASSIFICATION REPORT")
print("=" * 80)

print(classification_report(y_test, best_preds, target_names=["No Turnover", "Turnover"]))

# ============================================================================
# SECTION 9: SAVE RESULTS AND MODEL
# ============================================================================

print("\n" + "=" * 80)
print("SECTION 9: SAVE RESULTS AND MODEL")
print("=" * 80)

results_df.to_csv("model_performance_summary.csv", index=False)
print("✓ model_performance_summary.csv")

pd.DataFrame({
    "Actual": y_test.values,
    "Predicted": best_preds,
    "Probability_Turnover": best_probas,
}).to_csv("test_predictions.csv", index=False)
print("✓ test_predictions.csv")

if top_features:
    pd.DataFrame(top_features, columns=["Feature", "Importance"]).to_csv(
        "feature_importance.csv", index=False
    )
    print("✓ feature_importance.csv")

# Save to app/models for the FastAPI service
model_path = os.path.join(OUTPUT_DIR, "best_turnover_model.pkl")
scaler_path = os.path.join(OUTPUT_DIR, "scaler.pkl")
feature_path = os.path.join(OUTPUT_DIR, "turnover_features.pkl")

joblib.dump(best_final_model, model_path)
joblib.dump(scaler, scaler_path)
joblib.dump(list(X.columns), feature_path)

print(f"✓ Model saved  → {model_path}")
print(f"✓ Scaler saved → {scaler_path}")
print(f"✓ Feature list → {feature_path}")
print("\nModel 1 training complete.")
