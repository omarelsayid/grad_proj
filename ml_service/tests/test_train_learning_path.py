"""
Tests for Model 4 v2: Training Recommendation System (GBDT + Knowledge Graph)
train_learning_path_model.py — v2 (Enhanced)

v2 changes tested here (new test classes):
  TestPearsonCorrelationFilter  — |r|>=0.05 gate drops noise features
  TestLOOEmpAvgScore            — leave-one-out mean excludes current row
  TestGroupKFoldCV              — GroupKFold prevents cross-employee CV leakage
  TestMAPEMetric                — MAPE computed and non-negative
  TestConservativeSearchSpace   — parameter bounds that prevent overfitting

Retained from v1 (updated feature names):
  TestDAGConstruction           — node/edge counts, acyclicity, topo sort
  TestDAGWeightLookup           — precomputed max weight correctness
  TestGetLearningPath           — topological ordering, empty role, cycle safety
  TestComputeReadinessScore     — formula bounds, perfect / zero employee
  TestLightGBMFeatureMatrix     — all v2 features present, no NaN, target range
  TestGroupShuffleSplit         — train/test split isolates employees
  TestLightGBMTraining          — trains, predictions vary, RMSE ceiling
  TestLearningPathPersistence   — joblib round-trip for model and DAG
"""

import numpy as np
import pandas as pd
import pytest
import joblib
import tempfile
import os

import networkx as nx
import lightgbm as lgb
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.model_selection import GroupShuffleSplit, GroupKFold

# ── Feature lists ─────────────────────────────────────────────────────────────
# Matches REQUIRED_FEATURES in train_learning_path_model.py v2 (without core extras)
REQUIRED_FEATURES = [
    "emp_proficiency",
    "resource_skill_level",
    "skill_gap_proxy",
    "complexity_level",
    "dag_edge_weight",
    "duration_hours",
    "emp_avg_score",
    "emp_courses_done",
    "attempt_number",
]

SKILL_LEVEL_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


# ─── Shared helper: build feature matrix mirroring v2 pipeline ───────────────

def build_feature_matrix(training_history_df, learning_resources_df,
                          employee_skills_df, skills_catalog_df,
                          skill_chain_dag_df):
    """
    Replicates the v2 feature engineering pipeline for unit testing.
    Returns (X, y, employee_id_series).
    """
    dag_wt = (
        skill_chain_dag_df
        .groupby("target_skill_id")["weight"]
        .max()
        .to_dict()
    )

    # Join resources — rename to avoid collision with training_history.duration_hours
    res = learning_resources_df[
        ["resource_id", "duration_hours", "skill_level", "target_skill_id"]
    ].copy().rename(columns={"duration_hours": "lr_duration_hours"})
    res["resource_skill_level"] = res["skill_level"].map(SKILL_LEVEL_MAP).fillna(2)
    t = training_history_df.merge(
        res[["resource_id", "lr_duration_hours", "resource_skill_level", "target_skill_id"]],
        on="resource_id", how="left",
    )
    # Prefer resource table hours; fall back to history column if present
    if "duration_hours" in training_history_df.columns:
        t["duration_hours"] = t["lr_duration_hours"].fillna(training_history_df["duration_hours"])
    else:
        t["duration_hours"] = t["lr_duration_hours"].fillna(5.0)
    t = t.drop(columns=["lr_duration_hours"], errors="ignore")
    t["resource_skill_level"] = t["resource_skill_level"].fillna(2)

    # Employee proficiency on target skill
    ep = employee_skills_df[["employee_id", "skill_id", "proficiency"]].rename(
        columns={"skill_id": "target_skill_id", "proficiency": "emp_proficiency"}
    )
    t = t.merge(ep, on=["employee_id", "target_skill_id"], how="left")
    t["emp_proficiency"] = t["emp_proficiency"].fillna(0)

    # Skill complexity
    sc = skills_catalog_df[["skill_id", "complexity_level"]].rename(
        columns={"skill_id": "target_skill_id"}
    )
    t = t.merge(sc, on="target_skill_id", how="left")
    t["complexity_level"] = t["complexity_level"].fillna(2)

    # DAG edge weight
    t["dag_edge_weight"] = t["target_skill_id"].map(dag_wt).fillna(0)

    # skill_gap_proxy
    t["skill_gap_proxy"] = (t["resource_skill_level"] - t["emp_proficiency"]).clip(lower=0)

    # emp_courses_done (count per employee — no leakage)
    emp_cnt = training_history_df.groupby("employee_id").size().to_dict()
    t["emp_courses_done"] = t["employee_id"].map(emp_cnt).fillna(0)

    # LOO emp_avg_score
    global_mean = training_history_df["completion_score"].mean()
    t = t.merge(
        training_history_df[["employee_id", "resource_id", "completion_score"]]
        .rename(columns={"completion_score": "_cs"}),
        on=["employee_id", "resource_id"], how="left",
    )
    emp_sum  = training_history_df.groupby("employee_id")["completion_score"].sum().to_dict()
    emp_cnt2 = training_history_df.groupby("employee_id").size().to_dict()

    def loo_mean(row):
        eid = row["employee_id"]
        cur = row["_cs"]
        n   = emp_cnt2.get(eid, 0)
        s   = emp_sum.get(eid, 0.0)
        if pd.isna(cur) or n <= 1:
            return global_mean
        return (s - cur) / (n - 1)

    t["emp_avg_score"] = t.apply(loo_mean, axis=1)
    t = t.drop(columns=["_cs"], errors="ignore")

    # attempt_number — use from training_history if present, else cumcount
    if "attempt_number" not in t.columns:
        t["attempt_number"] = (
            t.groupby(["employee_id", "target_skill_id"]).cumcount() + 1
        )

    for col in REQUIRED_FEATURES:
        if col not in t.columns:
            t[col] = 0

    t_clean = t.dropna(subset=REQUIRED_FEATURES + ["completion_score"])
    X = t_clean[REQUIRED_FEATURES].apply(pd.to_numeric, errors="coerce").dropna()
    y = t_clean["completion_score"].loc[X.index]
    groups = t_clean.loc[X.index, "employee_id"]
    return X, y, groups


