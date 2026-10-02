import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="FORESIGHT | Inventory Intelligence", page_icon="🔮",
                   layout="wide", initial_sidebar_state="expanded")

# ---------------- Design tokens ----------------
INK, MUTED, LINE, CANVAS = "#0b1b2b", "#5b6b7c", "#e3e9f0", "#f3f6fa"
TEAL, CORAL, AMBER, INDIGO = "#0d9488", "#e11d48", "#f59e0b", "#4f46e5"
FONT = "Manrope, 'Segoe UI', sans-serif"

# Plain string (not an f-string) so CSS braces need no escaping.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: light only; --ink:#0b1b2b; --muted:#5b6b7c; --line:#e3e9f0; }
html, body, .stApp, [data-testid="stAppViewContainer"] { background:#f3f6fa !important; font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:transparent !important; }
.block-container { padding-top:1.6rem; max-width:1320px; }
/* Sidebar: style text elements only, so the icon font keeps working */
[data-testid="stSidebar"] { background:#0b1b2b !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] span[data-testid="stWidgetLabel"] { color:#dbe5ef !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#8fa3b8 !important; }
[data-testid="stSidebar"] hr { border-color:#1e3248; }
div[data-baseweb="select"] > div { border-radius:10px !important; }
/* Hero */
.hero { background:linear-gradient(120deg,#0b1b2b 0%,#12314a 55%,#0d9488 130%); border-radius:18px;
        padding:30px 34px; color:#fff; margin-bottom:18px; }
.hero h1 { font-size:38px; font-weight:800; letter-spacing:-1px; margin:0 0 6px 0; color:#fff; }
.hero p { color:#bcd0e2; font-size:15px; margin:0; max-width:640px; line-height:1.55; }
.pill { display:inline-block; background:rgba(255,255,255,.12); color:#e6f2fb; border-radius:999px;
        padding:4px 12px; font-size:12px; font-weight:600; margin:0 8px 14px 0; }
/* KPI cards */
.kpi { background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; min-height:118px; }
.kpi .l { color:var(--muted); font-size:13px; font-weight:600; }
.kpi .v { color:var(--ink); font-size:28px; font-weight:800; letter-spacing:-.5px; margin:6px 0 4px; }
.kpi .n { color:var(--muted); font-size:12px; line-height:1.4; }
.sec { font-size:20px; font-weight:800; color:var(--ink); margin:26px 0 2px; letter-spacing:-.3px; }
.sub { color:var(--muted); font-size:14px; margin-bottom:12px; }
.badge { display:inline-block; padding:5px 14px; border-radius:999px; font-weight:700; font-size:13px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px; }
div[data-testid="stPlotlyChart"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:6px; }
button[data-baseweb="tab"] { font-weight:700; font-size:15px; }
.term { background:#fff; border:1px solid var(--line); border-left:4px solid #0d9488; border-radius:12px;
        padding:14px 16px; margin-bottom:10px; }
.term b { color:var(--ink); } .term span { color:var(--muted); font-size:14px; }
.foot { text-align:center; color:var(--muted); font-size:12px; padding:30px 0 6px; }
</style>
""", unsafe_allow_html=True)


# ---------------- Helpers ----------------
def style_fig(fig, h=380, **kw):
    fig.update_layout(height=h, template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, color=INK, size=13),
                      title=dict(font=dict(size=16), x=0.01, xanchor="left"),
                      margin=kw.pop("margin", dict(l=20, r=20, t=60, b=20)),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
                      hoverlabel=dict(font_family=FONT), **kw)
    fig.update_xaxes(showgrid=False, linecolor=LINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor="#eef2f7", zeroline=False, rangemode="tozero", tickfont=dict(color=MUTED))
    return fig


def find_col(df, keys, numeric=False, exclude=()):
    for c in df.columns:
        lc = c.lower()
        if c in exclude or not any(k in lc for k in keys):
            continue
        if not numeric or pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def flag(s):
    return s.astype(str).str.lower().isin(["yes", "true", "1", "high"])


def money(x):
    return f"₹{x/1e6:.2f}M"


def kpi(col, label, value, note, color=TEAL):
    col.markdown(f'<div class="kpi" style="border-top:3px solid {color}"><div class="l">{label}</div>'
                 f'<div class="v">{value}</div><div class="n">{note}</div></div>', unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f'<div class="sec">{title}</div><div class="sub">{sub}</div>', unsafe_allow_html=True)


def line_with_ma(df, x, y, title, name="Weekly demand", h=400):
    d = df.sort_values(x).copy()
    d["ma4"], d["ma12"] = d[y].rolling(4, min_periods=1).mean(), d[y].rolling(12, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d[x], y=d[y], name=name, mode="lines", line=dict(color="#9db4c8", width=1.5),
                             fill="tozeroy", fillcolor="rgba(13,148,136,0.07)"))
    fig.add_trace(go.Scatter(x=d[x], y=d["ma4"], name="4-week average", mode="lines", line=dict(color=TEAL, width=3)))
    fig.add_trace(go.Scatter(x=d[x], y=d["ma12"], name="12-week trend", mode="lines",
                             line=dict(color=INDIGO, width=2.5, dash="dash")))
    fig.add_hline(y=d[y].mean(), line=dict(color=AMBER, width=1.2, dash="dot"),
                  annotation_text="Average", annotation_position="top left")
    style_fig(fig, h, title_text=title, hovermode="x unified")
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06),
                     rangeselector=dict(buttons=[dict(count=3, label="3M", step="month", stepmode="backward"),
                                                 dict(count=6, label="6M", step="month", stepmode="backward"),
                                                 dict(step="all", label="All")]))
    return fig


# ---------------- Data ----------------
BASE = Path(__file__).parent


@st.cache_data
def load(name):
    p = BASE / name
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d.columns = d.columns.str.strip()
    return d


risk_df, weekly_df, fc_df = load("business_risk_analysis.csv"), load("weekly_demand.csv"), load("model_forecast_results.csv")
if risk_df is None or weekly_df is None:
    st.error("Could not load business_risk_analysis.csv or weekly_demand.csv. Keep them next to dashboard.py.")
    st.stop()

# ---------------- Sidebar filters ----------------
st.sidebar.markdown("## 🔮 FORESIGHT")
st.sidebar.caption("Demand & inventory intelligence")
st.sidebar.markdown("---")
cats = ["All categories"] + (sorted(risk_df["Category"].dropna().astype(str).unique()) if "Category" in risk_df else [])
sel_cat = st.sidebar.selectbox("Category", cats)
view = risk_df if sel_cat == "All categories" or "Category" not in risk_df else risk_df[risk_df["Category"].astype(str) == sel_cat]
skus = ["All SKUs"] + sorted(view["SKU"].dropna().astype(str).unique())
sel_sku = st.sidebar.selectbox("SKU", skus)
if sel_sku != "All SKUs":
    view = view[view["SKU"].astype(str) == sel_sku]
st.sidebar.markdown("---")
st.sidebar.caption("Filters apply to every tab. Pick a SKU to jump straight to its details.")

if view.empty:
    st.warning("No records match these filters. Try 'All categories'.")
    st.stop()

latest = view.copy()
if "Snapshot_Date" in latest:
    latest["Snapshot_Date"] = pd.to_datetime(latest["Snapshot_Date"], errors="coerce")
    latest = latest[latest["Snapshot_Date"] == latest["Snapshot_Date"].max()]


def total(c):
    return pd.to_numeric(latest[c], errors="coerce").fillna(0).sum() if c in latest else 0


stock_val, over_val = total("Stockout_Sales_At_Risk"), total("Overstock_Value")
n = len(latest)
so_n = int(flag(latest["Stockout_Risk"]).sum()) if "Stockout_Risk" in latest else 0
ov_n = int(flag(latest["Overstock_Risk"]).sum()) if "Overstock_Risk" in latest else 0
at_risk = int((flag(latest["Stockout_Risk"]) | flag(latest["Overstock_Risk"])).sum()) if so_n + ov_n else 0
health = round(100 * (1 - at_risk / n)) if n else 100
snap = latest["Snapshot_Date"].max().strftime("%d %b %Y") if "Snapshot_Date" in latest and latest["Snapshot_Date"].notna().any() else "latest"

# ---------------- Hero ----------------
st.markdown(f"""<div class="hero"><span class="pill">NorthBay Living</span><span class="pill">Snapshot: {snap}</span>
<span class="pill">{n} SKUs in view</span><h1>FORESIGHT</h1>
<p>See what customers will buy next, where stock may run out, and where money is sitting idle on shelves.</p></div>""",
            unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Demand trends", "SKU explorer", "Risk map", "Key terms"])

# ================= TAB 1: OVERVIEW =================
with tab1:
    c = st.columns(5)
    kpi(c[0], "Inventory health", f"{health}%", f"{n - at_risk} of {n} SKUs have no risk flag", TEAL)
    kpi(c[1], "Possible stockouts", f"{so_n}", "SKUs that may run out before restock", CORAL)
    kpi(c[2], "Overstocked SKUs", f"{ov_n}", "SKUs holding more than demand needs", AMBER)
    kpi(c[3], "Sales at risk", money(stock_val), "Revenue exposed to stockouts", CORAL)
    kpi(c[4], "Cash tied in extra stock", money(over_val), "Working capital sitting idle", AMBER)

    g1, g2 = st.columns([1, 1.4])
    with g1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=health, number=dict(suffix="%", font=dict(size=42)),
                                     title=dict(text="Inventory health score", font=dict(size=16)),
                                     gauge=dict(axis=dict(range=[0, 100]), bar=dict(color=INK),
                                                steps=[dict(range=[0, 60], color="#fecdd3"), dict(range=[60, 85], color="#fde68a"),
                                                       dict(range=[85, 100], color="#99f6e4")])))
        st.plotly_chart(style_fig(fig, 360), use_container_width=True)
    with g2:
        if "Category" in latest and "Stockout_Sales_At_Risk" in latest:
            cd = latest.groupby("Category").agg(a=("Stockout_Sales_At_Risk", "sum"), b=("Overstock_Value", "sum")).reset_index()
            cd = cd.melt("Category", ["a", "b"], "Type", "Value").replace({"a": "Sales at risk", "b": "Extra stock"})
            fig = px.bar(cd, x="Category", y="Value", color="Type", barmode="group", title="Money at risk by category",
                         color_discrete_map={"Sales at risk": CORAL, "Extra stock": AMBER})
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(style_fig(fig, 360, yaxis_title="Value (₹)", xaxis_title=""), use_container_width=True)

    a1, a2 = st.columns(2)
    if "Recommended_Action" in latest:
        ac = latest["Recommended_Action"].fillna("Review").astype(str).value_counts().reset_index()
        ac.columns = ["Action", "SKUs"]
        with a1:
            fig = px.pie(ac, names="Action", values="SKUs", hole=0.62, title="What to do next",
                         color_discrete_sequence=[TEAL, CORAL, AMBER, INDIGO, "#94a3b8"])
            fig.update_traces(textinfo="label+value", marker=dict(line=dict(color="#fff", width=2)))
            st.plotly_chart(style_fig(fig, 380, showlegend=False), use_container_width=True)
    if "Total_Value_At_Risk" in latest:
        with a2:
            top = latest.nlargest(10, "Total_Value_At_Risk").sort_values("Total_Value_At_Risk")
            fig = px.bar(top, x="Total_Value_At_Risk", y="SKU", orientation="h", title="Top 10 SKUs by value at risk",
                         color="Total_Value_At_Risk", color_continuous_scale=["#fde68a", CORAL])
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_fig(fig, 380, xaxis_title="Value at risk (₹)", yaxis_title=""), use_container_width=True)

    section("Priority list", "SKUs with the biggest financial impact come first.")
    cols = [c for c in ["SKU", "Category", "Current_Stock", "Average_Weekly_Demand", "Weeks_of_Cover", "Stockout_Risk",
                        "Overstock_Risk", "Recommended_Action", "Total_Value_At_Risk"] if c in latest]
    pr = latest.sort_values("Total_Value_At_Risk", ascending=False) if "Total_Value_At_Risk" in latest else latest
    pr = pr[cols].head(15)
    cfg = {}
    if "Weeks_of_Cover" in pr:
        cfg["Weeks_of_Cover"] = st.column_config.ProgressColumn("Weeks of cover", min_value=0, max_value=12, format="%.1f")
    if "Total_Value_At_Risk" in pr:
        cfg["Total_Value_At_Risk"] = st.column_config.NumberColumn("Value at risk", format="₹%d")
    st.dataframe(pr, use_container_width=True, hide_index=True, column_config=cfg)
    st.download_button("Download priority list (CSV)", pr.to_csv(index=False), "foresight_priority_list.csv", "text/csv")

# ================= TAB 2: DEMAND TRENDS =================
dcol = find_col(weekly_df, ["week", "date"])
ycol = find_col(weekly_df, ["demand", "units", "qty", "quantity", "sales"], numeric=True, exclude=("SKU",))
with tab2:
    if not (dcol and ycol):
        st.info(f"Could not detect the date and demand columns. Columns found: {list(weekly_df.columns)}")
    else:
        wk = weekly_df.copy()
        wk[dcol] = pd.to_datetime(wk[dcol], errors="coerce")
        wk[ycol] = pd.to_numeric(wk[ycol], errors="coerce")
        wk = wk.dropna(subset=[dcol, ycol])
        if "Category" in risk_df and "SKU" in wk:
            cmap = risk_df.drop_duplicates("SKU").set_index(risk_df.drop_duplicates("SKU")["SKU"].astype(str))["Category"]
            wk["Category"] = wk["SKU"].astype(str).map(cmap)
        scope = wk[wk["Category"] == sel_cat] if sel_cat != "All categories" and "Category" in wk else wk
        overall = scope.groupby(dcol)[ycol].sum().reset_index()

        section("Demand over time", "Grey is the raw weekly demand. The coloured lines smooth it so the trend is easy to see.")
        t = overall[ycol]
        m = st.columns(4)
        m[0].metric("Total demand", f"{t.sum():,.0f}")
        m[1].metric("Average per week", f"{t.mean():,.0f}")
        m[2].metric("Peak week", f"{t.max():,.0f}")
        last8, prev8 = t.tail(8).mean(), t.iloc[-16:-8].mean() if len(t) >= 16 else t.mean()
        m[3].metric("Last 8 weeks vs previous 8", f"{last8:,.0f}", f"{(last8 / prev8 - 1) * 100:+.1f}%" if prev8 else None)
        st.plotly_chart(line_with_ma(overall, dcol, ycol, "Weekly demand with moving averages"), use_container_width=True)

        if "Category" in scope and scope["Category"].notna().any():
            cat_ts = scope.groupby([dcol, "Category"])[ycol].sum().reset_index().sort_values(dcol)
            cat_ts["Smoothed"] = cat_ts.groupby("Category")[ycol].transform(lambda s: s.rolling(4, min_periods=1).mean())
            fig = px.line(cat_ts, x=dcol, y="Smoothed", color="Category", title="Demand by category (4-week average)",
                          color_discrete_sequence=[TEAL, INDIGO, CORAL, AMBER, "#0ea5e9", "#84cc16"])
            fig.update_traces(line=dict(width=2.6))
            st.plotly_chart(style_fig(fig, 400, hovermode="x unified", xaxis_title="", yaxis_title="Demand"),
                            use_container_width=True)

        if fc_df is not None:
            fd = find_col(fc_df, ["week", "date"])
            fa = find_col(fc_df, ["actual"], numeric=True)
            ff = find_col(fc_df, ["forecast", "pred"], numeric=True)
            if fd and fa and ff:
                f = fc_df.copy()
                f[fd] = pd.to_datetime(f[fd], errors="coerce")
                if "SKU" in f and sel_sku != "All SKUs":
                    f = f[f["SKU"].astype(str) == sel_sku]
                f = f.groupby(fd)[[fa, ff]].sum().reset_index().sort_values(fd)
                section("Forecast vs actual", "How closely the Random Forest model tracked real demand.")
                wape = (f[fa] - f[ff]).abs().sum() / f[fa].sum() if f[fa].sum() else 0
                m = st.columns(3)
                m[0].metric("WAPE (lower is better)", f"{wape * 100:.1f}%")
                m[1].metric("Forecast accuracy", f"{(1 - wape) * 100:.1f}%")
                m[2].metric("Weeks evaluated", f"{len(f)}")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=f[fd], y=f[fa], name="Actual", line=dict(color=INK, width=3)))
                fig.add_trace(go.Scatter(x=f[fd], y=f[ff], name="Forecast", line=dict(color=TEAL, width=3, dash="dash")))
                style_fig(fig, 400, title_text="Forecast vs actual demand", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ================= TAB 3: SKU EXPLORER =================
with tab3:
    sku_list = sorted(risk_df["SKU"].dropna().astype(str).unique())
    idx = sku_list.index(sel_sku) if sel_sku in sku_list else 0
    pick = st.selectbox("Choose a SKU", sku_list, index=idx)
    one = risk_df[risk_df["SKU"].astype(str) == pick].copy()
    if "Snapshot_Date" in one:
        one["Snapshot_Date"] = pd.to_datetime(one["Snapshot_Date"], errors="coerce")
        one = one.sort_values("Snapshot_Date")
    d = one.iloc[-1]
    action = str(d.get("Recommended_Action", "Review"))
    tone = {"healthy": ("#ccfbf1", "#0f766e"), "reorder": ("#ffe4e6", "#be123c")}.get(
        next((k for k in ["healthy", "reorder"] if k in action.lower()), ""), ("#fef3c7", "#b45309"))
    st.markdown(f'<span class="badge" style="background:{tone[0]};color:{tone[1]}">{action}</span>', unsafe_allow_html=True)

    def num(k, fmt):
        v = pd.to_numeric(d.get(k), errors="coerce")
        return fmt.format(v) if pd.notna(v) else "n/a"

    m = st.columns(4)
    m[0].metric("Current stock", num("Current_Stock", "{:,.0f}"))
    m[1].metric("Weekly demand", num("Average_Weekly_Demand", "{:,.1f}"))
    m[2].metric("Weeks of cover", num("Weeks_of_Cover", "{:.1f}"))
    m[3].metric("Value at risk", num("Total_Value_At_Risk", "₹{:,.0f}"))

    cL, cR = st.columns([2.2, 1])
    with cL:
        if dcol and ycol and "SKU" in weekly_df:
            s = weekly_df[weekly_df["SKU"].astype(str) == pick].copy()
            s[dcol], s[ycol] = pd.to_datetime(s[dcol], errors="coerce"), pd.to_numeric(s[ycol], errors="coerce")
            s = s.dropna(subset=[dcol, ycol])
            if len(s):
                st.plotly_chart(line_with_ma(s, dcol, ycol, f"Demand history for {pick}", h=420), use_container_width=True)
            else:
                st.info("No weekly demand history for this SKU.")
    with cR:
        woc = pd.to_numeric(d.get("Weeks_of_Cover"), errors="coerce")
        if pd.notna(woc):
            fig = go.Figure(go.Indicator(mode="gauge+number", value=float(woc), number=dict(suffix=" wks"),
                                         title=dict(text="Stock cover", font=dict(size=16)),
                                         gauge=dict(axis=dict(range=[0, max(16, woc * 1.2)]), bar=dict(color=INK),
                                                    steps=[dict(range=[0, 2], color="#fecdd3"), dict(range=[2, 8], color="#99f6e4"),
                                                           dict(range=[8, 100], color="#fde68a")])))
            st.plotly_chart(style_fig(fig, 420), use_container_width=True)
            st.caption("Red: may run out. Green: comfortable. Amber: more stock than needed.")

# ================= TAB 4: RISK MAP =================
with tab4:
    section("Risk map", "Each bubble is a SKU. Big bubbles far from the middle deserve attention first.")
    need = {"Average_Weekly_Demand", "Weeks_of_Cover"}
    if need <= set(latest.columns):
        r = latest.copy()
        r["Size"] = pd.to_numeric(r.get("Total_Value_At_Risk", 1), errors="coerce").fillna(0).clip(lower=1)
        r["Status"] = "Healthy"
        if "Overstock_Risk" in r:
            r.loc[flag(r["Overstock_Risk"]), "Status"] = "Overstock"
        if "Stockout_Risk" in r:
            r.loc[flag(r["Stockout_Risk"]), "Status"] = "Stockout"
        fig = px.scatter(r, x="Average_Weekly_Demand", y="Weeks_of_Cover", size="Size", color="Status", hover_name="SKU",
                         size_max=44, title="Demand vs stock cover",
                         color_discrete_map={"Healthy": TEAL, "Stockout": CORAL, "Overstock": AMBER})
        fig.update_traces(marker=dict(line=dict(width=1, color="#fff"), opacity=0.85))
        st.plotly_chart(style_fig(fig, 520, xaxis_title="Weekly demand (units)", yaxis_title="Weeks of cover"),
                        use_container_width=True)
    else:
        st.info("Weekly demand and weeks of cover columns are needed for this chart.")

# ================= TAB 5: KEY TERMS =================
with tab5:
    section("Key terms", "Plain-language meanings for every number on this dashboard.")
    terms = [
        ("Weeks of cover", "How many weeks current stock lasts at the average sales rate. Stock ÷ weekly demand."),
        ("Stockout risk", "Stock is too low to meet expected demand, so sales may be lost."),
        ("Overstock risk", "Stock is far above expected demand, so cash is tied up and storage costs rise."),
        ("Safety stock", "A buffer kept to absorb sudden demand spikes or supplier delays."),
        ("Reorder point", "The stock level at which a new order should be placed."),
        ("Lead time", "Days or weeks between placing an order and receiving it."),
        ("Lead-time demand", "Expected sales while waiting for the order to arrive."),
        ("Forward demand", "Forecast sales over the coming weeks, used to judge future risk."),
        ("Sales at risk", "Estimated revenue lost if a stockout happens."),
        ("Extra stock value", "Value of inventory above what expected demand needs."),
        ("Inventory health score", "Share of SKUs that carry no stockout or overstock flag."),
        ("Seasonal-naive baseline", "A simple forecast that repeats last season's value. The model must beat it."),
        ("WAPE", "Weighted Absolute Percentage Error: total forecast error ÷ total actual demand. Lower is better."),
        ("Rolling-origin validation", "Testing the model repeatedly on later weeks, like real use, with an expanding training window."),
        ("Moving average", "Average of the last few weeks that smooths out noise to reveal the trend."),
    ]
    L, R = st.columns(2)
    for i, (k, v) in enumerate(terms):
        (L if i % 2 == 0 else R).markdown(f'<div class="term"><b>{k}</b><br><span>{v}</span></div>', unsafe_allow_html=True)

st.markdown('<div class="foot">FORESIGHT · Demand Forecasting & Inventory Risk Analytics · Zidio Development Internship</div>',
            unsafe_allow_html=True)
