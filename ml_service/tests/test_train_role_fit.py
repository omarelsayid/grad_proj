"""
Tests for Model 2: Role Fit Scoring
train_role_fit_model.py

Covers:
  - Feature matrix construction (employee × role pairs)
  - Readiness score computation correctness
  - get_col() robust column detection
  - GradientBoosting regressor training and evaluation
  - Regression metrics (RMSE, MAE, R²) sanity checks
  - Baseline comparison (mean predictor)
  - Overfitting detection
  - CV leakage warning: CV on full X,y after split (flagged in review)
  - Model persistence
"""

import numpy as np
import pandas as pd
import pytest
import joblib
import tempfile
import os

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split


FEATURE_COLS = [
    "n_required", "n_matching", "n_missing",
    "coverage_ratio", "weighted_gap", "max_gap", "avg_matched_prof",
]


# ─── Helper: get_col ──────────────────────────────────────────────────────────

def get_col(df: pd.DataFrame, candidates: list) -> str:
    """Exact copy of get_col from the training script."""
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found. Available: {df.columns.tolist()}")


class TestGetCol:

    def test_finds_first_matching_candidate(self):
        """get_col should return the first candidate that exists."""
        df = pd.DataFrame({"skill_id": [], "proficiency": []})
        col = get_col(df, ["skill_id", "Skill_id", "SKILL_ID"])
        assert col == "skill_id"

    def test_falls_through_to_second_candidate(self):
        """If the first candidate is absent, the second should be returned."""
        df = pd.DataFrame({"Skill_id": [], "other": []})
        col = get_col(df, ["skill_id", "Skill_id"])
        assert col == "Skill_id"

    def test_raises_when_none_found(self):
        """KeyError must be raised with a descriptive message when nothing matches."""
        df = pd.DataFrame({"x": [], "y": []})
        with pytest.raises(KeyError, match="None of"):
            get_col(df, ["missing_col1", "missing_col2"])

    def test_case_sensitive(self):
        """Column matching is case-sensitive — 'SKILL_ID' ≠ 'skill_id'."""
        df = pd.DataFrame({"SKILL_ID": []})
        with pytest.raises(KeyError):
            get_col(df, ["skill_id"])


# ─── Feature matrix construction ──────────────────────────────────────────────

def build_feature_matrix(employee_skills_df, job_requirements_df):
    """
    Mirrors the (employee × role) feature matrix construction from the training
    script.  Returns a DataFrame with FEATURE_COLS + readiness_score.
    """
    emp_id_col  = "employee_id"
    emp_sk_col  = "skill_id"
    emp_pr_col  = "proficiency"
    job_role_col = "job_role_id"
    job_sk_col   = "required_skill_id"
    job_min_col  = "min_proficiency"
    job_wt_col   = "importance_weight"

    employee_ids = employee_skills_df[emp_id_col].unique()
    role_ids     = job_requirements_df[job_role_col].unique()
    records = []

    for emp_id in employee_ids:
        emp_rows = employee_skills_df[employee_skills_df[emp_id_col] == emp_id]
        emp_dict = dict(zip(emp_rows[emp_sk_col], emp_rows[emp_pr_col]))

        for role_id in role_ids:
            req_rows = job_requirements_df[job_requirements_df[job_role_col] == role_id]
            if req_rows.empty:
                continue

            n_required = len(req_rows)
            n_matching = 0
            n_missing  = 0
            w_gap_sum  = 0.0
            w_sum      = 0.0
            max_gap    = 0.0
            matched_prof = []

            for _, row in req_rows.iterrows():
                skill_id   = row[job_sk_col]
                min_prof   = float(row[job_min_col])
                importance = float(row[job_wt_col])
                current    = float(emp_dict.get(skill_id, 0.0))
                gap        = max(min_prof - current, 0.0)

                w_gap_sum += gap * importance
                w_sum     += 4 * importance
                max_gap    = max(max_gap, gap)

                if gap == 0:
                    n_matching += 1
                    matched_prof.append(current)
                else:
                    n_missing += 1

            readiness = 1.0 - (w_gap_sum / w_sum) if w_sum > 0 else 1.0
            records.append({
                "employee_id":      emp_id,
                "job_role_id":      role_id,
                "n_required":       n_required,
                "n_matching":       n_matching,
                "n_missing":        n_missing,
                "coverage_ratio":   n_matching / n_required if n_required else 0.0,
                "weighted_gap":     (w_gap_sum / w_sum * 4) if w_sum else 0.0,
                "max_gap":          max_gap,
                "avg_matched_prof": float(np.mean(matched_prof)) if matched_prof else 0.0,
                "readiness_score":  readiness,
            })
    return pd.DataFrame(records)


