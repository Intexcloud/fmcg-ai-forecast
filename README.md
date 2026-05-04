# 📦 FMCG Sales Actuals & AI Forecasting Dashboard

Deployment Link : https://fmcg-ai-forecast.streamlit.app/

A comprehensive data web application built with Streamlit to visualize actual sales trends and AI-driven forecasts for Fast-Moving Consumer Goods (FMCG). This dashboard provides dynamic, interactive insights into product performance, growth metrics, and forecasting accuracy.

## 🚀 Features

- **Dynamic Filtering:** Filter data by specific SKU or view the grand total of all products, with adjustable date ranges.
- **Trend Visualization:** Interactive line charts comparing real historical sales against future AI predictions.
- **Top Product Analysis:** Automated ranking of the Top 3 SKUs with the highest demand potential.
- **Composition & Growth:** 
  - Donut charts for market share distribution across SKUs.
  - Month-over-Month (MoM) growth tracking for individual products.
- **Error Distribution Analysis:** Stacked bar charts tracking the difference between AI predictions and actual sales (Over-forecast vs. Under-forecast risks).
- **Granular Data Tables:** Complete, exportable breakdown of sales, forecasts, and error percentages per SKU.

## 📂 Data Sources

This application relies on two core datasets (included in this repository):
1. `FMCG_2022_2024.csv` - Contains the historical and actual monthly sales units per SKU[cite: 1].
2. `FMCG_SKU_Forecast_Best.csv` - Contains the machine learning forecast results per SKU[cite: 1].

## 🛠️ Installation & Setup

To run this dashboard locally on your machine, follow these steps:

**1. Clone the repository:**
```bash
git clone [https://github.com/yourusername/fmcg-ai-forecast.git](https://github.com/yourusername/fmcg-ai-forecast.git)
cd fmcg-ai-forecast
```

**2. Create a virtual environment (optional but recommended):**
```bash
python -m venv venv
env\\Scripts\\activate  # Windows
source env/bin/activate # Linux/Mac
```

**3. Install the required dependencies:**
```bash
pip install -r requirements.txt
```

**4. Run the Streamlit app:**
```bash
streamlit run app.py
```



