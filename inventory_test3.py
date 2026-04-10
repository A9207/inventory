import streamlit as st
import pandas as pd
import plotly.express as px
import os
from github import Github
import base64
from io import BytesIO

# =========================
# 🔐 GITHUB CONFIG
# =========================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "yourusername/yourrepo"   # 👈 CHANGE THIS
FILE_PATH = "inventory.xlsx"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)


# =========================
# 📥 LOAD FROM GITHUB
# =========================
def load_data():
    try:
        file = repo.get_contents(FILE_PATH)
        content = base64.b64decode(file.content)

        df = pd.read_excel(BytesIO(content))
        return df, file.sha

    except:
        df = pd.DataFrame({
            "Item": [],
            "Category": [],
            "Stock": [],
            "Price": []
        })
        return df, None


# =========================
# 💾 SAVE TO GITHUB
# =========================
def save_data(df, sha):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    content = base64.b64encode(buffer.getvalue()).decode()

    try:
        if sha:
            repo.update_file(
                FILE_PATH,
                "Update inventory",
                content,
                sha
            )
        else:
            repo.create_file(
                FILE_PATH,
                "Create inventory",
                content
            )
    except Exception as e:
        st.error(f"GitHub Save Error: {e}")


# =========================
# ⚙️ STREAMLIT SETUP
# =========================
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

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
}
h1, h2, h3 {
    color: #00f5ff;
}
</style>
""", unsafe_allow_html=True)

st.title("📦 DCD Maintenance Inventory Dashboard")


# =========================
# 📥 LOAD DATA
# =========================
df, sha = load_data()

if "inventory" not in st.session_state:
    st.session_state.inventory = df.copy()


# =========================
# 🧠 SAFE DATA CLEANING
# =========================
st.session_state.inventory["Price"] = pd.to_numeric(
    st.session_state.inventory["Price"],
    errors="coerce"
).fillna(0)

st.session_state.inventory["Stock"] = pd.to_numeric(
    st.session_state.inventory["Stock"],
    errors="coerce"
).fillna(0)


df = st.session_state.inventory.copy()


# =========================
# ✏️ EDITOR
# =========================
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


# =========================
# 💾 AUTO SAVE
# =========================
if not edited_df.equals(st.session_state.inventory):
    st.session_state.inventory = edited_df.copy()
    save_data(edited_df, sha)
    st.success("✅ Saved to GitHub!")


# =========================
# 📊 CALCULATIONS
# =========================
if not df.empty:
    df["Value"] = df["Stock"] * df["Price"]
else:
    df["Value"] = 0


# =========================
# 🔍 FILTERS
# =========================
st.sidebar.title("⚙️ Filters")

categories = df["Category"].dropna().unique()

selected_category = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

filtered_df = df[df["Category"].isin(selected_category)]


# =========================
# 📊 KPI METRICS
# =========================
total_items = filtered_df["Stock"].sum()
total_value = filtered_df["Value"].sum()
low_stock_count = filtered_df[filtered_df["Stock"] < 5].shape[0]

col1, col2, col3 = st.columns(3)

col1.metric("📦 Total Items", total_items)
col2.metric("💰 Inventory Value", f"RM{total_value:,.2f}")
col3.metric("⚠️ Low Stock Items", low_stock_count)


# =========================
# 📈 CHARTS
# =========================
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


# =========================
# ⚠️ LOW STOCK
# =========================
RESTOCK_TARGET = 5

low_stock_df = filtered_df[filtered_df["Stock"] < RESTOCK_TARGET].copy()

if not low_stock_df.empty:
    low_stock_df["Restock Quantity"] = RESTOCK_TARGET - low_stock_df["Stock"]
    low_stock_df["Restock Value (RM)"] = (
        low_stock_df["Restock Quantity"] * low_stock_df["Price"]
    )

    st.subheader("⚠️ Low Stock Alert")

    st.dataframe(
        low_stock_df[
            ["Item", "Category", "Restock Quantity", "Price", "Restock Value (RM)"]
        ],
        use_container_width=True
    )

    total_restock_value = low_stock_df["Restock Value (RM)"].sum()
    st.metric("💸 Total Restock Cost", f"RM{total_restock_value:,.2f}")
else:
    st.success("🎉 All items are sufficiently stocked!")