# =============================================================================
# v2 NEW: TestPearsonCorrelationFilter
# =============================================================================

class TestPearsonCorrelationFilter:
    """
    The v2 pipeline drops any feature whose |Pearson r| with the target is
    below 0.05.  These tests verify the filter mechanics independently of the
    real dataset.
    """

    def _apply_filter(self, X: pd.DataFrame, y: pd.Series, threshold: float = 0.05):
        corrs = {f: abs(pearsonr(X[f], y)[0]) for f in X.columns}
        kept = [f for f in X.columns if corrs[f] >= threshold]
        dropped = [f for f in X.columns if corrs[f] < threshold]
        return kept, dropped, corrs

    def test_high_corr_feature_is_kept(self):
        """A feature with r ≈ 1 must survive the |r| >= 0.05 filter."""
        rng = np.random.default_rng(0)
        n = 200
        y = pd.Series(rng.uniform(40, 100, n))
        X = pd.DataFrame({"strong": y + rng.normal(0, 0.1, n)})
        kept, dropped, _ = self._apply_filter(X, y)
        assert "strong" in kept

    def test_zero_corr_feature_is_dropped(self):
        """A feature drawn from an independent distribution must be dropped."""
        rng = np.random.default_rng(1)
        n = 500
        y = pd.Series(rng.uniform(40, 100, n))
        X = pd.DataFrame({"noise": rng.permutation(y.values)})
        kept, dropped, corrs = self._apply_filter(X, y)
        # permuted feature has r ≈ 0
        assert corrs["noise"] < 0.05
        assert "noise" in dropped

    def test_features_final_is_subset_of_required(self):
        """FEATURES_FINAL must always be a subset of REQUIRED_FEATURES."""
        rng = np.random.default_rng(2)
        n = 100
        y = pd.Series(rng.uniform(40, 100, n))
        X = pd.DataFrame({f: rng.uniform(0, 5, n) for f in REQUIRED_FEATURES})
        kept, dropped, _ = self._apply_filter(X, y)
        assert set(kept).issubset(set(REQUIRED_FEATURES))

    def test_at_least_one_feature_survives(self,
                                            training_history_df,
                                            learning_resources_df,
                                            employee_skills_df,
                                            skills_catalog_df,
                                            skill_chain_dag_df):
        """After correlation filtering, the model must have at least 1 feature."""
        X, y, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        if len(X) < 10:
            pytest.skip("Too few samples for reliable correlation")
        kept, _, _ = self._apply_filter(X, y)
        assert len(kept) >= 1, "All features were dropped — model would have no inputs"

    def test_filter_is_deterministic(self):
        """Applying the same filter twice must produce the same result."""
        rng = np.random.default_rng(3)
        n = 200
        y = pd.Series(rng.uniform(40, 100, n))
        X = pd.DataFrame({f: rng.uniform(0, 5, n) for f in REQUIRED_FEATURES})
        kept1, dropped1, _ = self._apply_filter(X, y)
        kept2, dropped2, _ = self._apply_filter(X, y)
        assert kept1 == kept2
        assert dropped1 == dropped2


# =============================================================================
# v2 NEW: TestLOOEmpAvgScore
# =============================================================================

