import streamlit as st
import pandas as pd
import plotly.express as px
import os

FILE = "inventory.xlsx"

# --- Page setup ---
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# Futuristic CSS
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #ffffff;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0e1117, #1a1f2b);
    padding: 15px;
    border-radius: 15px;
    backdrop-filter: blur(12px);
}
h1, h2, h3 {
    color: #00f5ff;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 DCD Maintenance Inventory Dashboard")

# --- Load inventory ---
if os.path.exists(FILE):
    df = pd.read_excel(FILE)
else:
    df = pd.DataFrame({
        "Item": ["kv N-24DR", "Blue wire", "Circuit breaker"],
        "Category": ["Keyence", "Smc", "Sanwa"],
        "Stock": [3, 2, 85],
        "Price": [1200, 25.00, 45]
    })
    df.to_csv(FILE, index=False)

# --- Ensure session state exists ---
if "inventory" not in st.session_state:
    st.session_state.inventory = df.copy()

# Ensure Price is float
st.session_state.inventory["Price"] = st.session_state.inventory["Price"].astype(float)

df = st.session_state.inventory

# --- Editable table ---
st.subheader("✏️ Manage Inventory")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Price": st.column_config.NumberColumn(
            "Price (RM)",
            format="%.2f",
            step=0.01,
            min_value=0.0
        ),
        "Stock": st.column_config.NumberColumn(
            "Stock",
            min_value=0
        )
    },
    key="inventory_editor"
)

# --- Auto-save any changes ---
if not edited_df.equals(st.session_state.inventory):
    st.session_state.inventory = edited_df
    edited_df.to_excel(FILE, index=False)
    st.success("✅ Changes saved automatically!")

# --- Calculate inventory value ---
df["Value"] = df["Stock"] * df["Price"]

# --- Sidebar filters ---
st.sidebar.title("⚙️ Filters")
category = st.sidebar.multiselect("Select Category", df["Category"], default=df["Category"])
filtered_df = df[df["Category"].isin(category)]

# --- KPIs ---
total_items = filtered_df["Stock"].sum()
total_value = filtered_df["Value"].sum()
low_stock_count = filtered_df[filtered_df["Stock"] < 5].shape[0]

col1, col2, col3 = st.columns(3)
col1.metric("📦 Total Items", total_items)
col2.metric("💰 Inventory Value", f"RM{total_value:,.2f}")
col3.metric("⚠️ Low Stock Items", low_stock_count)

# --- Charts ---
col4, col5 = st.columns(2)

with col4:
    fig1 = px.bar(
        filtered_df,
        x="Item",
        y="Stock",
        color="Category",
        title="Stock Levels",
        template="plotly_dark"
    )
    st.plotly_chart(fig1, use_container_width=True)

with col5:
    fig2 = px.pie(
        filtered_df,
        names="Category",
        values="Value",
        title="Inventory Value Distribution",
        template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)


# --- Low stock alert table ---
RESTOCK_TARGET = 5
low_stock_df = filtered_df[filtered_df["Stock"] < RESTOCK_TARGET].copy()

# Calculate only the units needed to reach target
low_stock_df["Restock Quantity"] = RESTOCK_TARGET - low_stock_df["Stock"]

# Optional: calculate total restock cost
low_stock_df["Restock Value (RM)"] = low_stock_df["Restock Quantity"] * low_stock_df["Price"]

# Show only Restock Quantity and relevant info in table
st.subheader("⚠️ Low Stock Alert")
st.dataframe(
    low_stock_df[["Item", "Category", "Restock Quantity", "Price", "Restock Value (RM)"]],
    use_container_width=True
)
    
# Show total cost for restocking all low stock items
total_restock_value = low_stock_df["Restock Value (RM)"].sum()
st.metric("💸 Total Restock Cost", f"RM{total_restock_value:,.2f}")

