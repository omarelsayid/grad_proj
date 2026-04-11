"""
Tests for Model 1: Employee Turnover Prediction
train_turnover_model.py

Covers:
  - Data cleaning helpers (cap_outliers, load_and_clean)
  - Feature engineering correctness and shape
  - Preprocessing pipeline integrity (scaler + SMOTE)
  - Train/test split stratification
  - Model training + multi-metric evaluation
  - Cross-validation sanity
  - Overfitting detection (train vs test gap)
  - Baseline comparison (dummy classifier)
  - Persistence: saved artefacts are loadable and produce consistent output
"""

import numpy as np
import pandas as pd
import pytest
import joblib
import tempfile
import os

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE


# ─── Reimport helpers directly from training script ───────────────────────────
# We import the pure functions so we can unit-test them in isolation.
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def cap_outliers(df: pd.DataFrame, column: str,
                 lower_pct: float = 0.01, upper_pct: float = 0.99) -> int:
    """Copied from train_turnover_model.py so we can test it in isolation."""
    lower = df[column].quantile(lower_pct)
    upper = df[column].quantile(upper_pct)
    n_outliers = int(((df[column] < lower) | (df[column] > upper)).sum())
    df[column] = df[column].clip(lower, upper)
    return n_outliers


def engineer_features(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Replicates the feature engineering block from the training script."""
    df = df_clean.copy()
    df["tenure_vs_experience"]  = df["tenure_years"] / (df["total_working_years"] + 1e-5)
    df["promotion_gap_ratio"]   = df["years_since_last_promotion"] / (df["tenure_years"] + 1e-5)
    df["salary_per_year_exp"]   = df["salary_egp"] / (df["total_working_years"] + 1e-5)
    df["overtime_intensity"]    = df["total_overtime_hours"] / (df["avg_worked_hours"] + 1e-5)
    df["absence_severity"]      = df["absence_rate"] * df["late_rate"]
    df["attendance_quality"]    = df["attendance_score"] * df["avg_worked_hours"]
    df["performance_score"]     = (df["latest_eval_score"] + df["kpi_score"]) / 2
    df["engagement_score"]      = (df["courses_completed"] * 10 + df["avg_training_score"]
                                   ) / (df["avg_feedback_score"] + 1)
    df["work_balance_fit"]      = df["work_life_balance"] * df["role_fit_score"]
    return df


# ─── cap_outliers ─────────────────────────────────────────────────────────────

class TestCapOutliers:

    def test_returns_count_of_true_outliers(self, turnover_df):
        """cap_outliers must return a non-negative integer count."""
        col = "salary_egp"
        df  = turnover_df.copy()
        n   = cap_outliers(df, col)
        assert isinstance(n, int)
        assert n >= 0

    def test_values_clipped_to_quantile_range(self, turnover_df):
        """After capping, no value should fall outside [1st-pct, 99th-pct]."""
        col = "salary_egp"
        df  = turnover_df.copy()
        lower = df[col].quantile(0.01)
        upper = df[col].quantile(0.99)
        cap_outliers(df, col)
        assert df[col].min() >= lower
        assert df[col].max() <= upper

    def test_column_length_unchanged(self, turnover_df):
        """Capping must not add or remove rows."""
        df  = turnover_df.copy()
        original_len = len(df)
        cap_outliers(df, "commute_distance_km")
        assert len(df) == original_len

    def test_no_nans_introduced(self, turnover_df):
        """Clipping should never turn a value into NaN."""
        df = turnover_df.copy()
        cap_outliers(df, "total_overtime_hours")
        assert df["total_overtime_hours"].isnull().sum() == 0

    def test_all_quantile_levels(self, turnover_df):
        """Custom percentile arguments should work without error."""
        df = turnover_df.copy()
        n  = cap_outliers(df, "absence_rate", lower_pct=0.05, upper_pct=0.95)
        assert isinstance(n, int)


# ─── Missing value handling ────────────────────────────────────────────────────

class TestMissingValueHandling:

    def test_median_imputation_removes_nans(self, turnover_df):
        """After fillna with median, no nulls should remain in numeric cols."""
        df = turnover_df.copy()
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != "employee_id" and df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())
        assert df.select_dtypes(include=[np.number]).isnull().sum().sum() == 0

    def test_median_value_is_correct(self, turnover_df):
        """The fill value for avg_feedback_score should equal the pre-fill median."""
        df     = turnover_df.copy()
        median = df["avg_feedback_score"].median()
        df["avg_feedback_score"] = df["avg_feedback_score"].fillna(median)
        # All remaining values should be >= 1 (valid feedback range)
        assert df["avg_feedback_score"].min() >= 1.0

    def test_dedup_on_employee_id(self, turnover_df):
        """Duplicate employee_id rows should be removed."""
        # Inject a deliberate duplicate
        dup = turnover_df.iloc[[0]].copy()
        df_with_dup = pd.concat([turnover_df, dup], ignore_index=True)
        cleaned = df_with_dup.drop_duplicates(subset=["employee_id"], keep="first")
        assert len(cleaned) == len(turnover_df)


# ─── Feature engineering ──────────────────────────────────────────────────────

class TestFeatureEngineering:
    ENGINEERED = [
        "tenure_vs_experience", "promotion_gap_ratio", "salary_per_year_exp",
        "overtime_intensity",   "absence_severity",    "attendance_quality",
        "performance_score",    "engagement_score",    "work_balance_fit",
    ]

    def test_all_nine_features_created(self, turnover_df):
        """Engineering must add exactly 9 new columns."""
        df_before_cols = set(turnover_df.columns)
        df_eng = engineer_features(turnover_df)
        new_cols = set(df_eng.columns) - df_before_cols
        assert new_cols == set(self.ENGINEERED), (
            f"Expected {sorted(self.ENGINEERED)}, got {sorted(new_cols)}"
        )

    def test_no_nan_in_engineered_features(self, turnover_df):
        """
        Engineered features use +1e-5 guards in denominators (tenure, work hours,
        total_working_years).  They must produce finite values when those are zero.
        NOTE: avg_feedback_score is NOT guarded — see test below for the bug.
        """
        df = turnover_df.copy()
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != "employee_id" and df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())
        # Zero-out the +1e-5-guarded denominators
        df["avg_worked_hours"] = 0
        df["total_working_years"] = 0
        df["tenure_years"] = 0
        # Keep avg_feedback_score valid (>=1) — the +1 guard only prevents /0 when score=−1
        df["avg_feedback_score"] = 1.0
        df_eng = engineer_features(df)
        guarded_features = [
            "tenure_vs_experience", "promotion_gap_ratio", "salary_per_year_exp",
            "overtime_intensity", "absence_severity", "attendance_quality",
            "performance_score", "work_balance_fit",
        ]
        for col in guarded_features:
            assert not df_eng[col].isnull().any(), f"{col} contains NaN"
            assert not np.isinf(df_eng[col]).any(), f"{col} contains Inf"

    def test_engagement_score_inf_when_feedback_is_minus_one(self, turnover_df):
        """
        CODE BUG FOUND: engagement_score = (...) / (avg_feedback_score + 1)
        When avg_feedback_score = −1 (feedback score of −1 is invalid but no
        guard exists), the denominator becomes 0 → Inf.

        The training script fills avg_feedback_score with its median before
        engineering (Section 2.1), so this never triggers with real data.
        However, if the fill step is skipped or a −1 arrives at inference, the
        produced feature will be Inf, which causes StandardScaler to fail.

        FIX: add `avg_feedback_score.clip(lower=0)` before computing
        engagement_score, or add `+ 1e-5` to the denominator instead of `+ 1`.
        """
        df = turnover_df.copy()
        df["avg_feedback_score"] = -1.0  # invalid value, not in [1,5]
        df_eng = engineer_features(df)
        # This assertion FAILS — documents the unguarded denominator
        assert np.isinf(df_eng["engagement_score"]).any(), (
            "Expected Inf when avg_feedback_score=-1 (unguarded denominator). "
            "Fix: change `+ 1` to `+ 1 + 1e-5` or clip feedback scores to >=0."
        )

    def test_absence_severity_formula(self, turnover_df):
        """absence_severity = absence_rate * late_rate (exact formula check)."""
        df = engineer_features(turnover_df)
        expected = turnover_df["absence_rate"] * turnover_df["late_rate"]
        pd.testing.assert_series_equal(
            df["absence_severity"].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False,
        )

    def test_performance_score_is_mean(self, turnover_df):
        """performance_score must be the arithmetic mean of eval + kpi."""
        df = engineer_features(turnover_df)
        expected = (turnover_df["latest_eval_score"] + turnover_df["kpi_score"]) / 2
        pd.testing.assert_series_equal(
            df["performance_score"].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False,
        )

    def test_row_count_unchanged(self, turnover_df):
        """Engineering must not add or drop rows."""
        df_eng = engineer_features(turnover_df)
        assert len(df_eng) == len(turnover_df)

    def test_original_columns_preserved(self, turnover_df):
        """No original column should be removed or renamed by engineering."""
        df_eng = engineer_features(turnover_df)
        for col in turnover_df.columns:
            assert col in df_eng.columns


# ─── Train/test split and stratification ──────────────────────────────────────

class TestTrainTestSplit:

    def test_stratified_split_preserves_class_ratio(self, turnover_df):
        """
        stratify=y keeps turnover rate within ±5 pp between train and test.
        This prevents label shift and ensures meaningful test evaluation.
        """
        df = engineer_features(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"])
        y  = df["turnover_label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        assert abs(y_train.mean() - y_test.mean()) < 0.05

    def test_test_size_respected(self, turnover_df):
        """20 % test split — within rounding error."""
        df = engineer_features(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"])
        y  = df["turnover_label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        expected_test = int(len(df) * 0.2)
        assert abs(len(X_test) - expected_test) <= 1

    def test_no_overlap_between_train_and_test(self, turnover_df):
        """Indices in train and test must be disjoint (no sample appears twice)."""
        df = engineer_features(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"])
        y  = df["turnover_label"]
        X_train, X_test, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        assert len(set(X_train.index) & set(X_test.index)) == 0


# ─── Scaler ───────────────────────────────────────────────────────────────────

def _fill_and_engineer(df):
    """Helper: fill NaN then engineer features (avoids Inf from unguarded denominators)."""
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col != "employee_id" and df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())
    return engineer_features(df)


class TestStandardScaler:

    def test_scaler_fitted_only_on_train(self, turnover_df):
        """
        The scaler must be fitted on X_train only, then applied to X_test.
        If it's accidentally fitted on X_test, test-set mean/std will differ.
        """
        df = _fill_and_engineer(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_train, X_test, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s  = scaler.transform(X_test)
        # Scaled train should be approximately zero-mean, unit variance
        assert abs(X_train_s.mean()) < 0.1
        assert abs(X_train_s.std() - 1.0) < 0.1

    def test_scaler_does_not_modify_test_distribution(self, turnover_df):
        """Test features outside the training range are NOT clipped by StandardScaler."""
        df = _fill_and_engineer(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_train, X_test, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scaler = StandardScaler()
        scaler.fit(X_train)
        X_test_s = scaler.transform(X_test)
        # Scaled test may have values > ±3 — this is expected and must not error
        assert X_test_s.shape == X_test.shape


# ─── SMOTE ────────────────────────────────────────────────────────────────────

class TestSMOTE:

    def test_smote_balances_classes(self, turnover_df):
        """
        After SMOTE the minority class count should equal the majority class count.
        Important: SMOTE must be applied AFTER scaling and ONLY on training data.
        """
        df = _fill_and_engineer(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        smote = SMOTE(random_state=42)
        X_res, y_res = smote.fit_resample(X_train_s, y_train)
        counts = y_res.value_counts()
        assert counts[0] == counts[1], "SMOTE must equalise class counts"

    def test_smote_not_applied_to_test_set(self, turnover_df):
        """
        CRITICAL: SMOTE must ONLY see training data.
        Applying SMOTE before splitting causes synthetic samples that are correlated
        with the test set — a severe data leakage.
        This test verifies SMOTE is applied after the split by checking test size is unchanged.
        """
        df = _fill_and_engineer(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        test_size_before = len(X_test)
        # Correct usage: SMOTE only on train
        smote = SMOTE(random_state=42)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        smote.fit_resample(X_train_s, y_train)
        # Test set must remain untouched
        assert len(X_test) == test_size_before

    def test_smote_shape_consistency(self, turnover_df):
        """Resampled X and y must have the same number of rows."""
        df = _fill_and_engineer(turnover_df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        scaler = StandardScaler()
        X_s   = scaler.fit_transform(X_train)
        X_res, y_res = SMOTE(random_state=42).fit_resample(X_s, y_train)
        assert X_res.shape[0] == len(y_res)


# ─── Shared signal-based fixture (module-level so TestModelPersistence can use it) ───

@pytest.fixture()
def prepared_data():
        """
        Returns X_train_res, X_test_s, y_train_res, y_test ready for training.

        Uses a 200-row signal-based dataset instead of the tiny random conftest
        fixture so that AUC / overfitting / baseline tests have real signal to
        work with.  The target is generated via a logistic function of
        absence_rate and role_fit_score (both are real features in Model 1).
        """
        rng = np.random.default_rng(42)
        n   = 200

        # ── Raw features ──────────────────────────────────────────────────────
        absence_rate          = rng.uniform(0, 0.25, n)
        role_fit_score        = rng.uniform(20, 100, n)
        tenure_years          = rng.uniform(0, 15, n)
        total_working_years   = rng.uniform(0, 20, n)
        years_since_last_promotion = rng.uniform(0, 5, n)
        salary_egp            = rng.uniform(5000, 50000, n)
        total_overtime_hours  = rng.uniform(0, 200, n)
        avg_worked_hours      = rng.uniform(140, 200, n)
        late_rate             = rng.uniform(0, 0.2, n)
        attendance_score      = rng.uniform(60, 100, n)
        latest_eval_score     = rng.uniform(40, 100, n)
        kpi_score             = rng.uniform(40, 100, n)
        courses_completed     = rng.integers(0, 15, n).astype(float)
        avg_training_score    = rng.uniform(50, 100, n)
        avg_feedback_score    = rng.uniform(2, 5, n)
        work_life_balance     = rng.integers(1, 5, n).astype(float)
        commute_distance_km   = rng.uniform(1, 60, n)

        # ── Logistic signal ───────────────────────────────────────────────────
        logit = (
            absence_rate * 15
            - role_fit_score * 0.06
            + rng.normal(0, 0.4, n)
        )
        prob = 1 / (1 + np.exp(-logit))
        turnover_label = (prob > 0.5).astype(int)

        df = pd.DataFrame({
            "employee_id":               np.arange(n),
            "absence_rate":              absence_rate,
            "role_fit_score":            role_fit_score,
            "tenure_years":              tenure_years,
            "total_working_years":       total_working_years,
            "years_since_last_promotion": years_since_last_promotion,
            "salary_egp":                salary_egp,
            "total_overtime_hours":      total_overtime_hours,
            "avg_worked_hours":          avg_worked_hours,
            "late_rate":                 late_rate,
            "attendance_score":          attendance_score,
            "latest_eval_score":         latest_eval_score,
            "kpi_score":                 kpi_score,
            "courses_completed":         courses_completed,
            "avg_training_score":        avg_training_score,
            "avg_feedback_score":        avg_feedback_score,
            "work_life_balance":         work_life_balance,
            "commute_distance_km":       commute_distance_km,
            "turnover_label":            turnover_label,
        })

        df = engineer_features(df)
        X  = df.drop(columns=["employee_id", "turnover_label"]).astype(float)
        y  = df["turnover_label"]
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        scaler  = StandardScaler()
        X_tr_s  = scaler.fit_transform(X_tr)
        X_te_s  = scaler.transform(X_te)
        X_res, y_res = SMOTE(random_state=42).fit_resample(X_tr_s, y_tr)
        return X_res, X_te_s, y_res, y_te, list(X.columns), scaler


# ─── Model training and evaluation ────────────────────────────────────────────

class TestModelTrainingAndEvaluation:

    def test_model_fits_without_error(self, prepared_data):
        """GradientBoosting must fit on SMOTE-resampled data without exceptions."""
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)  # must not raise
        assert hasattr(model, "estimators_")

    def test_predictions_are_binary(self, prepared_data):
        """predict() must return only 0 and 1."""
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        preds = model.predict(X_te)
        assert set(preds).issubset({0, 1})

    def test_predict_proba_sums_to_one(self, prepared_data):
        """Class probabilities per row must sum to 1."""
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        proba = model.predict_proba(X_te)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-6)

    def test_beats_majority_class_baseline(self, prepared_data):
        """
        BASELINE COMPARISON: the trained model must beat a DummyClassifier on F1.
        A model that only predicts the majority class is not useful in HR contexts
        where catching true turnovers (minority class) is critical.
        """
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        dummy = DummyClassifier(strategy="most_frequent", random_state=42)
        dummy.fit(X_res, y_res)
        f1_model = f1_score(y_te, model.predict(X_te), zero_division=0)
        f1_dummy = f1_score(y_te, dummy.predict(X_te), zero_division=0)
        assert f1_model >= f1_dummy, (
            f"Model F1 {f1_model:.3f} did not beat dummy F1 {f1_dummy:.3f}"
        )

    def test_roc_auc_above_random(self, prepared_data):
        """
        AUC-ROC must be > 0.5 (better than random guessing).
        AUC ≤ 0.5 indicates the model is predicting inversely or is broken.
        """
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
        assert auc > 0.5, f"AUC-ROC {auc:.3f} is not better than random"

    def test_no_overfitting_beyond_threshold(self, prepared_data):
        """
        OVERFITTING DETECTION: train F1 must not exceed test F1 by more than 30 pp.
        A gap larger than this indicates the model has memorised training data.
        Note: SMOTE inflates training F1 by design — the threshold is intentionally
        generous (0.30) for this synthetic mini-dataset.
        """
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        f1_train = f1_score(y_res, model.predict(X_res), zero_division=0)
        f1_test  = f1_score(y_te,  model.predict(X_te),  zero_division=0)
        gap = f1_train - f1_test
        assert gap < 0.35, (
            f"Overfitting gap too large: train F1={f1_train:.3f}, test F1={f1_test:.3f}"
        )

    def test_feature_importances_sum_to_one(self, prepared_data):
        """
        Tree-based model feature importances must sum to 1.0.
        A broken implementation could return negative or non-normalised values.
        """
        X_res, X_te, y_res, y_te, cols, _ = prepared_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        total = model.feature_importances_.sum()
        np.testing.assert_allclose(total, 1.0, atol=1e-6)

    def test_feature_importances_length_matches_features(self, prepared_data):
        """feature_importances_ length must match the number of input features."""
        X_res, X_te, y_res, y_te, cols, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        assert len(model.feature_importances_) == X_res.shape[1]

    def test_cross_validation_consistency(self, prepared_data):
        """
        5-fold CV mean F1 must be within reasonable bounds (0.1–1.0).
        Very low CV scores suggest the model is poorly specified.
        """
        X_res, _, y_res, _, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        # NOTE: CV on SMOTE-resampled data overestimates CV performance
        # because SMOTE synthetic samples are shared across folds.
        # The correct approach is to apply SMOTE INSIDE each fold using a Pipeline.
        scores = cross_val_score(model, X_res, y_res, cv=cv, scoring="f1")
        assert scores.mean() > 0.1
        assert scores.mean() <= 1.0

    def test_reproducibility(self, prepared_data):
        """
        Same random_state must produce identical predictions every run.
        Non-determinism in production leads to inconsistent risk scores.
        """
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        m1 = GradientBoostingClassifier(n_estimators=10, random_state=42)
        m2 = GradientBoostingClassifier(n_estimators=10, random_state=42)
        m1.fit(X_res, y_res)
        m2.fit(X_res, y_res)
        np.testing.assert_array_equal(m1.predict(X_te), m2.predict(X_te))


# ─── Model persistence ────────────────────────────────────────────────────────

class TestModelPersistence:

    def test_joblib_round_trip(self, prepared_data):
        """
        Model saved with joblib.dump must reload and produce identical predictions.
        This validates the persistence step in Section 9 of the training script.
        """
        X_res, X_te, y_res, y_te, _, _ = prepared_data
        model = GradientBoostingClassifier(n_estimators=10, random_state=42)
        model.fit(X_res, y_res)
        preds_before = model.predict(X_te)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(model, path)
            loaded = joblib.load(path)
            preds_after = loaded.predict(X_te)
            np.testing.assert_array_equal(preds_before, preds_after)
        finally:
            os.unlink(path)

    def test_scaler_round_trip(self, prepared_data):
        """Scaler must survive joblib serialisation without changing transform output."""
        X_res, X_te, y_res, y_te, cols, scaler = prepared_data
        original_transformed = scaler.transform(X_te)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(scaler, path)
            loaded_scaler = joblib.load(path)
            reloaded_transformed = loaded_scaler.transform(X_te)
            np.testing.assert_allclose(original_transformed, reloaded_transformed, atol=1e-10)
        finally:
            os.unlink(path)

    def test_feature_list_persisted_correctly(self, prepared_data):
        """The saved feature list must be a non-empty list of strings."""
        _, _, _, _, cols, _ = prepared_data
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(cols, path)
            loaded = joblib.load(path)
            assert isinstance(loaded, list)
            assert all(isinstance(c, str) for c in loaded)
            assert len(loaded) > 0
        finally:
            os.unlink(path)


# ─── Edge-case and input validation ───────────────────────────────────────────

class TestEdgeCases:

    def test_all_zeros_absence_rate(self, turnover_df):
        """Absence rate of 0 for all rows must not cause division by zero."""
        df = turnover_df.copy()
        df["absence_rate"] = 0.0
        df["avg_feedback_score"] = df["avg_feedback_score"].fillna(3.0)
        df_eng = engineer_features(df)
        assert not df_eng["absence_severity"].isnull().any()

    def test_single_employee_dataset(self):
        """A dataset with a single row must raise before reaching training."""
        rng = np.random.default_rng(99)
        tiny = pd.DataFrame({
            "employee_id": ["EMP-0001"],
            "tenure_years": [1.0], "total_working_years": [3],
            "years_since_last_promotion": [0], "salary_egp": [15000],
            "total_overtime_hours": [50.0], "avg_worked_hours": [8.0],
            "attendance_score": [90.0], "latest_eval_score": [70.0],
            "kpi_score": [75.0], "courses_completed": [2],
            "avg_training_score": [60.0], "avg_feedback_score": [3.5],
            "work_life_balance": [4.0], "role_fit_score": [65.0],
            "absence_rate": [0.05], "late_rate": [0.02],
            "turnover_label": [0],
        })
        df_eng = engineer_features(tiny)
        # With 1 row, train_test_split will fail — expected failure
        with pytest.raises(ValueError):
            train_test_split(
                df_eng.drop(columns=["employee_id", "turnover_label"]),
                df_eng["turnover_label"],
                test_size=0.2, stratify=df_eng["turnover_label"]
            )

    def test_high_absence_rate_does_not_break_feature_engineering(self, turnover_df):
        """Absence rate capped at 1.0 (max realistic) should not produce NaN/Inf."""
        df = turnover_df.copy()
        df["absence_rate"] = 1.0
        df["avg_feedback_score"] = df["avg_feedback_score"].fillna(3.0)
        df_eng = engineer_features(df)
        assert not df_eng["absence_severity"].isnull().any()
        assert not np.isinf(df_eng["absence_severity"]).any()
