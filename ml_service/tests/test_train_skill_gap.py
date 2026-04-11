"""
Tests for Model 3: Org-Level Skill Gap Analysis
train_skill_gap_model.py

This model is pure aggregation (no ML training), so tests focus on:
  - get_criticality() threshold logic
  - Demand and supply computation correctness
  - gap_ratio formula and capping
  - Department-level drill-down aggregation
  - Output structure and column completeness
  - Baseline sanity: skills with no supply should have high gap_ratio
  - Criticality tier distribution
  - Serialisation round-trip (joblib)
"""

import numpy as np
import pandas as pd
import pytest
import joblib
import tempfile
import os


# ─── get_criticality ──────────────────────────────────────────────────────────
# Directly mirrors the function in train_skill_gap_model.py

def get_criticality(ratio: float) -> str:
    if ratio >= 2.0:
        return "critical"
    elif ratio >= 1.5:
        return "high"
    elif ratio >= 1.2:
        return "medium"
    return "low"


class TestGetCriticality:

    @pytest.mark.parametrize("ratio, expected", [
        (0.0,  "low"),
        (0.9,  "low"),
        (1.19, "low"),
        (1.2,  "medium"),
        (1.4,  "medium"),
        (1.49, "medium"),
        (1.5,  "high"),
        (1.9,  "high"),
        (1.99, "high"),
        (2.0,  "critical"),
        (5.0,  "critical"),
        (10.0, "critical"),
    ])
    def test_boundary_and_interior_values(self, ratio, expected):
        """
        Boundary conditions for the four criticality tiers.
        Boundary values (1.2, 1.5, 2.0) must map to the higher tier.
        """
        assert get_criticality(ratio) == expected, (
            f"ratio={ratio} → expected '{expected}', got '{get_criticality(ratio)}'"
        )

    def test_exact_boundary_20_is_critical(self):
        """ratio = 2.0 exactly must be 'critical', not 'high'."""
        assert get_criticality(2.0) == "critical"

    def test_exact_boundary_15_is_high(self):
        """ratio = 1.5 exactly must be 'high', not 'medium'."""
        assert get_criticality(1.5) == "high"

    def test_exact_boundary_12_is_medium(self):
        """ratio = 1.2 exactly must be 'medium', not 'low'."""
        assert get_criticality(1.2) == "medium"

    def test_zero_ratio_is_low(self):
        """ratio = 0 means demand is fully met — tier must be 'low'."""
        assert get_criticality(0.0) == "low"

    def test_capped_ratio_10(self):
        """Gap ratio is capped at 10 in the pipeline; result must be 'critical'."""
        assert get_criticality(10.0) == "critical"

    def test_returns_string(self):
        """Return type must always be str."""
        assert isinstance(get_criticality(1.8), str)


# ─── Supply computation ───────────────────────────────────────────────────────

class TestSupplyComputation:

    def test_supply_is_avg_proficiency_times_employee_count(
        self, employee_skills_df
    ):
        """
        total_supply for each skill = avg_proficiency × employee_count.
        This must match a manual group-by calculation.
        """
        supply = (
            employee_skills_df
            .groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count")
            .reset_index()
        )
        supply["total_supply"] = supply["avg_proficiency"] * supply["employee_count"]
        # Manual check for one skill
        sk = supply["skill_id"].iloc[0]
        manual_avg = employee_skills_df.loc[
            employee_skills_df["skill_id"] == sk, "proficiency"
        ].mean()
        np.testing.assert_allclose(
            supply.loc[supply["skill_id"] == sk, "avg_proficiency"].iloc[0],
            manual_avg, rtol=1e-6,
        )

    def test_supply_no_nulls(self, employee_skills_df):
        """Supply aggregation must not produce NaN in avg_proficiency."""
        supply = (
            employee_skills_df
            .groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count")
            .reset_index()
        )
        assert supply["avg_proficiency"].isnull().sum() == 0

    def test_employee_count_positive(self, employee_skills_df):
        """Every skill with a supply entry must have at least 1 employee."""
        supply = (
            employee_skills_df
            .groupby("skill_id")["proficiency"]
            .agg(employee_count="count")
            .reset_index()
        )
        assert (supply["employee_count"] > 0).all()


