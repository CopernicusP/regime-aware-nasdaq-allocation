# Data access and exact reconstruction

The published calculations refer to frozen bytes, not whatever a live endpoint returns later. `MANIFEST_SHA256.json` identifies the archived versions. A differing download requires a separately labeled recomputation and reconciliation. Never overwrite the archived observations silently.

## Required schemas

| Input | Fields and scope | Access requirement |
|---|---|---|
| `raw/raw_adjusted_prices.csv` | `ticker,month,price`; adjusted monthly prices, December 1999–September 2026 | Authorized history with adjustment and distribution methodology |
| `raw/prior_returns.csv` | `month`; `QQQ,SPY,VTI_proxy,BND_proxy,Gold_proxy`; source-ticker columns; inherited additional exposures retained privately | Reconstruct from same-ticker adjacent prices, never a price-level ratio across two different funds |
| `raw/warmup_1999.csv` | `month,QQQ,US,BOND,GOLD`; March–December 1999 | Ten adjusted/indicative price levels yielding nine warm-up returns |
| `raw/warmup_sources.csv` | asset/source/field/retrieval/coverage | Source attribution; public access is not redistribution permission |
| `raw/qqq_warmup_and_bill_rates.csv` | `month,cash_yield_pct_source` required; inherited auxiliary columns retained | TB3MS monthly observations including preceding month for every modeled return |
| `raw/macro_current_vintage.csv` | `month,CPIAUCSL,IPMAN`; blanks remain missing | Legacy final-vintage inputs, not the new as-of experiment |
| `audit/external/pcpi.xlsx`, `ipm.xlsx` | Official Philadelphia Fed monthly-vintage matrices, unmodified | Research use subject to source terms; exact downloaded hashes in audit manifests |

`prepare_data.py` reads local files, contains no embedded vendor prices, and produces `raw/monthly_returns.csv`. It preserves all 330 months: nine warm-up and 321 evaluation returns. It applies the inherited pre-ETF gold custody assumption of 0.4% annually and reserve return `prior_month_TB3MS / 1200 − 0.0009 / 12`. These are modeled sleeves. SPY warm-up values are absent and unused.

## Sources and substitutions

QQQ and SPY use frozen [Digrin adjusted-price tables](https://www.digrin.com/stocks/detail/QQQ/price/). Broad U.S. equity uses VTSMX before the VTI splice in 2001; bonds use VBMFX before the BND splice in 2007. Gold uses indicative [Metalflow](https://metalflowapi.com/historical-gold-price/1999) spot prices before GLD in 2004. The exact return-row source ticker is authoritative. Displayed prices commonly have only two decimals. Fund and ETF series are not interchangeable executable instruments.

Issuer fact sheets confirm inception dates: QQQ trading on 10 March 1999, SPY 22 January 1993, VTI 24 May 2001, BND 3 April 2007, GLD 18 November 2004. These dates do not validate individual adjusted prices. A prospectus's legal trust-formation date can precede first trading.

Use the official [PCPI](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/pcpi) and [IPM](https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/ipm) pages to obtain monthly vintage workbooks. `macro_retrieval.json`, `retrieval.json`, and `macro_vintage_audit.json` record source URLs, hashes and coverage. The vintage algorithm uses month `t−1` or earlier for signal `t`, reference observation `t−2`, and exact within-vintage lags. Its SIC production definition is distinct from FRED's NAICS IPMAN. Missing origins use an explicit price-only fallback in both branches.

## Daily follow-up and authorized replacement route

The previous Yahoo failure was an earlier attempt, not the current access state. On this follow-up, ordinary unauthenticated chart requests succeeded for QQQ, VTI, BND, GLD, BIL and SPY. `audit/followup/source/daily_retrieval.json` records URLs, exact response SHA-256 hashes and coverage; responses remain private. `outputs/followup/daily_panel_quality.json` records checks. `protocol_followup.json` freezes the scope, and `code/followup_research.py` executes it without changing original raw inputs. No contractual data redistribution grant follows from HTTP 200.

The QQQ discrepancy is bounded as described in `docs/FOLLOWUP_FINDINGS.md`. It is no longer an unconditional preprint blocker. A next-observed-open replay is now complete for 2012–September 2026 and 2016–2025. It uses total-return-unit adjustment of actual vendor opens, not invented opens. All payment-date/auction/settlement limitations are disclosed. Early mutual-fund and spot proxies remain monthly-only.

For a licensed replacement, obtain CRSP through an authorized WRDS account or historical IBKR bars through an existing entitled account. Columbia's current WRDS guide describes master's-student registration: https://guides.library.columbia.edu/WRDS/overview . No such entitlement was used in this research. Record the CRSP tape/release (SIZ versus CIZ), stable security identifier selected from date-valid names, return/price field definitions, quote flags, corporate actions, ex/payment dates, timezone and observation period. Do not guess PERMNOs from tickers or convert negative CRSP quoted-price flags into executable positive closes. The tickers for searching are QQQ/QQQQ, VTI, BND, GLD, SPY and BIL; historical share classes/proxy names remain in the original mappings. Proprietary IDs may be exported only if the actual agreement permits it.

For IBKR, record contract/conid resolution and listing venue, regular-session setting, daily timestamp convention and TRADES versus ADJUSTED_LAST choice. Split and dividend adjustment are different. Do not assume an open bar is an exchange auction execution. The current official documentation is https://ibkrcampus.com/docs/tws-api/doc/market-data-historical/historical-bars/requesting-historical-bars ; legacy field explanations remain at https://interactivebrokers.github.io/tws-api/historical_bars.html . No paid market-data subscription is created by these scripts.

The vendor-neutral offline `code/import_daily_bars.py` validates an authorized CSV export with `ticker,date,open,high,low,close,adjclose`, enforces positive/consistent OHLC and unique dates, and records source hashes plus an operator-supplied adjustment description. It intentionally does not pretend to know an account's current WRDS schema or permissions. A new source is a labeled sensitivity or documented dataset revision, not a silent overwrite of the original archive. The full monthly construction remains reproducible from the authorized schemas above.

A public user can run the exact core on explicitly fictional inputs with `python reproduce.py demo`; eighteen accounting/as-of fixtures can run with `python -m unittest discover -s checks -v`. Neither command authenticates real prices or reproduces empirical tables. Empirical verification and `followup` require authorized observations, as do full production and macro-vintage stages. No data fetch runs automatically.