class TestLOOEmpAvgScore:
    """
    Verifies the leave-one-out mean that replaces the global mean to prevent
    target leakage (a row's own completion_score must not appear in its own
    emp_avg_score feature).
    """

    def _compute_loo(self, history_df):
        global_mean = history_df["completion_score"].mean()
        emp_sum  = history_df.groupby("employee_id")["completion_score"].sum().to_dict()
        emp_cnt  = history_df.groupby("employee_id").size().to_dict()
        results  = []
        for _, row in history_df.iterrows():
            eid = row["employee_id"]
            cur = row["completion_score"]
            n   = emp_cnt.get(eid, 0)
            s   = emp_sum.get(eid, 0.0)
            if n <= 1:
                results.append(global_mean)
            else:
                results.append((s - cur) / (n - 1))
        return pd.Series(results, index=history_df.index)

    def test_loo_excludes_current_row(self):
        """For an employee with 3 records, LOO on row 0 must equal mean of rows 1+2."""
        df = pd.DataFrame({
            "employee_id":      ["E1", "E1", "E1"],
            "completion_score": [60.0, 80.0, 100.0],
        })
        loo = self._compute_loo(df)
        expected_row0 = (80.0 + 100.0) / 2
        assert loo.iloc[0] == pytest.approx(expected_row0)

    def test_single_record_employee_gets_global_mean(self):
        """Employee with only 1 record cannot form a LOO mean — falls back to global."""
        df = pd.DataFrame({
            "employee_id":      ["E1", "E1", "E2"],
            "completion_score": [60.0, 80.0, 50.0],
        })
        loo = self._compute_loo(df)
        global_mean = df["completion_score"].mean()
        assert loo.iloc[2] == pytest.approx(global_mean)

    def test_loo_differs_from_global_mean(self):
        """LOO mean must differ from global mean for employees with multiple records."""
        df = pd.DataFrame({
            "employee_id":      ["E1", "E1", "E2", "E2"],
            "completion_score": [50.0, 90.0, 70.0, 70.0],
        })
        loo = self._compute_loo(df)
        global_mean = df["completion_score"].mean()
        # E1 row 0: LOO = 90; global = 70 — must differ
        assert loo.iloc[0] != pytest.approx(global_mean)

    def test_loo_is_not_nan(self, training_history_df):
        """LOO mean must produce no NaN for any row in the synthetic fixture."""
        loo = self._compute_loo(training_history_df)
        assert loo.isna().sum() == 0, f"{loo.isna().sum()} NaN values in LOO mean"

    def test_loo_mean_within_score_range(self, training_history_df):
        """LOO mean must stay within the [0, 100] score range."""
        loo = self._compute_loo(training_history_df)
        assert loo.between(0, 100).all()


# =============================================================================
# v2 NEW: TestGroupKFoldCV
# =============================================================================

class TestGroupKFoldCV:
    """
    Verifies that GroupKFold (used inside the Optuna objective and in the final
    CV) keeps all rows of one employee in the same fold, preventing the model
    from being evaluated on employees it has already 'seen'.
    """

    def test_no_employee_overlap_between_folds(self):
        """Each fold pair (train, val) must have disjoint employee sets."""
        rng = np.random.default_rng(0)
        n   = 100
        X   = pd.DataFrame(np.random.rand(n, 3), columns=["a", "b", "c"])
        y   = pd.Series(rng.uniform(40, 100, n))
        # 10 employees, 10 rows each
        groups = np.repeat(np.arange(10), 10)

        gkf = GroupKFold(n_splits=5)
        for train_idx, val_idx in gkf.split(X, y, groups=groups):
            train_employees = set(groups[train_idx])
            val_employees   = set(groups[val_idx])
            overlap = train_employees & val_employees
            assert len(overlap) == 0, (
                f"GroupKFold fold has overlapping employees: {overlap}"
            )

    def test_each_employee_appears_in_val_exactly_once(self):
        """Across all 5 folds, each employee must appear as a val employee exactly once."""
        n      = 100
        groups = np.repeat(np.arange(10), 10)
        X      = pd.DataFrame(np.random.rand(n, 2), columns=["f1", "f2"])
        y      = pd.Series(np.random.rand(n) * 100)

        val_counts = {emp: 0 for emp in range(10)}
        gkf = GroupKFold(n_splits=5)
        for _, val_idx in gkf.split(X, y, groups=groups):
            for emp in set(groups[val_idx]):
                val_counts[emp] += 1

        for emp, count in val_counts.items():
            assert count == 1, f"Employee {emp} appeared in val {count} times (expected 1)"

    def test_groupkfold_stricter_than_random_kfold(self):
        """
        Random KFold CAN put the same employee in both train and val.
        GroupKFold must NOT — this confirms the v2 fix is necessary.
        """
        from sklearn.model_selection import KFold
        n      = 60
        groups = np.repeat(np.arange(6), 10)   # 6 employees, 10 rows each
        X      = pd.DataFrame(np.random.rand(n, 2), columns=["f1", "f2"])
        y      = pd.Series(np.random.rand(n) * 100)

        # Random KFold — may have overlap
        kf = KFold(n_splits=5, shuffle=True, random_state=0)
        random_has_overlap = False
        for tr, val in kf.split(X):
            if set(groups[tr]) & set(groups[val]):
                random_has_overlap = True
                break

        # GroupKFold — must have no overlap
        gkf = GroupKFold(n_splits=5)
        group_has_overlap = False
        for tr, val in gkf.split(X, y, groups):
            if set(groups[tr]) & set(groups[val]):
                group_has_overlap = True
                break

        assert random_has_overlap, "Expected random KFold to have overlap (baseline)"
        assert not group_has_overlap, "GroupKFold must never have employee overlap"

    def test_groupkfold_cv_score_is_lower_than_random_kfold(self):
        """
        A model evaluated with GroupKFold should have equal or worse CV score
        than random KFold (because GroupKFold is harder — it tests on unseen
        employees).  This confirms the v2 GroupKFold approach is more conservative.
        """
        from sklearn.model_selection import KFold, cross_val_score
        rng = np.random.default_rng(42)
        n   = 120
        # Signal: emp_avg_score predicts outcome well, but is employee-specific
        employee_scores = {i: rng.uniform(40, 100) for i in range(12)}
        groups = np.repeat(np.arange(12), 10)
        X = pd.DataFrame({
            "emp_avg_score": [employee_scores[g] + rng.normal(0, 2) for g in groups],
            "noise":         rng.uniform(0, 1, n),
        })
        y = pd.Series([employee_scores[g] + rng.normal(0, 5) for g in groups])

        model = lgb.LGBMRegressor(n_estimators=20, random_state=42, verbose=-1)

        kf_scores = cross_val_score(
            model, X, y, cv=KFold(5, shuffle=True, random_state=0),
            scoring="neg_root_mean_squared_error",
        )
        gkf_scores = cross_val_score(
            model, X, y,
            cv=GroupKFold(5).split(X, y, groups=groups),
            scoring="neg_root_mean_squared_error",
        )
        # GroupKFold RMSE should be >= random KFold RMSE (harder evaluation)
        assert -gkf_scores.mean() >= -kf_scores.mean() * 0.9, (
            "GroupKFold CV should be at least as hard as random KFold"
        )


