# Oil-Market Tightness and Currency Exposure

Macro research on whether Brent curve tightness can inform relative currency positions across oil exporters and importers. The archive preserves the later weekly Brent implementation separately from the timing audit. It should not be conflated with an earlier monthly WTI version.

## Method
The archived carry proxy is CO3 minus CO12. Carry-momentum compares the proxy with its four-observation moving average. A common signal interacts with country oil-exposure groups to form long/short currency baskets. This is not the conventional currency interest-rate carry signal.

## Timing and costs
Separate source-price date, signal date, execution date and return end date. A Thursday signal cannot be credited with the return already earned from the preceding Friday. The later audit verifies the source dates and calculates a forward simple-return proxy, while retaining the original formula as a diagnostic.

## Limitations
Same-year country bins can be retrospective. Bloomberg price histories and vendor exports are excluded. A simple FX/futures price ratio is not a fully financed, rolled futures or NDF PnL; COP costs, financing, margin, quote direction and basket concentration still need resolution. Neither the archived original metric nor the forward proxy is investable performance.

## Run
`python src/reproduce.py` runs a synthetic timing and dollar-neutral-weight example. Historical notebooks are stored with all outputs cleared under `archive/notebooks/`. `src/reproduce_oil_local.py` accepts a locally authorized AQMS folder through `--data-dir`; it requires the original folder schema and is not run automatically.