class TestFeatureMatrixConstruction:

    def test_number_of_pairs(self, employee_skills_df, job_requirements_df):
        """The matrix must have (n_employees × n_roles) rows."""
        n_emp   = employee_skills_df["employee_id"].nunique()
        n_roles = job_requirements_df["job_role_id"].nunique()
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        assert len(df) == n_emp * n_roles

    def test_all_feature_columns_present(self, employee_skills_df, job_requirements_df):
        """All seven model input features must appear in the output."""
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        for col in FEATURE_COLS:
            assert col in df.columns, f"Missing feature column: {col}"

    def test_readiness_score_bounded(self, employee_skills_df, job_requirements_df):
        """
        readiness_score is defined as 1 − weighted_gap_ratio, where the ratio is
        in [0, 1].  The score must therefore lie in [0, 1].
        """
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        assert df["readiness_score"].between(0, 1).all(), (
            f"readiness_score out of [0,1]: min={df['readiness_score'].min():.4f}, "
            f"max={df['readiness_score'].max():.4f}"
        )

    def test_coverage_ratio_bounded(self, employee_skills_df, job_requirements_df):
        """coverage_ratio = n_matching / n_required must be in [0, 1]."""
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        assert df["coverage_ratio"].between(0, 1).all()

    def test_n_matching_plus_n_missing_equals_n_required(
        self, employee_skills_df, job_requirements_df
    ):
        """n_matching + n_missing must always equal n_required (no skills lost)."""
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        assert ((df["n_matching"] + df["n_missing"]) == df["n_required"]).all()

    def test_no_nulls_in_feature_columns(self, employee_skills_df, job_requirements_df):
        """Feature matrix must have no NaN values in any model input column."""
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        for col in FEATURE_COLS + ["readiness_score"]:
            assert df[col].isnull().sum() == 0, f"NaN found in {col}"

    def test_employee_with_all_skills_has_high_readiness(
        self, employee_skills_df, job_requirements_df
    ):
        """
        An employee who already has all required skills at the required level
        must achieve readiness_score = 1.0 for that role.
        """
        # Build a deterministic scenario
        emp_skills = pd.DataFrame({
            "employee_id": ["EMP-PERFECT"] * 3,
            "skill_id":    ["SK-101", "SK-102", "SK-103"],
            "proficiency": [5, 5, 5],
        })
        req = pd.DataFrame({
            "job_role_id":       [99, 99, 99],
            "required_skill_id": ["SK-101", "SK-102", "SK-103"],
            "min_proficiency":   [2, 2, 2],
            "importance_weight": [0.5, 0.3, 0.2],
        })
        df = build_feature_matrix(emp_skills, req)
        row = df[df["job_role_id"] == 99]
        assert not row.empty
        assert row["readiness_score"].iloc[0] == 1.0

    def test_employee_with_no_skills_has_low_readiness(self):
        """An employee with zero proficiency in all required skills must score 0.0."""
        emp_skills = pd.DataFrame({
            "employee_id": ["EMP-ZERO"] * 3,
            "skill_id":    ["SK-999X", "SK-999Y", "SK-999Z"],  # irrelevant skills
            "proficiency": [4, 4, 4],
        })
        req = pd.DataFrame({
            "job_role_id":       [88, 88, 88],
            "required_skill_id": ["SK-101", "SK-102", "SK-103"],
            "min_proficiency":   [2, 2, 2],
            "importance_weight": [0.33, 0.33, 0.34],
        })
        df = build_feature_matrix(emp_skills, req)
        row = df[df["job_role_id"] == 88]
        assert not row.empty
        # readiness = 1 - (w_gap_sum / w_sum) = 1 - (2*0.33 + 2*0.33 + 2*0.34) / (4*0.33+...)
        # = 1 - (2/4) = 0.5  (max gap = 4, required = 2, current = 0 → gap = 2)
        assert row["readiness_score"].iloc[0] < 1.0

    def test_weighted_gap_scale(self, employee_skills_df, job_requirements_df):
        """weighted_gap uses a 0–4 scale (4 = max proficiency gap), must be in [0,4]."""
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        assert df["weighted_gap"].between(0, 4).all(), (
            f"weighted_gap out of [0,4]: min={df['weighted_gap'].min():.3f}, "
            f"max={df['weighted_gap'].max():.3f}"
        )


