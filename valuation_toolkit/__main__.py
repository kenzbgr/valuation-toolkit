"""Run the frozen valuation benchmark and peer cases."""

import argparse
from dataclasses import replace
from datetime import date
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from .data import financial_snapshot, price_snapshot, read_config, yahoo_closes
from .legrand import TICKER as LEGRAND, case_inputs, legrand_tables
from .model import (ValuationError, comparable_multiples, implied_peer_values, number, positive,
                    sensitivity, value_company)


def valuation_range(grid):
    valid = grid.to_numpy()
    return float(np.nanmin(valid)), float(np.nanmax(valid))


def benchmark_row(company, assumption, costs, result, price, source, as_of):
    shares = positive(company.shares, "shares")
    margin25 = company.ebit / company.revenue if company.ebit is not None else np.nan
    net_debt = company.debt - company.cash
    reported_value = result.per_share if result.equity_value >= 0 else np.nan
    relative_gap = (reported_value / price - 1) * 100
    return dict(
        valuation_date=as_of.isoformat(), ticker=company.ticker, name=company.name,
        sector=company.sector, currency=company.currency, market_close=price, price_source=source,
        dcf_per_share=reported_value, difference_pct=relative_gap,
        within_15_pct=abs(relative_gap) <= 15, wacc=costs.wacc,
        dcf_status="Negative equity residual" if result.equity_value < 0 else "OK",
        terminal_growth=assumption["terminal_growth"], margin_fy23=company.margin_fy23,
        margin_fy24=company.margin_fy24, margin_fy25=margin25,
        net_debt_ebitda=net_debt / company.ebitda if company.ebitda and company.ebitda > 0 else np.nan,
        net_debt_per_share=net_debt / shares, net_claims_per_share=result.net_claims / shares,
        ev_per_share=result.enterprise_value / shares,
        pv_terminal_share_of_ev=result.pv_terminal / result.enterprise_value if result.enterprise_value else np.nan,
    )


def one_at_a_time(company, assumptions, wacc, base):
    """Compare equal percentage-point shifts, with all other inputs held fixed."""
    rows = []
    for parameter, key in (
        ("WACC", "wacc_override"), ("Terminal growth", "terminal_growth"),
        ("Revenue growth in all years", "revenue_growth"), ("EBIT margin in all years", "ebit_margin"),
    ):
        original = wacc if key == "wacc_override" else assumptions[key]
        for shift in (-0.01, 0.01):
            value = [rate + shift for rate in original] if isinstance(original, list) else original + shift
            try:
                _, result = value_company(company, {**assumptions, key: value})
                rows.append((parameter, shift, result.per_share, result.per_share - base, "Included"))
            except ValuationError as exc:
                rows.append((parameter, shift, np.nan, np.nan, str(exc)))
    return pd.DataFrame(rows, columns=["assumption", "shift", "dcf_per_share", "change_per_share", "status"])


def diagnostics(company, assumptions, base):
    """Separate a margin scenario from a change to the EV-to-equity bridge."""
    rows = [("Raw base DCF equity residual", base)]
    for label, alternate in (
        ("EBIT margin -1pp in each year", -0.01), ("EBIT margin +1pp in each year", 0.01),
    ):
        margin = assumptions["ebit_margin"]
        margin = [rate + alternate for rate in margin] if isinstance(margin, list) else margin + alternate
        try:
            _, dcf = value_company(company, {**assumptions, "ebit_margin": margin})
            rows.append((label, dcf.per_share))
        except ValuationError:
            rows.append((label, np.nan))
    _, zero_net_debt = value_company(replace(company, debt=company.cash), assumptions)
    rows.append(("Zero net debt, same WACC and operating cash flows", zero_net_debt.per_share))
    if "diagnostic_industrial_net_debt" in assumptions:
        net_debt = number(assumptions["diagnostic_industrial_net_debt"], "industrial net debt")
        alternative = replace(company, debt=max(net_debt, 0), cash=max(-net_debt, 0))
        _, bridge_only = value_company(alternative, assumptions)
        rows.append(("Industrial net debt substituted into group bridge, diagnostic only",
                     bridge_only.per_share))
    return [dict(ticker=company.ticker, scenario=label, dcf_per_share=value, change_per_share=value - base)
            for label, value in rows]


def sensitivity_csv(grid):
    grid = grid.copy()
    grid.index = pd.Index([f"{rate:.6%}" for rate in grid.index], name="WACC")
    grid.columns = [f"{rate:.6%}" for rate in grid.columns]
    return grid.reset_index()


def save_tables(files, out):
    out.mkdir(parents=True, exist_ok=True)
    for filename, frame in files.items():
        frame.to_csv(out / filename, index=False, float_format="%.8f", na_rep="N/A")
    print(f"Saved {len(files)} CSV files to {out}")


def report_legrand(config, data_path, out, as_of, financials, prices):
    snapshot = case_inputs(data_path / "legrand_q1.toml", as_of)
    peers = comparable_multiples(financials, prices, config["peers"][LEGRAND])
    implied = implied_peer_values(financials[LEGRAND], peers)
    cases, forecast, bridge, grid = legrand_tables(config, snapshot, financials[LEGRAND],
                                                   prices, implied, as_of)
    files = {
        "legrand_cases.csv": cases, "legrand_forecast.csv": forecast,
        "legrand_bridge.csv": bridge, "legrand_sensitivity.csv": sensitivity_csv(grid),
        "legrand_peers.csv": peers, "legrand_peer_values.csv": implied,
    }
    print(f"Legrand | {as_of} | EUR per share | Close {bridge.at[0, 'market_close']:.2f}")
    for row in cases.itertuples(index=False):
        print(f"{row.scenario:4} DCF {row.dcf_per_share:7.2f}")
    for row in implied.itertuples(index=False):
        if pd.isna(row.median):
            print(f"FY2025 peer {row.method} N/A ({row.status})")
        else:
            print(f"FY2025 peer {row.method} {row.low:.2f}–{row.high:.2f} (median {row.median:.2f})")
    save_tables(files, out)