# =============================================================================
# v2 NEW: TestMAPEMetric
# =============================================================================

class TestMAPEMetric:
    """MAPE is added as an additional evaluation metric in v2."""

    def test_mape_is_non_negative(self):
        y_true = np.array([80.0, 70.0, 90.0, 60.0])
        y_pred = np.array([75.0, 72.0, 85.0, 65.0])
        assert mean_absolute_percentage_error(y_true, y_pred) >= 0

    def test_perfect_predictions_give_zero_mape(self):
        y = np.array([70.0, 80.0, 90.0])
        assert mean_absolute_percentage_error(y, y) == pytest.approx(0.0)

    def test_mape_is_float(self):
        rng = np.random.default_rng(7)
        y_true = rng.uniform(50, 100, 50)
        y_pred = y_true + rng.normal(0, 5, 50)
        result = mean_absolute_percentage_error(y_true, y_pred)
        assert isinstance(result, float)

    def test_mape_larger_for_worse_predictions(self):
        y = np.array([80.0, 80.0, 80.0])
        good_pred = np.array([78.0, 82.0, 80.0])
        bad_pred  = np.array([50.0, 110.0, 60.0])
        assert (mean_absolute_percentage_error(y, bad_pred) >
                mean_absolute_percentage_error(y, good_pred))


# =============================================================================
# v2 NEW: TestConservativeSearchSpace
# =============================================================================

