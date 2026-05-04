import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="FMCG AI Forecast & Actuals", layout="wide", page_icon="🤖")

@st.cache_data
def load_raw_data():
    df = pd.read_csv('FMCG_2022_2024.csv')
    df['date'] = pd.to_datetime(df['date'])
    raw_monthly = df.groupby([pd.Grouper(key='date', freq='MS'), 'sku'])['units_sold'].sum().reset_index()
    raw_monthly.rename(columns={'date': 'Date', 'units_sold': 'Sales'}, inplace=True)
    return raw_monthly

@st.cache_data
def load_forecast_data():
    df = pd.read_csv('FMCG_SKU_Forecast_Best.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

raw_df = load_raw_data()
fcst_df = load_forecast_data()

# ==========================================
# 2. SIDEBAR & FILTER
# ==========================================
st.sidebar.header("🛠️ Filter Dashboard")

daftar_produk = raw_df['sku'].unique().tolist()
daftar_produk.sort()
pilih_produk = st.sidebar.selectbox("Select Analysis (SKU):", ["All Products (Total Sales)"] + daftar_produk)

min_date = raw_df['Date'].min().date()
max_date = raw_df['Date'].max().date()
start_date, end_date = st.sidebar.date_input(
    "Rentang Waktu", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

filt_raw = raw_df[(raw_df['Date'].dt.date >= start_date) & (raw_df['Date'].dt.date <= end_date)]
filt_fcst = fcst_df[(fcst_df['Date'].dt.date >= start_date) & (fcst_df['Date'].dt.date <= end_date)]

# ==========================================
# 3. GRAFIK (CHART) & METRIK DINAMIS
# ==========================================
st.title("📦 FMCG Sales Actuals & AI Forecasting")

if pilih_produk == "All Products (Total Sales)":
    plot_raw = filt_raw.groupby('Date')['Sales'].sum().reset_index()
    plot_fcst = filt_fcst.groupby('Date')['Forecast'].sum(min_count=1).reset_index()
    st.subheader("Overall Trend (Grand Total of All Products)")
else:
    plot_raw = filt_raw[filt_raw['sku'] == pilih_produk]
    plot_fcst = filt_fcst[filt_fcst['sku'] == pilih_produk]
    st.subheader(f"Product Sales Trends: {pilih_produk}")

col1, col2 = st.columns(2)
total_actual = plot_raw['Sales'].sum()

split_date = fcst_df['Date'].max() - pd.DateOffset(months=5)
test_fcst = plot_fcst[plot_fcst['Date'] >= split_date]
total_forecast = test_fcst['Forecast'].sum() if not test_fcst.empty else 0

col1.metric("Actual Grand Total (Real)", f"{total_actual:,.0f} Unit")
col2.metric("Total AI Prediction (Future)", f"{total_forecast:,.0f} Unit" if total_forecast > 0 else "N/A")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=plot_raw['Date'], y=plot_raw['Sales'], mode='lines+markers', name='Actual Sales', line=dict(color='#2ca02c', width=3)
))

if not plot_fcst.empty:
    fig.add_trace(go.Scatter(
        x=plot_fcst['Date'], y=plot_fcst['Forecast'], mode='lines+markers', name='AI Forecast', line=dict(color='#d62728', width=3, dash='dash')
    ))

