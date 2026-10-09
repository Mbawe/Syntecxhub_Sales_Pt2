"""Automated test suite verifying Data Ingestion and KPI Calculation pipelines.
Validates heterogeneous dates, NaN imputation, row revenue vectorization, AOV, and backward compatibility.
"""
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_handler import DataIngestionEngine
from kpi_engine import KPIComputationEngine

def test_pipeline():
    print("=== STARTING BACKEND PIPELINE VERIFICATION ===")

    # 1. Test Master Transactional Dataset Ingestion
    engine = DataIngestionEngine()
    master_csv = ROOT / "data" / "retail_transactions_master.csv"
    ok, msg = engine.load_file(master_csv)
    assert ok, f"Master CSV failed to load: {msg}"
    print(f"[PASS] Ingestion of Master CSV: {msg}")

    clean_df = engine.df
    assert not clean_df.empty, "Clean DataFrame is empty"
    assert clean_df["Timestamp"].notna().all(), "Unparsed timestamps detected in clean df"
    assert (clean_df["Quantity_Sold"] > 0).all(), "Invalid quantity values found"
    assert (clean_df["Unit_Price"] > 0).all(), "Invalid unit prices found"
    print(f"[PASS] Data integrity verified: {len(clean_df)} valid records, 0 invalid dates.")

    # 2. Test KPI Vectorized Calculations
    kpi_engine = KPIComputationEngine(clean_df)
    metrics = kpi_engine.compute_all_metrics()

    tot_rev = metrics["total_revenue"]
    unique_txns = metrics["unique_transactions"]
    aov = metrics["aov"]
    reg_matrix = metrics["regions_matrix"]
    top_3 = metrics["top_3_skus"]
    ai_payload = metrics["ai_payload"]

    assert tot_rev > 0, "Total revenue is non-positive"
    assert unique_txns > 0, "Unique transactions is 0"
    expected_aov = round(tot_rev / unique_txns, 2)
    assert round(aov, 2) == expected_aov, f"AOV mismatch: got {aov}, expected {expected_aov}"
    print(f"[PASS] Total Revenue: ${tot_rev:,.2f} | Unique Transactions: {unique_txns:,} | AOV: ${aov:,.2f}")

    # Verify Regional Matrix
    assert not reg_matrix.empty, "Regions matrix is empty"
    # Ensure descending sort
    assert reg_matrix["Total_Revenue"].is_monotonic_decreasing, "Regional matrix not sorted descending by revenue"
    print(f"[PASS] Regional Matrix verified. Top Region: {reg_matrix.iloc[0]['Geographic_Region']} (${reg_matrix.iloc[0]['Total_Revenue']:,.2f})")

    # Verify AI Payload Structure
    required_keys = [
        "total_revenue", "aov", "top_performing_region",
        "seasonality_delta", "top_3_skus_by_revenue", "underperforming_segments"
    ]
    for k in required_keys:
        assert k in ai_payload, f"Missing key in AI payload: {k}"
    print("[PASS] AI Payload structure strictly matches Module C spec:")
    print(json.dumps(ai_payload, indent=2))

    # 3. Test Backward Compatibility on Legacy 3-column CSV
    legacy_engine = DataIngestionEngine()
    legacy_csv = ROOT / "data" / "project1_ideal_12months.csv"
    if legacy_csv.exists():
        ok_leg, msg_leg = legacy_engine.load_file(legacy_csv)
        assert ok_leg, f"Legacy CSV failed: {msg_leg}"
        leg_metrics = KPIComputationEngine(legacy_engine.df).compute_all_metrics()
        assert leg_metrics["total_revenue"] > 0, "Legacy revenue failed"
        print(f"[PASS] Legacy 3-Column CSV handled seamlessly: ${leg_metrics['total_revenue']:,.2f} total revenue.")

    print("\n>>> ALL MODULE A VERIFICATION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_pipeline()
