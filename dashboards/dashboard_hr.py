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
from api_client import login_user, get_skill_gaps_ml

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillSync · HR Analytics",
    page_icon="🏢",
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
    st.sidebar.markdown("## 🏢 HR Analytics")
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
        f"<b>👤 {u.get('name', u.get('email',''))}</b><br>"
        f"<span style='font-size:0.8rem;color:#64748b'>{u.get('email','')}</span><br>"
        f"<span style='font-size:0.75rem;color:#0ea5e9'>🔑 HR Admin</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    now = datetime.now()
    st.sidebar.markdown(f"🕐 **{now.strftime('%H:%M')}** · {now.strftime('%d %b %Y')}")
    if st.sidebar.button("🔄 Refresh all data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("Sign Out", use_container_width=True):
        st.session_state.pop("hr_user",  None)
        st.session_state.pop("hr_token", None)
        st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.info("**Manager Dashboard** → port **8502**\n\nRun:\n```\nstreamlit run dashboard_manager.py --server.port 8502\n```")


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


@st.cache_data(ttl=300)
def _turnover_cache() -> pd.DataFrame:
    return query_df("""
        SELECT e.id, e.name, e.department, e.current_role,
               trc.risk_score, trc.risk_level,
               trc.factor_breakdown, trc.calculated_at
        FROM turnover_risk_cache trc
        JOIN employees e ON e.id = trc.employee_id
        ORDER BY trc.risk_score DESC
    """)


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
        st.metric("👥 Headcount", f"{kpis['headcount']:,}")
    with c2:
        rate = float(kpis["attendance_rate"])
        st.metric("✅ Attendance (30d)", f"{rate:.1f}%",
                  delta="Healthy" if rate >= 85 else "⚠ Below 85%",
                  delta_color="normal" if rate >= 85 else "inverse")
    with c3:
        res = int(kpis["active_resignations"])
        st.metric("📤 Resignations", res,
                  delta="Pending" if res else None,
                  delta_color="inverse" if res else "off")
    with c4:
        sl = int(kpis["stale_leaves"])
        st.metric("⏳ Stale Leaves >48h", sl,
                  delta="Action needed" if sl else "All clear",
                  delta_color="inverse" if sl else "off")
    with c5:
        st.metric("💰 Monthly Payroll", f"${float(kpis['monthly_payroll']):,.0f}")

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
    df = _turnover_cache()

    if df.empty:
        st.warning("""
**No turnover risk data found in `turnover_risk_cache`.**

Populate it by calling the ML prediction endpoint for each employee:
```
GET http://localhost:3000/api/v1/ml/turnover/{employeeId}
```
Or run the bulk scoring script if one exists.
        """)
        return

    counts = df["risk_level"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    for col, level, icon in zip([c1,c2,c3,c4], RISK_ORDER, ["🔴","🟠","🟡","🟢"]):
        with col:
            st.metric(f"{icon} {level.capitalize()}", int(counts.get(level, 0)))

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
            st.success("✅ No employees above the 55-point risk threshold.")
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

    # Factor breakdown
    st.markdown("---")
    st.markdown('<div class="section-header">Top Risk Factors (Employees > 55)</div>', unsafe_allow_html=True)
    factors = []
    for _, row in df[df["risk_score"] > 55].iterrows():
        fb = row.get("factor_breakdown")
        if isinstance(fb, dict):
            for k, v in fb.items():
                try:
                    factors.append({"Factor": k, "Weight": float(v)})
                except (TypeError, ValueError):
                    pass
        elif isinstance(fb, list):
            for item in fb:
                if isinstance(item, str):
                    factors.append({"Factor": item, "Weight": 1.0})

    if factors:
        fdf = pd.DataFrame(factors).groupby("Factor")["Weight"].sum().sort_values(ascending=False).head(12).reset_index()
        fig = px.bar(fdf, x="Weight", y="Factor", orientation="h",
                     color="Weight", color_continuous_scale="Reds",
                     text=fdf["Weight"].round(2))
        fig.update_traces(textposition="outside")
        fig.update_layout(height=340, margin=dict(l=0, r=60, t=5, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Factor breakdown JSON not available in current cache rows.")


def _tab_skill_gaps():
    with st.spinner("Fetching skill gap analysis from ML service…"):
        data = _skill_gaps()

    if "_error" in data:
        st.error(f"⚠️ ML service error: {data['_error']}")
        st.info("Start the ML service: `uvicorn app.main:app --port 8000` inside `ml_service/`")
        return

    gaps = data.get("skill_gaps", [])
    if not gaps:
        st.warning("ML service returned no skill gap data.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Skills Analyzed", data.get("total_skills_analyzed", len(gaps)))
    with c2: st.metric("🔴 Critical Skills", data.get("critical_skills", 0))
    with c3:
        high_n = sum(1 for g in gaps if g.get("criticality") == "high")
        st.metric("🟠 High Priority", high_n)
    with c4:
        surplus = sum(1 for g in gaps if g.get("criticality") == "surplus")
        st.metric("🟢 Surplus Skills", surplus)

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
    with c1: st.metric("💰 Total Payroll (This Month)", f"${total_cost:,.0f}")
    with c2: st.metric("👥 Employees Paid",             total_emps)
    with c3: st.metric("📊 Avg Net Salary",             f"${avg_sal:,.0f}")

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
        if st.button("🔄 Refresh", use_container_width=True):
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


# ══════════════════════════════════════════════════════════════════════════════
# Main entry-point
# ══════════════════════════════════════════════════════════════════════════════

if "hr_user" not in st.session_state:
    st.markdown("""
    <div class="dash-header">
        <h1>🏢 SkillSync · HR Admin Analytics Dashboard</h1>
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
    <h1>🏢 SkillSync · HR Admin Analytics Dashboard</h1>
    <p>Organization health overview &nbsp;·&nbsp; {now.strftime('%A, %d %B %Y')}
       &nbsp;·&nbsp; {now.strftime('%H:%M')}</p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs([
    "🏥 Workforce Health",
    "⚠️ Turnover Risk",
    "🎯 Skill Gaps",
    "💰 Payroll Analytics",
    "📋 Audit Log",
])
with t1: _tab_workforce()
with t2: _tab_turnover()
with t3: _tab_skill_gaps()
with t4: _tab_payroll()
with t5: _tab_audit()