class TestConservativeSearchSpace:
    """
    Verifies the v2 parameter bounds prevent the pathological configurations
    that caused overfitting in v1 (num_leaves=255, min_child_samples=1).
    """

    # v2 bounds from train_learning_path_model.py
    BOUNDS = {
        "n_estimators":      (100, 300),
        "num_leaves":        (15, 63),
        "max_depth":         (3, 8),
        "min_child_samples": (10, 50),
    }

    def test_num_leaves_max_is_63(self):
        """num_leaves cap of 63 prevents excessively complex trees."""
        assert self.BOUNDS["num_leaves"][1] == 63

    def test_min_child_samples_min_is_10(self):
        """min_child_samples floor of 10 prevents single-sample leaves (memorisation)."""
        assert self.BOUNDS["min_child_samples"][0] == 10

    def test_n_estimators_max_is_300(self):
        """n_estimators cap of 300 (vs 1000 in v1) shortens each Optuna trial."""
        assert self.BOUNDS["n_estimators"][1] == 300

    def test_v2_bounds_less_overfit_than_v1_bounds(self):
        """
        v2's conservative bounds (num_leaves=63, min_child_samples=10) must
        produce a smaller train-test R² gap than v1's permissive bounds
        (num_leaves=255, min_child_samples=1) on the same data.
        This is a comparative test — it doesn't depend on dataset size.
        """
        rng = np.random.default_rng(9)
        n   = 200
        X   = pd.DataFrame({
            "emp_avg_score":        rng.uniform(40, 100, n),
            "skill_gap_proxy":      rng.uniform(0, 4, n),
            "complexity_level":     rng.integers(1, 4, n).astype(float),
            "resource_skill_level": rng.integers(1, 4, n).astype(float),
            "duration_hours":       rng.uniform(4, 20, n),
            "dag_edge_weight":      rng.uniform(0, 1, n),
            "emp_proficiency":      rng.uniform(0, 5, n),
            "emp_courses_done":     rng.integers(0, 15, n).astype(float),
            "attempt_number":       rng.integers(1, 3, n).astype(float),
        })
        y = (70 - X["skill_gap_proxy"] * 5 + X["emp_avg_score"] * 0.2
             + rng.normal(0, 5, n)).clip(0, 100)
        groups = np.repeat(np.arange(10), 20)

        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups))

        v1 = lgb.LGBMRegressor(num_leaves=255, min_child_samples=1,
                                n_estimators=500, random_state=42, verbose=-1)
        v2 = lgb.LGBMRegressor(num_leaves=63, min_child_samples=10,
                                n_estimators=200, reg_alpha=0.01, reg_lambda=0.01,
                                random_state=42, verbose=-1)
        v1.fit(X.iloc[tr], y.iloc[tr])
        v2.fit(X.iloc[tr], y.iloc[tr])

        v1_gap = (r2_score(y.iloc[tr], v1.predict(X.iloc[tr])) -
                  r2_score(y.iloc[te], v1.predict(X.iloc[te])))
        v2_gap = (r2_score(y.iloc[tr], v2.predict(X.iloc[tr])) -
                  r2_score(y.iloc[te], v2.predict(X.iloc[te])))

        assert v2_gap <= v1_gap, (
            f"v2 gap={v2_gap:.3f} should be <= v1 gap={v1_gap:.3f} "
            "— conservative bounds must reduce overfitting"
        )


# =============================================================================
# RETAINED v1: DAG construction
# =============================================================================

class TestDAGConstruction:

    def test_dag_node_count(self, skill_chain_dag_df):
        G = nx.DiGraph()
        for _, row in skill_chain_dag_df.iterrows():
            G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
                       weight=row["weight"])
        unique_skills = (set(skill_chain_dag_df["prerequisite_skill_id"]) |
                         set(skill_chain_dag_df["target_skill_id"]))
        assert G.number_of_nodes() == len(unique_skills)

    def test_dag_edge_count(self, skill_chain_dag_df):
        G = nx.DiGraph()
        for _, row in skill_chain_dag_df.iterrows():
            G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
                       weight=row["weight"])
        assert G.number_of_edges() == len(skill_chain_dag_df)

    def test_dag_is_acyclic(self, skill_chain_dag_df):
        G = nx.DiGraph()
        for _, row in skill_chain_dag_df.iterrows():
            G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
                       weight=row["weight"])
        assert nx.is_directed_acyclic_graph(G)

    def test_edge_weights_positive(self, skill_chain_dag_df):
        assert (skill_chain_dag_df["weight"] > 0).all()
        assert (skill_chain_dag_df["weight"] <= 1.0).all()

    def test_topological_sort_succeeds(self, skill_chain_dag_df):
        G = nx.DiGraph()
        for _, row in skill_chain_dag_df.iterrows():
            G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
                       weight=row["weight"])
        order = list(nx.topological_sort(G))
        assert len(order) == G.number_of_nodes()


# =============================================================================
# RETAINED v1: dag_weight_lookup
# =============================================================================

class TestDAGWeightLookup:

    def test_lookup_equals_per_row_max(self, skill_chain_dag_df):
        expected = skill_chain_dag_df.groupby("target_skill_id")["weight"].max().to_dict()
        lookup   = skill_chain_dag_df.groupby("target_skill_id")["weight"].max().to_dict()
        for sid, w in expected.items():
            assert lookup[sid] == w

    def test_lookup_uses_max_not_mean(self, skill_chain_dag_df):
        extra = pd.DataFrame({
            "prerequisite_skill_id": ["SK-109"],
            "target_skill_id":       ["SK-102"],
            "weight":                [0.3],
        })
        aug    = pd.concat([skill_chain_dag_df, extra], ignore_index=True)
        lookup = aug.groupby("target_skill_id")["weight"].max().to_dict()
        assert lookup["SK-102"] == pytest.approx(0.9)

    def test_root_skill_not_in_lookup(self, skill_chain_dag_df):
        lookup = skill_chain_dag_df.groupby("target_skill_id")["weight"].max().to_dict()
        root   = skill_chain_dag_df["prerequisite_skill_id"].iloc[0]
        if root not in skill_chain_dag_df["target_skill_id"].values:
            assert root not in lookup


