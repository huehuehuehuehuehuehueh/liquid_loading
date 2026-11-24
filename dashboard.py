
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from liquid_loading_model import calculate_liquid_loading


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Liquid Loading Prediction",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Natural Gas Well Liquid Loading Predictor")

st.subheader(
    "Comparative Analysis Using Turner and Coleman Correlations"
)

st.write(
    "A Python-based tool for evaluating potential liquid loading "
    "in depleting natural gas wells."
)

st.info(
    "Enter well operating parameters in the sidebar. "
    "The dashboard will automatically calculate the results."
)


# ==========================================
# 2. FIELD DATA INPUT
# ==========================================

st.sidebar.header("Well Input Parameters")

st.sidebar.subheader("Gas Production")

gas_rate = st.sidebar.number_input(
    "Gas production rate (MMSCF/day)",
    min_value=0.001,
    value=2.0,
    step=0.1
)

st.sidebar.subheader("Flowing Conditions")

pressure = st.sidebar.number_input(
    "Flowing pressure (psia)",
    min_value=1.0,
    value=1000.0
)

temperature = st.sidebar.number_input(
    "Flowing temperature (°F)",
    min_value=-458.0,
    value=100.0
)

z_factor = st.sidebar.number_input(
    "Gas compressibility factor (Z)",
    min_value=0.01,
    value=0.90
)

st.sidebar.subheader("Gas Properties")

gas_sg = st.sidebar.number_input(
    "Gas specific gravity",
    min_value=0.01,
    value=0.65
)

st.sidebar.subheader("Liquid Properties")

liquid_density = st.sidebar.number_input(
    "Liquid density (lbm/ft³)",
    min_value=0.01,
    value=45.0
)

surface_tension = st.sidebar.number_input(
    "Surface tension (dynes/cm)",
    min_value=0.01,
    value=60.0
)

st.sidebar.subheader("Tubing Properties")

tubing_diameter = st.sidebar.number_input(
    "Tubing internal diameter (inches)",
    min_value=0.1,
    value=2.441
)

st.sidebar.subheader("Standard Conditions")

standard_pressure = st.sidebar.number_input(
    "Standard pressure (psia)",
    min_value=0.1,
    value=14.7
)

standard_temperature = st.sidebar.number_input(
    "Standard temperature (°F)",
    min_value=-458.0,
    value=60.0
)

standard_z = st.sidebar.number_input(
    "Standard Z-factor",
    min_value=0.01,
    value=1.0
)


# ==========================================
# 3. CALCULATION ENGINE
# ==========================================

if st.button("PREDICT LIQUID LOADING", type="primary"):

    try:

        result = calculate_liquid_loading(
            gas_rate=gas_rate,
            flowing_pressure=pressure,
            flowing_temperature_f=temperature,
            gas_specific_gravity=gas_sg,
            z_factor=z_factor,
            liquid_density=liquid_density,
            surface_tension=surface_tension,
            tubing_diameter=tubing_diameter,
            standard_pressure=standard_pressure,
            standard_temperature_f=standard_temperature,
            standard_z=standard_z
        )

        st.success("Prediction completed successfully!")


        # ==================================
        # 4. CALCULATED PARAMETERS
        # ==================================

        st.header("1. Calculated Well Parameters")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Gas Molecular Weight",
            f"{result['gas_molecular_weight']:.3f}",
            "lbm/lbmol"
        )

        col2.metric(
            "Gas Density",
            f"{result['gas_density']:.4f}",
            "lbm/ft³"
        )

        col3.metric(
            "Actual Gas Velocity",
            f"{result['actual_velocity']:.3f}",
            "ft/s"
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Actual Gas Flow Rate",
            f"{result['actual_gas_rate']:,.2f}",
            "ft³/day"
        )

        col2.metric(
            "Tubing Cross-sectional Area",
            f"{result['tubing_area']:.5f}",
            "ft²"
        )


        # ==================================
        # 5. CRITICAL VELOCITY COMPARISON
        # ==================================

        st.header("2. Critical Velocity Comparison")

        col1, col2 = st.columns(2)

        col1.metric(
            "Turner Critical Velocity",
            f"{result['turner_velocity']:.3f} ft/s"
        )

        col2.metric(
            "Coleman Critical Velocity",
            f"{result['coleman_velocity']:.3f} ft/s"
        )

        comparison = pd.DataFrame({
            "Parameter": [
                "Actual Gas Velocity",
                "Turner Critical Velocity",
                "Coleman Critical Velocity"
            ],

            "Velocity (ft/s)": [
                result["actual_velocity"],
                result["turner_velocity"],
                result["coleman_velocity"]
            ]
        })

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True
        )


        # ==================================
        # 6. LIQUID LOADING ASSESSMENT
        # ==================================

        st.header("3. Liquid Loading Assessment")

        if (
            result["actual_velocity"] < result["turner_velocity"]
            and result["actual_velocity"] < result["coleman_velocity"]
        ):

            st.warning(
                "Both correlations indicate potential liquid loading."
            )

        elif (
            result["actual_velocity"] >= result["turner_velocity"]
            and result["actual_velocity"] >= result["coleman_velocity"]
        ):

            st.success(
                "Actual gas velocity is above both critical thresholds."
            )

        else:

            st.warning(
                "Turner and Coleman provide different screening predictions."
            )

        st.caption(
            "This is an empirical correlation-based screening assessment, "
            "not definitive confirmation of liquid loading."
        )


        # ==================================
        # 7. VELOCITY COMPARISON GRAPH
        # ==================================

        st.header("4. Actual vs Critical Gas Velocity")

        labels = [
            "Actual Gas Velocity",
            "Turner",
            "Coleman"
        ]

        values = [
            result["actual_velocity"],
            result["turner_velocity"],
            result["coleman_velocity"]
        ]

        fig, ax = plt.subplots(figsize=(9, 5))

        ax.bar(labels, values)

        ax.set_ylabel("Velocity (ft/s)")
        ax.set_title("Comparison of Actual and Critical Velocities")

        ax.grid(axis="y", alpha=0.3)

        st.pyplot(fig)

        plt.close(fig)


        # ==================================
        # 8. DOWNLOAD RESULTS
        # ==================================

        st.header("5. Download Results")

        csv = comparison.to_csv(index=False)

        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="liquid_loading_results.csv",
            mime="text/csv"
        )


    except ValueError as error:

        st.error(f"Input error: {error}")


# ==========================================
# 9. PROJECT INFORMATION
# ==========================================

st.divider()

st.caption(
    "Natural Gas Engineering Mini Project | "
    "Python-Based Liquid Loading Prediction"
)
