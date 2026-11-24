
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from liquid_loading_model import calculate_liquid_loading


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Gas Well Liquid Loading Predictor",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Natural Gas Well Liquid Loading Predictor")

st.subheader(
    "Comparative Prediction Using Turner and Coleman Correlations"
)

st.write(
    "A Python-based tool for evaluating potential liquid loading "
    "under changing natural gas production conditions."
)

st.info(
    "Use illustrative assumptions for initial testing. "
    "Replace them with field measurements when available."
)


# ==================================================
# 2. COMMON WELL INPUTS
# ==================================================

st.sidebar.header("Well and Fluid Properties")

gas_sg = st.sidebar.number_input(
    "Gas specific gravity",
    min_value=0.01,
    value=0.65,
    step=0.01
)

temperature = st.sidebar.number_input(
    "Flowing temperature (°F)",
    min_value=-458.0,
    value=100.0
)

z_factor = st.sidebar.number_input(
    "Gas compressibility factor",
    min_value=0.01,
    value=0.90,
    step=0.01
)

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

tubing_diameter = st.sidebar.number_input(
    "Tubing internal diameter (inches)",
    min_value=0.1,
    value=2.441
)

st.sidebar.subheader("Standard Gas Conditions")

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


# ==================================================
# 3. COMMON CALCULATION FUNCTION
# ==================================================

def calculate_row(rate, pressure, temp, z):

    return calculate_liquid_loading(
        gas_rate=float(rate),
        flowing_pressure=float(pressure),
        flowing_temperature_f=float(temp),
        gas_specific_gravity=gas_sg,
        z_factor=float(z),
        liquid_density=liquid_density,
        surface_tension=surface_tension,
        tubing_diameter=tubing_diameter,
        standard_pressure=standard_pressure,
        standard_temperature_f=standard_temperature,
        standard_z=standard_z
    )


def add_predictions(data):

    records = []

    for _, row in data.iterrows():

        result = calculate_row(
            row["Gas Rate (MMSCF/day)"],
            row["Flowing Pressure (psia)"],
            row["Temperature (°F)"],
            row["Z-factor"]
        )

        records.append(result)

    calculated = pd.DataFrame(records, index=data.index)

    return pd.concat(
        [data.reset_index(drop=True),
         calculated.reset_index(drop=True)],
        axis=1
    )


def first_crossing(data, actual_col, critical_col):

    crossed = data[
        data[actual_col] < data[critical_col]
    ]

    if crossed.empty:
        return None

    return crossed.iloc[0]["Time (days)"]