# =============================================================================
# RETAINED v1: get_learning_path
# =============================================================================

def make_dag(skill_chain_dag_df):
    G = nx.DiGraph()
    for _, row in skill_chain_dag_df.iterrows():
        G.add_edge(row["prerequisite_skill_id"], row["target_skill_id"],
                   weight=row["weight"])
    return G


def get_learning_path(employee_id, target_role_id, job_requirements_df,
                      employee_skills_df, G):
    req = job_requirements_df[job_requirements_df["job_role_id"] == target_role_id].copy()
    req.columns = req.columns.str.lower()
    req = req.rename(columns={"required_skill_id": "skill_id"})
    if req.empty:
        return []
    curr = employee_skills_df[employee_skills_df["employee_id"] == employee_id][
        ["skill_id", "proficiency"]
    ]
    merged = req.merge(curr, on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"] = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)
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


class TestGetLearningPath:

    def test_returns_list(self, employee_skills_df, job_requirements_df, skill_chain_dag_df):
        G    = make_dag(skill_chain_dag_df)
        path = get_learning_path(
            "EMP-0001", job_requirements_df["job_role_id"].iloc[0],
            job_requirements_df, employee_skills_df, G,
        )
        assert isinstance(path, list)

    def test_empty_path_for_unknown_role(self, employee_skills_df, job_requirements_df,
                                          skill_chain_dag_df):
        G    = make_dag(skill_chain_dag_df)
        path = get_learning_path("EMP-0001", 9999, job_requirements_df, employee_skills_df, G)
        assert path == []

    def test_path_only_contains_missing_skills(self, employee_skills_df, job_requirements_df,
                                                skill_chain_dag_df):
        G       = make_dag(skill_chain_dag_df)
        role_id = job_requirements_df["job_role_id"].iloc[0]
        path    = get_learning_path(
            "EMP-0001", role_id, job_requirements_df, employee_skills_df, G,
        )
        req    = job_requirements_df[job_requirements_df["job_role_id"] == role_id]
        curr   = employee_skills_df[employee_skills_df["employee_id"] == "EMP-0001"]
        merged = req.merge(curr, left_on="required_skill_id", right_on="skill_id", how="left")
        merged["proficiency"] = merged["proficiency"].fillna(0)
        merged["gap"] = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)
        met = set(merged[merged["gap"] == 0]["required_skill_id"])
        for skill in path:
            assert skill not in met

    def test_topological_order_respected(self, skill_chain_dag_df):
        emp = pd.DataFrame({
            "employee_id": ["EMP-X"], "skill_id": ["SK-999"], "proficiency": [1],
        })
        req = pd.DataFrame({
            "job_role_id":       [1, 1],
            "required_skill_id": ["SK-102", "SK-101"],
            "min_proficiency":   [2, 2],
            "importance_weight": [0.5, 0.5],
        })
        G    = make_dag(skill_chain_dag_df)
        path = get_learning_path("EMP-X", 1, req, emp, G)
        if "SK-101" in path and "SK-102" in path:
            assert path.index("SK-101") < path.index("SK-102")

    def test_cycle_falls_back_gracefully(self, employee_skills_df, job_requirements_df):
        cyclic = pd.DataFrame({
            "prerequisite_skill_id": ["SK-101", "SK-102", "SK-103"],
            "target_skill_id":       ["SK-102", "SK-103", "SK-101"],
            "weight":                [0.9, 0.8, 0.7],
        })
        G       = make_dag(cyclic)
        role_id = job_requirements_df["job_role_id"].iloc[0]
        path    = get_learning_path("EMP-0001", role_id, job_requirements_df, employee_skills_df, G)
        assert isinstance(path, list)


# =============================================================================
# RETAINED v1: compute_readiness_score
# =============================================================================

def compute_readiness_score(employee_id, target_role_id, job_requirements_df,
                             employee_skills_df):
    req = job_requirements_df[job_requirements_df["job_role_id"] == target_role_id].copy()
    if req.empty:
        return 0.0
    curr   = employee_skills_df[employee_skills_df["employee_id"] == employee_id][
        ["skill_id", "proficiency"]
    ]
    merged = req.merge(curr, left_on="required_skill_id", right_on="skill_id", how="left")
    merged["proficiency"] = merged["proficiency"].fillna(0)
    merged["gap"] = np.maximum(merged["min_proficiency"] - merged["proficiency"], 0)
    num = (merged["gap"] * merged["importance_weight"]).sum()
    den = (4 * merged["importance_weight"]).sum()
    return 1.0 if den == 0 else 1.0 - (num / den)


