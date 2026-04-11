from typing import Optional
from pydantic import BaseModel


class SkillGapEntry(BaseModel):
    skill_id: str
    skill_name: Optional[str] = None
    demand_score: float
    supply_score: float
    gap_ratio: float        # 1 - pct_employees_meeting (higher = more critical)
    criticality: str        # "critical" | "high" | "medium" | "low" | "surplus"
    departments_affected: list[str]


class DepartmentGapSummary(BaseModel):
    department: str
    top_gaps: list[SkillGapEntry]
    overall_gap_score: float


class SkillGapsResponse(BaseModel):
    total_skills_analyzed: int
    critical_skills: int
    skill_gaps: list[SkillGapEntry]
    department_summaries: list[DepartmentGapSummary]
