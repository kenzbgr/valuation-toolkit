import csv
from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from valuation_toolkit.__main__ import run
from valuation_toolkit.data import financial_snapshot, read_config, yahoo_closes
from valuation_toolkit.legrand import case_inputs, value_case
from valuation_toolkit.model import (ValuationError, comparable_multiples, discount, sensitivity,
                                     value_company)


ROOT = Path(__file__).resolve().parents[1]
DATE = date(2026, 5, 29)


class ValuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.companies = financial_snapshot(ROOT / "data/financials.csv", DATE)
        cls.legrand = cls.companies["LR.PA"]
        cls.config = read_config(ROOT / "assumptions.toml")
        cls.assumptions = {**cls.config["defaults"], **cls.config["company"]["LR.PA"]}

    def test_reconciles_independent_legrand_calculation(self):
        cost, dcf = value_company(self.legrand, self.assumptions)
        for actual, expected in (
            (cost.cost_of_equity, 0.085),
            (cost.wacc, 0.076973875),
            (dcf.forecast.loc[1, "fcff"], 1335.459523436),
            (dcf.pv_forecast, 5948.029813821),
            (dcf.terminal_value, 29135.195097075),
            (dcf.pv_terminal, 20109.074753756),
            (dcf.enterprise_value, 26057.104567577),
            (dcf.equity_value, 21794.704567577),
            (dcf.per_share, 83.302500037),
        ):
            self.assertAlmostEqual(actual, expected, delta=0.0001)

    def test_rejects_terminal_growth_at_or_above_wacc(self):
        for growth in (0.07, 0.08):
            with self.subTest(growth=growth), self.assertRaisesRegex(
                ValuationError, "below WACC"
            ):
                value_company(self.legrand, {**self.assumptions, "wacc_override": 0.07,
                                             "terminal_growth": growth})

    def test_missing_revenue_and_shares_are_flagged(self):
        for field in ("revenue", "shares"):
            with self.subTest(field=field), self.assertRaisesRegex(
                ValuationError, f"Missing LR.PA .*{field}"
            ):
                value_company(replace(self.legrand, **{field: None}), self.assumptions)

    def test_sensitivity_flags_invalid_cells_and_preserves_center(self):
        assumptions = {**self.assumptions, "wacc_override": 0.07, "terminal_growth": 0.065}
        cost, dcf = value_company(self.legrand, assumptions)
        grid = sensitivity(self.legrand, dcf.forecast, cost.wacc, 0.065, 0.005, 0.005)
        self.assertEqual(grid.shape, (5, 5))
        self.assertAlmostEqual(grid.iloc[2, 2], dcf.per_share)
        self.assertTrue(pd.isna(grid.iloc[0, -1]))
        self.assertTrue(pd.isna(grid.iloc[2, 3]))
        self.assertGreater(grid.iloc[2, 2], grid.iloc[2, 1])

    def test_comps_exclude_negative_or_missing_denominators(self):
        peers = comparable_multiples(
            self.companies, {"STLAP.PA": 6.857}, {"STLAP.PA": "Autos"}
        )
        self.assertTrue(pd.isna(peers.at[0, "ev_ebitda"]))
        self.assertTrue(pd.isna(peers.at[0, "pe"]))
        self.assertIn("Nonpositive FY EBITDA", peers.at[0, "ev_flag"])
        self.assertIn("Nonpositive FY EPS", peers.at[0, "pe_flag"])
        peer = replace(self.companies["SU.PA"], eps=None)
        missing = comparable_multiples({"SU.PA": peer}, {"SU.PA": 269.95}, {"SU.PA": "Electrical"})
        self.assertEqual(missing.at[0, "pe_flag"], "Missing FY EPS")
        self.assertGreater(missing.at[0, "ev_ebitda"], 0)

    def test_yahoo_uses_exact_date_and_unadjusted_close(self):
        security = Mock()
        security.history_metadata = {"currency": "EUR"}
        security.history.return_value = pd.DataFrame(
            {"Close": [147.65], "Adj Close": [145.27]},
            index=pd.DatetimeIndex(["2026-05-29"], tz="Europe/Paris"),
        )
        with patch.dict("sys.modules", {"yfinance": SimpleNamespace(Ticker=Mock(return_value=security))}):
            prices, _ = yahoo_closes(["LR.PA"], DATE, self.companies)
            self.assertEqual(prices["LR.PA"], 147.65)
            self.assertEqual(security.history.call_args.kwargs["start"], "2026-05-29")
            self.assertEqual(security.history.call_args.kwargs["end"], "2026-05-30")
            self.assertFalse(security.history.call_args.kwargs["auto_adjust"])
            security.history_metadata = {"currency": "USD"}
            with self.assertRaisesRegex(ValuationError, "differs from financial statements"):
                yahoo_closes(["LR.PA"], DATE, self.companies)

    def test_offline_benchmark_has_all_eight_rows(self):
        with TemporaryDirectory() as directory, patch("builtins.print"):
            out = Path(directory)
            run(ROOT / "assumptions.toml", ROOT / "data", out, False)
            with (out / "benchmark.csv").open(newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 8)
            self.assertEqual(sum(row["within_15_pct"] == "True" for row in rows), 1)
            self.assertEqual({row["valuation_date"] for row in rows}, {"2026-05-29"})
            self.assertEqual(rows[2]["dcf_status"], "Negative equity residual")
            self.assertEqual(rows[2]["dcf_per_share"], "N/A")
            self.assertEqual(rows[2]["difference_pct"], "N/A")
            with (out / "ranges.csv").open(newline="") as file:
                renault = next(row for row in csv.DictReader(file) if row["ticker"] == "RNO.PA")
            self.assertEqual([renault[key] for key in ("low", "base", "high")], ["N/A"] * 3)
            with (out / "outlier_scenarios.csv").open(newline="") as file:
                raw = next(row for row in csv.DictReader(file)
                           if row["ticker"] == "RNO.PA" and row["scenario"] == "Raw base DCF equity residual")
            self.assertAlmostEqual(float(raw["dcf_per_share"]), -72, places=2)
            self.assertTrue((out / "LR.PA_sensitivity.csv").is_file())

    def test_dated_legrand_stub_and_debt_bridge_reconcile(self):
        snapshot = case_inputs(ROOT / "data/legrand_q1.toml", DATE)
        case = self.config["legrand"]
        assumptions = {**self.assumptions, **case["base"],
                       "post_q1_acquisition_sales_multiple": case["post_q1_acquisition_sales_multiple"]}
        costs, result, bridge_company, bridge = value_case(self.legrand, assumptions, snapshot, DATE)
        self.assertAlmostEqual(result.forecast.loc[1, "discount_years"], 216 / 365)
        self.assertAlmostEqual(result.forecast.loc[1, "fcff"], 891.097698569)
        self.assertAlmostEqual(bridge["ex_dividend_claim"], 622.12040702)
        self.assertAlmostEqual(bridge["acquisition_funding_reserve"], 300)
        self.assertAlmostEqual(bridge["adjusted_net_debt"], 5364.811830837)
        self.assertAlmostEqual(result.per_share, 92.419797044)
        implied_growth = 0.046290949567
        reverse = discount(bridge_company, result.forecast, costs.wacc, implied_growth,
                           discount_years=result.forecast["discount_years"].to_numpy())
        self.assertAlmostEqual(reverse.per_share, 173.27623, places=3)

    def test_dated_snapshot_cannot_be_reused_for_another_date(self):
        with self.assertRaisesRegex(ValuationError, "frozen"):
            case_inputs(ROOT / "data/legrand_q1.toml", date(2026, 5, 28))


if __name__ == "__main__":
    unittest.main()
