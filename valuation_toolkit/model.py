"""Five-year FCFF DCF and trailing comparable-company valuation."""

from dataclasses import dataclass
from math import isclose, isfinite
from numbers import Real

import numpy as np
import pandas as pd


class ValuationError(ValueError):
    """Missing or invalid valuation input."""


def number(value, label, minimum=None, maximum=None):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValuationError(f"Missing {label}")
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValuationError(f"{label} must be a finite number")
    value = float(value)
    if minimum is not None and value < minimum:
        raise ValuationError(f"{label} must be at least {minimum:g}")
    if maximum is not None and value > maximum:
        raise ValuationError(f"{label} must be at most {maximum:g}")
    return value


def positive(value, label):
    value = number(value, label)
    if value <= 0:
        raise ValuationError(f"{label} must be positive")
    return value


def annual_rates(value, label, minimum, maximum):
    rates = value if isinstance(value, list) else [value] * 5
    if len(rates) != 5:
        raise ValuationError(f"{label} needs one rate or five annual rates")
    return np.array([
        number(rate, f"{label} year {year}", minimum, maximum)
        for year, rate in enumerate(rates, 1)
    ])


@dataclass(frozen=True)
class Financials:
    ticker: str
    name: str
    sector: str
    currency: str
    revenue: float | None
    ebit: float | None
    ebitda: float | None
    eps: float | None
    debt: float | None
    cash: float | None
    minorities: float | None
    other_nonoperating: float | None
    shares: float | None
    margin_fy23: float | None
    margin_fy24: float | None

    @property
    def net_claims(self):
        """Claims to deduct from operating EV to reach common equity, in millions."""
        return (
            number(self.debt, f"{self.ticker} debt", 0)
            - number(self.cash, f"{self.ticker} cash", 0)
            + number(self.minorities, f"{self.ticker} minority interests", 0)
            - number(self.other_nonoperating, f"{self.ticker} other nonoperating assets")
        )


@dataclass(frozen=True)
class CapitalCost:
    cost_of_equity: float
    after_tax_cost_of_debt: float
    capm_wacc: float
    wacc: float


def capital_cost(assumptions):
    risk_free = number(assumptions.get("risk_free"), "risk-free rate", -0.1, 1)
    erp = number(assumptions.get("equity_risk_premium"), "equity risk premium", 0, 1)
    beta = number(assumptions.get("beta"), "beta", 0)
    debt_cost = number(assumptions.get("cost_of_debt"), "pre-tax cost of debt", 0, 1)
    debt_weight = number(assumptions.get("debt_weight"), "target debt weight", 0, 1)
    tax = number(assumptions.get("tax_rate"), "tax rate", 0, 1)
    cost_of_equity = risk_free + beta * erp
    after_tax_debt = debt_cost * (1 - tax)
    capm_wacc = cost_of_equity * (1 - debt_weight) + after_tax_debt * debt_weight
    wacc = positive(assumptions.get("wacc_override", capm_wacc), "WACC")
    return CapitalCost(cost_of_equity, after_tax_debt, capm_wacc, wacc)


def forecast(financials, assumptions):
    revenue0 = positive(financials.revenue, f"{financials.ticker} FY revenue")
    growth = annual_rates(assumptions.get("revenue_growth"), "revenue growth", -0.999, 5)
    margin = annual_rates(assumptions.get("ebit_margin"), "EBIT margin", -1, 1)
    tax = number(assumptions.get("tax_rate"), "tax rate", 0, 1)
    da_rate = number(assumptions.get("da_pct_sales"), "D&A / sales", 0, 1)
    capex_rate = number(assumptions.get("capex_pct_sales"), "capex / sales", 0, 1)
    nwc_rate = number(assumptions.get("nwc_pct_incremental_sales"), "NWC / incremental sales", -1, 1)
    revenue = revenue0 * np.cumprod(1 + growth)
    ebit = revenue * margin
    # Recognize no immediate cash tax benefit when EBIT is negative.
    nopat = ebit - np.maximum(ebit, 0) * tax
    da = revenue * da_rate
    capex = revenue * capex_rate
    delta_nwc = np.diff(revenue, prepend=revenue0) * nwc_rate
    return pd.DataFrame(
        dict(revenue=revenue, ebit=ebit, nopat=nopat, da=da, capex=capex,
             delta_nwc=delta_nwc, fcff=nopat + da - capex - delta_nwc),
        index=pd.Index(range(1, 6), name="year"),
    )


@dataclass(frozen=True)
class DCF:
    forecast: pd.DataFrame
    pv_forecast: float
    terminal_value: float
    pv_terminal: float
    enterprise_value: float
    net_claims: float
    equity_value: float
    per_share: float