def run(config_path, data_path, out, use_yahoo, *, legrand=False):
    config = read_config(config_path)
    as_of = date.fromisoformat(config["run"]["valuation_date"])
    tickers = [LEGRAND] if legrand else config["run"]["benchmark"]
    if not tickers or len(set(tickers)) != len(tickers):
        raise ValuationError("Benchmark tickers must be nonempty and unique")
    peer_sets = config.get("peers", {})
    if legrand:
        peer_sets = {LEGRAND: peer_sets[LEGRAND]}
    settings = config["sensitivity"]
    financials = financial_snapshot(data_path / "financials.csv", as_of)
    all_tickers = dict.fromkeys([*tickers, *(peer for selection in peer_sets.values() for peer in selection)])
    for ticker in all_tickers:
        if ticker not in financials:
            raise ValuationError(f"Missing financial snapshot for {ticker}")
    if use_yahoo:
        prices, sources = yahoo_closes(all_tickers, as_of, financials)
    else:
        prices, sources = price_snapshot(data_path / "prices.csv", as_of, financials)
    if legrand:
        report_legrand(config, data_path, out, as_of, financials, prices)
        return

    results, rows, scenarios, ranges = {}, [], [], []
    files = {}
    for ticker in tickers:
        company = financials[ticker]
        assumptions = {**config["defaults"], **config["company"][ticker]}
        try:
            costs, result = value_company(company, assumptions)
            grid = sensitivity(company, result.forecast, costs.wacc, assumptions["terminal_growth"],
                               settings["wacc_step"], settings["growth_step"])
        except ValuationError as exc:
            raise ValuationError(f"{ticker}: {exc}") from exc
        price = positive(prices.get(ticker), f"{ticker} close")
        row = benchmark_row(company, assumptions, costs, result, price, sources[ticker], as_of)
        if pd.isna(row["dcf_per_share"]):
            grid.iloc[:, :] = np.nan
            low = high = np.nan
        else:
            low, high = valuation_range(grid)
        rows.append(row)
        scenarios.extend(diagnostics(company, assumptions, result.per_share))
        ranges.append(dict(ticker=ticker, method="DCF", low=low, base=row["dcf_per_share"], high=high))
        results[ticker] = (assumptions, costs, result)
        files[f"{ticker}_sensitivity.csv"] = sensitivity_csv(grid)

    for target, selection in peer_sets.items():
        if target not in results or target in selection or not selection:
            raise ValuationError(f"{target}: peer set needs at least one other company and a benchmark target")
        multiples = comparable_multiples(financials, prices, selection)
        implied = implied_peer_values(financials[target], multiples)
        for row in implied.itertuples(index=False):
            ranges.append(dict(ticker=target, method=row.method, low=row.low, base=row.median, high=row.high))
        files[f"{target}_peers.csv"] = multiples
        files[f"{target}_peer_values.csv"] = implied

    example = config["run"]["worked_example"]
    if example not in results:
        raise ValuationError(f"{example}: worked example must be in the benchmark")
    assumptions, costs, result = results[example]
    files[f"{example}_forecast.csv"] = result.forecast.reset_index()
    files[f"{example}_bridge.csv"] = pd.DataFrame([{
        **vars(costs), "pv_forecast": result.pv_forecast, "terminal_value": result.terminal_value,
        "pv_terminal": result.pv_terminal, "enterprise_value": result.enterprise_value,
        "debt": financials[example].debt, "cash": financials[example].cash,
        "minorities": financials[example].minorities, "other_nonoperating": financials[example].other_nonoperating,
        "equity_value": result.equity_value, "shares": financials[example].shares, "per_share": result.per_share,
    }])
    files[f"{example}_assumption_impacts.csv"] = one_at_a_time(
        financials[example], assumptions, costs.wacc, result.per_share
    )
    benchmark = pd.DataFrame(rows)
    files.update({"benchmark.csv": benchmark, "ranges.csv": pd.DataFrame(ranges),
                  "outlier_scenarios.csv": pd.DataFrame(scenarios)})
    print(f"FY2025-based benchmark | Close date {as_of} | "
          f"{int(benchmark['within_15_pct'].sum())}/{len(benchmark)} within ±15%")
    print(benchmark[["ticker", "market_close", "dcf_per_share", "difference_pct", "dcf_status"]]
          .to_string(index=False, formatters={"market_close": lambda value: f"{value:.3f}"},
                     float_format=lambda value: f"{value:.2f}", na_rep="N/A"))
    save_tables(files, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("assumptions.toml"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--legrand", action="store_true", help="Run the dated Legrand case and peer analysis")
    parser.add_argument("--yahoo-prices", action="store_true",
                        help="Fetch exact-date unadjusted closes from Yahoo instead of the saved snapshot")
    args = parser.parse_args()
    try:
        run(args.config, args.data, args.out, args.yahoo_prices, legrand=args.legrand)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Valuation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
