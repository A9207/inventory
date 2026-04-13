import streamlit as st

st.set_page_config(page_title="Flow Calculator", page_icon="📊")

st.title("Flow Rate Calculator (m³/h)")

st.write("Enter the required values below:")

# Input fields
P = st.number_input("Enter P (float)", min_value=0.0, format="%.4f")

st.subheader("Enter V values")
V1 = st.number_input("V1", format="%.4f")
V2 = st.number_input("V2", format="%.4f")
V3 = st.number_input("V3", format="%.4f")
V4 = st.number_input("V4", format="%.4f")
V5 = st.number_input("V5", format="%.4f")

# Calculate button
if st.button("Calculate"):
    try:
        # Step 1: Average velocity
        V = (V1 + V2 + V3 + V4 + V5) / 5

        # Step 2: D calculation
        D = P / 3.142

        # Step 3: Area calculation
        A = (3.142 * D * D) / 4

        # Step 4: Flow rate
        Q = A * V * 3600

        # Output results
        st.success("Calculation Complete!")

        st.write(f"**Average V:** {V:.4f}")
        st.write(f"**D:** {D:.4f}")
        st.write(f"**A:** {A:.4f}")
        st.write(f"### Final Q: {Q:.4f} m³/h")

    except Exception as e:
        st.error(f"Error: {e}")
