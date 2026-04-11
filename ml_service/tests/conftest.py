"""
Shared pytest fixtures for SkillSync ML test suite.

All fixtures produce minimal but realistic synthetic data that mirrors the
actual CSV schemas discovered in Data/.  Tests run without the real CSVs or a
trained model on disk.
"""

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Turnover dataset (mirrors turnover_ml_dataset.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def turnover_df():
    """
    Minimal synthetic turnover dataset — 60 rows, realistic column names.
    30 % turnover rate matches the real dataset distribution.
    """
    rng = np.random.default_rng(0)
    n = 60
    df = pd.DataFrame({
        "employee_id":               [f"EMP-{i:04d}" for i in range(1, n + 1)],
        "job_role_id":               rng.integers(1, 25, n),
        "department_id":             rng.integers(1, 9,  n),
        "gender_enc":                rng.integers(0, 2,  n),
        "age":                       rng.integers(22, 55, n),
        "tenure_years":              rng.uniform(0.1, 10, n),
        "total_working_years":       rng.integers(1, 20, n),
        "years_since_last_promotion":rng.integers(0, 5,  n),
        "salary_egp":                rng.integers(8_000, 35_000, n),
        "overtime_enc":              rng.integers(0, 2, n),
        "leave_balance":             rng.integers(0, 21, n),
        "commute_distance_km":       rng.uniform(1, 50, n),
        "commute_category_enc":      rng.integers(0, 3,  n),
        "absence_rate":              rng.uniform(0, 0.2, n),
        "late_rate":                 rng.uniform(0, 0.3, n),
        "half_day_rate":             rng.uniform(0, 0.1, n),
        "total_early_leave_min":     rng.integers(0, 5000, n),
        "total_overtime_hours":      rng.uniform(0, 200, n),
        "attendance_score":          rng.uniform(60, 100, n),
        "avg_worked_hours":          rng.uniform(6, 10, n),
        "courses_completed":         rng.integers(0, 10, n),
        "avg_training_score":        rng.uniform(0, 100, n),
        "avg_feedback_score":        rng.uniform(1, 5, n),
        "latest_eval_score":         rng.uniform(30, 100, n),
        "kpi_score":                 rng.uniform(30, 100, n),
        "work_life_balance":         rng.uniform(1, 5, n),
        "role_fit_score":            rng.uniform(20, 100, n),
        "turnover_label":            rng.choice([0, 1], n, p=[0.7, 0.3]),
    })
    # Introduce ~10 % missing values in avg_feedback_score (mirrors real data)
    mask = rng.choice([True, False], n, p=[0.1, 0.9])
    df.loc[mask, "avg_feedback_score"] = np.nan
    return df


# ---------------------------------------------------------------------------
# Employee skill matrix (mirrors employee_skill_matrix.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def employee_skills_df():
    rng = np.random.default_rng(1)
    employees = [f"EMP-{i:04d}" for i in range(1, 21)]
    skills     = [f"SK-{i:03d}" for i in range(101, 121)]
    records    = []
    for emp in employees:
        # Each employee has 5–12 random skills
        chosen = rng.choice(skills, size=rng.integers(5, 13), replace=False)
        for sk in chosen:
            records.append({
                "employee_id":       emp,
                "skill_id":          sk,
                "proficiency":       int(rng.integers(1, 6)),
                "verification_status": rng.choice(["Verified", "Unverified"]),
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Job role requirements (mirrors job_role_requirements.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def job_requirements_df():
    rng = np.random.default_rng(2)
    roles  = list(range(1, 6))
    skills = [f"SK-{i:03d}" for i in range(101, 121)]
    records = []
    for role in roles:
        chosen = rng.choice(skills, size=rng.integers(3, 8), replace=False)
        for sk in chosen:
            records.append({
                "job_role_id":       role,
                "required_skill_id": sk,
                "min_proficiency":   int(rng.integers(1, 4)),
                "importance_weight": round(float(rng.uniform(0.1, 1.0)), 2),
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Skills catalog (mirrors skills_catalog.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def skills_catalog_df():
    domains = ["Technical", "Management", "Communication", "Data Science", "DevOps"]
    records = []
    for i in range(101, 141):
        records.append({
            "skill_id":        f"SK-{i:03d}",
            "skill_name":      f"Skill {i}",
            "domain":          domains[i % len(domains)],
            "complexity_level": (i % 3) + 1,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Skill gap dataset (mirrors skill_gap_dataset.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def skill_gap_df(employee_skills_df, job_requirements_df):
    """
    Generates a skill-gap dataset by merging employee skills against role
    requirements — mirroring how the real CSV is produced.
    """
    rng = np.random.default_rng(3)
    records = []
    for _, req in job_requirements_df.iterrows():
        emp_id = f"EMP-{rng.integers(1, 21):04d}"
        emp_row = employee_skills_df[
            (employee_skills_df["employee_id"] == emp_id) &
            (employee_skills_df["skill_id"]    == req["required_skill_id"])
        ]
        current = int(emp_row["proficiency"].iloc[0]) if not emp_row.empty else 0
        gap     = max(int(req["min_proficiency"]) - current, 0)
        severity_map = {0: "None", 1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
        records.append({
            "employee_id":         emp_id,
            "job_role_id":         req["job_role_id"],
            "skill_id":            req["required_skill_id"],
            "required_proficiency":req["min_proficiency"],
            "current_proficiency": current,
            "gap":                 gap,
            "gap_severity":        severity_map.get(gap, "High"),
            "importance_weight":   req["importance_weight"],
            "priority_score":      gap * req["importance_weight"],
            "recommended_resource_id": f"LR-{rng.integers(1, 10):03d}",
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Learning resources (mirrors learning_resources.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def learning_resources_df():
    rng = np.random.default_rng(4)
    skills = [f"SK-{i:03d}" for i in range(101, 121)]
    records = []
    for i in range(1, 31):
        records.append({
            "resource_id":    f"LR-{i:03d}",
            "title":          f"Course {i}",
            "type":           rng.choice(["Course", "Certification", "Mentorship", "Project"]),
            "duration_hours": float(rng.integers(4, 20)),
            "priority":       rng.choice(["High", "Medium", "Low"]),
            "target_skill_id":skills[i % len(skills)],
            "provider":       rng.choice(["Coursera", "edX", "Udemy", "Internal"]),
            "category":       rng.choice(["Technical", "Soft Skills", "Data Science"]),
            "skill_level":    rng.choice(["Beginner", "Intermediate", "Advanced"]),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Training history (mirrors training_history.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def training_history_df():
    rng = np.random.default_rng(5)
    n = 80
    employees = [f"EMP-{i:04d}" for i in range(1, 21)]
    resources = [f"LR-{i:03d}" for i in range(1, 31)]
    return pd.DataFrame({
        "training_id":         [f"TRN-{i:05d}" for i in range(1, n + 1)],
        "employee_id":         rng.choice(employees, n),
        "resource_id":         rng.choice(resources, n),
        "resource_title":      [f"Course {i}" for i in range(1, n + 1)],
        "completion_date":     ["2024-01-01"] * n,
        "completion_score":    rng.uniform(40, 100, n),
        "duration_hours":      rng.uniform(4, 20, n),
        "feedback_score":      rng.uniform(1, 5, n),
        "attempt_number":      rng.integers(1, 3, n),
        "status":              ["Completed"] * n,
        "validated_by_manager":rng.choice(["Yes", "No"], n),
    })


# ---------------------------------------------------------------------------
# Training skill map (mirrors training_skill_map.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def training_skill_map_df(training_history_df):
    skills = [f"SK-{i:03d}" for i in range(101, 121)]
    rng = np.random.default_rng(6)
    records = []
    for tid in training_history_df["training_id"].unique():
        records.append({
            "training_id": tid,
            "skill_id":    rng.choice(skills),
            "is_primary":  True,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Skill chain DAG (mirrors skill_chain_dag.csv)
# ---------------------------------------------------------------------------

@pytest.fixture()
def skill_chain_dag_df():
    """Acyclic prerequisite chain: SK-101 → SK-102 → SK-103, SK-101 → SK-104."""
    return pd.DataFrame({
        "prerequisite_skill_id": ["SK-101", "SK-102", "SK-101", "SK-103"],
        "target_skill_id":       ["SK-102", "SK-103", "SK-104", "SK-105"],
        "weight":                [0.9, 0.8, 0.8, 0.7],
    })
