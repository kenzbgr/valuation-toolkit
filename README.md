# Python Valuation Toolkit

The Legrand case study estimates a base-case value of €92.42 per share as of 29 May 2026, approximately 37% below the €147.65 closing price. The DCF uses a 7.70% WACC, 2.0% terminal growth and a forecast EBIT margin reaching 19.8% in 2030. The bull case reaches €146.46 by combining stronger growth, higher margins and a lower cost of capital. Peer EV/EBITDA multiples imply €147.18–€205.77 per share. This divergence highlights the sensitivity of the valuation to operating forecasts and discount-rate assumptions, alongside the higher valuations embedded in peer market prices.

[Read the updated Legrand investment note](LEGRAND_INVESTMENT_NOTE.md) for the reverse DCF and €15bn growth scenario.

## Run the Legrand demo

```bash
python -m valuation_toolkit --legrand
```

[One-page Legrand memo](LEGRAND_MEMO.md) · [PDF](LEGRAND_MEMO.pdf) · [Sample output](example_outputs/legrand_cases.csv)

```text
Legrand | 2026-05-29 | EUR per share | Close 147.65
Bear DCF   55.88
Base DCF   92.42
Bull DCF  146.46
FY2025 peer EV/EBITDA 147.18–205.77 (median 154.56)
FY2025 peer P/E 134.72–180.37 (median 173.28)
```

## Setup

From the extracted project folder, use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The demo uses frozen inputs and writes six CSVs to `outputs/`. Add `--yahoo-prices` to retrieve the same date’s unadjusted closes with yfinance. Run `python -m valuation_toolkit` for the eight-company FY2025-based benchmark and `python -m unittest discover -s tests -v` for the tests.

## Assumptions and methodology

Edit `assumptions.toml`. The `legrand` section contains the dated bear, base and bull cases. The `company` section contains the annual benchmark inputs and shared company assumptions. Growth and EBIT margin take one decimal rate or five annual rates. Edit the CAPM inputs or set `wacc_override`. Invalid WACC and terminal-growth pairs are marked `N/A` in the grid, and the CLI identifies missing required inputs.

The Legrand demo uses information public by 29 May 2026, including Q1 and the ex-dividend date. Its estimated net debt and FY2026 cash-flow stub are shown in the output. The benchmark uses a separate FY2025-based scenario compared with the May 29 close. Renault’s displayed value is `N/A`, with the signed residual in the diagnostics.

[Worked calculations](WORKED_EXAMPLE.md) · [Benchmark and diagnostics](BENCHMARK.md) · [Frozen inputs and sources](data/README.md) · [Interview walkthrough](INTERVIEW.md)
