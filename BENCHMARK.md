# Eight-company CAC 40 benchmark

**Basis** FY2025-based scenarios compared with the 29 May 2026 close. The separate [dated Legrand case](LEGRAND_MEMO.md) incorporates Q1 and the May debt bridge. The sample contains two companies each in industrials, consumer discretionary, health care and utilities. All eight prices are unadjusted Euronext Paris closes in euros. The input snapshot uses FY2025 fundamentals and year-end share counts. The live yfinance run matched the frozen closes for all eight companies and both additional peers to within €/$0.00002 per share. [Frozen prices](data/prices.csv) · [CAC 40 constituents](https://www.boursedirect.fr/fr/marche/euronext-paris/cac-40-FR0003500008-PX1-EUR-XPAR/composants) · [Euronext March review](https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-march-2026-quarterly-review-results-cacr) · [Euronext June review](https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-june-2026-quarterly-review-results-cacr)

The signed difference is (DCF ÷ close − 1) × 100. One of eight companies was within ±15%. Seven had reportable estimates. The denominator includes Renault as unavailable. This is the first measured benchmark for the project. Revenue, operating margins, reinvestment and financing assumptions are specified before the DCF is compared with price. The engine uses the close for the price comparison and peer multiples.

| Company | Ticker | Sector | Close | DCF per share | Difference |
| --- | --- | --- | ---: | ---: | ---: |
| Legrand | LR.PA | Industrials | €147.65 | €83.30 | −43.58% |
| Schneider Electric | SU.PA | Industrials | €269.95 | €169.72 | −37.13% |
| Renault | RNO.PA | Consumer discretionary | €29.59 | N/A | N/A |
| Stellantis | STLAP.PA | Consumer discretionary | €6.857 | €11.12 | +62.23% |
| Sanofi | SAN.PA | Health care | €75.29 | €128.10 | +70.15% |
| EssilorLuxottica | EL.PA | Health care | €175.15 | €112.72 | −35.64% |
| ENGIE | ENGI.PA | Utilities | €26.47 | €27.92 | **+5.48%** |
| Veolia | VIE.PA | Utilities | €34.73 | €57.00 | +64.13% |

[Benchmark data](example_outputs/benchmark.csv) · [Valuation ranges](example_outputs/ranges.csv)

## What moved the outliers

**Renault.** The [diagnostics](example_outputs/outlier_scenarios.csv) retain the raw −€72.00 equity residual per share. The model produces €115.99 of operating EV per share and deducts €187.99 of net claims per share. Consolidated debt less cash alone accounts for €182.49 per share. Renault reported €7.37 billion in automotive net cash. Substituting that number into the existing bridge, with group cash flows and WACC held fixed, adds €209.40 per share. That isolates the perimeter problem. A segment valuation would forecast automotive cash flows with the automotive bridge and value Mobilize Financial Services as equity. FY2025 also included a €9.315 billion loss from a change in accounting for the Nissan stake and a €2.331 billion negative Nissan contribution. A 1pp increase to every forecast EBIT margin adds €23.92 per share, far less than the bridge effect. [Renault FY2025 financial report](https://events.renaultgroup.com/app/uploads/sites/7/2026/02/RG_2025_FY_Results_Financial-Report_EN.pdf)

**Stellantis.** Reported operating margin went from 11.8% in 2023 to 2.4% in 2024 and −17.1% in 2025. The company reported €25.4 billion in unusual FY2025 charges, including effects of a strategic reset. The model assumes a recovery from 1.5% forecast EBIT margin in year one to 6% in year five. A 1pp lower margin in each forecast year reduces the estimate from €11.12 to €5.28. The annual report shows €6.69 billion of industrial net cash, down from €15.13 billion a year earlier. The consolidated debt deduction already reduces the estimate by €5.73 per share, so it narrows the positive gap. The recovery assumption is a plausible source of the gap. The evidence includes exceptional charges and operating deterioration alongside cyclical exposure. [Stellantis FY2025 results](https://www.stellantis.com/en/news/press-releases/2026/february/full-year-2025-results) · [Stellantis annual report, industrial net financial position](https://www.stellantis.com/content/dam/stellantis-corporate/investors/financial-reports/Stellantis-NV-20251231-Annual-Report-and-Form-20-F.pdf)

**The other five misses.** The scenarios isolate each input’s effect and leave the reported base cases in place.

| Company | What the model shows |
| --- | --- |
| Legrand | Net debt is 1.90× trailing EBITDA. Holding everything else fixed and zeroing net debt gives €99.44, still below €147.65. Even the highest WACC/growth-grid value is €132.39. The tapered cash-flow forecast and discount rate merit review. |
| Schneider Electric | Net debt is 1.84× trailing EBITDA. Removing it in isolation gives €196.89 versus €269.95. The high end of the WACC/growth grid is €268.08, showing substantial sensitivity to long-run assumptions. |
| Sanofi | Net debt is 1.01× trailing EBITDA. Zeroing it widens the positive gap. Even the grid low is €89.04 versus €75.29. The model carries an approximately 21% margin forward and uses a single growth path. Product-specific patent and pipeline risks could matter and are untested here. |
| EssilorLuxottica | Net debt is 1.95× trailing EBITDA. Removing it in isolation gives €136.16 versus €175.15. The close lies inside the €76.28–€196.44 grid, so the gap is sensitive to long-run rates. |
| Veolia | Net debt is 3.33× standardized EBITDA, and net debt reduces the estimate by €26.49 per share. The DCF still exceeds the close, so debt compresses the gap. The close is near the low end of a wide grid, and a 1pp margin reduction lowers the base estimate by €11.44. The company reports €19.66 billion of net financial debt under its own definition. |

ENGIE is inside the band despite 3.06× net debt to standardized EBITDA. Taken together, the cases show how leverage transmits an EV error to equity and why the direction of the gap matters. Market price gives a comparison for each scenario. It cannot establish intrinsic value or isolate a causal explanation. [Scenarios](example_outputs/outlier_scenarios.csv) · [Ranges](example_outputs/ranges.csv) · [Veolia FY2025 results, slide 4](https://www.veolia.com/sites/g/files/dvc4206/files/document/2026/03/Finance_Veolia_2025_full_year_results_presentation.pdf)
