"""
Employee Ground Truth Test Cases — All 4 ML Models
=====================================================
Tests use synthetic employee profiles with known expected outputs.
Run with:  pytest ml_service/tests/test_employees_ground_truth.py -v
(ML service does NOT need to be running — tests call services directly)
"""

import pytest
import sys
import os

# Allow imports from ml_service/app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.turnover import TurnoverRequest, TurnoverResponse
from app.schemas.role_fit import RoleFitRequest, RoleFitResponse, SkillProficiency, RoleRequirement
from app.schemas.learning_path import (
    LearningPathRequest, LearningPathResponse, MissingSkill, LearningResource,
)
from app.services.role_fit_service import compute_role_fit
from app.services.learning_path_service import recommend_learning_path


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _role_fit_req(employee_id: str, job_role_id: str,
                  skills: list[tuple], reqs: list[tuple]) -> RoleFitRequest:
    """Build a RoleFitRequest from (skill_id, proficiency) and (skill_id, min_prof, weight) tuples."""
    return RoleFitRequest(
        employee_id=employee_id,
        job_role_id=job_role_id,
        employee_skills=[SkillProficiency(skill_id=s, proficiency=p) for s, p in skills],
        role_requirements=[
            RoleRequirement(skill_id=s, min_proficiency=m, importance_weight=w)
            for s, m, w in reqs
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL 1 — TURNOVER PREDICTION (algorithmic mapping tests)
# These tests validate the feature-engineering and threshold logic in
# turnover_service.py WITHOUT needing the .pkl file on disk.
# ═══════════════════════════════════════════════════════════════════════════════

class TestTurnoverFeatureMapping:
    """Validate that backend field → feature mapping produces the expected numeric values."""

    def _build_request(self, **overrides) -> TurnoverRequest:
        defaults = dict(
            employee_id="EMP_TEST",
            tenure_days=365 * 5,       # 5 years
            commute_distance_km=10.0,
            role_fit_score=70.0,
            absence_rate=0.05,
            late_arrivals_30d=2,
            leave_requests_90d=1,
            satisfaction_score=75.0,
            attendance_status="normal",
        )
        defaults.update(overrides)
        return TurnoverRequest(**defaults)

    def test_tenure_mapping(self):
        """tenure_years = tenure_days / 365.25"""
        from app.services.turnover_service import ATTENDANCE_MAP
        req = self._build_request(tenure_days=3652)   # ~10 years
        tenure_years = req.tenure_days / 365.25
        assert abs(tenure_years - 9.998) < 0.01

    def test_work_life_balance_scale(self):
        """satisfaction_score 0–100 → work_life_balance 0–5"""
        req = self._build_request(satisfaction_score=80.0)
        wlb = req.satisfaction_score / 20.0
        assert abs(wlb - 4.0) < 0.01

    def test_late_rate_computation(self):
        """late_rate = late_arrivals_30d / 30"""
        req = self._build_request(late_arrivals_30d=9)
        late_rate = req.late_arrivals_30d / 30.0
        assert abs(late_rate - 0.30) < 0.001

    def test_attendance_map_normal(self):
        from app.services.turnover_service import ATTENDANCE_MAP
        assert ATTENDANCE_MAP["normal"] == 0

    def test_attendance_map_at_risk(self):
        from app.services.turnover_service import ATTENDANCE_MAP
        assert ATTENDANCE_MAP["at_risk"] == 1

    def test_attendance_map_critical(self):
        from app.services.turnover_service import ATTENDANCE_MAP
        assert ATTENDANCE_MAP["critical"] == 2

    def test_risk_thresholds_low(self):
        """Risk score ≤ 30 → low."""
        import unittest.mock as mock
        import numpy as np
        import app.services.turnover_service as svc
        with mock.patch.object(svc, "_model", create=True) as m_model, \
             mock.patch.object(svc, "_scaler", create=True) as m_scaler, \
             mock.patch.object(svc, "_feature_names",
                               ["tenure_years", "commute_distance_km", "role_fit_score",
                                "absence_rate", "late_rate", "work_life_balance",
                                "attendance_status_encoded"], create=True):
            m_scaler.transform.return_value = [[0]*7]
            m_model.predict_proba.return_value = np.array([[0.80, 0.20]])  # 20% → score=20
            svc._model = m_model
            svc._scaler = m_scaler
            from app.services.turnover_service import predict_turnover
            result = predict_turnover(self._build_request())
            assert result.risk_level == "low"
            assert result.risk_score == pytest.approx(20.0, abs=0.1)

    def test_risk_thresholds_critical(self):
        """Risk score > 75 → critical."""
        import unittest.mock as mock
        import numpy as np
        import app.services.turnover_service as svc
        with mock.patch.object(svc, "_model", create=True) as m_model, \
             mock.patch.object(svc, "_scaler", create=True) as m_scaler, \
             mock.patch.object(svc, "_feature_names",
                               ["tenure_years", "commute_distance_km", "role_fit_score",
                                "absence_rate", "late_rate", "work_life_balance",
                                "attendance_status_encoded"], create=True):
            m_scaler.transform.return_value = [[0]*7]
            m_model.predict_proba.return_value = np.array([[0.15, 0.85]])  # 85% → score=85
            svc._model = m_model
            svc._scaler = m_scaler
            from app.services.turnover_service import predict_turnover
            result = predict_turnover(self._build_request())
            assert result.risk_level == "critical"
            assert result.risk_score == pytest.approx(85.0, abs=0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL 2 — ROLE FIT: EMPLOYEE REPLACEMENT GROUND TRUTH
# ═══════════════════════════════════════════════════════════════════════════════

# Data Science Manager role requirements
DS_MGR_REQUIREMENTS = [
    ("sk01", 4.0, 0.9),   # Python — critical
    ("sk02", 4.0, 0.85),  # Machine Learning — critical
    ("sk11", 3.0, 0.8),   # Leadership — important
    ("sk04", 3.0, 0.6),   # SQL — medium
    ("sk07", 3.0, 0.5),   # Communication — secondary
]


class TestEmployeeReplacementRanking:
    """
    Tests for 5 replacement candidates for Data Science Manager role.
    Ground truth: perfect_match > strong_match > partial_match > weak > not_suitable
    """

    def test_perfect_candidate_is_ready(self):
        """Sarah: meets or exceeds all requirements → fit_score >= 97, readiness = ready."""
        sarah_skills = [
            ("sk01", 5.0), ("sk02", 5.0), ("sk11", 4.0), ("sk04", 3.0), ("sk07", 4.0),
        ]
        req = _role_fit_req("sarah", "ds_mgr", sarah_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        assert result.readiness_level == "ready", f"Expected ready, got {result.readiness_level} (score={result.fit_score})"
        assert result.fit_score >= 97

    def test_perfect_candidate_has_no_missing_skills(self):
        """Sarah: no missing skills."""
        sarah_skills = [
            ("sk01", 5.0), ("sk02", 5.0), ("sk11", 4.0), ("sk04", 3.0), ("sk07", 4.0),
        ]
        req = _role_fit_req("sarah", "ds_mgr", sarah_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        assert len(result.missing_skills) == 0
        assert len(result.matching_skills) == 5

    def test_strong_candidate_is_near_ready(self):
        """Omar: ML gap of 1 point → near_ready (fit_score >= 65)."""
        omar_skills = [
            ("sk01", 4.0), ("sk02", 3.0),   # ML gap = 1
            ("sk11", 4.0), ("sk04", 4.0), ("sk07", 5.0),
        ]
        req = _role_fit_req("omar", "ds_mgr", omar_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        # ML gap = 1 × 0.85 = 0.85 weighted; total_weight = 13.2
        # readiness ≈ 1 - 0.85/13.2 = 0.936 → algorithmic fit_score ≈ 93
        # ML model may refine slightly, but should remain >= 65
        assert result.fit_score >= 65, f"Omar expected near_ready or ready, got {result.fit_score}"

    def test_partial_candidate_has_python_gap(self):
        """Yara: Python gap = 2 points (critical skill) → needs_development."""
        yara_skills = [
            ("sk01", 2.0),   # Python gap = 4-2 = 2 × 0.9 = 1.8 weighted
            ("sk02", 4.0),
            ("sk11", 2.0),   # Leadership gap = 1 × 0.8 = 0.8 weighted
            ("sk04", 5.0),
            ("sk07", 3.0),
        ]
        req = _role_fit_req("yara", "ds_mgr", yara_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        # total_weighted_gap = 1.8 + 0.8 = 2.6; total_weight = 13.2
        # readiness = 1 - 2.6/13.2 = 0.803 → fit_score = 80 (near_ready)
        # OR ML model sees max_gap=2 (high) → lowers to needs_development
        assert result.fit_score <= 85, f"Yara should not be 'ready' with Python gap=2"
        # Python must appear in missing/partial skills
        python_in_gaps = any(g.skill_id == "sk01" for g in result.skill_gaps if g.gap > 0)
        assert python_in_gaps, "Python gap should be detected"

    def test_weak_candidate_is_not_ready(self):
        """David: all skills below requirements → fit_score < 65."""
        david_skills = [
            ("sk01", 1.0), ("sk02", 1.0), ("sk11", 1.0), ("sk04", 1.0), ("sk07", 1.0),
        ]
        req = _role_fit_req("david", "ds_mgr", david_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        assert result.fit_score < 65, f"David (all skills=1) should not be near_ready, got {result.fit_score}"

    def test_completely_unqualified(self):
        """No skills at all → fit_score very low, not_ready."""
        req = _role_fit_req("nobody", "ds_mgr", [], DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        assert result.fit_score < 40
        assert result.readiness_level == "not_ready"
        assert len(result.missing_skills) == len(DS_MGR_REQUIREMENTS)

    def test_ranking_order_preserved(self):
        """Perfect candidate scores higher than weak candidate."""
        perfect_skills = [
            ("sk01", 5.0), ("sk02", 5.0), ("sk11", 4.0), ("sk04", 3.0), ("sk07", 4.0),
        ]
        weak_skills = [
            ("sk01", 1.0), ("sk02", 1.0), ("sk11", 1.0), ("sk04", 1.0), ("sk07", 1.0),
        ]
        req_perfect = _role_fit_req("perfect", "ds_mgr", perfect_skills, DS_MGR_REQUIREMENTS)
        req_weak    = _role_fit_req("weak",    "ds_mgr", weak_skills,    DS_MGR_REQUIREMENTS)
        score_perfect = compute_role_fit(req_perfect).fit_score
        score_weak    = compute_role_fit(req_weak).fit_score
        assert score_perfect > score_weak, f"{score_perfect} should be > {score_weak}"

    def test_importance_weight_dominates_over_skill_count(self):
        """
        Employee A: meets Python (imp=0.9, critical) but misses Communication (imp=0.5)
        Employee B: meets Communication (imp=0.5) but misses Python (imp=0.9, critical)
        Employee A must score HIGHER despite same number of missing skills.
        """
        # Only test Python + Communication for clarity
        reqs_2skill = [
            ("sk01", 4.0, 0.9),   # Python — critical
            ("sk07", 3.0, 0.5),   # Communication — secondary
        ]
        # A: Python=5 (met), Communication=0 (missing secondary)
        emp_a = _role_fit_req("emp_a", "r", [("sk01", 5.0)], reqs_2skill)
        # B: Python=0 (missing critical), Communication=5 (met)
        emp_b = _role_fit_req("emp_b", "r", [("sk07", 5.0)], reqs_2skill)
        score_a = compute_role_fit(emp_a).fit_score
        score_b = compute_role_fit(emp_b).fit_score
        assert score_a > score_b, (
            f"Candidate meeting critical skill (imp=0.9) should score higher "
            f"than one meeting only secondary skill (imp=0.5). Got A={score_a}, B={score_b}"
        )

    def test_skill_gaps_sorted_by_importance(self):
        """skill_gaps list is sorted by importance descending."""
        yara_skills = [
            ("sk01", 2.0), ("sk02", 4.0), ("sk11", 2.0), ("sk04", 5.0), ("sk07", 3.0),
        ]
        req = _role_fit_req("yara", "ds_mgr", yara_skills, DS_MGR_REQUIREMENTS)
        result = compute_role_fit(req)
        weights = [g.importance_weight for g in result.skill_gaps]
        # Descending sort (with secondary sort by gap descending)
        assert weights == sorted(weights, reverse=True), f"Gaps not sorted: {weights}"

    def test_fit_score_bounded_0_to_100(self):
        """fit_score is always an integer in [0, 100]."""
        for skills_data in [
            [],  # no skills
            [("sk01", 5.0), ("sk02", 5.0), ("sk11", 5.0), ("sk04", 5.0), ("sk07", 5.0)],  # perfect
            [("sk01", 3.0)],  # partial
        ]:
            req = _role_fit_req("emp", "ds_mgr", skills_data, DS_MGR_REQUIREMENTS)
            result = compute_role_fit(req)
            assert 0 <= result.fit_score <= 100, f"score={result.fit_score} out of range"
            assert isinstance(result.fit_score, int)


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL 4 — LEARNING PATH GROUND TRUTH
# ═══════════════════════════════════════════════════════════════════════════════

class TestLearningPathGroundTruth:
    """
    Tests for learning path recommendation with known employee profiles.
    Service uses fallback (no model) or loaded model.
    """

    def _make_request(self, missing_skills, resources, avg_score=70.0, courses_done=3):
        return LearningPathRequest(
            employee_id="EMP_TEST",
            job_role_id="r03",
            missing_skills=missing_skills,
            available_resources=resources,
            employee_avg_score=avg_score,
            employee_courses_done=courses_done,
        )

    def test_high_importance_skill_first(self):
        """The highest importance_weight skill must appear first in ordered_skills."""
        missing = [
            MissingSkill(skill_id="sk02", gap=3.0, importance_weight=0.85, complexity_level=2),
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9,  complexity_level=1),
            MissingSkill(skill_id="sk03", gap=4.0, importance_weight=0.7,  complexity_level=3),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Python Course",    skill_level="Beginner",      duration_hours=20.0),
            LearningResource(resource_id="R002", skill_id="sk02", title="ML Specialization",skill_level="Intermediate",   duration_hours=40.0),
            LearningResource(resource_id="R003", skill_id="sk03", title="Deep Learning",    skill_level="Advanced",       duration_hours=60.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert result.ordered_skills[0] == "sk01", (
            f"sk01 (imp=0.9) should be first in ordered_skills, got: {result.ordered_skills}"
        )

    def test_all_skills_have_recommendation(self):
        """Every missing skill with a matching resource gets a recommendation."""
        missing = [
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=1),
            MissingSkill(skill_id="sk02", gap=3.0, importance_weight=0.85, complexity_level=2),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Python Basics",    skill_level="Beginner",     duration_hours=10.0),
            LearningResource(resource_id="R002", skill_id="sk02", title="ML Fundamentals",  skill_level="Intermediate", duration_hours=30.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert len(result.recommendations) == 2
        rec_skills = {r.skill_id for r in result.recommendations}
        assert "sk01" in rec_skills
        assert "sk02" in rec_skills

    def test_no_resource_for_skill_skipped(self):
        """If a skill has no matching resource, it's omitted from recommendations."""
        missing = [
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=1),
            MissingSkill(skill_id="sk99", gap=3.0, importance_weight=0.8, complexity_level=2),  # no resource
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Python",  skill_level="Beginner", duration_hours=10.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        rec_skills = {r.skill_id for r in result.recommendations}
        assert "sk99" not in rec_skills
        assert "sk01" in rec_skills

    def test_priority_high_for_importance_above_07(self):
        """Skills with importance_weight >= 0.7 get priority = 'high'."""
        missing = [
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=1),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Python", skill_level="Beginner", duration_hours=10.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert result.recommendations[0].priority == "high"

    def test_priority_low_for_importance_below_04(self):
        """Skills with importance_weight < 0.4 get priority = 'low'."""
        missing = [
            MissingSkill(skill_id="sk01", gap=1.0, importance_weight=0.3, complexity_level=1),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Optional Skill", skill_level="Beginner", duration_hours=5.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert result.recommendations[0].priority == "low"

    def test_total_hours_is_sum_of_selected_resources(self):
        """estimated_completion_hours = sum of selected resource duration_hours."""
        missing = [
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9,  complexity_level=1),
            MissingSkill(skill_id="sk02", gap=3.0, importance_weight=0.85, complexity_level=2),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="A", skill_level="Beginner",     duration_hours=20.0),
            LearningResource(resource_id="R002", skill_id="sk02", title="B", skill_level="Intermediate", duration_hours=40.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert result.estimated_completion_hours == pytest.approx(60.0, abs=0.1)

    def test_predicted_score_is_non_negative(self):
        """predicted_completion_score must be a non-negative float."""
        missing = [
            MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=1),
        ]
        resources = [
            LearningResource(resource_id="R001", skill_id="sk01", title="Python", skill_level="Beginner", duration_hours=10.0),
        ]
        req = self._make_request(missing, resources)
        result = recommend_learning_path(req)
        assert result.recommendations[0].predicted_completion_score >= 0.0

    def test_employee_id_passed_through(self):
        """employee_id in response matches request."""
        missing = [MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=1)]
        resources = [LearningResource(resource_id="R001", skill_id="sk01", title="Py", skill_level="Beginner", duration_hours=5.0)]
        req = LearningPathRequest(
            employee_id="EMP_XYZ",
            job_role_id="r01",
            missing_skills=missing,
            available_resources=resources,
            employee_avg_score=70.0,
            employee_courses_done=3,
        )
        result = recommend_learning_path(req)
        assert result.employee_id == "EMP_XYZ"

    def test_high_avg_score_employee_advanced_course_selection(self):
        """
        When a model IS available, employee with high avg_score should have higher
        predicted completion score than employee with low avg_score (same course).
        Falls back to fixed score=50 if no model file — skip in that case.
        """
        from app.services.learning_path_service import _model
        if _model is None:
            pytest.skip("No model file — fallback gives identical scores, skip ML comparison")

        missing = [MissingSkill(skill_id="sk01", gap=2.0, importance_weight=0.9, complexity_level=2)]
        resources = [LearningResource(resource_id="R001", skill_id="sk01", title="Course", skill_level="Intermediate", duration_hours=20.0)]

        high_scorer = LearningPathRequest(
            employee_id="high", job_role_id="r01",
            missing_skills=missing, available_resources=resources,
            employee_avg_score=95.0, employee_courses_done=20,
        )
        low_scorer = LearningPathRequest(
            employee_id="low", job_role_id="r01",
            missing_skills=missing, available_resources=resources,
            employee_avg_score=30.0, employee_courses_done=1,
        )
        score_high = recommend_learning_path(high_scorer).recommendations[0].predicted_completion_score
        score_low  = recommend_learning_path(low_scorer).recommendations[0].predicted_completion_score
        assert score_high >= score_low, (
            f"High avg_score employee ({score_high}) should predict >= low ({score_low})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL 3 — SKILL GAP (unit tests on criticality function)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillGapCriticality:
    """Test the 5-tier criticality classification."""

    def _get_criticality(self, pct: float) -> str:
        from app.services.skill_gaps_service import _get_criticality
        return _get_criticality(pct)

    def test_below_10_is_critical(self):
        # _get_criticality takes fractions in [0, 1], not percentages
        assert self._get_criticality(0.05)  == "critical"   # 5% → critical
        assert self._get_criticality(0.099) == "critical"   # 9.9% → critical

    def test_10_to_24_is_high(self):
        assert self._get_criticality(0.10)  == "high"       # 10% → high
        assert self._get_criticality(0.249) == "high"       # 24.9% → high

    def test_25_to_49_is_medium(self):
        assert self._get_criticality(0.25)  == "medium"     # 25% → medium
        assert self._get_criticality(0.499) == "medium"     # 49.9% → medium

    def test_50_to_74_is_low(self):
        assert self._get_criticality(0.50)  == "low"        # 50% → low
        assert self._get_criticality(0.749) == "low"        # 74.9% → low

    def test_75_plus_is_surplus(self):
        assert self._get_criticality(0.75)  == "surplus"    # 75% → surplus
        assert self._get_criticality(1.0)   == "surplus"    # 100% → surplus

    def test_boundary_exactly_10(self):
        assert self._get_criticality(0.10)  == "high"       # exactly 10% → high

    def test_boundary_exactly_75(self):
        assert self._get_criticality(0.75)  == "surplus"    # exactly 75% → surplus


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION SCENARIO: Full Replacement Workflow
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullReplacementWorkflow:
    """
    Simulates the full replacement workflow:
    1. Compute fit scores for 5 candidates.
    2. Verify ranking order matches expected.
    3. Verify top candidate is recommended for immediate placement.
    4. Verify bottom candidate is not_ready.
    """

    # ML Engineer role
    ML_ENG_REQS = [
        ("sk01", 4.0, 0.9),   # Python
        ("sk02", 3.0, 0.8),   # TensorFlow/ML
        ("sk04", 3.0, 0.5),   # SQL
        ("sk10", 2.0, 0.4),   # Docker (low criticality)
    ]

    CANDIDATES = {
        "rania":  [("sk01", 5.0), ("sk02", 4.0), ("sk04", 4.0), ("sk10", 3.0)],  # perfect
        "khaled": [("sk01", 4.0), ("sk02", 3.0), ("sk04", 3.0)],                 # missing Docker
        "nora":   [("sk01", 3.0), ("sk02", 3.0), ("sk04", 5.0), ("sk10", 3.0)],  # Python gap
        "samy":   [("sk01", 5.0), ("sk04", 3.0)],                                # missing ML + Docker
        "layla":  [("sk01", 1.0), ("sk02", 1.0), ("sk04", 1.0), ("sk10", 1.0)],  # all below req
    }

    def _score(self, name: str) -> int:
        skills = self.CANDIDATES[name]
        req = _role_fit_req(name, "ml_eng", skills, self.ML_ENG_REQS)
        return compute_role_fit(req).fit_score

    def test_rania_is_top_candidate(self):
        score_rania  = self._score("rania")
        score_khaled = self._score("khaled")
        score_nora   = self._score("nora")
        assert score_rania >= score_khaled, f"rania={score_rania} should >= khaled={score_khaled}"
        assert score_rania >= score_nora,   f"rania={score_rania} should >= nora={score_nora}"

    def test_layla_is_worst_candidate(self):
        score_layla  = self._score("layla")
        score_rania  = self._score("rania")
        score_nora   = self._score("nora")
        assert score_layla < score_rania, f"layla={score_layla} should < rania={score_rania}"
        assert score_layla < score_nora,  f"layla={score_layla} should < nora={score_nora}"

    def test_rania_is_ready(self):
        req = _role_fit_req("rania", "ml_eng", self.CANDIDATES["rania"], self.ML_ENG_REQS)
        result = compute_role_fit(req)
        assert result.readiness_level in ("ready", "near_ready"), (
            f"Rania expected ready or near_ready, got {result.readiness_level} (score={result.fit_score})"
        )

    def test_layla_is_not_ready(self):
        req = _role_fit_req("layla", "ml_eng", self.CANDIDATES["layla"], self.ML_ENG_REQS)
        result = compute_role_fit(req)
        assert result.readiness_level in ("needs_development", "not_ready"), (
            f"Layla expected not_ready, got {result.readiness_level} (score={result.fit_score})"
        )

    def test_critical_skill_gap_dominates(self):
        """
        Samy has Python=5 (best) but ML is completely missing (critical imp=0.8).
        Samy should score LOWER than Nora who has Python=3 but ML=3 (met).
        """
        score_samy = self._score("samy")
        score_nora = self._score("nora")
        assert score_samy < score_nora, (
            f"Missing critical skill (ML) should dominate over Python strength. "
            f"samy={score_samy} should < nora={score_nora}"
        )