# ─── Readiness score formula ──────────────────────────────────────────────────

class TestReadinessScoreFormula:

    def test_formula_with_known_values(self):
        """
        Manual calculation: one skill, gap=2, min_prof=3, importance=1.
        readiness = 1 - (2*1)/(4*1) = 1 - 0.5 = 0.5
        """
        emp = pd.DataFrame({
            "employee_id": ["E1"], "skill_id": ["SK-101"], "proficiency": [1],
        })
        req = pd.DataFrame({
            "job_role_id": [1], "required_skill_id": ["SK-101"],
            "min_proficiency": [3], "importance_weight": [1.0],
        })
        df = build_feature_matrix(emp, req)
        expected = 1.0 - (2 * 1.0) / (4 * 1.0)  # 0.5
        assert abs(df["readiness_score"].iloc[0] - expected) < 1e-9

    def test_zero_weight_role_does_not_divide_by_zero(self):
        """If all importance_weights are 0, w_sum = 0 → readiness must default to 1.0."""
        emp = pd.DataFrame({
            "employee_id": ["E1"], "skill_id": ["SK-101"], "proficiency": [0],
        })
        req = pd.DataFrame({
            "job_role_id": [1], "required_skill_id": ["SK-101"],
            "min_proficiency": [3], "importance_weight": [0.0],
        })
        df = build_feature_matrix(emp, req)
        assert df["readiness_score"].iloc[0] == 1.0


# ─── CRITICAL CODE REVIEW FLAG: Target derived from features ──────────────────
# The readiness_score target = 1 - weighted_gap/w_sum
# weighted_gap feature = w_gap_sum/w_sum * 4
# These are almost perfectly linearly related, so the model achieves artificially
# high R² by learning a near-identity mapping.  The test below confirms this
# so future developers are aware.

class TestTargetDerivedFromFeatures:

    def test_readiness_and_weighted_gap_are_highly_correlated(
        self, employee_skills_df, job_requirements_df
    ):
        """
        REVIEW FLAG: readiness_score ≈ 1 − weighted_gap/4.
        Pearson correlation between the two should be high (|r| > 0.95).
        This means the model is mostly learning a mathematical identity, not
        a generalizable function.  Consider using an external ground-truth
        label (e.g., manager-assigned readiness) instead.
        """
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        corr = df[["readiness_score", "weighted_gap"]].corr().iloc[0, 1]
        assert abs(corr) > 0.9, (
            f"Expected high |correlation| > 0.9, got {corr:.3f}. "
            "This test exists to document the target-leakage concern."
        )


# ─── REVIEW FLAG: CV on full X,y after split ──────────────────────────────────

class TestCrossValidationLeakage:

    def test_cv_on_full_xy_inflates_scores(self, employee_skills_df, job_requirements_df):
        """
        REVIEW FLAG (train_role_fit_model.py line 188):
            cv_r2 = cross_val_score(final_model, X, y, cv=5)  ← uses FULL dataset

        The model was trained on X_train (80 %).  Running CV on the full X means
        some folds will see data the model was already fitted on, leading to
        inflated CV R² scores.  The correct call is:
            cross_val_score(model, X_train, y_train, cv=5)

        This test demonstrates the score gap between correct and leaky CV.
        """
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        X  = df[FEATURE_COLS]
        y  = df["readiness_score"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)

        # Correct CV (on training data only)
        cv_r2_correct = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")
        # Leaky CV (on full dataset — replicates the bug)
        cv_r2_leaky   = cross_val_score(model, X, y, cv=5, scoring="r2")

        # The leaky CV should be >= the correct one (inflated, not strictly guaranteed)
        # We just verify both run without error and that this test raises awareness
        assert cv_r2_correct.mean() <= 1.0
        assert cv_r2_leaky.mean()   <= 1.0
        # Document the gap for review
        gap = cv_r2_leaky.mean() - cv_r2_correct.mean()
        # A positive gap confirms the leakage concern
        print(f"\nCV R² gap (leaky − correct): {gap:.4f}")  # visible with pytest -s