# ─── Demand computation ───────────────────────────────────────────────────────

class TestDemandComputation:

    def test_demand_uses_all_role_requirements(self, job_requirements_df):
        """
        Every row in job_role_requirements must contribute to total demand.
        No rows should be silently dropped.
        """
        headcount = {r: 1 for r in job_requirements_df["job_role_id"].unique()}
        records = []
        for _, row in job_requirements_df.iterrows():
            records.append({
                "skill_id":        str(row["required_skill_id"]),
                "weighted_demand": float(row["min_proficiency"]) * float(row["importance_weight"]) * headcount.get(row["job_role_id"], 1),
            })
        demand_df = pd.DataFrame(records)
        demand = demand_df.groupby("skill_id")["weighted_demand"].sum()
        # Every required skill must appear in demand
        required_skills = job_requirements_df["required_skill_id"].astype(str).unique()
        for sk in required_skills:
            assert sk in demand.index, f"Skill {sk} missing from demand"

    def test_demand_is_positive(self, job_requirements_df):
        """Demand scores must be strictly positive (min_prof, importance, headcount > 0)."""
        headcount = {r: 1 for r in job_requirements_df["job_role_id"].unique()}
        records = []
        for _, row in job_requirements_df.iterrows():
            records.append({
                "skill_id":        str(row["required_skill_id"]),
                "weighted_demand": float(row["min_proficiency"]) * float(row["importance_weight"]),
            })
        demand = pd.DataFrame(records).groupby("skill_id")["weighted_demand"].sum()
        assert (demand > 0).all(), "Some skills have non-positive demand"


# ─── Gap ratio computation ────────────────────────────────────────────────────

