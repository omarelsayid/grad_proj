"""
Model 3: Org-Level Skill Gap Analysis
Demand vs. Supply mapping across departments.

No ML training needed — pure aggregation analytics.
Saves a precomputed baseline DataFrame so the FastAPI service can serve
org-wide gaps instantly, then refreshes it from the live DB when called.
"""

import os
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "models")
DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("MODEL 3: ORG-LEVEL SKILL GAP ANALYSIS")
print("=" * 80)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_and_clean(filename: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, filename))
    df.columns = df.columns.str.replace(r"^\ufeff", "", regex=True).str.strip()
    return df


def get_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of {candidates} found. Available: {df.columns.tolist()}")


def get_criticality(ratio: float) -> str:
    if ratio >= 2.0:
        return "critical"
    elif ratio >= 1.5:
        return "high"
    elif ratio >= 1.2:
        return "medium"
    return "low"


# ─── Load data ───────────────────────────────────────────────────────────────

print("\nLoading data...")
employee_skills = load_and_clean("employee_skill_matrix.csv")
job_requirements = load_and_clean("job_role_requirements.csv")
skills_catalog   = load_and_clean("skills_catalog.csv")

# Optional: profiles with department+role for headcount weighting
try:
    profiles = load_and_clean("employee_profiles.csv")
    has_profiles = True
    print("  employee_profiles.csv loaded — using real headcount per role.")
except FileNotFoundError:
    profiles = None
    has_profiles = False
    print("  employee_profiles.csv not found — each role weighted equally.")

print(f"\nEmployee skills:  {employee_skills.shape}")
print(f"Job requirements: {job_requirements.shape}")
print(f"Skills catalog:   {skills_catalog.shape}")

# ─── Detect columns ──────────────────────────────────────────────────────────

emp_id_col  = get_col(employee_skills, ["employee_id", "Employee_id"])
emp_sk_col  = get_col(employee_skills, ["skill_id",    "Skill_id"])
emp_pr_col  = get_col(employee_skills, ["proficiency", "Proficiency"])

job_role_col = get_col(job_requirements, ["job_role_id",      "Job_role_id"])
job_sk_col   = get_col(job_requirements, ["required_skill_id","skill_id",   "Required_skill_id"])
job_min_col  = get_col(job_requirements, ["min_proficiency",  "Min_proficiency"])
job_wt_col   = get_col(job_requirements, ["importance_weight","Importance_weight"])

cat_sk_col   = get_col(skills_catalog, ["skill_id",   "Skill_id"])
cat_name_col = get_col(skills_catalog, ["skill_name", "Skill_name", "name", "Name"])

# ─── Compute Supply: average proficiency per skill ────────────────────────────

print("\nComputing skill supply...")
supply = (
    employee_skills
    .groupby(emp_sk_col)[emp_pr_col]
    .agg(avg_proficiency="mean", proficiency_std="std", employee_count="count")
    .reset_index()
    .rename(columns={emp_sk_col: "skill_id"})
)
supply["proficiency_std"] = supply["proficiency_std"].fillna(0)
print(f"Skills with supply data: {len(supply)}")

# ─── Compute Demand: weighted requirements per skill ─────────────────────────

print("Computing skill demand...")

if has_profiles:
    role_col_prof = get_col(profiles, ["job_role_id", "role_id", "position"])
    headcount = profiles[role_col_prof].value_counts().to_dict()
else:
    headcount = {r: 1 for r in job_requirements[job_role_col].unique()}

demand_records = []
dept_skill_map: dict[str, list[str]] = {}   # skill_id -> list of departments

for _, row in job_requirements.iterrows():
    role_id    = row[job_role_col]
    skill_id   = str(row[job_sk_col])
    min_prof   = float(row[job_min_col])
    importance = float(row[job_wt_col])
    count      = int(headcount.get(role_id, 1))

    demand_records.append({
        "skill_id":        skill_id,
        "role_id":         role_id,
        "weighted_demand": min_prof * importance * count,
        "importance":      importance,
        "headcount":       count,
    })

    dept_skill_map.setdefault(skill_id, [])
    role_str = str(role_id)
    if role_str not in dept_skill_map[skill_id]:
        dept_skill_map[skill_id].append(role_str)

demand_df = pd.DataFrame(demand_records)
demand = (
    demand_df
    .groupby("skill_id")
    .agg(
        total_demand=("weighted_demand", "sum"),
        roles_requiring=("role_id", "nunique"),
        avg_importance=("importance", "mean"),
    )
    .reset_index()
)
print(f"Skills with demand data: {len(demand)}")

# ─── Merge and compute gap ratios ─────────────────────────────────────────────

print("Computing gap ratios...")
analysis = demand.merge(supply, on="skill_id", how="outer")
analysis["avg_proficiency"] = analysis["avg_proficiency"].fillna(0)
analysis["total_demand"]    = analysis["total_demand"].fillna(0)
analysis["employee_count"]  = analysis["employee_count"].fillna(0)

