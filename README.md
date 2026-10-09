# Syntecxhub Sales Intelligence & Executive Analytics Dashboard

![Dashboard Screenshot](assets/dashboard.png)

## 🎯 What is this?
A **single‑page, Streamlit‑powered** dashboard that transforms raw retail transaction logs into **actionable executive insights** in seconds. It combines clean data ingestion, high‑performance KPI calculations, interactive Plotly visualizations, and AI‑driven narrative generation—all wrapped in a sleek dark/light theme.

## ✨ Key Features
- **Zero‑setup data loader** – upload CSV or Excel (up to 500 MB) and let the engine normalise columns automatically.
- **Vectorised KPI engine** – total revenue, AOV, top region, monthly seasonality, SKU‑level breakdowns, and daily trends – all computed with pandas/Numpy for speed.
- **Interactive visualizations** – responsive time‑series line chart & horizontal bar chart, theme‑aware, with hover details.
- **AI executive summary** – deterministic fallback engine (no API key needed) generates **exactly 3 trend bullets** and **3 hyper‑local recommendations**; optional LLM integration for richer language.
- **One‑page PDF export** – A4, single‑page PDF that includes KPI cards, both charts, and the AI insights; ready for board‑room briefings or stakeholder emails.
- **Theme toggle** – dark & light modes with corporate colours (electric blue accent).

## 🚀 How to Run
```powershell
# Clone the repo
git clone https://github.com/your-username/Syntecxhub-Sales-Analysis.git
cd Syntecxhub_Sales_Analysis

# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run src/app.py
```

## 📊 Sample Workflow
1. **Load data** – pick a sample CSV from `data/` or upload your own.
2. **Filter** – dynamic sidebar filters for geographic region & product category.
3. **Explore KPIs** – three lightweight KPI cards on the top row.
4. **Visualise** – revenue time‑series (left) & top‑10 products bar chart (right).
5. **AI insights** – press *Generate & Download One‑Page PDF* to receive a concise executive summary and downloadable PDF.

## 🛠️ Technical Stack
- **Python 3.12**
- **Streamlit** – UI/UX framework
- **Pandas / NumPy** – data processing
- **Plotly** – interactive charts
- **FPDF** – PDF generation
- **OpenAI / Anthropic / Gemini (optional)** – LLM integration

## 🤝 Contributing
Pull requests are welcome! Please open an issue first to discuss major changes. Follow the standard GitHub flow:
```bash
git checkout -b feature/your-feature
# make changes
git commit -m "Add new feature"
git push origin feature/your-feature
# open a PR
```

## 📄 License
This project is licensed under the **MIT License** – feel free to use, adapt, and share.

---

*Built with love by Mbawe – your go‑to partner for data‑driven retail strategy.*