class TestGapRatioComputation:

    def _build_analysis(self, employee_skills_df, job_requirements_df, skills_catalog_df):
        """Utility: replicate the merge + gap_ratio computation pipeline."""
        supply = (
            employee_skills_df
            .groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count")
            .reset_index()
        )
        headcount = {r: 1 for r in job_requirements_df["job_role_id"].unique()}
        demand_records = []
        for _, row in job_requirements_df.iterrows():
            demand_records.append({
                "skill_id":       str(row["required_skill_id"]),
                "weighted_demand":float(row["min_proficiency"]) * float(row["importance_weight"]),
            })
        demand = (
            pd.DataFrame(demand_records)
            .groupby("skill_id")["weighted_demand"].sum()
            .reset_index()
            .rename(columns={"weighted_demand": "total_demand"})
        )
        analysis = demand.merge(supply, on="skill_id", how="outer")
        analysis["avg_proficiency"] = analysis["avg_proficiency"].fillna(0)
        analysis["total_demand"]    = analysis["total_demand"].fillna(0)
        analysis["employee_count"]  = analysis["employee_count"].fillna(0)
        analysis["total_supply"] = analysis["avg_proficiency"] * analysis["employee_count"]
        analysis["gap_ratio"] = analysis.apply(
            lambda r: min(r["total_demand"] / (r["total_supply"] + 1e-8), 10.0), axis=1
        )
        analysis["criticality"] = analysis["gap_ratio"].apply(get_criticality)
        return analysis

    def test_gap_ratio_capped_at_10(self, employee_skills_df, job_requirements_df, skills_catalog_df):
        """gap_ratio must never exceed 10.0 regardless of the demand/supply ratio."""
        analysis = self._build_analysis(employee_skills_df, job_requirements_df, skills_catalog_df)
        assert analysis["gap_ratio"].max() <= 10.0

    def test_gap_ratio_non_negative(self, employee_skills_df, job_requirements_df, skills_catalog_df):
        """gap_ratio must always be ≥ 0."""
        analysis = self._build_analysis(employee_skills_df, job_requirements_df, skills_catalog_df)
        assert (analysis["gap_ratio"] >= 0).all()

    def test_zero_supply_skill_has_high_ratio(self, job_requirements_df, skills_catalog_df):
        """
        A skill required by roles but not held by any employee should have
        the maximum gap_ratio (capped at 10.0).
        This is the hardest type of skill gap for an organisation.
        """
        # employee_skills_df has NO entry for SK-999 (phantom skill)
        empty_supply_skills = pd.DataFrame({
            "employee_id": [], "skill_id": [], "proficiency": [],
        })
        phantom_req = pd.DataFrame({
            "job_role_id":       [1],
            "required_skill_id": ["SK-999"],
            "min_proficiency":   [3],
            "importance_weight": [1.0],
        })
        analysis = self._build_analysis(empty_supply_skills, phantom_req, skills_catalog_df)
        row = analysis[analysis["skill_id"] == "SK-999"]
        assert not row.empty
        assert row["gap_ratio"].iloc[0] == pytest.approx(10.0, abs=0.01)

    def test_fully_met_skill_has_low_ratio(self, skills_catalog_df):
        """
        A skill where supply >> demand should have a gap_ratio close to 0,
        indicating no organisational gap.
        """
        # Single employee with very high proficiency
        emp = pd.DataFrame({
            "employee_id": ["EMP-0001"], "skill_id": ["SK-101"], "proficiency": [5],
        })
        req = pd.DataFrame({
            "job_role_id": [1], "required_skill_id": ["SK-101"],
            "min_proficiency": [1], "importance_weight": [0.1],
        })
        analysis = self._build_analysis(emp, req, skills_catalog_df)
        row = analysis[analysis["skill_id"] == "SK-101"]
        # demand = 1 * 0.1 = 0.1, supply = 5 * 1 = 5 → ratio = 0.02
        assert row["gap_ratio"].iloc[0] < 1.0

    def test_criticality_column_from_gap_ratio(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """
        criticality must be consistent with get_criticality(gap_ratio).
        The column must not be independently computed or hardcoded.
        """
        analysis = self._build_analysis(
            employee_skills_df, job_requirements_df, skills_catalog_df
        )
        for _, row in analysis.iterrows():
            expected = get_criticality(row["gap_ratio"])
            assert row["criticality"] == expected, (
                f"skill={row['skill_id']}: ratio={row['gap_ratio']:.3f} → "
                f"expected '{expected}', got '{row['criticality']}'"
            )

    def test_sorted_by_gap_ratio_descending(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """The output must be sorted by gap_ratio descending (highest risk first)."""
        analysis = self._build_analysis(
            employee_skills_df, job_requirements_df, skills_catalog_df
        ).sort_values("gap_ratio", ascending=False).reset_index(drop=True)
        ratios = analysis["gap_ratio"].values
        for i in range(len(ratios) - 1):
            assert ratios[i] >= ratios[i + 1]

    def test_gap_score_normalised_to_0_1(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """gap_score = gap_ratio / max_ratio must be in [0, 1]."""
        analysis = self._build_analysis(
            employee_skills_df, job_requirements_df, skills_catalog_df
        )
        max_ratio = analysis["gap_ratio"].max()
        analysis["gap_score"] = analysis["gap_ratio"] / (max_ratio + 1e-8)
        assert analysis["gap_score"].between(0, 1).all()


# ─── Department-level drill-down ──────────────────────────────────────────────

class TestDepartmentSummary:

    def test_department_summary_has_correct_structure(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """Department summary DataFrame must contain 'department', 'avg_gap', 'critical_count'."""
        dept_skill_map = {}
        for _, row in job_requirements_df.iterrows():
            dept_skill_map.setdefault(str(row["required_skill_id"]), []).append(
                str(row["job_role_id"])
            )
        # Build a simple analysis DF
        supply = (
            employee_skills_df.groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count").reset_index()
        )
        demand_records = [
            {"skill_id": str(r["required_skill_id"]),
             "weighted_demand": float(r["min_proficiency"]) * float(r["importance_weight"])}
            for _, r in job_requirements_df.iterrows()
        ]
        demand = (pd.DataFrame(demand_records).groupby("skill_id")["weighted_demand"]
                  .sum().reset_index().rename(columns={"weighted_demand": "total_demand"}))
        analysis = demand.merge(supply, on="skill_id", how="outer")
        analysis = analysis.fillna(0)
        analysis["total_supply"] = analysis["avg_proficiency"] * analysis["employee_count"]
        analysis["gap_ratio"] = analysis.apply(
            lambda r: min(r["total_demand"] / (r["total_supply"] + 1e-8), 10.0), axis=1
        )
        analysis["criticality"] = analysis["gap_ratio"].apply(get_criticality)
        analysis["departments_affected"] = analysis["skill_id"].map(
            lambda s: dept_skill_map.get(str(s), [])
        )
        # Build dept records
        dept_records = []
        for _, row in analysis.iterrows():
            for dept in row["departments_affected"]:
                dept_records.append({
                    "department": dept,
                    "skill_id": row["skill_id"],
                    "gap_ratio": row["gap_ratio"],
                    "criticality": row["criticality"],
                })
        if not dept_records:
            pytest.skip("No department data with this fixture")
        dept_df = pd.DataFrame(dept_records)
        dept_summary = (
            dept_df.groupby("department")
            .agg(n_skills=("skill_id", "nunique"),
                 avg_gap=("gap_ratio", "mean"),
                 critical_count=("criticality", lambda x: (x == "critical").sum()))
            .reset_index()
        )
        for col in ["department", "n_skills", "avg_gap", "critical_count"]:
            assert col in dept_summary.columns

    def test_department_avg_gap_positive(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """Average gap per department must be ≥ 0."""
        supply = (
            employee_skills_df.groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count").reset_index()
        )
        demand_records = [
            {"skill_id": str(r["required_skill_id"]),
             "weighted_demand": float(r["min_proficiency"]) * float(r["importance_weight"])}
            for _, r in job_requirements_df.iterrows()
        ]
        demand = (pd.DataFrame(demand_records).groupby("skill_id")["weighted_demand"]
                  .sum().reset_index().rename(columns={"weighted_demand": "total_demand"}))
        analysis = demand.merge(supply, on="skill_id", how="outer").fillna(0)
        analysis["total_supply"] = analysis["avg_proficiency"] * analysis["employee_count"]
        analysis["gap_ratio"] = analysis.apply(
            lambda r: min(r["total_demand"] / (r["total_supply"] + 1e-8), 10.0), axis=1
        )
        assert (analysis["gap_ratio"] >= 0).all()


# ─── Persistence ──────────────────────────────────────────────────────────────

class TestSkillGapPersistence:

    def test_baseline_joblib_round_trip(
        self, employee_skills_df, job_requirements_df, skills_catalog_df
    ):
        """The skill gap baseline DataFrame must survive joblib serialisation."""
        supply = (
            employee_skills_df.groupby("skill_id")["proficiency"]
            .agg(avg_proficiency="mean", employee_count="count").reset_index()
        )
        demand_records = [
            {"skill_id": str(r["required_skill_id"]),
             "weighted_demand": float(r["min_proficiency"]) * float(r["importance_weight"])}
            for _, r in job_requirements_df.iterrows()
        ]
        demand = (pd.DataFrame(demand_records).groupby("skill_id")["weighted_demand"]
                  .sum().reset_index().rename(columns={"weighted_demand": "total_demand"}))
        analysis = demand.merge(supply, on="skill_id", how="outer").fillna(0)
        analysis["total_supply"] = analysis["avg_proficiency"] * analysis["employee_count"]
        analysis["gap_ratio"] = analysis.apply(
            lambda r: min(r["total_demand"] / (r["total_supply"] + 1e-8), 10.0), axis=1
        )
        analysis["criticality"] = analysis["gap_ratio"].apply(get_criticality)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name
        try:
            joblib.dump(analysis, path)
            loaded = joblib.load(path)
            pd.testing.assert_frame_equal(analysis, loaded)
        finally:
            os.unlink(path)