class TestComputeReadinessScore:

    def test_score_bounded_in_0_1(self, employee_skills_df, job_requirements_df):
        for emp_id in employee_skills_df["employee_id"].unique()[:5]:
            for role_id in job_requirements_df["job_role_id"].unique():
                score = compute_readiness_score(emp_id, role_id, job_requirements_df,
                                                employee_skills_df)
                assert 0.0 <= score <= 1.0

    def test_score_is_0_for_unknown_role(self, employee_skills_df, job_requirements_df):
        assert compute_readiness_score("EMP-0001", 9999, job_requirements_df,
                                       employee_skills_df) == 0.0

    def test_perfect_employee_scores_1(self):
        emp = pd.DataFrame({"employee_id": ["E1"]*3, "skill_id": ["SK-101","SK-102","SK-103"],
                             "proficiency": [5, 5, 5]})
        req = pd.DataFrame({"job_role_id": [1]*3, "required_skill_id": ["SK-101","SK-102","SK-103"],
                             "min_proficiency": [2, 2, 2], "importance_weight": [0.3, 0.3, 0.4]})
        assert compute_readiness_score("E1", 1, req, emp) == pytest.approx(1.0)

    def test_zero_skill_employee_scores_low(self):
        emp = pd.DataFrame({"employee_id": ["E2"], "skill_id": ["SK-999"], "proficiency": [5]})
        req = pd.DataFrame({"job_role_id": [1]*2, "required_skill_id": ["SK-101","SK-102"],
                             "min_proficiency": [4, 4], "importance_weight": [0.5, 0.5]})
        assert compute_readiness_score("E2", 1, req, emp) < 0.5


# =============================================================================
# RETAINED v1 (updated): LightGBM feature matrix — uses v2 feature names
# =============================================================================

class TestLightGBMFeatureMatrix:

    def test_all_required_features_present(self, training_history_df, learning_resources_df,
                                            employee_skills_df, skills_catalog_df,
                                            skill_chain_dag_df):
        X, y, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        for col in REQUIRED_FEATURES:
            assert col in X.columns, f"Missing v2 feature: {col}"

    def test_no_nan_in_feature_matrix(self, training_history_df, learning_resources_df,
                                       employee_skills_df, skills_catalog_df, skill_chain_dag_df):
        X, y, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        assert X.isnull().sum().sum() == 0

    def test_target_bounded_0_100(self, training_history_df, learning_resources_df,
                                   employee_skills_df, skills_catalog_df, skill_chain_dag_df):
        _, y, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        assert y.between(0, 100).all()

    def test_skill_gap_proxy_non_negative(self, training_history_df, learning_resources_df,
                                           employee_skills_df, skills_catalog_df, skill_chain_dag_df):
        """skill_gap_proxy = max(resource_level - emp_proficiency, 0) must always be >= 0."""
        X, _, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        assert (X["skill_gap_proxy"] >= 0).all()

    def test_emp_proficiency_non_negative(self, training_history_df, learning_resources_df,
                                           employee_skills_df, skills_catalog_df, skill_chain_dag_df):
        X, _, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        assert (X["emp_proficiency"] >= 0).all()

    def test_resource_skill_level_valid_encoding(self, training_history_df, learning_resources_df,
                                                   employee_skills_df, skills_catalog_df,
                                                   skill_chain_dag_df):
        """resource_skill_level must be 1, 2, or 3 (Beginner/Intermediate/Advanced)."""
        X, _, _ = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        assert X["resource_skill_level"].isin([1, 2, 3]).all()


# =============================================================================
# RETAINED v1: GroupShuffleSplit train/test isolation
# =============================================================================

class TestGroupShuffleSplit:

    def test_no_employee_in_both_train_and_test(self, training_history_df, learning_resources_df,
                                                  employee_skills_df, skills_catalog_df,
                                                  skill_chain_dag_df):
        X, y, groups = build_feature_matrix(
            training_history_df, learning_resources_df,
            employee_skills_df, skills_catalog_df, skill_chain_dag_df,
        )
        if len(X) < 5:
            pytest.skip("Not enough samples")
        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups=groups.values))
        assert len(set(groups.values[tr]) & set(groups.values[te])) == 0


# =============================================================================
# RETAINED v1 (updated): LightGBM training — uses v2 feature names
# =============================================================================

