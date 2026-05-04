import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ==========================================
# 1. PAGE CONFIGURATION
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
# 2. SIDEBAR & FILTERS
# ==========================================
st.sidebar.header("🛠️ Dashboard Filters")

product_list = raw_df['sku'].unique().tolist()
product_list.sort()
selected_sku = st.sidebar.selectbox("Select Analysis (SKU):", ["All Products (Total Sales)"] + product_list)

min_date = raw_df['Date'].min().date()
max_date = raw_df['Date'].max().date()
start_date, end_date = st.sidebar.date_input(
    "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

filtered_raw = raw_df[(raw_df['Date'].dt.date >= start_date) & (raw_df['Date'].dt.date <= end_date)]
filtered_fcst = fcst_df[(fcst_df['Date'].dt.date >= start_date) & (fcst_df['Date'].dt.date <= end_date)]

# ==========================================
# 3. DYNAMIC CHARTS & METRICS
# ==========================================
st.title("📦 FMCG Sales Actuals & AI Forecasting")

if selected_sku == "All Products (Total Sales)":
    plot_raw = filtered_raw.groupby('Date')['Sales'].sum().reset_index()
    plot_fcst = filtered_fcst.groupby('Date')['Forecast'].sum(min_count=1).reset_index()
    st.subheader("Overall Trend (Grand Total All Products)")
else:
    plot_raw = filtered_raw[filtered_raw['sku'] == selected_sku]
    plot_fcst = filtered_fcst[filtered_fcst['sku'] == selected_sku]
    st.subheader(f"Sales Trend for Product: {selected_sku}")

# MAIN METRICS (3 Columns)
col1, col2, col3 = st.columns(3)

# 1. Grand Total Actual (From Start to End of Filter)
total_actual = plot_raw['Sales'].sum()

# 2. Total Actual for the Last 6 Months
split_date_actual = raw_df['Date'].max() - pd.DateOffset(months=5)
last_6m_raw = plot_raw[plot_raw['Date'] >= split_date_actual]
total_actual_6m = last_6m_raw['Sales'].sum() if not last_6m_raw.empty else 0

# 3. Total Forecast for the Last 6 Months
split_date_fcst = fcst_df['Date'].max() - pd.DateOffset(months=5)
test_fcst = plot_fcst[plot_fcst['Date'] >= split_date_fcst]
total_forecast = test_fcst['Forecast'].sum() if not test_fcst.empty else 0

col1.metric("Grand Total Actual", f"{total_actual:,.0f} Units")
col2.metric("Last 6 Months Actual", f"{total_actual_6m:,.0f} Units")
col3.metric("Last 6 Months AI Forecast", f"{total_forecast:,.0f} Units" if total_forecast > 0 else "N/A")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=plot_raw['Date'], y=plot_raw['Sales'], mode='lines+markers', name='Actual Sales', line=dict(color='#2ca02c', width=3)
))

if not plot_fcst.empty:
    fig.add_trace(go.Scatter(
        x=plot_fcst['Date'], y=plot_fcst['Forecast'], mode='lines+markers', name='AI Forecast', line=dict(color='#d62728', width=3, dash='dash')
    ))

