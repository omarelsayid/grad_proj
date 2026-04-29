"""SkillSync · HR Admin Analytics Dashboard  —  streamlit run dashboard_hr.py --server.port 8501"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st

from db_connection import query_df, query_scalar, query_one
from api_client import login_user, get_skill_gaps_ml, predict_role_fit_ml

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillSync · HR Analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme constants ───────────────────────────────────────────────────────────
RISK_COLORS = {
    "critical": "#dc2626",
    "high":     "#f97316",
    "medium":   "#eab308",
    "low":      "#22c55e",
}
RISK_ORDER = ["critical", "high", "medium", "low"]

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container { padding-top: 1.25rem; padding-bottom: 1rem; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}

.dash-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
    color: white; padding: 1.25rem 1.75rem;
    border-radius: 14px; margin-bottom: 1.25rem;
}
.dash-header h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }
.dash-header p  { margin: 0.3rem 0 0; font-size: 0.85rem; opacity: 0.82; }

.section-header { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 0.6rem; }

.risk-pill { display:inline-block; border-radius:999px; padding:2px 10px; font-size:12px; font-weight:600; }
.risk-critical { background:#fee2e2; color:#991b1b; }
.risk-high     { background:#ffedd5; color:#9a3412; }
.risk-medium   { background:#fef9c3; color:#854d0e; }
.risk-low      { background:#dcfce7; color:#166534; }

.alert-row {
    background:#fff7ed; border:1px solid #fed7aa;
    border-left:4px solid #ea580c; border-radius:8px;
    padding:0.6rem 1rem; margin-bottom:0.4rem; font-size:0.88rem;
}

.user-card {
    background:#f0f9ff; border-radius:10px; padding:0.75rem 1rem; margin-bottom:1rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════════════════════════════════════

def _sidebar_login():
    st.sidebar.markdown("## HR Analytics")
    st.sidebar.markdown("---")
    with st.sidebar.form("login"):
        email    = st.text_input("Email",    value="rana.essam@skillsync.dev",  placeholder="rana.essam@skillsync.dev")
        password = st.text_input("Password", type="password", placeholder="Admin@123")
        submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
    if submitted:
        if not email or not password:
            st.sidebar.error("Enter both fields.")
            return
        try:
            result = login_user(email, password)
            # API returns { role, employee, accessToken, refreshToken } at top level
            role     = result.get("role", "")
            emp_data = result.get("employee") or {}
            user = {
                "id":    emp_data.get("id", ""),
                "name":  emp_data.get("name", email),
                "email": email,
                "role":  role,
            }
            if role != "hr_admin":
                st.sidebar.error(f"HR Admin role required (got: '{role}').")
                return
            st.session_state["hr_user"]  = user
            st.session_state["hr_token"] = result.get("accessToken", "")
            st.rerun()
        except requests.ConnectionError:
            st.sidebar.error("Cannot reach API (port 3000). Is the Node.js server running?")
        except requests.HTTPError as exc:
            st.sidebar.error(f"Login failed ({exc.response.status_code}).")
        except Exception as exc:
            st.sidebar.error(f"Error: {exc}")


def _sidebar_user():
    u = st.session_state["hr_user"]
    st.sidebar.markdown(
        f"<div class='user-card'>"
        f"<b>{u.get('name', u.get('email',''))}</b><br>"
        f"<span style='font-size:0.8rem;color:#64748b'>{u.get('email','')}</span><br>"
        f"<span style='font-size:0.75rem;color:#0ea5e9'>HR Admin</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    now = datetime.now()
    st.sidebar.markdown(f"**{now.strftime('%H:%M')}** · {now.strftime('%d %b %Y')}")
    if st.sidebar.button("Refresh all data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.pop("hr_user",  None)
        st.session_state.pop("hr_token", None)
        st.rerun()
    st.sidebar.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# Data fetchers
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def _kpis() -> dict:
    now = datetime.now()
    return {
        "headcount": query_scalar("SELECT COUNT(*) FROM employees") or 0,
        "attendance_rate": query_scalar("""
            SELECT ROUND(100.0 *
                COUNT(CASE WHEN status IN ('present','remote') THEN 1 END)
                / NULLIF(COUNT(*), 0), 1)
            FROM attendance WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        """) or 0,
        "active_resignations": query_scalar(
            "SELECT COUNT(*) FROM resignation_requests WHERE status = 'pending'"
        ) or 0,
        "stale_leaves": query_scalar("""
            SELECT COUNT(*) FROM leave_requests
            WHERE status = 'pending' AND created_at < NOW() - INTERVAL '48 hours'
        """) or 0,
        "monthly_payroll": query_scalar(
            "SELECT COALESCE(SUM(net_salary),0) FROM payroll WHERE month=%s AND year=%s",
            (now.month, now.year),
        ) or 0,
    }


@st.cache_data(ttl=300)
def _dept_breakdown() -> pd.DataFrame:
    return query_df("""
        SELECT department,
               COUNT(*)                              AS headcount,
               ROUND(AVG(satisfaction_score)::numeric,1) AS avg_satisfaction,
               ROUND(AVG(salary)::numeric,0)         AS avg_salary
        FROM employees
        GROUP BY department
        ORDER BY headcount DESC
    """)


@st.cache_data(ttl=300)
def _recent_joiners() -> pd.DataFrame:
    return query_df("""
        SELECT e.name, e.current_role, e.department, e.join_date, e.salary
        FROM employees e
        WHERE e.join_date >= CURRENT_DATE - INTERVAL '90 days'
        ORDER BY e.join_date DESC LIMIT 15
    """)


@st.cache_data(ttl=600)
def _turnover_live() -> pd.DataFrame:
    """
    Compute live turnover risk for all employees.
    Features are derived from PostgreSQL; scores come from the ML service.
    Cached for 10 min — click "Refresh all data" to force a reload.
    """
    import requests as _req

    ML_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")

    # Quick health check — bail immediately if ML service is offline
    try:
        _req.get(f"{ML_URL}/health", timeout=2)
    except Exception:
        return pd.DataFrame(columns=["id", "name", "department", "current_role",
                                     "risk_score", "risk_level", "factor_breakdown",
                                     "_ml_offline"])

    emps = query_df("""
        SELECT e.id, e.name, e.department, e.current_role,
               e.commute_distance_km,
               e.satisfaction_score,
               (CURRENT_DATE - e.join_date::date) AS tenure_days
        FROM employees e
        ORDER BY e.name
    """)
    if emps.empty:
        return pd.DataFrame()

    # Attendance features (last 30 days)
    att = query_df("""
        SELECT employee_id,
               COUNT(*)                                              AS total_att,
               SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END)  AS absent_count,
               SUM(CASE WHEN status = 'late'   THEN 1 ELSE 0 END)  AS late_count
        FROM attendance
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY employee_id
    """)
    emps = emps.merge(att, left_on="id", right_on="employee_id", how="left")
    emps["total_att"]    = emps["total_att"].fillna(0).astype(int)
    emps["absent_count"] = emps["absent_count"].fillna(0).astype(int)
    emps["late_count"]   = emps["late_count"].fillna(0).astype(int)
    emps["absence_rate"] = (emps["absent_count"] / emps["total_att"].clip(lower=1)).round(3)
    emps["late_rate_raw"] = emps["late_count"]          # backend field name

    # Simplified role-fit from employee_skills vs role_required_skills
    fit = query_df("""
        SELECT es.employee_id,
               ROUND(
                   100.0 * SUM(CASE WHEN es.proficiency >= COALESCE(jr.min_proficiency, 1) THEN 1 ELSE 0 END)
                   / NULLIF(COUNT(jr.skill_id), 0), 1
               ) AS role_fit_score
        FROM employee_skills es
        JOIN employees e ON e.id = es.employee_id
        LEFT JOIN role_required_skills jr ON jr.skill_id = es.skill_id
                                         AND jr.role_id = e.role_id
        GROUP BY es.employee_id
    """)
    emps = emps.merge(fit, on="employee_id", how="left")
    emps["role_fit_score"] = emps["role_fit_score"].fillna(70.0)

    rows = []
    for _, r in emps.iterrows():
        absence = float(r["absence_rate"])
        att_status = "critical" if absence > 0.2 else ("at_risk" if absence > 0.1 else "normal")
        payload = {
            "employee_id":        str(r["id"]),
            "commute_distance_km": float(r["commute_distance_km"]),
            "tenure_days":         int(r["tenure_days"]),
            "role_fit_score":      float(r["role_fit_score"]),
            "absence_rate":        absence,
            "late_arrivals_30d":   int(r["late_rate_raw"]),
            "leave_requests_90d":  0,
            "satisfaction_score":  float(r["satisfaction_score"]),
            "attendance_status":   att_status,
        }
        try:
            resp = _req.post(f"{ML_URL}/predict/turnover", json=payload, timeout=5)
            pred = resp.json() if resp.status_code == 200 else {}
        except Exception:
            pred = {}

        rows.append({
            "id":               r["id"],
            "name":             r["name"],
            "department":       r["department"],
            "current_role":     r["current_role"],
            "risk_score":       pred.get("risk_score", 0.0),
            "risk_level":       pred.get("risk_level", "low"),
            "factor_breakdown": pred.get("top_factors", []),
        })

    df = pd.DataFrame(rows)
    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=600)
def _skill_gaps() -> dict:
    try:
        return get_skill_gaps_ml()
    except requests.ConnectionError:
        return {"_error": "ML service offline (port 8000)", "skill_gaps": [], "total_skills_analyzed": 0, "critical_skills": 0}
    except Exception as exc:
        return {"_error": str(exc), "skill_gaps": [], "total_skills_analyzed": 0, "critical_skills": 0}


@st.cache_data(ttl=300)
def _payroll_trend() -> pd.DataFrame:
    return query_df("""
        SELECT e.department, p.month, p.year,
               SUM(p.net_salary)  AS total_cost,
               COUNT(*)           AS employee_count,
               AVG(p.net_salary)  AS avg_salary
        FROM payroll p
        JOIN employees e ON e.id = p.employee_id
        WHERE (p.year * 100 + p.month) >=
              (EXTRACT(YEAR FROM CURRENT_DATE)::int * 100
               + EXTRACT(MONTH FROM CURRENT_DATE)::int - 6)
        GROUP BY e.department, p.month, p.year
        ORDER BY p.year, p.month, e.department
    """)


@st.cache_data(ttl=60)
def _audit_logs(entity_type: str, limit: int) -> pd.DataFrame:
    where = "" if entity_type == "All" else f"WHERE al.entity_type = '{entity_type}'"
    return query_df(f"""
        SELECT al.created_at,
               al.action,
               al.entity_type,
               al.entity_id,
               COALESCE(u.email, 'system') AS actor,
               al.ip_address
        FROM audit_logs al
        LEFT JOIN users u ON u.id = al.user_id
        {where}
        ORDER BY al.created_at DESC
        LIMIT %s
    """, (limit,))


# ══════════════════════════════════════════════════════════════════════════════
# Tab renderers
# ══════════════════════════════════════════════════════════════════════════════

def _tab_workforce():
    kpis = _kpis()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Headcount", f"{kpis['headcount']:,}")
    with c2:
        rate = float(kpis["attendance_rate"])
        st.metric("Attendance (30d)", f"{rate:.1f}%",
                  delta="Healthy" if rate >= 85 else "⚠ Below 85%",
                  delta_color="normal" if rate >= 85 else "inverse")
    with c3:
        res = int(kpis["active_resignations"])
        st.metric("Resignations", res,
                  delta="Pending" if res else None,
                  delta_color="inverse" if res else "off")
    with c4:
        sl = int(kpis["stale_leaves"])
        st.metric("Stale Leaves (>48h)", sl,
                  delta="Action needed" if sl else "All clear",
                  delta_color="inverse" if sl else "off")
    with c5:
        st.metric("Monthly Payroll", f"${float(kpis['monthly_payroll']):,.0f}")

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-header">Headcount by Department</div>', unsafe_allow_html=True)
        dept = _dept_breakdown()
        if not dept.empty:
            fig = px.bar(dept, x="headcount", y="department", orientation="h",
                         color="headcount", color_continuous_scale="Blues",
                         text="headcount", labels={"headcount": "Employees", "department": ""})
            fig.update_traces(textposition="outside")
            fig.update_layout(height=360, margin=dict(l=0, r=40, t=10, b=0),
                              coloraxis_showscale=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">Department Summary</div>', unsafe_allow_html=True)
        dept = _dept_breakdown()
        if not dept.empty:
            d = dept[["department","headcount","avg_satisfaction","avg_salary"]].copy()
            d.columns = ["Department","Staff","Satisfaction","Avg Salary"]
            d["Avg Salary"] = d["Avg Salary"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
            st.dataframe(d, use_container_width=True, hide_index=True, height=320)

    st.markdown("---")
    st.markdown('<div class="section-header">Recent Joiners (Last 90 Days)</div>', unsafe_allow_html=True)
    joiners = _recent_joiners()
    if joiners.empty:
        st.info("No new joiners in the last 90 days.")
    else:
        joiners["salary"] = joiners["salary"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(joiners, use_container_width=True, hide_index=True)


def _tab_turnover():
    with st.spinner("Scoring all employees via ML service…"):
        df = _turnover_live()

    if df.empty or "_ml_offline" in df.columns:
        st.error(
            "ML service is offline — turnover scoring unavailable.\n\n"
            "Start it with:\n```\ncd ml_service\nuvicorn app.main:app --port 8000\n```"
        )
        return

    ml_offline = df["risk_score"].eq(0).all()
    if ml_offline:
        st.error("ML service appears offline (all scores = 0). Start it with: `uvicorn app.main:app --port 8000` inside `ml_service/`")
        return

    counts = df["risk_level"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    for col, level in zip([c1,c2,c3,c4], RISK_ORDER):
        with col:
            st.metric(level.capitalize(), int(counts.get(level, 0)))

    st.markdown("---")
    col_l, col_r = st.columns([2, 3])

    with col_l:
        st.markdown('<div class="section-header">Risk Distribution</div>', unsafe_allow_html=True)
        dist = (df["risk_level"].value_counts()
                .reindex(RISK_ORDER, fill_value=0)
                .reset_index())
        dist.columns = ["risk_level", "count"]

        fig = go.Figure(go.Bar(
            x=dist["count"], y=dist["risk_level"], orientation="h",
            marker_color=[RISK_COLORS[r] for r in dist["risk_level"]],
            text=dist["count"], textposition="outside",
        ))
        fig.update_layout(height=220, margin=dict(l=0, r=50, t=5, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(categoryorder="array", categoryarray=RISK_ORDER))
        st.plotly_chart(fig, use_container_width=True)

        pie_data = dist[dist["count"] > 0]
        fig2 = px.pie(pie_data, values="count", names="risk_level", hole=0.55,
                      color="risk_level", color_discrete_map=RISK_COLORS)
        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(height=260, margin=dict(l=0, r=0, t=0, b=0),
                           paper_bgcolor="rgba(0,0,0,0)",
                           legend=dict(orientation="h", yanchor="bottom", y=-0.25))
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">Employees with Risk Score > 55</div>', unsafe_allow_html=True)
        at_risk = df[df["risk_score"] > 55].copy()
        if at_risk.empty:
            st.success("No employees above the 55-point risk threshold.")
        else:
            disp = at_risk[["name","department","current_role","risk_score","risk_level"]].copy()
            disp.columns = ["Name","Department","Role","Score","Level"]
            disp["Score"] = disp["Score"].round(1)

            def _bg(val):
                m = {"critical":"background-color:#fee2e2;color:#991b1b",
                     "high":"background-color:#ffedd5;color:#9a3412",
                     "medium":"background-color:#fef9c3;color:#854d0e",
                     "low":"background-color:#dcfce7;color:#166534"}
                return m.get(val, "")

            st.dataframe(
                disp.style.applymap(_bg, subset=["Level"]),
                use_container_width=True, hide_index=True, height=420,
            )

    # Factor breakdown — model returns top_factors as list[str]
    st.markdown("---")
    st.markdown('<div class="section-header">Top Risk Factors (Employees > 55)</div>', unsafe_allow_html=True)
    factor_counts: dict[str, int] = {}
    for _, row in df[df["risk_score"] > 55].iterrows():
        fb = row.get("factor_breakdown")
        if isinstance(fb, list):
            for item in fb:
                if isinstance(item, str):
                    factor_counts[item] = factor_counts.get(item, 0) + 1

    # Map raw feature names to readable labels
    _LABEL = {
        "tenure_years":              "Short Tenure",
        "work_life_balance":         "Low Work-Life Balance",
        "role_fit_score":            "Low Role Fit",
        "absence_rate":              "High Absence Rate",
        "commute_distance_km":       "Long Commute",
        "late_rate":                 "High Late Rate",
        "attendance_status_encoded": "Poor Attendance Status",
    }

    if factor_counts:
        fdf = (pd.DataFrame(list(factor_counts.items()), columns=["Feature", "Count"])
               .sort_values("Count", ascending=False).head(7))
        fdf["Factor"] = fdf["Feature"].map(lambda x: _LABEL.get(x, x))
        fig = px.bar(fdf, x="Count", y="Factor", orientation="h",
                     color="Count", color_continuous_scale="Reds", text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, margin=dict(l=0, r=60, t=5, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No employees above the 55-point threshold to show factor breakdown.")


def _tab_skill_gaps():
    with st.spinner("Fetching skill gap analysis from ML service…"):
        data = _skill_gaps()

    if "_error" in data:
        st.error(f"ML service error: {data['_error']}")
        st.info("Start the ML service: `uvicorn app.main:app --port 8000` inside `ml_service/`")
        return

    gaps = data.get("skill_gaps", [])
    if not gaps:
        st.warning("ML service returned no skill gap data.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Skills Analyzed", data.get("total_skills_analyzed", len(gaps)))
    with c2: st.metric("Critical Skills", data.get("critical_skills", 0))
    with c3:
        high_n = sum(1 for g in gaps if g.get("criticality") == "high")
        st.metric("High Priority", high_n)
    with c4:
        surplus = sum(1 for g in gaps if g.get("criticality") == "surplus")
        st.metric("Surplus Skills", surplus)

    st.markdown("---")
    gaps_df = pd.DataFrame(gaps)
    crit_order  = {"critical": 0, "high": 1, "medium": 2, "low": 3, "surplus": 4}
    crit_colors = {"critical":"#dc2626","high":"#f97316","medium":"#eab308",
                   "low":"#22c55e","surplus":"#3b82f6"}

    if "criticality" in gaps_df.columns:
        gaps_df["_sort"] = gaps_df["criticality"].map(crit_order).fillna(99)
        gaps_df = gaps_df.sort_values("_sort").drop(columns="_sort")

    name_col = "skill_name" if "skill_name" in gaps_df.columns else "skill_id"
    plot_df  = gaps_df.head(25).copy()

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-header">Skill Gap Severity (top 25, ranked by criticality)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        for crit in ["critical", "high", "medium", "low", "surplus"]:
            sub = plot_df[plot_df.get("criticality", pd.Series(dtype=str)) == crit] if "criticality" in plot_df.columns else pd.DataFrame()
            if sub.empty:
                continue
            y_labels = sub[name_col].fillna(sub["skill_id"])
            x_vals   = sub.get("gap_ratio", sub.get("demand_score", pd.Series([0]*len(sub))))
            fig.add_trace(go.Bar(
                x=x_vals, y=y_labels, orientation="h",
                name=crit.capitalize(),
                marker_color=crit_colors[crit],
                text=[f"{v:.0%}" if "gap_ratio" in sub.columns else f"{v:.2f}" for v in x_vals],
                textposition="outside",
            ))

        fig.update_layout(
            height=max(420, len(plot_df) * 22),
            barmode="overlay", margin=dict(l=0, r=70, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.18),
            xaxis_title="Gap Ratio  (1.0 = nobody meets demand)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">Full Skill Gap Table</div>', unsafe_allow_html=True)
        show_cols = [c for c in ["skill_name","skill_id","criticality","gap_ratio","demand_score","supply_score"] if c in gaps_df.columns]
        disp = gaps_df[show_cols].head(25).copy()
        if "gap_ratio" in disp.columns:
            disp["gap_ratio"] = disp["gap_ratio"].apply(lambda x: f"{x:.0%}" if pd.notna(x) else "—")
        for col in ["demand_score","supply_score"]:
            if col in disp.columns:
                disp[col] = disp[col].round(2)
        disp.columns = [c.replace("_"," ").title() for c in disp.columns]
        st.dataframe(disp, use_container_width=True, hide_index=True, height=440)

    # Department summaries
    dept_summaries = data.get("department_summaries", [])
    if dept_summaries:
        st.markdown("---")
        st.markdown('<div class="section-header">Org-Wide Gap Score by Department</div>', unsafe_allow_html=True)
        ddf = pd.DataFrame([{
            "Department": d["department"],
            "Gap Score":  round(d.get("overall_gap_score", 0), 3),
            "Top Gaps":   ", ".join(
                (g.get("skill_name") or g.get("skill_id","")) for g in (d.get("top_gaps") or [])[:3]
            ),
        } for d in dept_summaries])

        fig = px.bar(ddf.sort_values("Gap Score", ascending=False),
                     x="Department", y="Gap Score", color="Gap Score",
                     color_continuous_scale="OrRd", text="Gap Score")
        fig.update_traces(textposition="outside", texttemplate="%{text:.3f}")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        ddf_disp = ddf.rename(columns={"Gap Score":"Org Gap Score","Top Gaps":"Top Missing Skills"})
        st.dataframe(ddf_disp, use_container_width=True, hide_index=True)


def _tab_payroll():
    df = _payroll_trend()
    if df.empty:
        st.warning("No payroll records found. Generate payroll via the Node.js API first.")
        return

    now = datetime.now()
    current = df[(df["month"] == now.month) & (df["year"] == now.year)]
    total_cost    = float(current["total_cost"].sum())    if not current.empty else 0.0
    total_emps    = int(current["employee_count"].sum())  if not current.empty else 0
    avg_sal       = total_cost / total_emps if total_emps else 0

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Payroll (This Month)", f"${total_cost:,.0f}")
    with c2: st.metric("Employees Paid",             total_emps)
    with c3: st.metric("Avg Net Salary",             f"${avg_sal:,.0f}")

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-header">Payroll Cost by Department — Current Month</div>', unsafe_allow_html=True)
        if not current.empty:
            cur_sorted = current.sort_values("total_cost", ascending=False)
            fig = px.bar(cur_sorted, x="department", y="total_cost", color="department",
                         text=cur_sorted["total_cost"].apply(lambda x: f"${x:,.0f}"),
                         labels={"total_cost": "Net Salary ($)", "department": ""})
            fig.update_traces(textposition="outside")
            fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No payroll processed for {now.strftime('%B %Y')} yet.")

    with col_r:
        st.markdown('<div class="section-header">Department Breakdown</div>', unsafe_allow_html=True)
        if not current.empty:
            d = current[["department","total_cost","employee_count","avg_salary"]].copy()
            d.columns = ["Department","Total ($)","Count","Avg ($)"]
            d["Total ($)"] = d["Total ($)"].apply(lambda x: f"${x:,.0f}")
            d["Avg ($)"]   = d["Avg ($)"].apply(lambda x:   f"${x:,.0f}")
            st.dataframe(d, use_container_width=True, hide_index=True, height=340)

    st.markdown("---")
    st.markdown('<div class="section-header">Month-over-Month Payroll Trend</div>', unsafe_allow_html=True)
    trend = df.copy()
    trend["period"] = trend["year"].astype(str) + "-" + trend["month"].astype(str).str.zfill(2)
    trend_agg = trend.groupby("period")["total_cost"].sum().reset_index().sort_values("period")

    if len(trend_agg) >= 2:
        fig = px.line(trend_agg, x="period", y="total_cost", markers=True,
                      labels={"total_cost": "Total Payroll ($)", "period": "Month"},
                      color_discrete_sequence=["#3b82f6"])
        fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Stack by dept if only one month
        fig = px.bar(trend, x="period", y="total_cost", color="department", barmode="stack",
                     labels={"total_cost":"Total ($)","period":"Month"})
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)


def _tab_audit():
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        entity = st.selectbox("Entity type", ["All","employee","leave_request","payroll",
                                               "resignation","auth","department","role"])
    with c2:
        limit  = st.selectbox("Max records", [50, 100, 200, 500], index=1)
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()

    df = _audit_logs(entity, limit)
    if df.empty:
        st.info("No audit log entries match the filter.")
        return

    # Action summary
    action_counts = df["action"].value_counts().reset_index()
    action_counts.columns = ["action", "count"]
    col_a, col_b = st.columns([3, 1])
    with col_a:
        fig = px.bar(action_counts, x="action", y="count", color="action", text="count",
                     color_discrete_map={
                         "CREATE":"#22c55e","UPDATE":"#3b82f6","DELETE":"#ef4444",
                         "LOGIN":"#a855f7","LOGOUT":"#64748b","READ":"#94a3b8",
                     })
        fig.update_traces(textposition="outside")
        fig.update_layout(height=220, margin=dict(l=0, r=0, t=5, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.dataframe(action_counts, use_container_width=True, hide_index=True)

    # Log feed
    st.markdown('<div class="section-header">Event Feed</div>', unsafe_allow_html=True)
    disp = df.copy()
    if "created_at" in disp.columns:
        disp["created_at"] = pd.to_datetime(disp["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    disp.columns = [c.replace("_"," ").title() for c in disp.columns]
    st.dataframe(disp, use_container_width=True, hide_index=True, height=460)


@st.cache_data(ttl=300)
def _all_employees_for_replacement() -> pd.DataFrame:
    return query_df("""
        SELECT e.id, e.name, e.current_role, e.role_id, e.department
        FROM employees e
        ORDER BY e.name
    """)


@st.cache_data(ttl=300)
def _role_req_hr(role_id: str) -> list[dict]:
    df = query_df("""
        SELECT rrs.skill_id, s.name AS skill_name,
               rrs.min_proficiency, rrs.importance_weight
        FROM role_required_skills rrs
        JOIN skills s ON s.id = rrs.skill_id
        WHERE rrs.role_id = %s
    """, (role_id,))
    return df.to_dict("records")


@st.cache_data(ttl=300)
def _emp_skills_hr(employee_id: str) -> list[dict]:
    df = query_df(
        "SELECT skill_id, proficiency FROM employee_skills WHERE employee_id = %s",
        (employee_id,)
    )
    return df.to_dict("records")


@st.cache_data(ttl=600)
def _hr_replacement_candidates(
    departing_id: str, role_id: str,
    same_dept_only: bool, departing_dept: str,
) -> list[dict]:
    reqs = _role_req_hr(role_id)
    if not reqs:
        return []

    all_emps = _all_employees_for_replacement()
    pool = all_emps[all_emps["id"] != departing_id]
    if same_dept_only:
        pool = pool[pool["department"] == departing_dept]

    results = []
    for _, cand in pool.iterrows():
        skills = _emp_skills_hr(cand["id"])
        payload = {
            "employee_id":       cand["id"],
            "job_role_id":       role_id,
            "employee_skills":   [{"skill_id": s["skill_id"], "proficiency": s["proficiency"]} for s in skills],
            "role_requirements": [{"skill_id": r["skill_id"], "min_proficiency": r["min_proficiency"],
                                   "importance_weight": r["importance_weight"]} for r in reqs],
        }
        try:
            resp = predict_role_fit_ml(payload)
            results.append({
                "name":         cand["name"],
                "department":   cand["department"],
                "current_role": cand["current_role"],
                "fit_score":    resp.get("fit_score", 0),
                "readiness":    resp.get("readiness_level", "unknown"),
                "matching":     resp.get("matching_skills", []),
                "missing":      resp.get("missing_skills", []),
            })
        except Exception:
            met = sum(1 for r in reqs if any(
                s["skill_id"] == r["skill_id"] and s["proficiency"] >= r["min_proficiency"]
                for s in skills
            ))
            results.append({
                "name":         cand["name"],
                "department":   cand["department"],
                "current_role": cand["current_role"],
                "fit_score":    int(100 * met / len(reqs)) if reqs else 0,
                "readiness":    "estimated (ML offline)",
                "matching":     [],
                "missing":      [],
            })

    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results[:10]


def _tab_replacements_hr():
    all_emps = _all_employees_for_replacement()
    if all_emps.empty:
        st.warning("No employee data found.")
        return

    dept_options = ["All Departments"] + sorted(all_emps["department"].unique().tolist())
    dept_count   = all_emps["department"].nunique()

    col_ctrl1, col_ctrl2 = st.columns([3, 2])
    with col_ctrl1:
        dept_filter = st.selectbox("Filter employees by department", dept_options)
    with col_ctrl2:
        same_dept_only = st.toggle("Same department candidates only", value=False)

    filtered_emps = (
        all_emps[all_emps["department"] == dept_filter]
        if dept_filter != "All Departments"
        else all_emps
    )

    selected_name = st.selectbox(
        "Departing Employee",
        filtered_emps["name"].tolist(),
        format_func=lambda n: f"{n} ({filtered_emps[filtered_emps['name'] == n]['current_role'].values[0]})"
        if not filtered_emps[filtered_emps["name"] == n].empty else n,
    )
    emp_row = filtered_emps[filtered_emps["name"] == selected_name].iloc[0]
    departing_dept = emp_row["department"]
    role_id        = emp_row["role_id"]

    pool_size = (
        len(all_emps[all_emps["department"] == departing_dept]) - 1
        if same_dept_only
        else len(all_emps) - 1
    )
    depts_searched = 1 if same_dept_only else dept_count
    role_name = query_df(
        "SELECT title FROM job_roles WHERE id = %s", (role_id,)
    )
    role_label = role_name.iloc[0]["title"] if not role_name.empty else role_id

    # Stats banner
    st.markdown(f"""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;
                padding:1rem 1.5rem;margin:1rem 0;display:flex;gap:2rem">
        <div>
            <div style="font-size:1.5rem;font-weight:800;color:#1e40af">{pool_size:,}</div>
            <div style="font-size:0.78rem;color:#64748b">Candidates Searched</div>
        </div>
        <div style="width:1px;background:#bfdbfe"></div>
        <div>
            <div style="font-size:1.5rem;font-weight:800;color:#1e40af">{depts_searched}</div>
            <div style="font-size:0.78rem;color:#64748b">Departments</div>
        </div>
        <div style="width:1px;background:#bfdbfe"></div>
        <div>
            <div style="font-size:1.5rem;font-weight:800;color:#1e40af">{role_label}</div>
            <div style="font-size:0.78rem;color:#64748b">Open Role</div>
        </div>
        <div style="width:1px;background:#bfdbfe"></div>
        <div>
            <div style="font-size:1.5rem;font-weight:800;color:#1e40af">{departing_dept}</div>
            <div style="font-size:0.78rem;color:#64748b">Departing From</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner(f"Scoring {pool_size:,} candidates via ML service…"):
        candidates = _hr_replacement_candidates(
            emp_row["id"], role_id, same_dept_only, departing_dept,
        )

    if not candidates:
        st.warning("No candidates found or the role has no skill requirements configured.")
        return

    st.markdown(
        f'<div class="section-header">Top {len(candidates)} Replacement Candidates '
        f'for "{role_label}" — ranked by skill-fit score across {pool_size:,} employees</div>',
        unsafe_allow_html=True,
    )

    READINESS_COLORS = {
        "ready":             "#22c55e",
        "near_ready":        "#eab308",
        "needs_development": "#f97316",
        "not_ready":         "#ef4444",
    }
    READINESS_BG = {
        "ready":             "#dcfce7",
        "near_ready":        "#fef9c3",
        "needs_development": "#ffedd5",
        "not_ready":         "#fee2e2",
    }

    col_l, col_r = st.columns([3, 2])

    with col_l:
        for i, c in enumerate(candidates, 1):
            fit     = c["fit_score"]
            ready   = c["readiness"]
            color   = READINESS_COLORS.get(ready, "#64748b")
            bg      = READINESS_BG.get(ready, "#f1f5f9")
            bar_pct = min(max(fit, 0), 100)
            matching_str = ", ".join(c["matching"][:5]) if c["matching"] else "—"
            missing_str  = ", ".join(c["missing"][:5])  if c["missing"]  else "—"
            ready_label  = ready.replace("_", " ").upper()

            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                        padding:0.85rem 1rem;margin-bottom:0.6rem">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="background:#dbeafe;color:#1e40af;font-weight:700;
                                     padding:2px 8px;border-radius:6px;font-size:0.8rem">
                            #{i}
                        </span>
                        &nbsp;
                        <span style="font-weight:700;font-size:1rem">{c['name']}</span>
                        &nbsp;
                        <span style="color:#64748b;font-size:0.82rem">{c['current_role']}</span>
                        &nbsp;
                        <span style="background:#e2e8f0;color:#475569;font-size:0.72rem;
                                     padding:1px 7px;border-radius:999px">{c['department']}</span>
                    </div>
                    <div style="text-align:right">
                        <span style="font-size:1.4rem;font-weight:800;color:#1e40af">{fit}</span>
                        <span style="color:#94a3b8;font-size:0.75rem">/100</span>
                        &nbsp;
                        <span style="background:{bg};color:{color};font-size:0.72rem;
                                     font-weight:700;padding:2px 8px;border-radius:999px">
                            {ready_label}
                        </span>
                    </div>
                </div>
                <div style="background:#e2e8f0;border-radius:999px;height:6px;margin:8px 0">
                    <div style="background:{color};width:{bar_pct}%;height:6px;border-radius:999px"></div>
                </div>
                <div style="font-size:0.78rem;color:#475569">
                    <b style="color:#16a34a">+ Matching:</b> {matching_str}<br>
                    <b style="color:#dc2626">- Missing:</b>  {missing_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">Fit Score Distribution</div>', unsafe_allow_html=True)
        scores_df = pd.DataFrame({
            "Candidate": [f"#{i+1} {c['name']}" for i, c in enumerate(candidates)],
            "Score":     [c["fit_score"] for c in candidates],
            "Readiness": [c["readiness"].replace("_", " ").title() for c in candidates],
        })
        color_seq = [READINESS_COLORS.get(c["readiness"], "#64748b") for c in candidates]
        fig = go.Figure(go.Bar(
            x=scores_df["Score"],
            y=scores_df["Candidate"],
            orientation="h",
            marker_color=color_seq,
            text=scores_df["Score"].apply(lambda x: f"{x}%"),
            textposition="outside",
        ))
        fig.update_layout(
            height=max(300, len(candidates) * 44),
            xaxis_range=[0, 110],
            margin=dict(l=0, r=60, t=5, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-header">Readiness Breakdown</div>', unsafe_allow_html=True)
        readiness_counts = {}
        for c in candidates:
            lbl = c["readiness"].replace("_", " ").title()
            readiness_counts[lbl] = readiness_counts.get(lbl, 0) + 1
        rc_df = pd.DataFrame(list(readiness_counts.items()), columns=["Level", "Count"])
        fig2 = px.pie(rc_df, values="Count", names="Level", hole=0.5,
                      color="Level",
                      color_discrete_map={
                          "Ready":             "#22c55e",
                          "Near Ready":        "#eab308",
                          "Needs Development": "#f97316",
                          "Not Ready":         "#ef4444",
                      })
        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(
            height=240, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# Main entry-point
# ══════════════════════════════════════════════════════════════════════════════

if "hr_user" not in st.session_state:
    st.markdown("""
    <div class="dash-header">
        <h1>SkillSync · HR Admin Analytics Dashboard</h1>
        <p>Sign in with your HR Admin credentials to access the full dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    _sidebar_login()
    st.info("**Demo credentials:** `rana.essam@skillsync.dev` / `Admin@123`")
    st.stop()

_sidebar_user()

now = datetime.now()
st.markdown(f"""
<div class="dash-header">
    <h1>SkillSync · HR Admin Analytics Dashboard</h1>
    <p>Organization health overview &nbsp;·&nbsp; {now.strftime('%A, %d %B %Y')}
       &nbsp;·&nbsp; {now.strftime('%H:%M')}</p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4, t5, t6 = st.tabs([
    "Workforce Health",
    "Turnover Risk",
    "Skill Gaps",
    "Replacement Planning",
    "Payroll Analytics",
    "Audit Log",
])
with t1: _tab_workforce()
with t2: _tab_turnover()
with t3: _tab_skill_gaps()
with t4: _tab_replacements_hr()
with t5: _tab_payroll()
with t6: _tab_audit()