def display_analysis(data):

    # Sort observations in chronological order
    data = data.sort_values("Time (days)").reset_index(drop=True)

    # Calculate results
    results = add_predictions(data)

    st.success("Analysis completed successfully!")

    # ----------------------------------------------
    # RESULTS SUMMARY
    # ----------------------------------------------

    st.header("1. Calculated Parameters")

    latest = results.iloc[-1]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Latest Gas Density",
        f"{latest['gas_density']:.4f} lbm/ft³"
    )

    col2.metric(
        "Latest Actual Velocity",
        f"{latest['actual_velocity']:.3f} ft/s"
    )

    col3.metric(
        "Latest Gas Rate",
        f"{latest['Gas Rate (MMSCF/day)']:.3f} MMSCF/day"
    )

    # ----------------------------------------------
    # VELOCITY GRAPH
    # ----------------------------------------------

    st.header("2. Actual vs Critical Gas Velocity")

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        results["Time (days)"],
        results["actual_velocity"],
        marker="o",
        label="Actual gas velocity"
    )

    ax.plot(
        results["Time (days)"],
        results["turner_velocity"],
        linestyle="--",
        label="Turner critical velocity"
    )

    ax.plot(
        results["Time (days)"],
        results["coleman_velocity"],
        linestyle="--",
        label="Coleman critical velocity"
    )

    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Velocity (ft/s)")
    ax.set_title("Liquid Loading Screening During Production")

    ax.legend()
    ax.grid(alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    # ----------------------------------------------
    # GAS RATE GRAPH
    # ----------------------------------------------

    st.header("3. Gas Production Trend")

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        results["Time (days)"],
        results["Gas Rate (MMSCF/day)"],
        marker="o"
    )

    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Gas production (MMSCF/day)")
    ax.set_title("Gas Production Profile")

    ax.grid(alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    # ----------------------------------------------
    # PRESSURE GRAPH
    # ----------------------------------------------

    st.header("4. Flowing Pressure Trend")

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        results["Time (days)"],
        results["Flowing Pressure (psia)"],
        marker="o"
    )

    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Flowing pressure (psia)")
    ax.set_title("Flowing Pressure Profile")

    ax.grid(alpha=0.3)

    st.pyplot(fig)
    plt.close(fig)

    # ----------------------------------------------
    # THRESHOLD CROSSINGS
    # ----------------------------------------------

    st.header("5. Predicted Threshold Crossings")

    turner_day = first_crossing(
        results,
        "actual_velocity",
        "turner_velocity"
    )

    coleman_day = first_crossing(
        results,
        "actual_velocity",
        "coleman_velocity"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Turner")

        if turner_day is None:
            st.success("No threshold crossing observed.")
        else:
            st.warning(
                f"Potential loading first indicated near "
                f"day {turner_day:.1f}."
            )

    with col2:

        st.subheader("Coleman")

        if coleman_day is None:
            st.success("No threshold crossing observed.")
        else:
            st.warning(
                f"Potential loading first indicated near "
                f"day {coleman_day:.1f}."
            )

    # ----------------------------------------------
    # DETAILED RESULTS
    # ----------------------------------------------

    st.header("6. Complete Simulation Results")

    st.dataframe(
        results.round(4),
        use_container_width=True,
        hide_index=True
    )

    # ----------------------------------------------
    # DOWNLOAD
    # ----------------------------------------------

    st.header("7. Export Results")

    csv = results.to_csv(index=False)

    st.download_button(
        "Download Analysis Results",
        data=csv,
        file_name="liquid_loading_analysis.csv",
        mime="text/csv"
    )

    return results


# ==================================================
# 4. SELECT ANALYSIS MODE
# ==================================================

mode = st.radio(
    "Select Analysis Mode",
    [
        "Single Well Assessment",
        "Decline Curve Simulation",
        "Historical Field Data Upload"
    ],
    horizontal=True
)


# ==================================================
# 5. SINGLE WELL ASSESSMENT
# ==================================================

if mode == "Single Well Assessment":

    st.header("Single Well Operating Conditions")

    col1, col2 = st.columns(2)

    with col1:

        rate = st.number_input(
            "Gas production rate (MMSCF/day)",
            min_value=0.001,
            value=2.0
        )

        pressure = st.number_input(
            "Flowing pressure (psia)",
            min_value=1.0,
            value=1000.0
        )

    with col2:

        st.write("The other properties are entered in the sidebar.")

    if st.button("PREDICT LIQUID LOADING", type="primary"):

        try:

            result = calculate_row(
                rate,
                pressure,
                temperature,
                z_factor
            )

            st.success("Calculation completed!")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Gas Density",
                f"{result['gas_density']:.4f} lbm/ft³"
            )

            col2.metric(
                "Actual Velocity",
                f"{result['actual_velocity']:.3f} ft/s"
            )

            col3.metric(
                "Turner Critical Velocity",
                f"{result['turner_velocity']:.3f} ft/s"
            )

            st.metric(
                "Coleman Critical Velocity",
                f"{result['coleman_velocity']:.3f} ft/s"
            )

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
                    "Actual velocity is above both critical thresholds."
                )

            else:

                st.warning(
                    "The two correlations provide different screening results."
                )

        except ValueError as error:

            st.error(str(error))


# ==================================================
# 6. DECLINE CURVE SIMULATION
# ==================================================