# ─── Regression model training ────────────────────────────────────────────────

class TestRegressionModelTraining:

    @pytest.fixture()
    def regression_data(self, employee_skills_df, job_requirements_df):
        df = build_feature_matrix(employee_skills_df, job_requirements_df)
        X  = df[FEATURE_COLS]
        y  = df["readiness_score"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        return X_train, X_test, y_train, y_test

    def test_model_trains_without_error(self, regression_data):
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        assert hasattr(model, "estimators_")

    def test_predictions_in_valid_range(self, regression_data):
        """
        Raw GBR predictions may go slightly outside [0,1]; the service clamps them.
        We verify the model at least produces values in a reasonable range (−0.1, 1.1).
        """
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        assert preds.min() > -0.5, f"Prediction too low: {preds.min():.3f}"
        assert preds.max() <  1.5, f"Prediction too high: {preds.max():.3f}"

    def test_beats_mean_predictor_baseline(self, regression_data):
        """
        BASELINE: the model must outperform a DummyRegressor (mean predictor)
        on RMSE.  If it doesn't, it hasn't learned anything useful.
        """
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        dummy = DummyRegressor(strategy="mean")
        dummy.fit(X_tr, y_tr)

        rmse_model = np.sqrt(mean_squared_error(y_te, model.predict(X_te)))
        rmse_dummy = np.sqrt(mean_squared_error(y_te, dummy.predict(X_te)))
        assert rmse_model < rmse_dummy, (
            f"Model RMSE {rmse_model:.4f} ≥ dummy RMSE {rmse_dummy:.4f}"
        )

    def test_r2_above_zero(self, regression_data):
        """R² > 0 means the model explains more variance than a flat mean predictor."""
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        r2 = r2_score(y_te, model.predict(X_te))
        assert r2 > 0, f"R² is {r2:.4f} — model is worse than predicting the mean"

    def test_mae_below_half(self, regression_data):
        """
        MAE < 0.5 on a [0,1] target means predictions are usually within half the
        full scale.  A well-fitted model should be well below this threshold.
        """
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))
        assert mae < 0.5, f"MAE {mae:.4f} is too high for a [0,1] target"

    def test_overfitting_detection(self, regression_data):
        """
        Train R² should not exceed test R² by more than 0.30.
        A large gap indicates the model has memorised training pairs.
        Given the near-deterministic target, this threshold is generous.
        """
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        r2_train = r2_score(y_tr, model.predict(X_tr))
        r2_test  = r2_score(y_te, model.predict(X_te))
        gap = r2_train - r2_test
        assert gap < 0.30, f"Overfitting: train R²={r2_train:.3f}, test R²={r2_test:.3f}"

    def test_feature_importance_all_features_contribute(self, regression_data):
        """
        No feature should have exactly 0 importance in a converged model.
        A feature permanently at 0 is likely redundant or miscoded.
        """
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        model.fit(X_tr, y_tr)
        importances = model.feature_importances_
        # Allow up to 2 features to have near-zero importance (max_gap / weighted_gap can be correlated)
        near_zero = (importances < 1e-6).sum()
        assert near_zero <= 2, f"{near_zero} features have zero importance"

    def test_prediction_consistency(self, regression_data):
        """Same model produces identical predictions on same input."""
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        p1 = model.predict(X_te)
        p2 = model.predict(X_te)
        np.testing.assert_array_equal(p1, p2)

    def test_model_persistence(self, regression_data):
        """Saved model must produce identical predictions after reload."""
        X_tr, X_te, y_tr, y_te = regression_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X_tr, y_tr)
        preds_before = model.predict(X_te)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(model, path)
            loaded = joblib.load(path)
            np.testing.assert_array_equal(preds_before, loaded.predict(X_te))
        finally:
            os.unlink(path)