# Total supply: avg proficiency x number of employees who have this skill
analysis["total_supply"] = analysis["avg_proficiency"] * analysis["employee_count"]

# gap_ratio = demand / supply (capped at 10 to avoid ∞)
analysis["gap_ratio"] = analysis.apply(
    lambda r: min(r["total_demand"] / (r["total_supply"] + 1e-8), 10.0),
    axis=1,
)

# Normalised gap score 0–1
max_ratio = analysis["gap_ratio"].max()
analysis["gap_score"] = analysis["gap_ratio"] / (max_ratio + 1e-8)

analysis["criticality"]         = analysis["gap_ratio"].apply(get_criticality)
analysis["departments_affected"] = analysis["skill_id"].map(
    lambda s: dept_skill_map.get(str(s), [])
)

# Attach skill names
skill_name_map = dict(zip(skills_catalog[cat_sk_col], skills_catalog[cat_name_col]))
analysis["skill_name"] = analysis["skill_id"].map(skill_name_map)

analysis = analysis.sort_values("gap_ratio", ascending=False).reset_index(drop=True)

print(f"\nTotal skills analysed: {len(analysis)}")
print(f"Critical:              {(analysis['criticality'] == 'critical').sum()}")
print(f"High:                  {(analysis['criticality'] == 'high').sum()}")
print(f"Medium:                {(analysis['criticality'] == 'medium').sum()}")
print(f"Low / met:             {(analysis['criticality'] == 'low').sum()}")

print("\nTop 10 Skill Gaps:")
print("-" * 80)
print(
    analysis[["skill_id", "skill_name", "total_demand",
              "total_supply", "gap_ratio", "criticality"]]
    .head(10)
    .to_string(index=False)
)

# ─── Department-level drill-down ──────────────────────────────────────────────

print("\nBuilding department-level summaries...")
dept_records = []
for _, row in analysis.iterrows():
    for dept in row["departments_affected"]:
        dept_records.append({
            "department": dept,
            "skill_id":   row["skill_id"],
            "gap_ratio":  row["gap_ratio"],
            "criticality":row["criticality"],
        })

dept_df = pd.DataFrame(dept_records)
if not dept_df.empty:
    dept_summary = (
        dept_df
        .groupby("department")
        .agg(
            n_skills=("skill_id", "nunique"),
            avg_gap=("gap_ratio", "mean"),
            critical_count=("criticality", lambda x: (x == "critical").sum()),
        )
        .reset_index()
        .sort_values("avg_gap", ascending=False)
    )
    print("\nDepartment Summary (by avg gap):")
    print(dept_summary.to_string(index=False))

# ─── Visualisations ───────────────────────────────────────────────────────────

print("\nGenerating visualisations...")

colors = {"critical": "#d32f2f", "high": "#f57c00", "medium": "#fbc02d", "low": "#388e3c"}

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

top20 = analysis.head(20)
bar_colors = [colors[c] for c in top20["criticality"]]
labels = top20["skill_name"].fillna(top20["skill_id"])
axes[0].barh(labels[::-1], top20["gap_ratio"][::-1], color=bar_colors[::-1])
axes[0].set_xlabel("Gap Ratio (Demand / Supply)")
axes[0].set_title("Top 20 Skill Gaps by Gap Ratio", fontweight="bold")

crit_counts = analysis["criticality"].value_counts()
pie_colors  = [colors.get(c, "gray") for c in crit_counts.index]
axes[1].pie(crit_counts, labels=crit_counts.index, autopct="%1.1f%%", colors=pie_colors)
axes[1].set_title("Skill Gap Criticality Distribution", fontweight="bold")

plt.tight_layout()
plt.savefig("skill_gap_analysis.png", dpi=150)
plt.close()
print("Saved skill_gap_analysis.png")

# Heatmap: top 15 skills vs demand/supply
fig2, ax = plt.subplots(figsize=(12, 6))
top15 = analysis.head(15).copy()
top15.index = top15["skill_name"].fillna(top15["skill_id"])
heat_data = top15[["total_demand", "total_supply", "gap_ratio"]]
sns.heatmap(heat_data, annot=True, fmt=".2f", cmap="RdYlGn_r", ax=ax)
ax.set_title("Top 15 Skills — Demand / Supply / Gap Ratio", fontweight="bold")
plt.tight_layout()
plt.savefig("skill_gap_heatmap.png", dpi=150)
plt.close()
print("Saved skill_gap_heatmap.png")

# ─── Save results ─────────────────────────────────────────────────────────────

analysis.to_csv("skill_gap_analysis_results.csv", index=False)
print("Saved skill_gap_analysis_results.csv")

# Save serialised baseline for FastAPI service
baseline_path = os.path.join(OUTPUT_DIR, "skill_gap_baseline.pkl")
joblib.dump(analysis, baseline_path)
print(f"Saved skill_gap_baseline -> {baseline_path}")

print("\nModel 3 analysis complete.")
