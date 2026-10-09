"""Enterprise Data Ingestion and Normalization Engine.
Handles heterogeneous date formats, streaming/chunked processing for up to 500MB files,
imputation/dropping of critical keys, and automatic schema alignment.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO, Generator
import pandas as pd
import numpy as np


class DataIngestionEngine:
    """Robust file ingestion pipeline for transactional retail sales ledgers.

    Attributes:
        df: Cleaned and normalized DataFrame ready for KPI computation.
        raw_df: Original un-manipulated preview DataFrame.
        ingestion_metadata: Execution diagnostics and statistics.
    """

    CRITICAL_NUMERICS = ["Quantity_Sold", "Unit_Price"]
    STANDARD_COLUMNS = [
        "Transaction_ID",
        "Timestamp",
        "Product_SKU",
        "Product_Category",
        "Quantity_Sold",
        "Unit_Price",
        "Discount_Applied",
        "Geographic_Region",
    ]

    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.raw_df: pd.DataFrame | None = None
        self.ingestion_metadata: dict = {}
        self.column_mapping: dict[str, str] = {}

    def load_file(
        self,
        source: str | Path | BinaryIO | bytes,
        filename: str = "upload.csv",
        chunk_size: int = 50_000,
        impute_critical: bool = True,
    ) -> tuple[bool, str]:
        """Ingest CSV/XLSX file with streaming chunk support, encoding fallbacks, and schema alignment.

        Args:
            source: File path, stream, or raw bytes.
            filename: Source file name for extension inference.
            chunk_size: Row batch size for chunked memory-efficient ingestion.
            impute_critical: If True, attempts intelligent SKU-median imputation for missing critical keys before dropping.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            filename_lower = filename.lower()
            if filename_lower.endswith((".xlsx", ".xls")):
                df = self._read_excel(source)
            else:
                df = self._read_csv_optimized(source, chunk_size=chunk_size)

            if df is None or df.empty:
                return False, "Uploaded file contains no parseable data rows."

            self.raw_df = df.head(100).copy()
            clean_df, meta = self._normalize_pipeline(df, impute_critical=impute_critical)

            if clean_df.empty:
                return False, "No valid transactional records remained after data cleaning and validation."

            self.df = clean_df
            self.ingestion_metadata = meta
            return (
                True,
                f"Successfully ingested {len(clean_df):,} rows ({meta['dropped_rows']} invalid rows sanitized). "
                f"Date span: {meta.get('date_min', 'N/A')} to {meta.get('date_max', 'N/A')}.",
            )

        except Exception as e:
            return False, f"Ingestion pipeline failure: {str(e)}"

    def _read_excel(self, source: str | Path | BinaryIO | bytes) -> pd.DataFrame:
        """Read Excel workbook into DataFrame."""
        if isinstance(source, bytes):
            source = io.BytesIO(source)
        return pd.read_excel(source, engine="openpyxl")

    def _read_csv_optimized(
        self,
        source: str | Path | BinaryIO | bytes,
        chunk_size: int = 50_000,
    ) -> pd.DataFrame:
        """Stream/chunk large CSVs up to 500MB with encoding and separator auto-sniffing."""
        encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
        buffer_data: bytes | None = None

        if isinstance(source, (str, Path)):
            path = Path(source)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            # For massive files, chunk and downcast datatypes iteratively
            if file_size_mb > 20:
                return self._read_csv_in_chunks(str(path), encodings, chunk_size)
            with open(path, "rb") as f:
                buffer_data = f.read()
        elif isinstance(source, bytes):
            buffer_data = source
        elif hasattr(source, "read"):
            buffer_data = source.read()
            if hasattr(source, "seek"):
                source.seek(0)
        else:
            raise ValueError("Unsupported source format for ingestion")

        # Sniff delimiter from first 4KB
        sample = buffer_data[:4096].decode("utf-8", errors="ignore")
        sep = self._sniff_delimiter(sample)

        last_error = None
        for enc in encodings:
            try:
                bio = io.BytesIO(buffer_data)
                df = pd.read_csv(
                    bio,
                    sep=sep,
                    encoding=enc,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"Unable to parse CSV with standard encodings. Last error: {last_error}")

    def _read_csv_in_chunks(
        self,
        file_path: str,
        encodings: list[str],
        chunk_size: int,
    ) -> pd.DataFrame:
        """Iteratively parse very large files (up to 500MB) without memory spikes."""
        with open(file_path, "rb") as f:
            sample = f.read(4096).decode("utf-8", errors="ignore")
        sep = self._sniff_delimiter(sample)

        for enc in encodings:
            try:
                chunks: list[pd.DataFrame] = []
                for chunk in pd.read_csv(
                    file_path,
                    sep=sep,
                    encoding=enc,
                    chunksize=chunk_size,
                    low_memory=True,
                    on_bad_lines="skip",
                ):
                    # Downcast numeric types in chunks
                    for col in chunk.select_dtypes(include=["float64"]).columns:
                        chunk[col] = pd.to_numeric(chunk[col], downcast="float")
                    for col in chunk.select_dtypes(include=["int64"]).columns:
                        chunk[col] = pd.to_numeric(chunk[col], downcast="integer")
                    chunks.append(chunk)

                if chunks:
                    return pd.concat(chunks, ignore_index=True)
            except Exception:
                continue

        # Final fallback standard read
        return pd.read_csv(file_path, sep=sep, encoding="latin1", on_bad_lines="skip")

    @staticmethod
    def _sniff_delimiter(sample_text: str) -> str:
        """Detect dominant delimiter (, ; \t |)."""
        counts = {
            ",": sample_text.count(","),
            ";": sample_text.count(";"),
            "\t": sample_text.count("\t"),
            "|": sample_text.count("|"),
        }
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","

    def _normalize_pipeline(
        self,
        df: pd.DataFrame,
        impute_critical: bool = True,
    ) -> tuple[pd.DataFrame, dict]:
        """Normalize columns, catch heterogeneous dates, drop/impute numerical keys, and derive standard schema."""
        initial_count = len(df)
        df = df.copy()

        # Clean string whitespace in headers
        df.columns = [str(c).strip() for c in df.columns]

        # 1. Map columns to standard target schema
        mapping = self._detect_column_mapping(df)
        self.column_mapping = mapping

        # Check if legacy 3-column schema (Date, Category, Sales_Amount)
        is_legacy = "Sales_Amount" in df.columns and "Quantity_Sold" not in df.columns

        standard_df = pd.DataFrame()

        # --- Transaction_ID ---
        if mapping.get("transaction_id") and mapping["transaction_id"] in df.columns:
            standard_df["Transaction_ID"] = df[mapping["transaction_id"]].astype(str).str.strip()
        else:
            standard_df["Transaction_ID"] = [f"TXN-{100000 + i}" for i in range(len(df))]

        # --- Timestamp / Date (Heterogeneous parsing) ---
        date_src_col = mapping.get("timestamp")
        if date_src_col and date_src_col in df.columns:
            standard_df["Timestamp"] = self._parse_heterogeneous_dates(df[date_src_col])
        else:
            standard_df["Timestamp"] = pd.NaT

        # --- Product SKU & Category ---
        if mapping.get("product_sku") and mapping["product_sku"] in df.columns:
            standard_df["Product_SKU"] = df[mapping["product_sku"]].astype(str).str.strip().fillna("SKU-UNKNOWN")
        elif mapping.get("product_category") and mapping["product_category"] in df.columns:
            standard_df["Product_SKU"] = df[mapping["product_category"]].astype(str).str.strip()
        else:
            standard_df["Product_SKU"] = "STANDARD-ITEM"

        if mapping.get("product_category") and mapping["product_category"] in df.columns:
            standard_df["Product_Category"] = df[mapping["product_category"]].astype(str).str.strip()
            standard_df["Product_Category"] = standard_df["Product_Category"].replace(["nan", "None", ""], "Uncategorized")
        else:
            standard_df["Product_Category"] = "General Retail"

        # --- Geographic_Region ---
        if mapping.get("geographic_region") and mapping["geographic_region"] in df.columns:
            standard_df["Geographic_Region"] = df[mapping["geographic_region"]].astype(str).str.strip()
            standard_df["Geographic_Region"] = standard_df["Geographic_Region"].replace(["nan", "None", ""], "National")
        else:
            standard_df["Geographic_Region"] = "National"

        # --- Critical Numerics: Quantity_Sold & Unit_Price ---
        if is_legacy:
            # Adapt legacy single-amount dataset: Quantity=1, Unit_Price=Sales_Amount, Discount=0.0
            sales_val = pd.to_numeric(df["Sales_Amount"], errors="coerce")
            standard_df["Quantity_Sold"] = 1
            standard_df["Unit_Price"] = sales_val
            standard_df["Discount_Applied"] = 0.0
        else:
            qty_col = mapping.get("quantity_sold")
            price_col = mapping.get("unit_price")
            disc_col = mapping.get("discount_applied")

            standard_df["Quantity_Sold"] = pd.to_numeric(df[qty_col], errors="coerce") if qty_col and qty_col in df.columns else np.nan
            standard_df["Unit_Price"] = pd.to_numeric(df[price_col], errors="coerce") if price_col and price_col in df.columns else np.nan

            if disc_col and disc_col in df.columns:
                standard_df["Discount_Applied"] = pd.to_numeric(df[disc_col], errors="coerce").fillna(0.0)
            else:
                standard_df["Discount_Applied"] = 0.0

        # Non-critical cleaning: discounts cannot be negative
        standard_df["Discount_Applied"] = standard_df["Discount_Applied"].clip(lower=0.0)

        # 2. Imputation & Dropping of Critical Numerics
        imputed_count = 0
        if impute_critical:
            # Try to impute Unit_Price using median of the same Product_SKU or Product_Category
            price_na = standard_df["Unit_Price"].isna() | (standard_df["Unit_Price"] <= 0)
            if price_na.any():
                sku_price_median = standard_df.groupby("Product_SKU")["Unit_Price"].transform("median")
                standard_df.loc[price_na, "Unit_Price"] = sku_price_median[price_na]
                
                # Secondary fallback: category median
                cat_price_median = standard_df.groupby("Product_Category")["Unit_Price"].transform("median")
                still_na = standard_df["Unit_Price"].isna() | (standard_df["Unit_Price"] <= 0)
                standard_df.loc[still_na, "Unit_Price"] = cat_price_median[still_na]
                imputed_count += int(price_na.sum() - still_na.sum())

            # Try to impute Quantity_Sold: default to 1 if missing but Unit_Price exists
            qty_na = standard_df["Quantity_Sold"].isna() | (standard_df["Quantity_Sold"] <= 0)
            if qty_na.any():
                standard_df.loc[qty_na, "Quantity_Sold"] = 1
                imputed_count += int(qty_na.sum())

        # Drop any remaining rows missing critical keys or valid timestamp
        critical_mask = (
            standard_df["Timestamp"].notna()
            & standard_df["Quantity_Sold"].notna()
            & (standard_df["Quantity_Sold"] > 0)
            & standard_df["Unit_Price"].notna()
            & (standard_df["Unit_Price"] > 0)
        )

        valid_df = standard_df[critical_mask].copy()

        # Enforce exact dtypes
        valid_df["Quantity_Sold"] = valid_df["Quantity_Sold"].round().astype(int)
        valid_df["Unit_Price"] = valid_df["Unit_Price"].astype(float)
        valid_df["Discount_Applied"] = valid_df["Discount_Applied"].astype(float)
        valid_df["Product_SKU"] = valid_df["Product_SKU"].astype(str)
        valid_df["Product_Category"] = valid_df["Product_Category"].astype(str)
        valid_df["Geographic_Region"] = valid_df["Geographic_Region"].astype(str)
        valid_df["Transaction_ID"] = valid_df["Transaction_ID"].astype(str)

        # Sort chronologically
        valid_df = valid_df.sort_values("Timestamp").reset_index(drop=True)

        dropped_count = initial_count - len(valid_df)

        meta = {
            "initial_rows": initial_count,
            "retained_rows": len(valid_df),
            "dropped_rows": dropped_count,
            "imputed_cells": imputed_count,
            "date_min": str(valid_df["Timestamp"].min().date()) if not valid_df.empty else None,
            "date_max": str(valid_df["Timestamp"].max().date()) if not valid_df.empty else None,
            "unique_transactions": int(valid_df["Transaction_ID"].nunique()) if not valid_df.empty else 0,
            "categories": sorted(valid_df["Product_Category"].unique().tolist()) if not valid_df.empty else [],
            "regions": sorted(valid_df["Geographic_Region"].unique().tolist()) if not valid_df.empty else [],
        }

        return valid_df, meta

    @staticmethod
    def _parse_heterogeneous_dates(series: pd.Series) -> pd.Series:
        """Robust multi-format date parser handling mixed ISO, US MM/DD/YYYY, EU DD/MM/YYYY, and timestamps."""
        # Check if already datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return pd.to_datetime(series, errors="coerce")

        # First attempt: pandas mixed format parser (handles ISO, YYYY-MM-DD, MM/DD/YYYY seamlessly in pandas 2.0+)
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")

        # Check for unparsed entries and run explicit regex/strptime passes
        if parsed.isna().sum() > 0:
            unparsed_mask = parsed.isna() & series.notna()
            if unparsed_mask.any():
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m-%d-%Y", "%Y.%m.%d", "%b %d, %Y"]:
                    retry = pd.to_datetime(series[unparsed_mask], errors="coerce", format=fmt)
                    valid_fill = retry.notna()
                    if valid_fill.any():
                        parsed.loc[retry[valid_fill].index] = retry[valid_fill]
                        unparsed_mask = parsed.isna() & series.notna()
                        if not unparsed_mask.any():
                            break

        return parsed

    @staticmethod
    def _detect_column_mapping(df: pd.DataFrame) -> dict[str, str]:
        """Auto-detect columns from variable raw schemas based on fuzzy keyword scoring."""
        cols = df.columns.tolist()
        mapping: dict[str, str] = {}

        patterns = {
            "transaction_id": ["transaction_id", "transactionid", "order_id", "orderid", "invoice_id", "invoice_no", "trans_id", "receipt_id"],
            "timestamp": ["timestamp", "date", "order_date", "trans_date", "transaction_date", "invoice_date", "time", "datetime"],
            "product_sku": ["product_sku", "sku", "item_code", "product_code", "product_id", "item_id", "product_name"],
            "product_category": ["product_category", "category", "dept", "department", "segment", "item_group", "family"],
            "quantity_sold": ["quantity_sold", "quantity", "qty", "units_sold", "units", "volume", "count"],
            "unit_price": ["unit_price", "price", "unit_cost", "rate", "price_per_unit"],
            "discount_applied": ["discount_applied", "discount", "disc", "discount_amount", "markdown"],
            "geographic_region": ["geographic_region", "region", "territory", "zone", "market", "area", "country", "state", "city", "store_location"],
        }

        assigned_cols = set()

        for key, aliases in patterns.items():
            best_col = None
            best_score = -1

            for c in cols:
                if c in assigned_cols:
                    continue
                low = c.lower().replace(" ", "_").replace("-", "_")

                # Exact match
                if low in aliases:
                    score = 100 - aliases.index(low)
                # Substring match
                elif any(a in low for a in aliases):
                    score = 60
                else:
                    score = -1

                if score > best_score:
                    best_score = score
                    best_col = c

            if best_col and best_score > 0:
                mapping[key] = best_col
                assigned_cols.add(best_col)

        return mapping