fig.update_layout(xaxis_title="Bulan", yaxis_title="Volume Penjualan", hovermode="x unified", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. TOP 3 PRODUK FORECAST
# ==========================================
st.markdown("---")
st.subheader("🏆 Top 3 Products with the Highest Demand Potential")

valid_fcst = filt_fcst.dropna(subset=['Forecast'])

if not valid_fcst.empty:
    top_sku = valid_fcst.groupby('sku')['Forecast'].sum().reset_index()
    top_3 = top_sku.sort_values(by='Forecast', ascending=False).head(3)
    
    medali = ["🥇", "🥈", "🥉"]
    warna = ["#FFD700", "#C0C0C0", "#CD7F32"]
    
    cols = st.columns(3)
    for i, (index, row) in enumerate(top_3.iterrows()):
        cols[i].metric(label=f"{medali[i]} Rank {i+1}: {row['sku']}", value=f"{row['Forecast']:,.0f} Unit")

    fig_top = go.Figure(go.Bar(
        x=top_3['Forecast'], y=top_3['sku'], orientation='h', marker_color=warna[::-1], 
        text=top_3['Forecast'], textposition='auto', texttemplate='%{text:,.0f}'
    ))
    
    fig_top.update_layout(
        yaxis={'categoryorder':'total ascending'}, template="plotly_dark", 
        height=250, margin=dict(l=0, r=0, t=30, b=0), xaxis_visible=False
    )
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("⚠️ There is no forecasting data in the date range you selected.")

# ==========================================
# 5. VISUALISASI TAMBAHAN
# ==========================================
st.markdown("---")
st.subheader("📊 Composition Analysis & Prediction Accuracy")

col_v1, col_v2 = st.columns(2)

# Visual Kiri: Donut Chart atau Growth Chart
with col_v1:
    if pilih_produk == "All Products (Total Sales)":
        pie_data = filt_raw.groupby('sku')['Sales'].sum().reset_index()
        fig_pie = px.pie(pie_data, values='Sales', names='sku', hole=0.4, title='Actual Market Share per Product')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        # Tampilkan MoM Growth jika filter 1 produk
        growth_df = plot_raw.copy()
        growth_df = growth_df.sort_values('Date') # Pastikan urut waktu
        growth_df['Growth %'] = growth_df['Sales'].pct_change() * 100
        
        # PERBAIKAN: Buang baris pertama yang bernilai NaN agar tidak error saat diwarnai
        growth_df = growth_df.dropna(subset=['Growth %'])
        
        if not growth_df.empty:
            fig_growth = px.bar(growth_df, x='Date', y='Growth %', title=f'Monthly Growth (MoM): {pilih_produk}',
                                color='Growth %', color_continuous_scale=px.colors.diverging.RdYlGn)
            fig_growth.update_layout(template="plotly_dark")
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("⚠️ It takes at least 2 months of consecutive data to calculate the growth percentage.")

# Visual Kanan: Distribusi Error (Over vs Under Forecast)
with col_v2:
    err_df = plot_fcst.dropna(subset=['Forecast']).copy()
    
    if not err_df.empty:
        # PERBAIKAN: Jika kolom 'Sales' sudah ada, kita buang dulu agar 
        # saat di-merge tidak duplikat menjadi 'Sales_x' dan 'Sales_y'
        if 'Sales' in err_df.columns:
            err_df = err_df.drop(columns=['Sales'])
            
        # Gabungkan secara aman dengan data aktual
        err_df = pd.merge(err_df, plot_raw[['Date', 'Sales']], on='Date', how='left')
        
        # Hapus baris jika aktualnya belum ada (mencegah error NaN)
        err_df = err_df.dropna(subset=['Sales'])
        
        if not err_df.empty:
            err_df['Selisih'] = err_df['Forecast'] - err_df['Sales']
            err_df['Kategori'] = err_df['Selisih'].apply(lambda x: 'Over Forecast (Remaining Stock Risk)' if x > 0 else 'Under Forecast (Risk of Understock)')
            
            fig_err = px.bar(err_df, x='Date', y='Selisih', color='Kategori',
                             title='AI Prediction vs Actual Difference Analysis',
                             color_discrete_map={'Over Forecast (Remaining Stock Risk)': '#1f77b4', 'Under Forecast (Risk of Understock)': '#d62728'})
            fig_err.update_layout(template="plotly_dark", barmode='relative', yaxis_title="Unit Difference")
            st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.info("⚠️ There is no actual sales data during the prediction period to calculate the difference.")
    else:
        st.info("⚠️ Difference (error) data is not available in this time range.")

# ==========================================
# 6. TABEL DATA RINCIAN SKU
# ==========================================
st.markdown("---")
st.subheader("📋 Complete Details of Data per SKU")

tabel_forecast = filt_fcst.dropna(subset=['Forecast']).copy()

if pilih_produk != "All Products (Total Sales)":
    tabel_forecast = tabel_forecast[tabel_forecast['sku'] == pilih_produk]

if not tabel_forecast.empty:
    tabel_forecast['Selisih'] = (tabel_forecast['Forecast'] - tabel_forecast['Sales']).round(0)
    tabel_forecast['% Error'] = tabel_forecast.apply(
        lambda row: (abs(row['Selisih']) / row['Sales'] * 100) if row['Sales'] > 0 else 0, axis=1
    )
    tabel_forecast['% Error'] = tabel_forecast['% Error'].map("{:.2f}%".format)
    tabel_forecast['Forecast'] = tabel_forecast['Forecast'].round(0)
    
    kolom_tampil = ['Date', 'sku', 'Sales', 'Forecast', 'Selisih', '% Error']
        
    display_df = tabel_forecast[kolom_tampil].sort_values(by=['Date', 'sku'], ascending=[True, True])
    display_df['Date'] = display_df['Date'].dt.strftime('%B %Y')

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("⚠️ The time period you selected has no history/AI predictions.")