elif mode == "Decline Curve Simulation":

    st.header("Gas Production Decline Simulation")

    st.write(
        "Compare exponential and hyperbolic production decline "
        "under a separately specified flowing-pressure profile."
    )

    col1, col2 = st.columns(2)

    with col1:

        initial_rate = st.number_input(
            "Initial gas rate (MMSCF/day)",
            min_value=0.001,
            value=2.0
        )

        initial_pressure = st.number_input(
            "Initial flowing pressure (psia)",
            min_value=1.0,
            value=1000.0
        )

        duration = st.number_input(
            "Simulation duration (days)",
            min_value=30,
            max_value=3000,
            value=365
        )

        decline_rate = st.number_input(
            "Initial nominal gas decline rate (% per year)",
            min_value=0.1,
            max_value=99.0,
            value=30.0
        )

    with col2:

        decline_type = st.selectbox(
            "Production decline model",
            ["Exponential", "Hyperbolic"]
        )

        hyperbolic_b = st.number_input(
            "Hyperbolic b-factor",
            min_value=0.01,
            max_value=1.5,
            value=0.5,
            step=0.1,
            disabled=(decline_type == "Exponential")
        )

        final_pressure = st.number_input(
            "Final assumed flowing pressure (psia)",
            min_value=1.0,
            value=600.0
        )

        pressure_decline = st.number_input(
            "Assumed pressure decline rate (% per year)",
            min_value=0.1,
            max_value=99.0,
            value=20.0
        )

    st.caption(
        "Pressure is independently assumed to follow an exponential "
        "profile. It is not derived from the gas production decline equation."
    )

    if st.button("RUN DECLINE SIMULATION", type="primary"):

        if final_pressure > initial_pressure:

            st.error(
                "Final pressure must not exceed initial pressure "
                "for this depletion scenario."
            )

        else:

            time = np.linspace(0, duration, 50)

            # Convert annual nominal decline rate to per-year fraction
            D = decline_rate / 100
            Dp = pressure_decline / 100

            # Gas production decline
            if decline_type == "Exponential":

                gas_rates = initial_rate * np.exp(
                    -D * time / 365
                )

            else:

                gas_rates = initial_rate / (
                    1 + hyperbolic_b * D * time / 365
                ) ** (1 / hyperbolic_b)

            # Independently assumed exponential pressure profile
            if initial_pressure == final_pressure:

                pressures = np.full(
                    len(time),
                    initial_pressure
                )

            else:

                # Choose the pressure decline constant so the
                # final value matches the selected final pressure.
                Dp = (
                    -np.log(final_pressure / initial_pressure)
                    * 365 / duration
                )

                pressures = initial_pressure * np.exp(
                    -Dp * time / 365
                )

            data = pd.DataFrame({
                "Time (days)": time,
                "Gas Rate (MMSCF/day)": gas_rates,
                "Flowing Pressure (psia)": pressures,
                "Temperature (°F)": temperature,
                "Z-factor": z_factor
            })

            st.write(
                f"Production model: **{decline_type} decline**"
            )

            st.write(
                f"Pressure model: **Assumed exponential pressure profile**"
            )

            st.write(
                f"Gas production at end of simulation: "
                f"**{gas_rates[-1]:.3f} MMSCF/day**"
            )

            display_analysis(data)


# ==================================================
# 7. HISTORICAL FIELD DATA UPLOAD
# ==================================================