def valid_terminal_growth(wacc, growth):
    return -1 < growth < wacc and not isclose(wacc, growth, rel_tol=0, abs_tol=1e-12)


def discount(financials, projection, wacc, terminal_growth, *, discount_years=None):
    wacc = positive(wacc, "WACC")
    growth = number(terminal_growth, "terminal growth")
    if not valid_terminal_growth(wacc, growth):
        raise ValuationError("Terminal growth must be above -100% and below WACC")
    shares = positive(financials.shares, f"{financials.ticker} shares")
    net_claims = financials.net_claims
    terminal_fcff = positive(projection["fcff"].iloc[-1], "year-five FCFF for perpetuity")
    years = projection.index.to_numpy() if discount_years is None else discount_years
    factors = (1 + wacc) ** years
    discounted = projection.assign(discount_factor=1 / factors, pv_fcff=projection["fcff"] / factors)
    pv_forecast = float(discounted["pv_fcff"].sum())
    terminal_value = terminal_fcff * (1 + growth) / (wacc - growth)
    pv_terminal = terminal_value / factors[-1]
    ev = pv_forecast + pv_terminal
    equity = ev - net_claims
    return DCF(discounted, pv_forecast, terminal_value, pv_terminal, ev, net_claims, equity, equity / shares)


def value_company(financials, assumptions):
    costs = capital_cost(assumptions)
    projection = forecast(financials, assumptions)
    return costs, discount(financials, projection, costs.wacc, assumptions.get("terminal_growth"))


def sensitivity(financials, projection, wacc, growth, wacc_step, growth_step, *, discount_years=None):
    shifts = np.arange(-2, 3)
    wacc_step = positive(wacc_step, "WACC sensitivity step")
    growth_step = positive(growth_step, "growth sensitivity step")
    rates = wacc + shifts * wacc_step
    growth_rates = growth + shifts * growth_step
    rows = [
        [discount(financials, projection, rate, g, discount_years=discount_years).per_share
         if rate > 0 and valid_terminal_growth(rate, g) else np.nan for g in growth_rates]
        for rate in rates
    ]
    return pd.DataFrame(
        rows, index=pd.Index(rates, name="WACC"), columns=pd.Index(growth_rates, name="terminal growth")
    )


def _multiple(numerator, denominator, denominator_label):
    if denominator is None:
        return np.nan, f"Missing {denominator_label}"
    if denominator <= 0:
        return np.nan, f"Nonpositive {denominator_label} ({denominator:g})"
    if numerator is None or not isfinite(numerator):
        return np.nan, "Missing valuation numerator"
    if numerator <= 0:
        return np.nan, "Nonpositive valuation numerator"
    return numerator / denominator, "Included"


def comparable_multiples(financials, prices, selections):
    rows = []
    for ticker, reason in selections.items():
        if ticker not in financials:
            raise ValuationError(f"Missing peer financials for {ticker}")
        peer = financials[ticker]
        price = prices.get(ticker)
        ev = None
        ev_issue = None
        try:
            ev = positive(price, f"{ticker} close") * positive(peer.shares, f"{ticker} shares") + peer.net_claims
        except ValuationError as exc:
            ev_issue = str(exc)
        ev_multiple, ev_flag = _multiple(ev, peer.ebitda, "FY EBITDA")
        pe_multiple, pe_flag = _multiple(price, peer.eps, "FY EPS")
        if ev_flag == "Missing valuation numerator" and ev_issue:
            ev_flag = ev_issue
        if pe_flag == "Missing valuation numerator":
            pe_flag = f"Missing {ticker} close"
        rows.append(dict(ticker=ticker, name=peer.name, rationale=reason, currency=peer.currency,
                         close=price, ebitda=peer.ebitda, eps=peer.eps,
                         ev_ebitda=ev_multiple, ev_flag=ev_flag, pe=pe_multiple, pe_flag=pe_flag))
    return pd.DataFrame(rows)


def implied_peer_values(target, multiples):
    shares = positive(target.shares, f"{target.ticker} shares")
    rows = []
    for column, label, driver in (
        ("ev_ebitda", "EV/EBITDA", target.ebitda), ("pe", "P/E", target.eps)
    ):
        valid = multiples[column].dropna()
        low = median = high = np.nan
        flag = "Included"
        if driver is None or driver <= 0:
            flag = "Target denominator missing or nonpositive"
        elif valid.empty:
            flag = "No valid peers"
        else:
            values = valid * driver
            if column == "ev_ebitda":
                values = (values - target.net_claims) / shares
            low, median, high = values.min(), values.median(), values.max()
            if len(valid) == 1:
                flag = "One peer provides a single point"
        rows.append(dict(method=label, peer_count=len(valid), low=low, median=median, high=high, status=flag))
    return pd.DataFrame(rows)
