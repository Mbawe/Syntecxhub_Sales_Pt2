"""Syntecxhub Retail Sales Intelligence & Executive Analytics Dashboard.
Built with Streamlit, Plotly, and Pandas.
Implements dual-theming (Dark/Light), 3-row scannable hierarchy, and automated AI summary.
"""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

if __package__:
    from .ai_engine import AIInsightsEngine
    from .config import DATA_DIR, REPORTS_DIR
    from .data_handler import DataIngestionEngine
    from .kpi_engine import KPIComputationEngine
    from .report import build_summary_pdf
    from .theme import get_custom_css, get_theme_colors
    from .visuals import DashboardVisuals
else:
    src_dir = Path(__file__).resolve().parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from ai_engine import AIInsightsEngine
    from config import DATA_DIR, REPORTS_DIR
    from data_handler import DataIngestionEngine
    from kpi_engine import KPIComputationEngine
    from report import build_summary_pdf
    from theme import get_custom_css, get_theme_colors
    from visuals import DashboardVisuals


def toggle_theme():
    st.session_state.is_dark = not st.session_state.is_dark


def main():
    # Configure page layout and meta
    st.set_page_config(
        page_title="Syntecxhub | Sales Intelligence Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize Session State
    if "is_dark" not in st.session_state:
        st.session_state.is_dark = True

    if "active_df" not in st.session_state:
        st.session_state.active_df = None

    if "dataset_name" not in st.session_state:
        st.session_state.dataset_name = "retail_transactions_master.csv"

    if "ai_summary_text" not in st.session_state:
        st.session_state.ai_summary_text = None

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    # Inject theme CSS
    st.markdown(get_custom_css(st.session_state.is_dark), unsafe_allow_html=True)
    theme_colors = get_theme_colors(st.session_state.is_dark)

    # ==========================================
    # SIDEBAR: DATA INGESTION & CONTROLS
    # ==========================================
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <div style="background-color: {theme_colors['accent']}; color: white; font-weight: 800; font-size: 18px; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">S</div>
                <div>
                    <div style="font-weight: 800; font-size: 16px; color: {theme_colors['text_primary']};">SYNTECXHUB</div>
                    <div style="font-size: 11px; color: {theme_colors['text_secondary']};">Executive BI Suite</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Theme Toggle
        theme_label = "🌙 Dark Mode Active" if st.session_state.is_dark else "☀️ Light Mode Active"
        if st.button(f"Switch Theme ({theme_label})", use_container_width=True):
            toggle_theme()
            st.rerun()

        st.markdown("---")
        st.subheader("📁 Ingestion & Source Data")

        # Quick Demo Loaders
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("Load Master Data", use_container_width=True):
                st.session_state.dataset_name = "retail_transactions_master.csv"
                st.session_state.active_df = None
                st.rerun()
        with col_d2:
            if st.button("Load Legacy 3-Col", use_container_width=True):
                st.session_state.dataset_name = "project1_ideal_12months.csv"
                st.session_state.active_df = None
                st.rerun()

        # File Uploader (Up to 500MB)
        uploaded_file = st.file_uploader(
            "Upload Sales Ledger (CSV/XLSX)",
            type=["csv", "xlsx", "xls"],
            help="Supports files up to 500MB with mixed date formats and automatic delimiter sniffing.",
        )

        if uploaded_file is not None:
            ingestion = DataIngestionEngine()
            file_bytes = uploaded_file.getvalue()
            ok, msg = ingestion.load_file(file_bytes, filename=uploaded_file.name)
            if ok:
                st.session_state.active_df = ingestion.df
                st.session_state.dataset_name = uploaded_file.name
                st.success(f"Loaded: {uploaded_file.name}")
            else:
                st.error(msg)

        st.markdown("---")
        st.subheader("🤖 AI Summary Settings")
        api_key_input = st.text_input(
            "OpenAI / Anthropic / Gemini Key (Optional)",
            value=st.session_state.api_key,
            type="password",
            help="Leave blank to use the deterministic local analytical intelligence engine.",
        )
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input

    # ==========================================
    # LOAD DATASET PIPELINE
    # ==========================================
    if st.session_state.active_df is None:
        ingestion = DataIngestionEngine()
        source_path = DATA_DIR / st.session_state.dataset_name
        if not source_path.exists():
            # Fallback to master
            source_path = DATA_DIR / "retail_transactions_master.csv"

        ok, msg = ingestion.load_file(source_path, filename=source_path.name)
        if ok:
            st.session_state.active_df = ingestion.df
        else:
            st.error(f"Failed to load dataset: {msg}")
            st.stop()

    # Interactive Filter Controls in Sidebar
    df_working = st.session_state.active_df.copy()

    with st.sidebar:
        st.markdown("---")
        st.subheader("🔍 Dynamic Filters")
        available_regions = ["All Regions"] + sorted(df_working["Geographic_Region"].unique().tolist())
        selected_region = st.selectbox("Geographic Region", available_regions)

        available_categories = ["All Categories"] + sorted(df_working["Product_Category"].unique().tolist())
        selected_category = st.selectbox("Product Category", available_categories)

        if selected_region != "All Regions":
            df_working = df_working[df_working["Geographic_Region"] == selected_region]

        if selected_category != "All Categories":
            df_working = df_working[df_working["Product_Category"] == selected_category]

    # ==========================================
    # COMPUTE KPIS
    # ==========================================
    kpi_engine = KPIComputationEngine(df_working)
    kpi_data = kpi_engine.compute_all_metrics()
    visuals = DashboardVisuals(is_dark=st.session_state.is_dark)

    # ==========================================
    # HEADER BRANDING BAR
    # ==========================================
    st.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-title">
                <span style="color: {theme_colors['accent']}; font-weight: 900;">SYNTECXHUB</span>
                <span style="font-weight: 300; opacity: 0.5;">|</span>
                <span>Retail Business Intelligence</span>
                <span class="brand-badge">Executive Edition</span>
            </div>
            <div style="font-size: 0.8rem; color: {theme_colors['text_secondary']}; display: flex; align-items: center; gap: 12px;">
                <span>Source: <b>{st.session_state.dataset_name}</b></span>
                <span>•</span>
                <span>{len(df_working):,} Active Transactions</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # ROW 1 (TOP): 3 LIGHTWEIGHT KPI CARDS
    # ==========================================
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    tot_rev = kpi_data["total_revenue"]
    aov = kpi_data["aov"]
    top_reg = kpi_data["top_region_name"]
    top_reg_share = kpi_data["top_region_share"]
    peak_info = kpi_data.get("peak_month_info", {})
    peak_month = peak_info.get("month", "Peak")

    with kpi_col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Net Revenue</div>
                <div class="kpi-value">${tot_rev:,.2f}</div>
                <div class="kpi-trend trend-up">
                    <span>▲</span>
                    <span>Peak in {peak_month}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Average Order Value (AOV)</div>
                <div class="kpi-value">${aov:,.2f}</div>
                <div class="kpi-trend trend-neutral">
                    <span>⚡</span>
                    <span>{kpi_data['unique_transactions']:,} Distinct Orders</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Top Geographic Region</div>
                <div class="kpi-value">{top_reg}</div>
                <div class="kpi-trend trend-up">
                    <span>★</span>
                    <span>{top_reg_share:.1f}% Revenue Share</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")  # Visual spacer

    # ==========================================
    # ROW 2 (MIDDLE): SPLIT-SCREEN VISUALIZATIONS
    # ==========================================
    row2_col_left, row2_col_right = st.columns([1.1, 0.9])

    with row2_col_left:
        st.markdown(
            """
            <div class="dashboard-panel" style="margin-bottom: 0px;">
                <div class="panel-header">
                    <div class="panel-title">📈 Revenue Performance Time-Series</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Monthly Aggregation</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_timeseries = visuals.chart_revenue_timeseries(kpi_data["monthly_trends"])
        st.plotly_chart(fig_timeseries, use_container_width=True, config={"displayModeBar": False})

    with row2_col_right:
        st.markdown(
            """
            <div class="dashboard-panel" style="margin-bottom: 0px;">
                <div class="panel-header">
                    <div class="panel-title">🏆 Top 10 Products by Revenue</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Product SKU Ranking</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig_products = visuals.chart_top_products_bar(kpi_data["sku_breakdown"], top_n=10)
        st.plotly_chart(fig_products, use_container_width=True, config={"displayModeBar": False})

    st.write("")  # Visual spacer

    # ==========================================
    # ROW 3 (BOTTOM): AI EXECUTIVE SUMMARY & ONE-PAGE PDF EXPORT
    # ==========================================
    st.markdown(
        """
        <div class="dashboard-panel">
            <div class="panel-header">
                <div class="panel-title">🤖 AI Executive Insights & Strategy Engine</div>
                <div style="font-size: 0.75rem; color: #3B82F6; font-weight: 600;">Autonomous Diagnostic Model</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # AI Summary generation via AIInsightsEngine (Module C)
    ai_payload = kpi_data["ai_payload"]
    ai_engine = AIInsightsEngine(api_key=st.session_state.api_key)

    if "ai_insights" not in st.session_state or st.session_state.get("last_payload_hash") != hash(str(ai_payload)):
        st.session_state.ai_insights = ai_engine.generate_executive_insights(ai_payload)
        st.session_state.last_payload_hash = hash(str(ai_payload))

    trends = st.session_state.ai_insights.get("trends", [])
    recs = st.session_state.ai_insights.get("recommendations", [])

    summary_col_left, summary_col_right = st.columns([1.5, 0.5])

    with summary_col_left:
        bullet_trends_html = "".join([f'<div class="ai-bullet"><span class="ai-bullet-icon">●</span><span>{t}</span></div>' for t in trends])
        bullet_recs_html = "".join([f'<div class="ai-bullet"><span class="ai-bullet-icon">▸</span><span>{r}</span></div>' for r in recs])

        st.markdown(
            f"""
            <div class="ai-summary-box">
                <div style="font-weight: 700; font-size: 0.85rem; color: {theme_colors['accent']}; margin-bottom: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em;">
                    Executive Performance Summary (3 Key Observations)
                </div>
                {bullet_trends_html}
                <div style="font-weight: 700; font-size: 0.85rem; color: {theme_colors['accent']}; margin: 0.85rem 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.05em;">
                    Hyper-Local Strategic Recommendations (3 Tactical Initiatives)
                </div>
                {bullet_recs_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with summary_col_right:
        st.markdown(
            f"""
            <div style="background-color: {theme_colors['card_bg']}; border: 1px solid {theme_colors['card_border']}; border-radius: 10px; padding: 1.1rem; text-align: center;">
                <div style="font-size: 0.85rem; font-weight: 700; margin-bottom: 0.4rem; color: {theme_colors['text_primary']};">Executive Report Export</div>
                <div style="font-size: 0.75rem; color: {theme_colors['text_secondary']}; margin-bottom: 1rem;">
                    Compiles KPIs, Plotly charts, and AI strategic recommendations into a guaranteed single-page PDF.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Generate & Download One-Page PDF", use_container_width=True):
            # Prepare chart base64 strings for the PDF engine
            chart_b64s = {}
            # Revenue timeseries chart
            fig_ts = visuals.chart_revenue_timeseries(kpi_data["monthly_trends"])
            img_ts = fig_ts.to_image(format="png")
            chart_b64s["trend"] = base64.b64encode(img_ts).decode()
            # Top products bar chart
            fig_prod = visuals.chart_top_products_bar(kpi_data["sku_breakdown"], top_n=10)
            img_prod = fig_prod.to_image(format="png")
            chart_b64s["category"] = base64.b64encode(img_prod).decode()
            # Generate PDF (also write to a temporary file for debugging)
            pdf_path = REPORTS_DIR / "temp_executive_report.pdf"
            pdf_bytes = build_summary_pdf(
                str(pdf_path),
                kpis=kpi_data,
                chart_b64s=chart_b64s,
                theme="dark" if st.session_state.is_dark else "light",
            )
            # Provide download button
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="Executive_Summary.pdf",
                mime="application/pdf",
            )

    # Collapsible Data Table
    with st.expander("🔍 View Raw Cleaned Ledger Data (Top 50 Rows)"):
        st.dataframe(df_working.head(50), use_container_width=True)


if __name__ == "__main__":
    main()
