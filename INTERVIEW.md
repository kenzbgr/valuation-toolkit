# Interview walkthrough

> I built a Python toolkit that projects unlevered cash flows, calculates a CAPM-based WACC, and bridges enterprise value to value per share. It also screens and applies EV/EBITDA and P/E multiples. I reconciled Legrand’s FY2025-based scenario by hand at €83.30, then built a May 29 case using Q1 figures, a partial-year discount period and an estimated net debt bridge. The updated base was €92.42 versus the trailing peer P/E median of €173.28.
>
> WACC was the largest driver in the original one-point sensitivity. In the updated case, cutting WACC by one point raises the estimate to €116.81. Roughly 79% of enterprise value comes from the terminal value. At base WACC, matching the peer P/E median with the same cash flows would require 4.63% perpetual growth.
>
> One of eight CAC 40 estimates was within 15% of its closing price. Renault was the most informative case. I display N/A and show the signed residual in diagnostics. I would value its auto business with an automotive debt bridge and treat the captive finance business as a separate equity valuation.

## CV wording

> Built a Python valuation toolkit with a five-year DCF, sensitivity tables, and trading comparables. Developed a dated Legrand case using Q1 filings, tested three scenarios, and benchmarked the model across eight CAC 40 companies.

[Legrand memo](LEGRAND_MEMO.md) · [Dated sensitivity](example_outputs/legrand_sensitivity.csv) · [Benchmark and Renault analysis](BENCHMARK.md)
