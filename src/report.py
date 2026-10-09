import io
import base64
import unicodedata
from fpdf import FPDF
import pandas as pd
# The recommendation generation is handled within the KPI engine or via a deterministic fallback.

NAVY = (30, 58, 95)
NAVY_LIGHT = (46, 90, 139)
SLATE = (71, 85, 105)
BORDER_COLOR = (226, 232, 240)
BG_LIGHT = (248, 250, 252)


def _b64_to_bytes(b64: str) -> io.BytesIO:
    return io.BytesIO(base64.b64decode(b64))


def clean_pdf_text(text: any) -> str:
    """Normalize and encode text for standard Helvetica font (Latin-1 compatible)."""
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "—": "-", "–": "-", "’": "'", "‘": "'",
        "“": '"', "”": '"', "•": "*", "€": "EUR", "£": "GBP",
        "→": "->", "←": "<-", "…": "...", "×": "x", "\xa0": " "
    }
    for orig, repl in replacements.items():
        s = s.replace(orig, repl)
    # Decompose accented characters and strip incompatible non-latin1 glyphs
    normalized = unicodedata.normalize("NFKD", s)
    return normalized.encode("latin-1", "ignore").decode("latin-1")


class SummaryPDF(FPDF):
    """Executive 1-Page Summary PDF Generator."""
    pass


