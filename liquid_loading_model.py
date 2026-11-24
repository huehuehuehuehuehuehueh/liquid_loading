
import math


def calculate_liquid_loading(
    gas_rate,
    flowing_pressure,
    flowing_temperature_f,
    gas_specific_gravity,
    z_factor,
    liquid_density,
    surface_tension,
    tubing_diameter,
    standard_pressure=14.7,
    standard_temperature_f=60.0,
    standard_z=1.0
):
    """
    Liquid loading screening using Turner and Coleman correlations.

    Gas rate: MMSCF/day
    Pressure: psia
    Temperature: °F
    Density: lbm/ft3
    Surface tension: dynes/cm
    Tubing ID: inches
    Velocity: ft/s
    """

    # Convert temperatures to Rankine
    T = flowing_temperature_f + 459.67
    T_sc = standard_temperature_f + 459.67

    # Validate inputs
    if gas_rate <= 0:
        raise ValueError("Gas rate must be positive.")

    if flowing_pressure <= 0 or z_factor <= 0:
        raise ValueError("Pressure and Z-factor must be positive.")

    if gas_specific_gravity <= 0:
        raise ValueError("Gas specific gravity must be positive.")

    if liquid_density <= 0 or surface_tension <= 0:
        raise ValueError("Liquid properties must be positive.")

    if tubing_diameter <= 0:
        raise ValueError("Tubing diameter must be positive.")

    if standard_pressure <= 0 or standard_z <= 0:
        raise ValueError("Standard conditions must be positive.")

    if T <= 0 or T_sc <= 0:
        raise ValueError("Temperature must be above absolute zero.")

    # 1. Gas molecular weight
    molecular_weight = 28.967 * gas_specific_gravity

    # 2. Gas density
    R = 10.7316

    gas_density = (
        flowing_pressure * molecular_weight
        / (z_factor * R * T)
    )

    if liquid_density <= gas_density:
        raise ValueError(
            "Liquid density must exceed gas density."
        )

    # 3. Standard-to-actual gas rate conversion
    Q_sc = gas_rate * 1_000_000

    Q_actual_day = Q_sc * (
        standard_pressure / flowing_pressure
    ) * (
        z_factor * T / (standard_z * T_sc)
    )

    # 4. Tubing area
    diameter_ft = tubing_diameter / 12

    area = math.pi * diameter_ft**2 / 4

    # 5. Actual gas velocity
    Q_actual_second = Q_actual_day / 86400

    actual_velocity = Q_actual_second / area

    # 6. Turner and Coleman correlations
    critical_term = (
        surface_tension
        * (liquid_density - gas_density)
        / gas_density**2
    )**0.25

    turner_velocity = 1.92 * critical_term
    coleman_velocity = 1.593 * critical_term

    # 7. Screening results
    turner_status = (
        "Potential liquid loading"
        if actual_velocity < turner_velocity
        else "Above critical velocity"
    )

    coleman_status = (
        "Potential liquid loading"
        if actual_velocity < coleman_velocity
        else "Above critical velocity"
    )

    return {
        "gas_molecular_weight": molecular_weight,
        "gas_density": gas_density,
        "actual_gas_rate": Q_actual_day,
        "tubing_area": area,
        "actual_velocity": actual_velocity,
        "turner_velocity": turner_velocity,
        "coleman_velocity": coleman_velocity,
        "turner_status": turner_status,
        "coleman_status": coleman_status
    }
