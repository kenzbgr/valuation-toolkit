"""Legrand case using the last public quarter and a dated cash-flow stub."""

from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd

from .data import read_config
from .model import (ValuationError, capital_cost, discount, forecast, number,
                    positive, sensitivity)

TICKER = "LR.PA"


def case_inputs(path, as_of):
    snapshot = read_config(path)
    if snapshot["valuation_date"] != as_of:
        raise ValuationError("Legrand Q1 snapshot is frozen for 2026-05-29")
    if not snapshot["quarter_end"] < snapshot["results_released"] <= as_of:
        raise ValuationError("Legrand Q1 results must be public on the valuation date")
    if not snapshot["share_count_date"] < snapshot["share_count_released"] <= as_of:
        raise ValuationError("Legrand share count must be public on the valuation date")
    if not snapshot["dividend_approved"] <= snapshot["ex_dividend"] <= as_of:
        raise ValuationError("Legrand dividend must be detached by the valuation date")
    return snapshot


def value_case(company, assumptions, snapshot, as_of):
    """Estimate interim net debt and value only cash flows after the close."""
    costs = capital_cost(assumptions)
    projection = forecast(company, assumptions)
    quarter_end = snapshot["quarter_end"]
    ends = [date(as_of.year + offset, 12, 31) for offset in range(5)]
    discount_years = np.array([(end - as_of).days / 365 for end in ends])
    elapsed_days = (as_of - quarter_end).days
    remaining_fraction = (ends[0] - as_of).days / (ends[0] - quarter_end).days

    def amount(key, minimum=0):
        return number(snapshot.get(key), f"Legrand Q1 snapshot {key}", minimum)

    tax = assumptions["tax_rate"]
    q1_fcff = (amount("ebit") * (1 - tax) + amount("da") - amount("capex")
               - amount("increase_in_nwc", minimum=None))
    apr_dec_fcff = projection["fcff"].iloc[0] - q1_fcff
    elapsed_fcff = apr_dec_fcff * (1 - remaining_fraction)
    quarter_days = (quarter_end - date(as_of.year - 1, 12, 31)).days
    net_interest = amount("net_financial_expense") * elapsed_days / quarter_days * (1 - tax)
    shares = positive(snapshot.get("shares"), "Legrand April shares")
    dividend = amount("dividend_per_share") * shares
    acquisition = snapshot["post_q1_acquisitions"]
    acquired_sales = sum(number(acquisition.get(field), field, 0)
                         for field in ("keydak_revenue", "srs_revenue"))
    acquisition_reserve = acquired_sales * number(
        assumptions.get("post_q1_acquisition_sales_multiple"), "post-Q1 acquisition cost/revenue", 0
    )
    net_debt = amount("net_debt", minimum=None)
    rolled_net_debt = net_debt - elapsed_fcff + net_interest
    adjusted_net_debt = rolled_net_debt + dividend + acquisition_reserve
    bridge_company = replace(
        company, debt=max(adjusted_net_debt, 0), cash=max(-adjusted_net_debt, 0),
        minorities=amount("minorities"), shares=shares,
    )

    projection["full_fy_fcff"] = projection["fcff"]
    projection.loc[1, "fcff"] = apr_dec_fcff * remaining_fraction
    projection["cash_flow_from"] = [as_of.isoformat(), *(end.isoformat() for end in ends[:-1])]
    projection["cash_flow_to"] = [end.isoformat() for end in ends]
    projection["discount_years"] = discount_years
    result = discount(bridge_company, projection, costs.wacc, assumptions.get("terminal_growth"),
                      discount_years=discount_years)
    bridge = dict(
        valuation_date=as_of.isoformat(), reported_net_debt_q1=net_debt,
        reported_q1_sales=amount("revenue"), q1_fcff=q1_fcff, elapsed_fcff=elapsed_fcff,
        elapsed_after_tax_net_interest=net_interest, rolled_net_debt=rolled_net_debt,
        ex_dividend_claim=dividend, acquisition_funding_reserve=acquisition_reserve,
        adjusted_net_debt=adjusted_net_debt,
        minorities=bridge_company.minorities, shares=shares, net_claims=result.net_claims,
        **vars(costs), pv_forecast=result.pv_forecast, terminal_value=result.terminal_value,
        pv_terminal=result.pv_terminal, enterprise_value=result.enterprise_value,
        equity_value=result.equity_value, per_share=result.per_share,
    )
    return costs, result, bridge_company, bridge


def legrand_tables(config, snapshot, company, prices, implied, as_of):
    benchmark_assumptions = {**config["defaults"], **config["company"][TICKER]}
    case_config = config["legrand"]
    shared = {**benchmark_assumptions,
              "post_q1_acquisition_sales_multiple": case_config["post_q1_acquisition_sales_multiple"]}
    rows = []
    for scenario in ("bear", "base", "bull"):
        assumptions = {**shared, **case_config[scenario]}
        costs, result, bridge_company, bridge = value_case(company, assumptions, snapshot, as_of)
        rows.append(dict(
            scenario=scenario.title(), dcf_per_share=result.per_share, wacc=costs.wacc,
            terminal_growth=assumptions["terminal_growth"],
            fy26_growth=assumptions["revenue_growth"][0]
            if isinstance(assumptions["revenue_growth"], list) else assumptions["revenue_growth"],
            fy30_ebit_margin=assumptions["ebit_margin"][-1]
            if isinstance(assumptions["ebit_margin"], list) else assumptions["ebit_margin"],
            fy26_stub_fcff=result.forecast["fcff"].iloc[0],
        ))
        if scenario == "base":
            base = costs, result, bridge_company, bridge, assumptions
    costs, result, bridge_company, bridge, assumptions = base
    growth = assumptions["terminal_growth"]
    steps = config["sensitivity"]
    grid = sensitivity(bridge_company, result.forecast, costs.wacc, growth,
                       steps["wacc_step"], steps["growth_step"],
                       discount_years=result.forecast["discount_years"].to_numpy())
    pe_median = implied.loc[implied["method"] == "P/E", "median"].iloc[0]
    # Algebraic reverse DCF. Required undiscounted TV = FCF5 × (1+g)/(WACC−g).
    required_tv = (pe_median * bridge_company.shares + result.net_claims - result.pv_forecast)
    required_tv /= result.forecast["discount_factor"].iloc[-1]
    last_fcff = result.forecast["fcff"].iloc[-1]
    bridge.update(
        market_close=positive(prices.get(TICKER), "Legrand close"),
        pv_terminal_share_of_ev=result.pv_terminal / result.enterprise_value,
        peer_pe_median_price=pe_median,
        peer_pe_equivalent_terminal_growth=(required_tv * costs.wacc - last_fcff) / (required_tv + last_fcff),
    )
    return pd.DataFrame(rows), result.forecast.reset_index(), pd.DataFrame([bridge]), grid