fig.update_layout(xaxis_title="Month", yaxis_title="Sales Volume", hovermode="x unified", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. TOP 3 FORECASTED PRODUCTS
# ==========================================
st.markdown("---")
st.subheader("🏆 Top 3 Products with Highest Demand Potential")
st.markdown("*Based on total AI forecast units within the selected time range.*")

valid_fcst = filtered_fcst.dropna(subset=['Forecast'])

if not valid_fcst.empty:
    top_sku = valid_fcst.groupby('sku')['Forecast'].sum().reset_index()
    top_3 = top_sku.sort_values(by='Forecast', ascending=False).head(3)
    
    medals = ["🥇", "🥈", "🥉"]
    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
    
    cols = st.columns(3)
    for i, (index, row) in enumerate(top_3.iterrows()):
        cols[i].metric(label=f"{medals[i]} Rank {i+1}: {row['sku']}", value=f"{row['Forecast']:,.0f} Units")

    fig_top = go.Figure(go.Bar(
        x=top_3['Forecast'], y=top_3['sku'], orientation='h', marker_color=colors[::-1], 
        text=top_3['Forecast'], textposition='auto', texttemplate='%{text:,.0f}'
    ))
    
    fig_top.update_layout(
        yaxis={'categoryorder':'total ascending'}, template="plotly_dark", 
        height=250, margin=dict(l=0, r=0, t=30, b=0), xaxis_visible=False
    )
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("⚠️ No forecasting data available for the selected date range.")

# ==========================================
# 5. ADDITIONAL VISUALIZATIONS
# ==========================================
st.markdown("---")
st.subheader("📊 Composition & Prediction Accuracy Analysis")

col_v1, col_v2 = st.columns(2)

with col_v1:
    if selected_sku == "All Products (Total Sales)":
        pie_data = filtered_raw.groupby('sku')['Sales'].sum().reset_index()
        fig_pie = px.pie(pie_data, values='Sales', names='sku', hole=0.4, title='Actual Market Share per Product')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        growth_df = plot_raw.copy()
        growth_df = growth_df.sort_values('Date')
        growth_df['Growth %'] = growth_df['Sales'].pct_change() * 100
        growth_df = growth_df.dropna(subset=['Growth %'])
        
        if not growth_df.empty:
            fig_growth = px.bar(growth_df, x='Date', y='Growth %', title=f'Month-over-Month (MoM) Growth: {selected_sku}',
                                color='Growth %', color_continuous_scale=px.colors.diverging.RdYlGn)
            fig_growth.update_layout(template="plotly_dark")
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("⚠️ At least 2 consecutive months of data are required to calculate growth percentage.")

with col_v2:
    err_df = plot_fcst.dropna(subset=['Forecast']).copy()
    
    if not err_df.empty:
        if 'Sales' in err_df.columns:
            err_df = err_df.drop(columns=['Sales'])
            
        err_df = pd.merge(err_df, plot_raw[['Date', 'Sales']], on='Date', how='left')
        err_df = err_df.dropna(subset=['Sales'])
        
        if not err_df.empty:
            err_df['Variance'] = err_df['Forecast'] - err_df['Sales']
            err_df['Category'] = err_df['Variance'].apply(lambda x: 'Over Forecast (Risk of Overstock)' if x > 0 else 'Under Forecast (Risk of Stockout)')
            
            fig_err = px.bar(err_df, x='Date', y='Variance', color='Category',
                             title='AI Prediction vs Actual Sales Variance Analysis',
                             color_discrete_map={'Over Forecast (Risk of Overstock)': '#1f77b4', 'Under Forecast (Risk of Stockout)': '#d62728'})
            fig_err.update_layout(template="plotly_dark", barmode='relative', yaxis_title="Unit Variance")
            st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.info("⚠️ No actual sales data available in the forecast period to calculate variance.")
    else:
        st.info("⚠️ Variance (error) data is not available for this time range.")

# ==========================================
# 6. DETAILED SKU DATA TABLE
# ==========================================
st.markdown("---")
st.subheader("📋 Comprehensive SKU Data Details")

table_forecast = filtered_fcst.dropna(subset=['Forecast']).copy()

if selected_sku != "All Products (Total Sales)":
    table_forecast = table_forecast[table_forecast['sku'] == selected_sku]

if not table_forecast.empty:
    table_forecast['Variance'] = (table_forecast['Forecast'] - table_forecast['Sales']).round(0)
    table_forecast['% Error'] = table_forecast.apply(
        lambda row: (abs(row['Variance']) / row['Sales'] * 100) if row['Sales'] > 0 else 0, axis=1
    )
    table_forecast['% Error'] = table_forecast['% Error'].map("{:.2f}%".format)
    table_forecast['Forecast'] = table_forecast['Forecast'].round(0)
    
    display_columns = ['Date', 'sku', 'Sales', 'Forecast', 'Variance', '% Error']
        
    display_df = table_forecast[display_columns].sort_values(by=['Date', 'sku'], ascending=[True, True])
    display_df['Date'] = display_df['Date'].dt.strftime('%B %Y')

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("⚠️ The selected time period does not contain AI history/predictions.")
