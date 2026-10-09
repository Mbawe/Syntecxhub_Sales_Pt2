"""Interactive Plotly Visualization Engine with Dual-Theme Responsiveness.
Renders interactive time-series trend lines and Top 10 Products horizontal bar charts
styled strictly with Dark/Light mode tokens and Electric Blue primary highlights.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

if __package__:
    from .theme import get_theme_colors
else:
    from theme import get_theme_colors


class DashboardVisuals:
    """Plotly chart generator implementing corporate dual-theming specifications."""

    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.colors = get_theme_colors(is_dark)

    def chart_revenue_timeseries(self, monthly_df: pd.DataFrame, daily_df: pd.DataFrame | None = None) -> go.Figure:
        """Interactive time-series trend line for Row 2 (Left Side).

        Features:
        - Electric Blue primary line with soft area fill.
        - Dynamic hover tooltips showing revenue and transaction volume.
        - Theme-aware background and gridlines.
        """
        fig = go.Figure()

        accent = self.colors["accent"]
        card_bg = self.colors["chart_paper"]
        text_primary = self.colors["text_primary"]
        text_muted = self.colors["text_secondary"]
        grid_color = self.colors["grid_color"]

        # Prefer monthly data for smooth executive clarity
        if monthly_df is not None and not monthly_df.empty:
            x_vals = monthly_df["Month_Name"]
            y_vals = monthly_df["Revenue"]
            orders = monthly_df.get("Transactions", [0] * len(monthly_df))

            # Primary Revenue Line & Fill
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines+markers",
                    name="Revenue",
                    line=dict(color=accent, width=3.2, shape="spline", smoothing=1.1),
                    marker=dict(size=7, color=accent, line=dict(color="#FFFFFF", width=1.5)),
                    fill="tozeroy",
                    fillcolor="rgba(0, 82, 255, 0.10)" if not self.is_dark else "rgba(59, 130, 246, 0.15)",
                    hovertemplate="<b>%{x}</b><br>Revenue: <b>$%{y:,.2f}</b><br><extra></extra>",
                )
            )

        # Safely update layout; fallback on error
        try:
            fig.update_layout(
                paper_bgcolor=card_bg,
                plot_bgcolor=card_bg,
                margin=dict(l=15, r=15, t=35, b=25),
                height=370,
                hovermode="x unified",
                xaxis=dict(
                    showgrid=True,
                    gridcolor=grid_color,
                    tickfont=dict(color=text_muted, size=11, family="Inter"),
                    showline=False,
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=grid_color,
                    tickprefix="$",
                    tickformat="~s",
                    tickfont=dict(color=text_muted, size=11, family="Inter"),
                    showline=False,
                ),
                showlegend=False,
            )
        except Exception as e:
            print(f"[visuals] layout error: {e}")
            fig.update_layout(
                paper_bgcolor=card_bg,
                plot_bgcolor=card_bg,
                margin=dict(l=15, r=15, t=35, b=25),
                height=370,
                xaxis=dict(showgrid=False, showline=False),
                yaxis=dict(showgrid=False, showline=False),
                legend=dict(showlegend=False),
            )

        return fig

    def chart_top_products_bar(self, sku_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Horizontal bar chart for Top 10 Products by Revenue for Row 2 (Right Side).

        Features:
        - Sorted descending (top performer at the top).
        - Electric Blue bars with clean value tags.
        - Hover details showing SKU, Category, and Units Sold.
        """
        fig = go.Figure()

        accent = self.colors["accent"]
        card_bg = self.colors["chart_paper"]
        text_primary = self.colors["text_primary"]
        text_muted = self.colors["text_secondary"]
        grid_color = self.colors["grid_color"]

        if sku_df is not None and not sku_df.empty:
            top_subset = sku_df.head(top_n).copy()
            # Reverse order so the highest product is rendered at the top of the horizontal bar chart
            top_subset = top_subset.iloc[::-1]

            fig.add_trace(
                go.Bar(
                    x=top_subset["Total_Revenue"],
                    y=top_subset["Product_SKU"],
                    orientation="h",
                    marker=dict(
                        color=accent,
                        opacity=0.92,
                        line=dict(color=accent, width=1),
                    ),
                    text=top_subset["Total_Revenue"].apply(lambda v: f"${v:,.0f}"),
                    textposition="auto",
                    textfont=dict(color="#FFFFFF", size=10, family="Inter"),
                    customdata=top_subset[["Product_Category", "Units_Sold"]].values,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Category: %{customdata[0]}<br>"
                        "Revenue: <b>$%{x:,.2f}</b><br>"
                        "Units Sold: %{customdata[1]:,}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            paper_bgcolor=card_bg,
            plot_bgcolor=card_bg,
            margin=dict(l=15, r=25, t=35, b=25),
            height=370,
            xaxis=dict(
                showgrid=True,
                gridcolor=grid_color,
                tickprefix="$",
                tickformat="~s",
                tickfont=dict(color=text_muted, size=11, family="Inter"),
                showline=False,
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(color=text_primary, size=11, family="Inter"),
                showline=False,
            ),
            legend=dict(showlegend=False),
        )

        return fig

    def chart_regional_yield(self, regions_matrix: pd.DataFrame) -> go.Figure:
        """Donut/Bar visualization of Regional Revenue Distribution."""
        fig = go.Figure()
        card_bg = self.colors["chart_paper"]
        text_muted = self.colors["text_secondary"]
        accent = self.colors["accent"]

        if regions_matrix is not None and not regions_matrix.empty:
            # Corporate color palette with Electric Blue as dominant slice
            palette = [
                accent,
                "#10B981" if self.is_dark else "#059669",
                "#8B5CF6" if self.is_dark else "#7C3AED",
                "#F59E0B" if self.is_dark else "#D97706",
                "#EC4899" if self.is_dark else "#DB2777",
                "#64748B",
            ]

            fig.add_trace(
                go.Pie(
                    labels=regions_matrix["Geographic_Region"],
                    values=regions_matrix["Total_Revenue"],
                    hole=0.62,
                    marker=dict(colors=palette[: len(regions_matrix)]),
                    textinfo="label+percent",
                    textfont=dict(size=11, family="Inter"),
                    hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
                )
            )

        fig.update_layout(
            paper_bgcolor=card_bg,
            plot_bgcolor=card_bg,
            margin=dict(l=10, r=10, t=25, b=25),
            height=280,
            showlegend=False,
        )
        return fig