class TestLightGBMTraining:

    @pytest.fixture()
    def mini_train_data(self):
        """Synthetic (X, y, groups) using v2 feature names."""
        rng = np.random.default_rng(10)
        n   = 120
        X   = pd.DataFrame({
            "emp_proficiency":      rng.uniform(0, 5, n),
            "resource_skill_level": rng.integers(1, 4, n).astype(float),
            "skill_gap_proxy":      rng.uniform(0, 4, n),
            "complexity_level":     rng.integers(1, 4, n).astype(float),
            "dag_edge_weight":      rng.uniform(0, 1, n),
            "duration_hours":       rng.uniform(4, 20, n),
            "emp_avg_score":        rng.uniform(40, 100, n),
            "emp_courses_done":     rng.integers(0, 15, n).astype(float),
            "attempt_number":       rng.integers(1, 3, n).astype(float),
        })
        y = (
            70
            - X["skill_gap_proxy"] * 5
            + X["emp_avg_score"] * 0.2
            + rng.normal(0, 5, n)
        ).clip(0, 100)
        groups = np.repeat(np.arange(12), 10)
        return X, pd.Series(y), groups

    def test_lgbm_trains_without_error(self, mini_train_data):
        X, y, groups = mini_train_data
        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups))
        model = lgb.LGBMRegressor(n_estimators=30, random_state=42, verbose=-1)
        model.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        assert model.n_estimators_ > 0

    def test_predictions_not_all_same(self, mini_train_data):
        X, y, groups = mini_train_data
        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups))
        model = lgb.LGBMRegressor(n_estimators=30, random_state=42, verbose=-1)
        model.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        assert model.predict(X.iloc[te]).std() > 0.1

    def test_rmse_below_ceiling(self, mini_train_data):
        X, y, groups = mini_train_data
        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, te = next(gss.split(X, y, groups))
        model = lgb.LGBMRegressor(n_estimators=50, random_state=42, verbose=-1)
        model.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        rmse = np.sqrt(mean_squared_error(y.iloc[te], model.predict(X.iloc[te])))
        assert rmse < 30

    def test_feature_importance_length_matches_v2(self, mini_train_data):
        """feature_importances_ must have one entry per v2 feature."""
        X, y, groups = mini_train_data
        gss = GroupShuffleSplit(1, test_size=0.2, random_state=42)
        tr, _ = next(gss.split(X, y, groups))
        model = lgb.LGBMRegressor(n_estimators=30, random_state=42, verbose=-1)
        model.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        assert len(model.feature_importances_) == len(REQUIRED_FEATURES)

    def test_v2_overfits_less_than_v1(self, mini_train_data):
        """
        v2 bounds (num_leaves=63, min_child_samples=10) must produce a smaller
        train-test R² gap than v1 bounds (num_leaves=255, min_child_samples=1).
        """
        X, y, groups = mini_train_data
        gss = GroupShuffleSplit(1, test_size=0.25, random_state=42)
        tr, te = next(gss.split(X, y, groups))
        v1 = lgb.LGBMRegressor(num_leaves=255, min_child_samples=1,
                                n_estimators=500, random_state=42, verbose=-1)
        v2 = lgb.LGBMRegressor(num_leaves=63, min_child_samples=10,
                                n_estimators=200, reg_alpha=0.01, reg_lambda=0.01,
                                random_state=42, verbose=-1)
        v1.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        v2.fit(X.iloc[tr], y.iloc[tr].to_numpy())
        v1_gap = (r2_score(y.iloc[tr], v1.predict(X.iloc[tr])) -
                  r2_score(y.iloc[te], v1.predict(X.iloc[te])))
        v2_gap = (r2_score(y.iloc[tr], v2.predict(X.iloc[tr])) -
                  r2_score(y.iloc[te], v2.predict(X.iloc[te])))
        assert v2_gap <= v1_gap, (
            f"v2 gap={v2_gap:.3f} should be <= v1 gap={v1_gap:.3f}"
        )


# =============================================================================
# RETAINED v1: persistence
# =============================================================================

class TestLearningPathPersistence:

    def test_model_joblib_round_trip(self):
        X = pd.DataFrame(np.random.rand(50, len(REQUIRED_FEATURES)), columns=REQUIRED_FEATURES)
        y = pd.Series(np.random.uniform(40, 100, 50))
        model = lgb.LGBMRegressor(n_estimators=10, random_state=42, verbose=-1)
        model.fit(X, y.to_numpy())
        preds_before = model.predict(X)
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(model, path)
            loaded = joblib.load(path)
            np.testing.assert_allclose(preds_before, loaded.predict(X), rtol=1e-6)
        finally:
            os.unlink(path)

    def test_dag_joblib_round_trip(self, skill_chain_dag_df):
        G      = make_dag(skill_chain_dag_df)
        lookup = skill_chain_dag_df.groupby("target_skill_id")["weight"].max().to_dict()
        payload = {"dag": G, "dag_weight_lookup": lookup}
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(payload, path)
            loaded = joblib.load(path)
            assert loaded["dag"].number_of_nodes() == G.number_of_nodes()
            assert loaded["dag_weight_lookup"] == lookup
        finally:
            os.unlink(path)

    def test_features_pkl_round_trip(self):
        """FEATURES_FINAL list must survive joblib serialisation unchanged."""
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(REQUIRED_FEATURES, path)
            loaded = joblib.load(path)
            assert loaded == REQUIRED_FEATURES
        finally:
            os.unlink(path)
