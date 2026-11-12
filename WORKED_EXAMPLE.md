# Legrand DCF calculations by hand

The [dated Legrand memo](LEGRAND_MEMO.md) summarizes the May 29 case. The original benchmark calculation and the dated reconciliation are both shown below.

## FY2025-based scenario compared with the 29 May close

**Market comparison date** 29 May 2026. Financial amounts and share count are in millions, with per-share values in euros. The model uses five full annual forecast periods after the FY2025 base, with year-end discounting.

## Financial inputs

| FY ended 31 December 2025 | Value | Source |
| --- | ---: | --- |
| Revenue | 9,480.6 | Full-year release, p. 3 |
| IFRS operating profit | 1,808.5 | Full-year release, p. 3 |
| EBITDA | 2,217.6 | Full-year release, p. 9 |
| Tangible and intangible D&A including impairment, EBITDA bridge | 409.1 | Full-year release, p. 9 |
| Operating working capital | 1,013.7 | Full-year release, p. 9 |
| Historical capex including capitalized development | 248.7 | Full-year release, p. 10 |
| Income-tax rate | 25.9% | Full-year release, p. 4 |
| Short- and long-term borrowings | 544.5 + 6,059.3 | Full-year release, p. 9 |
| Cash and equivalents | 2,381.2 | Full-year release, p. 9 |
| Non-controlling interests | 39.8 | Universal Registration Document, consolidated balance sheet |
| Ordinary shares excluding treasury | 261.633259 | Universal Registration Document, note 4.1.2.1 |
| Diluted EPS | €4.705 | Universal Registration Document, note 4.1.3 |

