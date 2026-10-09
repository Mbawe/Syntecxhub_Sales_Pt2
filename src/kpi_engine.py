"""Enterprise KPI and Business Intelligence Computation Engine.
Implements vectorized, mathematically precise financial calculations, AOV based on unique transaction IDs,
regional volume/yield matrix, seasonality delta analysis, and structured AI payload generation.
"""
from __future__ import annotations

import pandas as pd
import numpy as np


class KPIComputationEngine:
    """Vectorized calculation engine for retail transaction analytics."""

    def __init__(self, df: pd.DataFrame):
        """Initialize engine with normalized retail DataFrame.

        DataFrame must contain columns:
        ['Transaction_ID', 'Timestamp', 'Product_SKU', 'Product_Category',
         'Quantity_Sold', 'Unit_Price', 'Discount_Applied', 'Geographic_Region']
        """
        self.df = df.copy()
        self._prepare_data()

    def _prepare_data(self):
        """Perform row-level vectorized revenue calculation and extract temporal features."""
        # Row-level Total Revenue = (Quantity_Sold * Unit_Price) - Discount_Applied
        # Clip row revenue at 0.0 to prevent negative line items if discount exceeds gross price
        gross_revenue = self.df["Quantity_Sold"] * self.df["Unit_Price"]
        self.df["Gross_Revenue"] = gross_revenue
        self.df["Row_Revenue"] = (gross_revenue - self.df["Discount_Applied"]).clip(lower=0.0)

        # Temporal dimensions
        self.df["Year"] = self.df["Timestamp"].dt.year
        self.df["Month"] = self.df["Timestamp"].dt.to_period("M").astype(str)
        self.df["Month_Name"] = self.df["Timestamp"].dt.strftime("%b %Y")
        self.df["Date"] = self.df["Timestamp"].dt.date

    def compute_all_metrics(self) -> dict:
        """Compute comprehensive dashboard KPIs, matrices, time series, and AI payload."""
        if self.df.empty:
            return {}

        total_revenue = float(self.df["Row_Revenue"].sum())
        total_quantity = int(self.df["Quantity_Sold"].sum())
        unique_transactions = int(self.df["Transaction_ID"].nunique())

        # Average Order Value (AOV) = Total Revenue / Count(Unique Transaction_ID)
        aov = (total_revenue / unique_transactions) if unique_transactions > 0 else 0.0

        # Average Selling Price (ASP)
        asp = (total_revenue / total_quantity) if total_quantity > 0 else 0.0

        # Top Regions Matrix
        regions_matrix = self._compute_regions_matrix(total_revenue)
        top_region_name = regions_matrix.iloc[0]["Geographic_Region"] if not regions_matrix.empty else "N/A"
        top_region_share = regions_matrix.iloc[0]["Revenue_Share_Pct"] if not regions_matrix.empty else 0.0

        # Monthly Trends & Seasonality Delta
        monthly_trends, seasonality_delta, peak_month_info = self._compute_seasonality()

        # Product SKU Breakdown & Top 10 Products
        sku_breakdown, top_3_skus = self._compute_sku_metrics()

        # Category Breakdown
        category_breakdown = self._compute_category_metrics(total_revenue)

        # Underperforming Segments Analysis
        underperforming_segments = self._compute_underperforming_segments(category_breakdown, regions_matrix)

        # Daily time-series for granular interactive charts
        daily_trends = (
            self.df.groupby("Date")
            .agg(
                Revenue=("Row_Revenue", "sum"),
                Units=("Quantity_Sold", "sum"),
                Orders=("Transaction_ID", "nunique"),
            )
            .reset_index()
            .sort_values("Date")
        )

        # Structured AI Insights Payload matching Module C specification
        ai_payload = {
            "total_revenue": f"${total_revenue:,.2f}",
            "aov": f"${aov:,.2f}",
            "top_performing_region": f"{top_region_name} ({top_region_share:.1f}% of total sales)",
            "seasonality_delta": seasonality_delta,
            "top_3_skus_by_revenue": top_3_skus,
            "underperforming_segments": underperforming_segments,
        }

        return {
            "total_revenue": total_revenue,
            "unique_transactions": unique_transactions,
            "total_quantity": total_quantity,
            "aov": aov,
            "asp": asp,
            "top_region_name": top_region_name,
            "top_region_share": top_region_share,
            "regions_matrix": regions_matrix,
            "monthly_trends": monthly_trends,
            "seasonality_delta": seasonality_delta,
            "peak_month_info": peak_month_info,
            "sku_breakdown": sku_breakdown,
            "top_3_skus": top_3_skus,
            "category_breakdown": category_breakdown,
            "underperforming_segments": underperforming_segments,
            "daily_trends": daily_trends,
            "ai_payload": ai_payload,
            "date_min": self.df["Timestamp"].min(),
            "date_max": self.df["Timestamp"].max(),
        }

    def _compute_regions_matrix(self, total_revenue: float) -> pd.DataFrame:
        """Group data by Geographic_Region, calculating total sales volume and total revenue yield sorted desc."""
        matrix = (
            self.df.groupby("Geographic_Region")
            .agg(
                Total_Volume=("Quantity_Sold", "sum"),
                Total_Revenue=("Row_Revenue", "sum"),
                Order_Count=("Transaction_ID", "nunique"),
            )
            .reset_index()
            .sort_values(by="Total_Revenue", ascending=False)
        )

        matrix["Revenue_Share_Pct"] = (
            (matrix["Total_Revenue"] / total_revenue * 100).round(2) if total_revenue > 0 else 0.0
        )
        matrix["AOV_Per_Region"] = (
            (matrix["Total_Revenue"] / matrix["Order_Count"]).round(2)
        )
        return matrix

    def _compute_seasonality(self) -> tuple[pd.DataFrame, str, dict]:
        """Aggregate monthly revenue and calculate MoM seasonality delta during peak month."""
        monthly = (
            self.df.groupby(["Year", "Month", "Month_Name"])
            .agg(
                Revenue=("Row_Revenue", "sum"),
                Units=("Quantity_Sold", "sum"),
                Transactions=("Transaction_ID", "nunique"),
            )
            .reset_index()
            .sort_values(by=["Year", "Month"])
        )

        monthly["MoM_Growth_Pct"] = monthly["Revenue"].pct_change() * 100

        if monthly.empty:
            return monthly, "N/A (Insufficient time range)", {}

        peak_idx = monthly["Revenue"].idxmax()
        peak_row = monthly.loc[peak_idx]
        peak_month_name = peak_row["Month_Name"]
        peak_rev = peak_row["Revenue"]

        if peak_idx > 0:
            prev_row = monthly.iloc[monthly.index.get_loc(peak_idx) - 1]
            prev_rev = prev_row["Revenue"]
            growth_pct = ((peak_rev - prev_rev) / prev_rev) * 100 if prev_rev > 0 else 0.0
            direction = "growth" if growth_pct >= 0 else "decline"
            seasonality_delta = f"{abs(growth_pct):.1f}% MoM {direction} during peak month ({peak_month_name})"
        else:
            seasonality_delta = f"Peak month is {peak_month_name} (${peak_rev:,.0f}, baseline month)"

        peak_info = {
            "month": peak_month_name,
            "revenue": peak_rev,
            "units": peak_row["Units"],
        }

        return monthly, seasonality_delta, peak_info

    def _compute_sku_metrics(self) -> tuple[pd.DataFrame, list[str]]:
        """Calculate Product SKU revenue and units sold, identifying Top 3 SKUs."""
        sku_grouped = (
            self.df.groupby(["Product_SKU", "Product_Category"])
            .agg(
                Total_Revenue=("Row_Revenue", "sum"),
                Units_Sold=("Quantity_Sold", "sum"),
                Avg_Unit_Price=("Unit_Price", "mean"),
            )
            .reset_index()
            .sort_values(by="Total_Revenue", ascending=False)
        )

        top_3 = sku_grouped.head(3)["Product_SKU"].tolist()
        return sku_grouped, top_3

    def _compute_category_metrics(self, total_revenue: float) -> pd.DataFrame:
        """Calculate category revenue share, volume, and average discount."""
        cat_grouped = (
            self.df.groupby("Product_Category")
            .agg(
                Total_Revenue=("Row_Revenue", "sum"),
                Units_Sold=("Quantity_Sold", "sum"),
                Total_Discounts=("Discount_Applied", "sum"),
                Transactions=("Transaction_ID", "nunique"),
            )
            .reset_index()
            .sort_values(by="Total_Revenue", ascending=False)
        )

        cat_grouped["Share_Pct"] = (
            (cat_grouped["Total_Revenue"] / total_revenue * 100).round(2) if total_revenue > 0 else 0.0
        )
        return cat_grouped

    def _compute_underperforming_segments(
        self,
        category_df: pd.DataFrame,
        regions_matrix: pd.DataFrame,
    ) -> list[str]:
        """Detect underperforming categories or regions based on revenue contribution and trend thresholds."""
        underperformers: list[str] = []

        # Flag lowest-yield categories (< 10% share or bottom 2)
        if not category_df.empty and len(category_df) > 1:
            low_cats = category_df[category_df["Share_Pct"] < 12.0]
            if low_cats.empty:
                low_cats = category_df.tail(1)
            for _, r in low_cats.head(2).iterrows():
                underperformers.append(
                    f"{r['Product_Category']} Category ({r['Share_Pct']:.1f}% total share, ${r['Total_Revenue']:,.0f})"
                )

        # Flag lowest-yield region
        if not regions_matrix.empty and len(regions_matrix) > 1:
            bottom_region = regions_matrix.iloc[-1]
            underperformers.append(
                f"{bottom_region['Geographic_Region']} Region ({bottom_region['Revenue_Share_Pct']:.1f}% regional share, ${bottom_region['Total_Revenue']:,.0f})"
            )

        return underperformers if underperformers else ["No severe underperforming segments detected"]
