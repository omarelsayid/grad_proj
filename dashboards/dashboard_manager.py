"""SkillSync · Manager Analytics Dashboard  —  streamlit run dashboard_manager.py --server.port 8502"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st

from db_connection import query_df, query_scalar, query_one
from api_client import login_user, predict_role_fit_ml

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillSync · Manager Analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme ─────────────────────────────────────────────────────────────────────
RISK_COLORS = {"critical":"#dc2626","high":"#f97316","medium":"#eab308","low":"#22c55e"}
PROF_COLORS = ["#f1f5f9","#fecaca","#fed7aa","#fef9c3","#bbf7d0","#16a34a"]  # 0-5

st.markdown("""
<style>
.block-container { padding-top: 1.25rem; }

[data-testid="metric-container"] {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.dash-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0369a1 100%);
    color: white; padding: 1.25rem 1.75rem;
    border-radius: 14px; margin-bottom: 1.25rem;
}
.dash-header h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }
.dash-header p  { margin: 0.3rem 0 0; font-size: 0.85rem; opacity: 0.82; }

.section-header { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 0.6rem; }

.risk-flag {
    background: #fff7ed; border: 1px solid #fed7aa;
    border-left: 4px solid #f97316; border-radius: 8px;
    padding: 0.6rem 1rem; margin-bottom: 0.45rem; font-size: 0.88rem;
}
.risk-flag-critical {
    background: #fef2f2; border-color: #fecaca;
    border-left-color: #dc2626;
}
.stale-badge {
    background: #fef2f2; color: #991b1b;
    border-radius: 999px; padding: 2px 8px; font-size: 11px; font-weight: 600;
}
.user-card {
    background: #f0f9ff; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;
}
.candidate-card {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 0.85rem 1rem; margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════════════════════════════════════

def _sidebar_login():
    st.sidebar.markdown("## Manager Analytics")
    st.sidebar.markdown("---")
    with st.sidebar.form("login"):
        email    = st.text_input("Email",    value="tarek.mansour@skillsync.dev")
        password = st.text_input("Password", type="password", placeholder="Manager@123")
        submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
    if submitted:
        if not email or not password:
            st.sidebar.error("Enter both fields.")
            return
        try:
            result = login_user(email, password)
            # API returns { role, employee, accessToken, refreshToken } at top level
            role   = result.get("role", "")
            emp_data = result.get("employee") or {}
            user = {
                "id":    emp_data.get("id", ""),
                "name":  emp_data.get("name", email),
                "email": email,
                "role":  role,
            }
            if role not in ("manager", "hr_admin"):
                st.sidebar.error(f"Manager role required (got: '{role}').")
                return
            # Resolve manager's department from DB
            emp = query_one(
                "SELECT id, name, department FROM employees WHERE user_id = %s",
                (emp_data.get("userId", emp_data.get("user_id", "")),)
            )
            user["_department"] = emp["department"] if emp else None
            user["_emp_id"]     = emp["id"]         if emp else None
            st.session_state["mgr_user"]  = user
            st.session_state["mgr_token"] = result.get("accessToken", "")
            st.rerun()
        except requests.ConnectionError:
            st.sidebar.error("Cannot reach API (port 3000). Is Node.js running?")
        except requests.HTTPError as exc:
            st.sidebar.error(f"Login failed ({exc.response.status_code}).")
        except Exception as exc:
            st.sidebar.error(f"Error: {exc}")


def _sidebar_user(department: str):
    u = st.session_state["mgr_user"]
    st.sidebar.markdown(
        f"<div class='user-card'>"
        f"<b>{u.get('name', u.get('email',''))}</b><br>"
        f"<span style='font-size:0.8rem;color:#64748b'>{u.get('email','')}</span><br>"
        f"<span style='font-size:0.75rem;color:#0369a1'>Manager</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(f"**Team Dept:** {department}")
    now = datetime.now()
    st.sidebar.markdown(f"{now.strftime('%H:%M')} · {now.strftime('%d %b %Y')}")
    if st.sidebar.button("Refresh all data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.pop("mgr_user",  None)
        st.session_state.pop("mgr_token", None)
        st.rerun()
    st.sidebar.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# Data fetchers
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def _team(department: str) -> pd.DataFrame:
    return query_df(
        "SELECT e.id, e.name, e.current_role, e.role_id, e.satisfaction_score FROM employees e WHERE e.department = %s ORDER BY e.name LIMIT 10",
        (department,)
    )


@st.cache_data(ttl=300)
def _team_kpis(department: str) -> dict:
    headcount = min(10, query_scalar(
        "SELECT COUNT(*) FROM employees WHERE department = %s", (department,)
    ) or 0)

    att_rate = query_scalar("""
        SELECT ROUND(100.0 *
            COUNT(CASE WHEN a.status IN ('present','remote') THEN 1 END)
            / NULLIF(COUNT(*), 0), 1)
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE e.department = %s AND a.date >= CURRENT_DATE - INTERVAL '30 days'
    """, (department,)) or 0

    pending_leaves = query_scalar("""
        SELECT COUNT(*) FROM leave_requests lr
        JOIN employees e ON e.id = lr.employee_id
        WHERE e.department = %s AND lr.status = 'pending'
    """, (department,)) or 0

    at_risk_count = query_scalar("""
        SELECT COUNT(*) FROM turnover_risk_cache trc
        JOIN employees e ON e.id = trc.employee_id
        WHERE e.department = %s AND trc.risk_score > 55
    """, (department,)) or 0

    return {
        "headcount":     int(headcount),
        "att_rate":      float(att_rate),
        "pending_leaves":int(pending_leaves),
        "at_risk":       int(at_risk_count),
    }


@st.cache_data(ttl=300)
def _skill_heatmap_data(department: str) -> pd.DataFrame:
    return query_df("""
        SELECT e.name AS employee, s.name AS skill, es.proficiency
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        JOIN skills s    ON s.id = es.skill_id
        WHERE e.department = %s
        ORDER BY e.name, s.name
    """, (department,))


@st.cache_data(ttl=30)   # short TTL — live check-in data
def _todays_checkins(department: str) -> pd.DataFrame:
    return query_df("""
        SELECT e.name, e.current_role,
               a.check_in, a.check_out, a.status,
               CASE WHEN a.check_in > '09:15' THEN true ELSE false END AS is_late
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE e.department = %s AND a.date = CURRENT_DATE
        ORDER BY a.check_in ASC NULLS LAST
    """, (department,))


@st.cache_data(ttl=300)
def _role_req_df(department: str) -> pd.DataFrame:
    """Required skills for all roles in the department (for heatmap annotation)."""
    return query_df("""
        SELECT DISTINCT s.name AS skill, rrs.min_proficiency
        FROM role_required_skills rrs
        JOIN skills s   ON s.id = rrs.skill_id
        JOIN job_roles jr ON jr.id = rrs.role_id
        WHERE jr.department = %s
    """, (department,))


@st.cache_data(ttl=300)
def _attendance_trend(department: str) -> pd.DataFrame:
    return query_df("""
        SELECT
            date_trunc('week', a.date::date) AS week_start,
            COUNT(CASE WHEN a.status IN ('present','remote') THEN 1 END) AS present_count,
            COUNT(*) AS total_count
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE e.department = %s
          AND a.date >= CURRENT_DATE - INTERVAL '28 days'
        GROUP BY week_start
        ORDER BY week_start
    """, (department,))


@st.cache_data(ttl=120)
def _pending_leaves(department: str) -> pd.DataFrame:
    return query_df("""
        SELECT
            e.name,
            lr.leave_type,
            lr.start_date,
            lr.end_date,
            lr.reason,
            lr.created_at,
            EXTRACT(EPOCH FROM (NOW() - lr.created_at)) / 3600 AS hours_pending
        FROM leave_requests lr
        JOIN employees e ON e.id = lr.employee_id
        WHERE e.department = %s AND lr.status = 'pending'
        ORDER BY lr.created_at ASC
    """, (department,))


@st.cache_data(ttl=300)
def _risk_flags(department: str) -> pd.DataFrame:
    return query_df("""
        SELECT e.name, e.current_role, trc.risk_score, trc.risk_level
        FROM turnover_risk_cache trc
        JOIN employees e ON e.id = trc.employee_id
        WHERE e.department = %s AND trc.risk_score > 55
        ORDER BY trc.risk_score DESC
    """, (department,))


@st.cache_data(ttl=300)
def _role_requirements(role_id: str) -> list[dict]:
    df = query_df("""
        SELECT rrs.skill_id, s.name AS skill_name,
               rrs.min_proficiency, rrs.importance_weight
        FROM role_required_skills rrs
        JOIN skills s ON s.id = rrs.skill_id
        WHERE rrs.role_id = %s
    """, (role_id,))
    return df.to_dict("records")


@st.cache_data(ttl=300)
def _employee_skills_list(employee_id: str) -> list[dict]:
    df = query_df(
        "SELECT skill_id, proficiency FROM employee_skills WHERE employee_id = %s",
        (employee_id,)
    )
    return df.to_dict("records")


@st.cache_data(ttl=600)
def _replacement_candidates(departing_id: str, role_id: str, department: str) -> list[dict]:
    """Score candidates outside the team for the departing employee's role."""
    reqs = _role_requirements(role_id)
    if not reqs:
        return []

    # Load all employees NOT in same department as candidates
    cands_df = query_df("""
        SELECT e.id, e.name, e.current_role, e.department
        FROM employees e
        WHERE e.id != %s
        ORDER BY e.name
        LIMIT 40
    """, (departing_id,))

    results = []
    for _, cand in cands_df.iterrows():
        skills = _employee_skills_list(cand["id"])
        payload = {
            "employee_id":      cand["id"],
            "job_role_id":      role_id,
            "employee_skills":  [{"skill_id": s["skill_id"], "proficiency": s["proficiency"]} for s in skills],
            "role_requirements":[{"skill_id": r["skill_id"], "min_proficiency": r["min_proficiency"],
                                  "importance_weight": r["importance_weight"]} for r in reqs],
        }
        try:
            resp = predict_role_fit_ml(payload)
            results.append({
                "name":          cand["name"],
                "department":    cand["department"],
                "current_role":  cand["current_role"],
                "fit_score":     resp.get("fit_score", 0),
                "readiness":     resp.get("readiness_level", "unknown"),
                "matching":      resp.get("matching_skills", []),
                "missing":       resp.get("missing_skills", []),
            })
        except Exception:
            # ML service unavailable or error — use a local skill-match score
            met = sum(1 for r in reqs if any(
                s["skill_id"] == r["skill_id"] and s["proficiency"] >= r["min_proficiency"]
                for s in skills
            ))
            local_score = int(100 * met / len(reqs)) if reqs else 0
            results.append({
                "name":         cand["name"],
                "department":   cand["department"],
                "current_role": cand["current_role"],
                "fit_score":    local_score,
                "readiness":    "estimated (ML offline)",
                "matching":     [],
                "missing":      [],
            })

    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results[:5]


# ══════════════════════════════════════════════════════════════════════════════
# Tab renderers
# ══════════════════════════════════════════════════════════════════════════════

def _tab_overview(department: str):
    kpis = _team_kpis(department)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Team Size", kpis["headcount"])
    with c2:
        r = kpis["att_rate"]
        st.metric("Attendance (30d)", f"{r:.1f}%",
                  delta="Healthy" if r >= 85 else "⚠ Below 85%",
                  delta_color="normal" if r >= 85 else "inverse")
    with c3:
        pl = kpis["pending_leaves"]
        st.metric("Pending Leaves", pl,
                  delta="Awaiting action" if pl else None,
                  delta_color="inverse" if pl else "off")
    with c4:
        ar = kpis["at_risk"]
        st.metric("At-Risk Members", ar,
                  delta="Needs attention" if ar else "All clear",
                  delta_color="inverse" if ar else "off")

    st.markdown("---")
    col_l, col_r = st.columns([2, 3])

    with col_l:
        # Subtle risk flags — sensitive, shown as compact cards
        flags = _risk_flags(department)
        if not flags.empty:
            st.markdown('<div class="section-header">Retention Risk Flags</div>', unsafe_allow_html=True)
            for _, row in flags.iterrows():
                lvl = row["risk_level"]
                cls = "risk-flag-critical" if lvl == "critical" else "risk-flag"
                risk_color = RISK_COLORS.get(lvl, "#64748b")
                st.markdown(
                    f"<div class='{cls}'>"
                    f"<b>{row['name']}</b> · {row['current_role']}<br>"
                    f"<span style='color:{risk_color};font-weight:600'>"
                    f"{lvl.upper()} · {row['risk_score']:.0f}/100</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("No retention risk flags for your team.")

    with col_r:
        st.markdown('<div class="section-header">Team Members</div>', unsafe_allow_html=True)
        team = _team(department)
        if not team.empty:
            disp = team[["name","current_role","satisfaction_score"]].copy()
            disp.columns = ["Name","Role","Satisfaction"]
            disp["Satisfaction"] = disp["Satisfaction"].round(1).astype(str) + " / 100"
            st.dataframe(disp, use_container_width=True, hide_index=True, height=360)

    # Today's live check-ins
    st.markdown("---")
    st.markdown('<div class="section-header">Today\'s Check-ins (live)</div>', unsafe_allow_html=True)
    checkins = _todays_checkins(department)
    if checkins.empty:
        st.info("No check-ins recorded yet today for this department.")
    else:
        checked_in  = checkins[checkins["check_in"].notna()]
        checked_out = checkins[checkins["check_out"].notna()]
        not_in      = _team(department)
        not_in_ids  = set(not_in["name"]) - set(checkins["name"])

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Checked In", len(checked_in))
        mc2.metric("Checked Out", len(checked_out))
        mc3.metric("Not Yet", len(not_in_ids))

        disp = checkins[["name", "current_role", "check_in", "check_out", "status", "is_late"]].copy()
        disp.columns = ["Name", "Role", "Check In", "Check Out", "Status", "Late?"]
        disp["Late?"] = disp["Late?"].map({True: "Late", False: "On time"})
        disp["Check In"]  = disp["Check In"].fillna("—")
        disp["Check Out"] = disp["Check Out"].fillna("ongoing")

        def _row_style(row):
            if row["Late?"] == "⚠ Late":
                return ["background-color:#fef9c3"] * len(row)
            return [""] * len(row)

        st.dataframe(
            disp.style.apply(_row_style, axis=1),
            use_container_width=True, hide_index=True
        )

    # Satisfaction score distribution
    st.markdown("---")
    st.markdown('<div class="section-header">Satisfaction Score Distribution</div>', unsafe_allow_html=True)
    team = _team(department)
    if not team.empty:
        fig = px.histogram(team, x="satisfaction_score", nbins=15,
                           range_x=[0, 100],
                           color_discrete_sequence=["#3b82f6"],
                           labels={"satisfaction_score": "Satisfaction Score (0–100)", "count": "Employees"})
        fig.update_layout(height=240, margin=dict(l=0, r=0, t=5, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)


def _tab_heatmap(department: str):
    team = _team(department)  # already capped at 10
    df = _skill_heatmap_data(department)
    if df.empty or team.empty:
        st.warning("No skill data found for this team. Ensure employees have skills recorded.")
        return

    # Restrict heatmap to the same 10 employees shown elsewhere
    team_names = set(team["name"].tolist())
    df = df[df["employee"].isin(team_names)]
    if df.empty:
        st.warning("No skill records found for the 10 team members.")
        return

    # Pivot: employees × skills
    pivot = df.pivot_table(index="employee", columns="skill", values="proficiency", fill_value=0)

    st.markdown(
        f'<div class="section-header">Team Skill Proficiency Matrix '
        f'— {department} ({len(pivot)} employees × {len(pivot.columns)} skills)</div>',
        unsafe_allow_html=True,
    )

    # Annotation text: show actual value or dash
    text_matrix = pivot.applymap(lambda v: str(int(v)) if v > 0 else "—").values

    colorscale = [
        [0.0,  "#f1f5f9"],  # 0 — not assessed (light gray)
        [0.2,  "#fecaca"],  # 1 — beginner (light red)
        [0.4,  "#fed7aa"],  # 2 — basic (orange)
        [0.6,  "#fef9c3"],  # 3 — intermediate (yellow)
        [0.8,  "#bbf7d0"],  # 4 — advanced (light green)
        [1.0,  "#16a34a"],  # 5 — expert (dark green)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        zmin=0, zmax=5,
        colorscale=colorscale,
        text=text_matrix,
        texttemplate="%{text}",
        hoverongaps=False,
        showscale=True,
        colorbar=dict(
            title="Proficiency",
            tickvals=[0, 1, 2, 3, 4, 5],
            ticktext=["None","Beginner","Basic","Intermediate","Advanced","Expert"],
        ),
    ))
    fig.update_layout(
        height=max(320, len(pivot) * 36 + 80),
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-35, tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=12)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Role requirement overlay
    req_df = _role_req_df(department)
    if not req_df.empty:
        st.markdown("---")
        st.markdown('<div class="section-header">Required Skill Levels for Department Roles</div>', unsafe_allow_html=True)
        disp = req_df.rename(columns={"skill":"Skill","min_proficiency":"Min Proficiency Required"})
        st.dataframe(disp, use_container_width=True, hide_index=True)

    # Coverage summary
    st.markdown("---")
    st.markdown('<div class="section-header">Skill Coverage (% of team meeting or exceeding level 3+)</div>', unsafe_allow_html=True)
    coverage = {}
    for skill in pivot.columns:
        vals = pivot[skill]
        met = int((vals >= 3).sum())
        total = len(vals)
        coverage[skill] = round(100 * met / total, 1)

    cov_df = pd.DataFrame.from_dict(coverage, orient="index", columns=["Coverage %"]).reset_index()
    cov_df.columns = ["Skill", "Coverage %"]
    cov_df = cov_df.sort_values("Coverage %")

    fig2 = px.bar(cov_df, x="Coverage %", y="Skill", orientation="h",
                  color="Coverage %", color_continuous_scale="RdYlGn",
                  range_color=[0, 100],
                  text=cov_df["Coverage %"].apply(lambda x: f"{x:.0f}%"))
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        height=max(300, len(cov_df) * 22 + 60),
        margin=dict(l=0, r=60, t=5, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig2, use_container_width=True)


def _tab_replacements(department: str):
    team = _team(department)
    if team.empty:
        st.warning("No team members found.")
        return

    st.markdown("**Select a team member to find ranked replacement candidates from the wider org:**")
    selected_name = st.selectbox("Employee", team["name"].tolist(), label_visibility="collapsed")
    emp_row = team[team["name"] == selected_name].iloc[0]

    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.markdown(f"""
        <div class="candidate-card">
            <b>Departing:</b> {emp_row['name']}<br>
            <b>Role:</b> {emp_row['current_role']}<br>
            <b>Role ID:</b> {emp_row['role_id']}
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        with st.spinner("Scoring replacement candidates via ML service…"):
            candidates = _replacement_candidates(emp_row["id"], emp_row["role_id"], department)

    if not candidates:
        st.warning("No candidates found or role has no skill requirements configured.")
        return

    st.markdown(f'<div class="section-header">Top {len(candidates)} Replacement Candidates</div>', unsafe_allow_html=True)

    readiness_colors = {
        "ready":             "#22c55e",
        "near_ready":        "#eab308",
        "needs_development": "#f97316",
        "not_ready":         "#ef4444",
    }

    for i, c in enumerate(candidates, 1):
        fit   = c["fit_score"]
        ready = c["readiness"]
        color = readiness_colors.get(ready, "#64748b")

        bar_pct = min(max(fit, 0), 100)
        matching_str = ", ".join(c["matching"][:5]) if c["matching"] else "—"
        missing_str  = ", ".join(c["missing"][:5])  if c["missing"]  else "—"

        st.markdown(f"""
        <div class="candidate-card">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="font-size:1rem;font-weight:700">#{i} {c['name']}</span>
                    &nbsp;<span style="color:#64748b;font-size:0.85rem">{c['current_role']} · {c['department']}</span>
                </div>
                <div style="text-align:right">
                    <span style="font-size:1.3rem;font-weight:800;color:#1e40af">{fit}</span>
                    <span style="font-size:0.75rem;color:#64748b">/100</span>
                    <br><span style="font-size:0.75rem;color:{color};font-weight:600">{ready.replace('_',' ').upper()}</span>
                </div>
            </div>
            <div style="background:#e2e8f0;border-radius:999px;height:6px;margin:8px 0">
                <div style="background:#3b82f6;width:{bar_pct}%;height:6px;border-radius:999px"></div>
            </div>
            <div style="font-size:0.8rem;color:#475569">
                <b>Matching:</b> {matching_str}<br>
                <b>Missing:</b> {missing_str}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _tab_attendance(department: str):
    df = _attendance_trend(department)
    if df.empty:
        st.warning("No attendance records found for the last 28 days.")
        return

    df["week_start"] = pd.to_datetime(df["week_start"])
    df["label"]      = df["week_start"].dt.strftime("Week of %d %b")
    df["att_rate"]   = (df["present_count"] / df["total_count"].replace(0, 1) * 100).round(1)

    # KPI row
    avg_rate = df["att_rate"].mean()
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Weeks Analysed", len(df))
    with c2: st.metric("Avg Attendance Rate", f"{avg_rate:.1f}%")
    with c3:
        trend_dir = "↑ Improving" if len(df) > 1 and df["att_rate"].iloc[-1] > df["att_rate"].iloc[0] else "↓ Declining"
        st.metric("Trend", trend_dir,
                  delta_color="normal" if "↑" in trend_dir else "inverse",
                  delta=trend_dir)

    st.markdown("---")

    # Week-by-week bar chart
    st.markdown('<div class="section-header">Weekly Attendance Rate — Last 4 Weeks</div>', unsafe_allow_html=True)

    colors = ["#22c55e" if r >= 85 else "#f97316" if r >= 70 else "#ef4444"
              for r in df["att_rate"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["label"], y=df["att_rate"],
        marker_color=colors,
        text=[f"{r:.1f}%" for r in df["att_rate"]],
        textposition="outside",
        name="Attendance Rate",
    ))
    fig.add_hline(y=85, line_dash="dash", line_color="#ef4444",
                  annotation_text="85% target", annotation_position="top right")
    fig.update_layout(
        height=320, yaxis_range=[0, 110],
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Attendance Rate (%)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Present vs absent stacked
    st.markdown('<div class="section-header">Present vs Absent — Weekly Breakdown</div>', unsafe_allow_html=True)
    df["absent_count"] = df["total_count"] - df["present_count"]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Present", x=df["label"], y=df["present_count"],
                          marker_color="#22c55e"))
    fig2.add_trace(go.Bar(name="Absent / Late", x=df["label"], y=df["absent_count"],
                          marker_color="#f97316"))
    fig2.update_layout(barmode="stack", height=280, margin=dict(l=0, r=0, t=5, b=0),
                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)


def _tab_leaves(department: str):
    df = _pending_leaves(department)

    if df.empty:
        st.success("✅ No pending leave requests — your queue is clear.")
        return

    # Flag stale (>24h)
    df["stale"] = df["hours_pending"] > 24

    n_total = len(df)
    n_stale = int(df["stale"].sum())

    c1, c2 = st.columns(2)
    with c1: st.metric("Pending Approvals", n_total)
    with c2: st.metric("Stale > 24h", n_stale,
                       delta="Action needed" if n_stale else "All fresh",
                       delta_color="inverse" if n_stale else "off")

    st.markdown("---")
    st.markdown('<div class="section-header">Pending Leave Queue</div>', unsafe_allow_html=True)

    for _, row in df.sort_values("hours_pending", ascending=False).iterrows():
        hrs   = float(row["hours_pending"])
        stale = bool(row["stale"])
        cls   = "risk-flag" if stale else "candidate-card"
        stale_badge = "<span class='stale-badge'>STALE</span>" if stale else ""

        reason = str(row.get("reason", "")) or "—"

        st.markdown(f"""
        <div class='{cls}'>
            <div style="display:flex;justify-content:space-between;align-items:start">
                <div>
                    <b>{row['name']}</b> &nbsp;
                    <span style="background:#dbeafe;color:#1e40af;border-radius:999px;
                                 padding:2px 8px;font-size:11px;font-weight:600">
                        {str(row['leave_type']).upper()}
                    </span>
                    &nbsp;{stale_badge}
                </div>
                <div style="font-size:0.8rem;color:#64748b;text-align:right">
                    {hrs:.0f}h pending
                </div>
            </div>
            <div style="font-size:0.85rem;color:#475569;margin-top:4px">
                📅 {row['start_date']} → {row['end_date']} &nbsp;·&nbsp; Reason: {reason[:80]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("**Approve/Reject** via the Flutter Manager portal → Leaves screen, or call:\n"
            "```\nPATCH http://localhost:3000/api/v1/leaves/{id}/approve\nPATCH .../reject\n```")


# ══════════════════════════════════════════════════════════════════════════════
# Department selector (when manager has no employee record in DB)
# ══════════════════════════════════════════════════════════════════════════════

def _pick_department() -> str:
    depts_df = query_df("SELECT DISTINCT department FROM employees ORDER BY department")
    if depts_df.empty:
        return "Engineering"
    depts = depts_df["department"].tolist()
    return st.sidebar.selectbox("Your Department", depts, index=0)


# ══════════════════════════════════════════════════════════════════════════════
# Main entry-point
# ══════════════════════════════════════════════════════════════════════════════

if "mgr_user" not in st.session_state:
    st.markdown("""
    <div class="dash-header">
        <h1>SkillSync · Manager Analytics Dashboard</h1>
        <p>Sign in with your Manager credentials to access team analytics</p>
    </div>
    """, unsafe_allow_html=True)
    _sidebar_login()
    st.info("**Demo credentials:** `tarek.mansour@skillsync.dev` / `Manager@123`")
    st.stop()

user       = st.session_state["mgr_user"]
department = user.get("_department")

if not department:
    st.sidebar.markdown("⚠️ No employee record linked to your account. Pick a department:")
    department = _pick_department()

_sidebar_user(department)

now = datetime.now()
st.markdown(f"""
<div class="dash-header">
    <h1>SkillSync · Manager Analytics Dashboard</h1>
    <p>Team: <b>{department}</b> &nbsp;·&nbsp; {now.strftime('%A, %d %B %Y')} &nbsp;·&nbsp; {now.strftime('%H:%M')}</p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs([
    "Team Overview",
    "Skill Heatmap",
    "Replacements",
    "Attendance",
    "Leave Approvals",
])
with t1: _tab_overview(department)
with t2: _tab_heatmap(department)
with t3: _tab_replacements(department)
with t4: _tab_attendance(department)
with t5: _tab_leaves(department)