The results were released on **12 February 2026** and the registration document was filed on **8 April 2026**. The 29 May unadjusted close was **€147.65**. [Full-year release](https://www.legrand.com/sites/default/files/Documents_PDF_Legrand/Finance/2025/1Y/Legrand_Press_Release_Full-Year_Results-2025_1770814869.pdf) · [Registration document](https://www.legrand.com/sites/default/files/Documents_PDF_Legrand/Finance/2026/autre/DUE/Legrand_URD_2025_ENGLISH_1775649568.pdf) · [Filing notice](https://www.legrand.com/fr/actualites/mise-a-disposition-du-document-denregistrement-universel-2025) · [Historical close](https://stockanalysis.com/quote/epa/LR/history/)

## CAPM and WACC

Use a **3.00%** EUR risk-free rate, in line with the Bundesbank’s 10-year fitted yield for listed federal securities that day. Use a **5.00%** equity risk premium, **1.10** equity beta, **4.25%** pre-tax borrowing cost, and **85% equity / 15% debt** target weights as editable assumptions. The target weights are independent of Legrand’s closing price. [Bundesbank capital market indicators, June 2026](https://statistiken.bundesbank.de/caas/v1/media/809524/data/cb745586c4d354f193bd7b9790975b5b)

- Cost of equity = 3.00% + 1.10 × 5.00% = **8.50%**.
- After-tax cost of debt = 4.25% × (1 − 25.9%) = **3.14925%**.
- WACC = 85% × 8.50% + 15% × 3.14925% = **7.6973875%**.

## Five-year forecast

Revenue grows 6%, 6%, 5%, 4%, and 3%, anchored to Legrand’s 4–7% FY2026 organic growth guidance and tapered thereafter. The model excludes a separately valued acquisition program. Hold EBIT margin at 19%, close to the FY2025 reported margin. D&A is 409.1 ÷ 9,480.6 of forecast sales, capex is a normalized 4.5% of sales, and incremental working capital is (1,013.7 ÷ 9,480.6) × the change in sales. The capex assumption allows for reinvestment against a D&A base that includes depreciation of leased assets. [Legrand full-year results and outlook](https://www.legrand.com/en/news/2025-full-year-results)

For year 1, revenue is 9,480.6 × 1.06 = 10,049.436. EBIT is 10,049.436 × 19% = 1,909.393. After 25.9% tax, NOPAT is 1,414.860. Add D&A of 433.646, deduct capex of 452.225 and incremental working capital of 60.822, yielding **1,335.460 FCFF**. Discount at 7.6973875% for one year to get **1,240.011**.

| Year | Revenue | EBIT | NOPAT | D&A | Capex | Increase in NWC | FCFF | PV of FCFF |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10,049.44 | 1,909.39 | 1,414.86 | 433.65 | 452.22 | 60.82 | 1,335.46 | 1,240.01 |
| 2 | 10,652.40 | 2,023.96 | 1,499.75 | 459.66 | 479.36 | 64.47 | 1,415.59 | 1,220.47 |
| 3 | 11,185.02 | 2,125.15 | 1,574.74 | 482.65 | 503.33 | 56.95 | 1,497.11 | 1,198.50 |
| 4 | 11,632.42 | 2,210.16 | 1,637.73 | 501.95 | 523.46 | 47.84 | 1,568.39 | 1,165.82 |
| 5 | 11,981.40 | 2,276.47 | 1,686.86 | 517.01 | 539.16 | 37.31 | 1,627.40 | 1,123.23 |

Sum the unrounded cash-flow present values to get **5,948.03**. With perpetual growth of **2.00%**, Year 6 FCFF is **1,659.94**. Divide by 7.6973875% − 2.00% to get end-of-year-five terminal value of **29,135.20**. Divide by (1 + WACC)⁵ to get **20,109.07** in present value. [NYU Stern FCFF methodology](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/fcff.html)

| Bridge | €m except shares and per share |
| --- | ---: |
| PV of five-year forecast | 5,948.03 |
| PV of terminal value | 20,109.07 |
| Enterprise value | 26,057.10 |
| Less borrowings | (6,603.80) |
| Plus cash and equivalents | 2,381.20 |
| Less non-controlling interests | (39.80) |
| Common equity value | 21,794.70 |
| Shares outstanding, millions | 261.633259 |
| **Value per share** | **€83.30** |

The independent calculation gives €83.302500037 per share. Python returns €83.30250004 at eight decimal places. The test checks WACC, year-one FCFF, both terminal values, EV, equity, and value per share. [Python forecast](example_outputs/LR.PA_forecast.csv) · [Python bridge](example_outputs/LR.PA_bridge.csv)

## WACC versus terminal growth

| WACC | 1.0% | 1.5% | 2.0% | 2.5% | 3.0% |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6.6974% | €86.82 | €94.92 | €104.75 | €116.92 | €132.39 |
| 7.1974% | €78.37 | €85.04 | €92.99 | €102.64 | €114.59 |
| 7.6974% | €71.19 | €76.76 | **€83.30** | €91.11 | €100.58 |
| 8.1974% | €65.00 | €69.71 | €75.18 | €81.60 | €89.27 |
| 8.6974% | €59.62 | €63.64 | €68.26 | €73.63 | €79.94 |

## Peer valuation

| Selected peer | EV/EBITDA | P/E | Reason for inclusion |
| --- | ---: | ---: | --- |
| Schneider Electric | 20.16× | 36.83× | Electrical distribution and data-center power. It also has significant automation and software exposure. |
| Eaton | 26.20× | 38.33× | Electrical distribution and data-center power. It has greater U.S. exposure and an aerospace business. |
| Hubbell | 19.29× | 28.63× | Electrical and power infrastructure. It is smaller and more exposed to U.S. utilities. |

Each multiple uses a 29 May close and FY2025 fundamentals in the peer’s own currency. EV is share price × year-end shares plus net debt and minority interests. EV/EBITDA is applied to Legrand’s FY2025 EBITDA, with Legrand’s net claims deducted and equity divided by year-end shares. P/E is applied to Legrand’s FY2025 diluted EPS. All six Legrand peer observations pass the denominator checks. The separate Renault example flags both Stellantis multiples as excluded because FY2025 EBITDA and EPS are negative. Renault’s own FY2025 denominators are also negative on the reported basis, so that peer example has no implied range. [Peer inputs and sources](data/README.md) · [Renault exclusion output](example_outputs/RNO.PA_peers.csv)

| Method | Low | Base or median | High |
| --- | ---: | ---: | ---: |
| DCF sensitivity | €59.62 | €83.30 | €132.39 |
| Peer EV/EBITDA | €147.18 | €154.56 | €205.77 |
| Peer P/E | €134.72 | €173.28 | €180.37 |

The DCF range spans the valid WACC and terminal-growth combinations in the grid. Each peer range spans the lowest and highest implied values from the selected peers. Their multiples reflect market prices, different business mixes and capital structures, and expectations that may differ from the DCF’s 19% margin and tapered growth. P/E is also affected by interest expense and taxes. With only three peers, the endpoints depend on individual names. [Valuation ranges](example_outputs/ranges.csv)

## Dated May 29 case reconciliation

The FY2026 revenue estimate is 9,480.6 × 1.11 = **€10,523.466m**. The base 19.2% reported EBIT margin produces €2,020.505m of EBIT. With 25.9% tax, D&A at 409.1 ÷ 9,480.6 of sales, capex at 4.5% of sales and incremental NWC at 1,013.7 ÷ 9,480.6 of incremental sales, full FY2026 FCFF is **€1,366.233m**. The reported 19.1% Q1 margin anchors the full-year margin. A reported margin below management’s adjusted target allows for acquisition-related amortization and other operating items.

Approximate realized Q1 unlevered FCFF as 485.2 × (1 − 25.9%) + 102.7 − 36.4 − 194.1 = **€231.733m**. The April–December amount is €1,134.499m. Allocate that amount evenly over its 275 days. The 59 elapsed days account for €243.402m of estimated FCFF. The remaining 216 days contribute **€891.098m**. This allocation ignores intra-quarter seasonality.

| Cash-flow endpoint | Time from 29 May, ACT/365 | FCFF included, €m | PV at base WACC, €m |
| --- | ---: | ---: | ---: |
| 31 Dec 2026 | 0.591781 | 891.098 | 852.839 |
| 31 Dec 2027 | 1.591781 | 1,519.104 | 1,349.970 |
| 31 Dec 2028 | 2.594521 | 1,639.191 | 1,352.299 |
| 31 Dec 2029 | 3.594521 | 1,742.477 | 1,334.766 |
| 31 Dec 2030 | 4.594521 | 1,834.597 | 1,304.888 |

The same CAPM assumptions give **7.6973875%** base WACC. The 3.00% risk-free input uses the 29 May German government yield. Beta of 1.10 represents modest above-market exposure to the building and data-center investment cycles. The 5.00% equity risk premium and 125bp spread over the risk-free rate are analyst assumptions. The 15% target debt weight represents a moderate long-run capital structure. Bear and bull WACC stress these judgments. Growth fades after FY2026. The base reaches €13.03bn of FY2030 sales and a 19.8% reported EBIT margin, with no additional deal program after FY2026. Legrand’s €15bn FY2030 ambition makes future deals and their cost an important difference to investigate. [Q1 results and outlook](https://www.legrand.com/en/news/2026-first-quarter-results) · [FY2025 release and 2030 ambitions](https://www.legrand.com/en/news/2025-full-year-results) · [Bundesbank yield](https://statistiken.bundesbank.de/caas/v1/media/809524/data/cb745586c4d354f193bd7b9790975b5b)

| Bridge to the ex-dividend close | €m except shares and per share |
| --- | ---: |
| PV of forecast cash flows | 6,194.761 |
| PV of terminal value, 2% growth | 23,361.336 |
| Enterprise value | 29,556.097 |
| Reported March 31 net financial debt | 4,670.500 |
| Less elapsed FCFF | (243.402) |
| Plus elapsed after-tax net financial expense | 15.593 |
| Rolled net debt before dividend and deals | 4,442.691 |
| Plus detached dividend claim | 622.120 |
| Plus Keydak and SRS acquisition funding allowance | 300.000 |
| Adjusted net debt | 5,364.812 |
| Plus minority interests, deducted from EV | 33.200 |
| Common equity value | 24,158.085 |
| Shares, millions | 261.395129 |
| **Value per share** | **€92.42** |

The terminal value at FY2030 is 1,834.597 × 1.02 ÷ (7.6973875% − 2.00%) = **€32,844.676m**, discounted over 1,677 days. The independent arithmetic produces **€92.419797044** per share. Python returns **€92.41979704**. The estimated net debt bridge uses Q1 net financial expense of €32.1m as a daily run-rate proxy, applies the announced dividend and provides for post-quarter deals. Actual daily cash flows, deal prices and any other April or May balance-sheet changes are unresolved. [Dated inputs and sources](data/README.md#dated-legrand-inputs) · [Forecast CSV](example_outputs/legrand_forecast.csv) · [Bridge CSV](example_outputs/legrand_bridge.csv)

### April and May retained cash

The model estimates cash retained from April 1 through the May 29 close in three steps. Values are in €m.

| Calculation | Formula | Result |
| --- | --- | ---: |
| April to December unlevered FCFF | 1,366.232585 full-year forecast − 231.733200 Q1 FCFF | 1,134.499385 |
| Unlevered FCFF through May 29 | 1,134.499385 × 59 elapsed days ÷ 275 days in April to December | 243.401686 |
| After-tax net financial expense through May 29 | (47.5 Q1 financial expense − 15.4 financial income) × 59 ÷ 90 × (1 − 25.9%) | 15.593110 |
| **Estimated cash retained** | **243.401686 − 15.593110** | **227.808576** |

The bridge deducts the estimated €227.81m from March 31 net debt. The model applies a straight-line daily allocation to the April–December forecast and uses Q1 net financial expense as an April–May proxy. The separate dividend claim is €2.38 × 261.395129m shares = €622.120407m. The €300m acquisition funding allowance is modeled separately. Using unrounded inputs, adjusted net debt is €5,364.811831m. [Q1 release appendices](https://www.legrand.com/sites/default/files/Documents_PDF_Legrand/Finance/2026/3m/Legrand_Press_Release_Results_3M2026_1778074218.pdf) · [Frozen bridge output](example_outputs/legrand_bridge.csv)
