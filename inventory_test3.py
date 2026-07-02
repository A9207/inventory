import streamlit as st
import pandas as pd
import plotly.express as px
import os

FILE = "inventory.xlsx"
RESTOCK_TARGET = 5

# ---------------- Page Setup ----------------
st.set_page_config(
    page_title="Inventory Dashboard",
    layout="wide"
)

st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}

[data-testid="stAppViewContainer"]{
    background: linear-gradient(135deg,#0e1117,#1a1f2b);
}

h1,h2,h3{
    color:#00F5FF;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 DCD Maintenance Inventory Dashboard")

# ---------------- Load Data ----------------
if os.path.exists(FILE):
    df = pd.read_excel(FILE)
else:
    df = pd.DataFrame({
        "Item": ["KV N-24DR", "Blue Wire", "Circuit Breaker"],
        "Category": ["Keyence", "SMC", "Sanwa"],
        "Stock": [3, 2, 85],
        "Price": [1200.00, 25.00, 45.00]
    })
    df.to_excel(FILE, index=False)

# Ensure correct data types
df["Stock"] = df["Stock"].fillna(0).astype(int)
df["Price"] = df["Price"].fillna(0).astype(float)

# ---------------- Session State ----------------
if "inventory" not in st.session_state:
    st.session_state.inventory = df.copy()

# ---------------- Inventory Editor ----------------
st.subheader("✏️ Manage Inventory")

edited_df = st.data_editor(
    st.session_state.inventory,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    column_config={
        "Stock": st.column_config.NumberColumn(
            "Stock",
            min_value=0,
            step=1
        ),
        "Price": st.column_config.NumberColumn(
            "Price (RM)",
            min_value=0.0,
            step=0.01,
            format="RM %.2f"
        )
    },
    key="inventory_editor"
)

# ---------------- Auto Save ----------------
if not edited_df.equals(st.session_state.inventory):

    st.session_state.inventory = edited_df.copy()

    save_df = edited_df.copy()

    # Remove calculated column if exists
    if "Value" in save_df.columns:
        save_df = save_df.drop(columns=["Value"])

    save_df.to_excel(FILE, index=False)

    st.toast("✅ Inventory Saved")

# ---------------- Display Data ----------------
display_df = st.session_state.inventory.copy()

display_df["Value"] = (
    display_df["Stock"] *
    display_df["Price"]
)

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ Filters")

category = st.sidebar.multiselect(
    "Category",
    options=sorted(display_df["Category"].unique()),
    default=sorted(display_df["Category"].unique())
)

filtered_df = display_df[
    display_df["Category"].isin(category)
]

# ---------------- KPI ----------------
total_items = int(filtered_df["Stock"].sum())
total_value = filtered_df["Value"].sum()
low_stock = filtered_df[filtered_df["Stock"] < RESTOCK_TARGET].shape[0]

col1, col2, col3 = st.columns(3)

col1.metric("📦 Total Items", total_items)
col2.metric("💰 Inventory Value", f"RM {total_value:,.2f}")
col3.metric("⚠️ Low Stock Items", low_stock)

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:

    fig1 = px.bar(
        filtered_df,
        x="Item",
        y="Stock",
        color="Category",
        template="plotly_dark",
        title="Stock Levels"
    )

    st.plotly_chart(fig1, use_container_width=True)

with right:

    fig2 = px.pie(
        filtered_df,
        names="Category",
        values="Value",
        template="plotly_dark",
        title="Inventory Value Distribution"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ---------------- Low Stock ----------------
st.subheader("⚠️ Low Stock Alert")

low_stock_df = filtered_df[
    filtered_df["Stock"] < RESTOCK_TARGET
].copy()

if not low_stock_df.empty:

    low_stock_df["Restock Quantity"] = (
        RESTOCK_TARGET - low_stock_df["Stock"]
    )

    low_stock_df["Restock Value (RM)"] = (
        low_stock_df["Restock Quantity"] *
        low_stock_df["Price"]
    )

    st.dataframe(
        low_stock_df[
            [
                "Item",
                "Category",
                "Stock",
                "Restock Quantity",
                "Price",
                "Restock Value (RM)"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    total_cost = low_stock_df["Restock Value (RM)"].sum()

    st.metric(
        "💸 Total Restock Cost",
        f"RM {total_cost:,.2f}"
    )

else:

    st.success("✅ All inventory items are sufficiently stocked.")