def build_summary_pdf(path: str, kpis: dict, chart_b64s: dict, theme: str = "light") -> bytes:
    """Create a balanced, production-grade one-page A4 summary with KPIs, charts, and recommendations."""
    pdf = SummaryPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    W = 210
    H = 297
    M = 10  # 10mm margins for clean executive layout

    # 1. Header Bar
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, W, 20, "F")
    pdf.set_y(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W, 7, clean_pdf_text("SALES ANALYSIS  -  Executive Performance Summary"), align="C", new_x="LMARGIN", new_y="NEXT")

    # Subtitle with date ranges
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(203, 213, 225)
    d_min = kpis.get("date_min")
    d_max = kpis.get("date_max")
    if (
        isinstance(d_min, pd.Timestamp)
        and pd.notna(d_min)
        and isinstance(d_max, pd.Timestamp)
        and pd.notna(d_max)
    ):
        sub = f"Period: {d_min.date()} to {d_max.date()}   |   Total Orders: {kpis.get('total_orders', 0):,}   |   AOV: ${kpis.get('aov', 0):,.2f}"
    else:
        sub = f"Total Orders: {kpis.get('total_orders', 0):,}   |   AOV: ${kpis.get('aov', 0):,.2f}"
    pdf.cell(W, 4, clean_pdf_text(sub), align="C", new_x="LMARGIN", new_y="NEXT")

    # 2. KPI Cards Row
    y_kpi = 24
    card_w = (W - M * 2 - 9) / 4
    card_h = 16
    kpi_items = [
        ("TOTAL REVENUE", f"${kpis.get('total_revenue', 0):,.0f}"),
        ("AVG ORDER VALUE", f"${kpis.get('aov', 0):,.2f}"),
        ("TOP CATEGORY", str(kpis.get("top_category") or "-")),
        ("PEAK MONTH", str(kpis.get("best_month") or "-")),
    ]

    for i, (label, val) in enumerate(kpi_items):
        x = M + i * (card_w + 3)
        # Card background based on theme
        if theme == "dark":
            card_bg = SLATE  # darker card background for dark mode
            txt_color = NAVY
        else:
            card_bg = BG_LIGHT
            txt_color = NAVY
        pdf.set_fill_color(*card_bg)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.rect(x, y_kpi, card_w, card_h, "DF")
        # Label
        pdf.set_xy(x, y_kpi + 2.5)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*SLATE)
        pdf.cell(card_w, 3, clean_pdf_text(label), align="C", new_x="LMARGIN", new_y="NEXT")
        # Value
        pdf.set_xy(x, y_kpi + 6.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*txt_color)
        txt = clean_pdf_text(val)
        if len(txt) > 20:
            txt = txt[:18] + ".."
        pdf.cell(card_w, 4.5, txt, align="C", new_x="LMARGIN", new_y="NEXT")

        # Context subtext on first card
        if i == 0 and kpis.get("top_category_revenue"):
            pdf.set_xy(x, y_kpi + 11.5)
            pdf.set_font("Helvetica", "", 5.5)
            pdf.set_text_color(100, 116, 139)
            sub_txt = f"Leader: ${kpis.get('top_category_revenue', 0):,.0f}"
            pdf.cell(card_w, 3, clean_pdf_text(sub_txt), align="C", new_x="LMARGIN", new_y="NEXT")

    # 3. Charts Grid (2x2) - Scaled proportionally for full A4 coverage
    y_charts = y_kpi + card_h + 4
    chart_h = 70
    chart_w = (W - M * 2 - 4) / 2
    gap = 4
    positions = [
        (M, y_charts),
        (M + chart_w + gap, y_charts),
        (M, y_charts + chart_h + gap),
        (M + chart_w + gap, y_charts + chart_h + gap),
    ]
    chart_keys = ["trend", "category", "share", "region"]
    chart_titles = ["Monthly & Quarterly Trends", "Top Categories", "Market Share", "Regional Performance"]

    for idx, key in enumerate(chart_keys):
        x, ypos = positions[idx]
        b64 = chart_b64s.get(key)
        
        # Border container
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.rect(x, ypos, chart_w, chart_h, "DF")

        if b64:
            img_bytes = _b64_to_bytes(b64)
            try:
                pdf.image(img_bytes, x=x + 1, y=ypos + 1, w=chart_w - 2, h=chart_h - 2)
            except Exception:
                pass
        else:
            # Elegant placeholder if optional dimension (like Region) is absent
            pdf.set_xy(x, ypos + chart_h / 2 - 4)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*SLATE)
            pdf.cell(chart_w, 4, clean_pdf_text(f"{chart_titles[idx]}: Not Mapped"), align="C", new_x="LMARGIN", new_y="NEXT")

    # 4. Strategic Recommendations
    y_rec = y_charts + chart_h * 2 + gap + 4
    pdf.set_fill_color(*NAVY)
    pdf.rect(M, y_rec, W - M * 2, 6.5, "F")
    pdf.set_xy(M + 3, y_rec + 1.2)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W - M * 2 - 6, 4, clean_pdf_text("STRATEGIC ACTION RECOMMENDATIONS"), new_x="LMARGIN", new_y="NEXT")

    # Retrieve recommendations generated by AIInsightsEngine; fallback to default if unavailable
    recs = kpis.get("_recommendations") or []
    if not recs:
        recs = ["No specific recommendations available for the selected period."]

    y_text = y_rec + 8.5
    for i, r in enumerate(recs[:4], 1):
        if y_text > H - 14:
            break
        pdf.set_xy(M + 2, y_text)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*NAVY)
        pdf.cell(5, 4, f"{i}.", new_x="RIGHT", new_y="TOP")

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*NAVY)
        w_avail = W - M * 2 - 9
        pdf.set_xy(M + 7, y_text)
        pdf.multi_cell(w_avail, 3.6, clean_pdf_text(r), new_x="LMARGIN", new_y="NEXT")
        y_text = pdf.get_y() + 1.2

    # 5. Executive Footer
    pdf.set_y(H - 7)
    pdf.set_font("Helvetica", "I", 6)
    pdf.set_text_color(148, 163, 184)
    footer_text = "Generated by Syntecxhub Sales Analysis  |  A4 Executive Performance Report  |  Confidential"
    pdf.cell(W, 4, clean_pdf_text(footer_text), align="C", new_x="LMARGIN", new_y="NEXT")

    # 5. Executive Footer
    pdf.set_y(H - 7)
    pdf.set_font("Helvetica", "I", 6)
    pdf.set_text_color(148, 163, 184)
    footer_text = "Generated by Syntecxhub Sales Analysis  |  A4 Executive Performance Report  |  Confidential"
    pdf.cell(W, 4, clean_pdf_text(footer_text), align="C", new_x="LMARGIN", new_y="NEXT")

    # Output PDF to bytes (in‑memory) and also write to the requested path for debugging
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    if path:
        # Ensure the directory exists
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes

