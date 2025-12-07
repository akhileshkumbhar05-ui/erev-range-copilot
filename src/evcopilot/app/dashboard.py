from __future__ import annotations

import pandas as pd
import streamlit as st

from evcopilot.model.range_scenarios import compute_range_scenario
from evcopilot.data.fhwa_api import (
    fetch_vm1_vehicle_type_panel,
    fetch_vm1_vehicle_type_totals,
)
from evcopilot.model.erev_calculations import run_erev_analysis


# -------------------------------------------------------------------
# Tab 1 – EREV Range Explorer
# -------------------------------------------------------------------


def _tab_range_explorer() -> None:
    st.subheader("EREV Range Explorer")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        range_miles = st.slider(
            "EREV electric range (miles)",
            min_value=25,
            max_value=150,
            step=5,
            value=100,
        )

        charges_per_week = st.select_slider(
            "Number of full charges per week",
            options=[2, 3, 5, 7],
            value=5,
        )

        scenario_name = st.selectbox(
            "Scenario (grid + costs)",
            options=["Worst", "Average", "Best"],
            index=1,
        )

        annual_vmt = st.number_input(
            "Annual miles per vehicle",
            min_value=5_000,
            max_value=25_000,
            step=500,
            value=12_000,
            help="Used to turn EV share into annual EV / gasoline VMT.",
        )

    with col_right:
        st.markdown("#### Model notes")
        st.write(
            "- EV VMT share comes from a trip-distance bin model that maps "
            "range to electrified miles.\n"
            "- Charging frequency scales that base EV share up or down.\n"
            "- CO₂ and cost metrics are pulled from the same logic used in the "
            "paper’s analytical model."
        )

    # Run the scenario model
    result = compute_range_scenario(
        range_miles=range_miles,
        charges_per_week=charges_per_week,
        scenario_name=scenario_name,
        annual_vmt=annual_vmt,
    )

    st.markdown("### Results")

    m1, m2, m3 = st.columns(3)
    m1.metric("EV share of VMT", f"{result.ev_share * 100:,.1f} %")
    m2.metric("Annual EV miles", f"{result.ev_vmt:,.0f} mi")
    m3.metric("Annual gasoline miles", f"{result.gas_vmt:,.0f} mi")

    m4, m5 = st.columns(2)
    m4.metric(
        "Annual CO₂ savings vs all-gas baseline",
        f"{result.co2_savings_tons:,.2f} tCO₂/veh/yr",
    )
    if result.capex_per_ton_usd != float("inf"):
        m5.metric(
            "Battery CAPEX per ton CO₂ (lifetime)",
            f"${result.capex_per_ton_usd:,.0f} / tCO₂",
        )
    else:
        m5.metric("Battery CAPEX per ton CO₂ (lifetime)", "N/A")

    # Simple EV/Gas mileage bar chart
    st.markdown("#### Annual mileage breakdown")
    df_miles = pd.DataFrame(
        {
            "Mode": ["EV", "Gasoline"],
            "Miles": [result.ev_vmt, result.gas_vmt],
        }
    ).set_index("Mode")
    st.bar_chart(df_miles)


# -------------------------------------------------------------------
# Tab 2 – FHWA VM-1 VMT Analytics
# -------------------------------------------------------------------


from evcopilot.data.fhwa_api import fetch_vm1_ldv_total_vmt_billion_miles


def _tab_fhwa_vmt() -> None:
    st.subheader("FHWA VM-1 VMT – 2023 Summary")

    st.markdown(
        "This tab reports the **2023 light-duty vehicle VMT** used in the "
        "EREV analytical model. For this project, we align exactly with the "
        "paper, which uses the FHWA VM-1 total LDV VMT for 2023."
    )

    with st.spinner("Retrieving 2023 LDV VMT used in the model…"):
        vmt_ldv_2023_bil = fetch_vm1_ldv_total_vmt_billion_miles(2023)

    st.metric(
        "2023 LDV VMT (FHWA VM-1)",
        f"{vmt_ldv_2023_bil:,.1f} billion miles",
    )

    st.markdown(
        "This value is plugged into the EREV calculations module as "
        "`VMT_TOTAL` (in miles), and all CO₂ savings and cost metrics are "
        "scaled to match this national travel volume."
    )

# -------------------------------------------------------------------
# Tab 3 – EREV Calculations Results (paper-style analysis)
# -------------------------------------------------------------------


def _tab_erev_calculations() -> None:
    st.subheader("EREV Calculations Results")

    st.markdown(
        "These results come from the `erev_calculations` module, which "
        "implements the full analytical model from the EREV paper: "
        "installed battery capacity, electrified miles, CO₂ savings, and "
        "cost-effectiveness metrics by range and scenario."
    )

    with st.spinner("Running EREV calculations…"):
        df = run_erev_analysis(save_csv=False)

    st.markdown("#### Raw results table")
    st.dataframe(df.round(3), use_container_width=True)

    st.markdown("#### CO₂ savings vs range (by scenario)")
    co2_pivot = df.pivot(
        index="Range_mi", columns="Scenario", values="CO2_saved_Mt"
    ).sort_index()
    st.line_chart(co2_pivot)

    st.markdown("#### Battery CAPEX per ton CO₂ (by scenario)")
    cost_pivot = df.pivot(
        index="Range_mi", columns="Scenario", values="$/tCO2"
    ).sort_index()
    st.line_chart(cost_pivot)


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="EREV Copilot – Range, FHWA VMT & EREV Analysis",
        layout="wide",
    )

    st.title("EREV Copilot – Range, FHWA VMT & Analytical Results")

    tab1, tab2, tab3 = st.tabs(
        [
            "EREV Range Explorer",
            "FHWA VM-1 VMT Analytics",
            "EREV Calculations Results",
        ]
    )

    with tab1:
        _tab_range_explorer()

    with tab2:
        _tab_fhwa_vmt()

    with tab3:
        _tab_erev_calculations()


if __name__ == "__main__":
    main()