elif mode == "Historical Field Data Upload":

    st.header("Historical Production Data Analysis")

    st.write(
        "Upload a CSV containing historical gas production "
        "and, where available, measured flowing pressure."
    )

    st.markdown(
        """
        **Required CSV columns:**
        - `time_days`
        - `gas_rate_mmscfd`

        **Optional columns:**
        - `flowing_pressure_psia`
        - `temperature_f`
        - `z_factor`
        """
    )

    st.download_button(
        "Download CSV Template",
        data=pd.DataFrame({
            "time_days": [0, 30, 60, 90],
            "gas_rate_mmscfd": [2.0, 1.8, 1.5, 1.2],
            "flowing_pressure_psia": [1000, 950, 850, 750],
            "temperature_f": [100, 100, 100, 100],
            "z_factor": [0.90, 0.90, 0.90, 0.90]
        }).to_csv(index=False),
        file_name="field_data_template.csv",
        mime="text/csv"
    )

    uploaded_file = st.file_uploader(
        "Upload historical field data",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:

            raw = pd.read_csv(uploaded_file)

            raw.columns = raw.columns.str.strip().str.lower()

            required_columns = [
                "time_days",
                "gas_rate_mmscfd"
            ]

            missing = [
                column for column in required_columns
                if column not in raw.columns
            ]

            if missing:

                st.error(
                    "Missing required columns: "
                    + ", ".join(missing)
                )

            else:

                # Convert optional columns to numeric values
                for column in [
                    "time_days",
                    "gas_rate_mmscfd",
                    "flowing_pressure_psia",
                    "temperature_f",
                    "z_factor"
                ]:

                    if column in raw.columns:

                        raw[column] = pd.to_numeric(
                            raw[column],
                            errors="coerce"
                        )

                if raw[required_columns].isna().any().any():

                    st.error(
                        "Required columns contain missing or "
                        "non-numeric values."
                    )

                elif (
                    raw["time_days"].lt(0).any()
                    or raw["gas_rate_mmscfd"].le(0).any()
                ):

                    st.error(
                        "Time must be non-negative and gas rate "
                        "must be positive."
                    )

                else:

                    raw = raw.sort_values(
                        "time_days"
                    ).reset_index(drop=True)

                    st.subheader("Uploaded Data Preview")

                    st.dataframe(
                        raw,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Pressure handling
                    if "flowing_pressure_psia" in raw.columns:

                        if raw["flowing_pressure_psia"].notna().all():

                            st.success(
                                "Measured flowing pressure found. "
                                "Using uploaded pressure observations."
                            )

                            pressures = raw[
                                "flowing_pressure_psia"
                            ].to_numpy()

                        else:

                            st.warning(
                                "Some pressure measurements are missing. "
                                "Use the assumed profile for all observations "
                                "to avoid mixing measured and assumed values."
                            )

                            use_measured = st.checkbox(
                                "Use measured pressure only if every row "
                                "contains a valid measurement",
                                value=False
                            )

                            if use_measured:

                                pressures = raw[
                                    "flowing_pressure_psia"
                                ].to_numpy()

                            else:

                                pressures = None

                    else:

                        st.info(
                            "No pressure column found. "
                            "An assumed pressure profile will be required."
                        )

                        pressures = None

                    # If pressure is missing or incomplete
                    if pressures is None:

                        st.subheader(
                            "Assumed Pressure Profile"
                        )

                        start_p = st.number_input(
                            "Initial assumed flowing pressure (psia)",
                            min_value=1.0,
                            value=1000.0,
                            key="csv_initial_pressure"
                        )

                        end_p = st.number_input(
                            "Final assumed flowing pressure (psia)",
                            min_value=1.0,
                            value=600.0,
                            key="csv_final_pressure"
                        )

                        if end_p > start_p:

                            st.error(
                                "Final assumed pressure must not "
                                "exceed initial pressure."
                            )

                            pressures = None

                        else:

                            pressure_decline_pct = st.number_input(
                                "Assumed pressure decline (% per year)",
                                min_value=0.1,
                                max_value=99.0,
                                value=20.0,
                                key="csv_pressure_decline"
                            )

                            t = raw["time_days"].to_numpy()

                            elapsed = t[-1] - t[0]

                            if elapsed == 0:

                                pressures = np.full(
                                    len(t),
                                    start_p
                                )

                            elif start_p == end_p:

                                pressures = np.full(
                                    len(t),
                                    start_p
                                )

                            else:

                                # Fit exponential pressure profile
                                # to initial and final assumed values.
                                k = (
                                    np.log(start_p / end_p)
                                    / elapsed
                                )

                                pressures = start_p * np.exp(
                                    -k * (t - t[0])
                                )

                    # Continue only when pressure is available
                    if pressures is not None:

                        if (
                            not np.isfinite(pressures).all()
                            or (pressures <= 0).any()
                        ):

                            st.error(
                                "Pressure values must be positive "
                                "and numeric."
                            )

                        else:

                            raw["Flowing Pressure (psia)"] = pressures

                            # Temperature and Z-factor columns
                            if "temperature_f" in raw.columns:

                                if raw["temperature_f"].isna().any():

                                    st.error(
                                        "Temperature column has missing values."
                                    )

                                    raw = None

                                else:

                                    raw["Temperature (°F)"] = (
                                        raw["temperature_f"]
                                    )

                            else:

                                raw["Temperature (°F)"] = temperature

                            if raw is not None:

                                if "z_factor" in raw.columns:

                                    if raw["z_factor"].isna().any():

                                        st.error(
                                            "Z-factor column has missing values."
                                        )

                                        raw = None

                                    else:

                                        raw["Z-factor"] = raw["z_factor"]

                                else:

                                    raw["Z-factor"] = z_factor

                            if raw is not None:

                                # Check valid operating conditions
                                if (
                                    raw["Temperature (°F)"].le(-459.67).any()
                                    or raw["Z-factor"].le(0).any()
                                ):

                                    st.error(
                                        "Temperature or Z-factor values "
                                        "are outside valid limits."
                                    )

                                else:

                                    st.success(
                                        "Field data prepared for analysis."
                                    )

                                    analysis_data = raw[[
                                        "time_days",
                                        "gas_rate_mmscfd",
                                        "Flowing Pressure (psia)",
                                        "Temperature (°F)",
                                        "Z-factor"
                                    ]].copy()

                                    analysis_data.columns = [
                                        "Time (days)",
                                        "Gas Rate (MMSCF/day)",
                                        "Flowing Pressure (psia)",
                                        "Temperature (°F)",
                                        "Z-factor"
                                    ]

                                    display_analysis(
                                        analysis_data
                                    )

        except Exception as error:

            st.error(
                f"Unable to process uploaded data: {error}"
            )


# ==================================================
# 8. FOOTER
# ==================================================

st.divider()

st.caption(
    "Natural Gas Engineering Mini Project | "
    "Turner and Coleman Correlation-Based Screening"
)
