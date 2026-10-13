# Regime-Aware Nasdaq Allocation

**Yudian Pan — Working Paper, 13 October 2026.**

This retrospective study compares a monthly state rule (R), constrained cost-aware optimization (M), Nasdaq buy-and-hold and simpler controls. The 33-page paper preserves unfavorable comparisons, including weak forecasting evidence and unstable relative growth. A finite QQQ data audit and an observed daily-bar next-open study now supplement the frozen monthly results. It is not a certified executable investment strategy.

Repository: https://github.com/CopernicusP/regime-aware-nasdaq-allocation

## Read and inspect

- `paper/Pan_2026_Regime_Aware_Nasdaq_Allocation.pdf`: complete named Working Paper.
- `docs/Verification_Report.pdf`: final review and the three distinct publication/execution levels.
- `docs/FOLLOWUP_FINDINGS.md`: QQQ convention analysis, bounded sensitivities, daily results and data-rights treatment.
- `docs/RELEASE_GATES.json`: the three release levels and actual dissemination status.
- `manuscript/paper.tex`: canonical source; editable tables and build-ready figure PDFs.
- `docs/DATA_ACCESS.md`: exact schemas, source identifiers, lawful acquisition route and substitution rules.

Yudian Pan reviewed and approved the manuscript and explicitly authorized this GitHub Working Paper release on 13 October 2026. Funding, possible personal financial interests, author responsibility and substantive AI assistance are disclosed in the paper and `docs/AUTHOR_COMPLETION.md`. No DOI, journal submission, peer review or acceptance is claimed. SSRN, arXiv and journal submission are deferred by the author.

## Reproduction without vendor data

Python 3.12.14 and `requirements-lock.txt` describe the checked numerical environment.

```bash
python -m pip install -r requirements-lock.txt
python reproduce.py demo
python -m unittest discover -s checks -v
python reproduce.py build
```

`demo` runs the unchanged allocation/accounting core with deterministic, entirely **FICTIONAL** observations in a temporary directory. It cannot overwrite research data and does not reproduce empirical paper statistics. The eighteen accounting/as-of/calendar fixtures are also vendor-free. Building the paper requires XeLaTeX, BibTeX and latexmk; included tables and figure PDFs are sufficient. `manuscript/BUILD_README.md` gives a direct build command.

## Empirical replication with authorized inputs

`core`, `full`, `followup`, `verify` and figure regeneration require the relevant authorized market/macro inputs and outputs. They are not claimed to run from this public research package alone. `followup` runs the fixed QQQ and observed-bar experiments plus targeted checks. In the complete private research environment, 35 tests pass, the 26 fixed QQQ perturbations and 32 execution scenarios are executed, and solver failures in the follow-up are zero.

Raw vendor observations, commercial source captures, macro workbook copies, full monthly asset/strategy paths and figure source-data CSVs are deliberately absent. Research code, aggregate results, clear schemas, source hashes and access instructions provide the established restricted-data reproduction route. This is not a claim that all derivatives are freely distributable or that the fictional demo satisfies every program-execution condition of every finance journal.

## Research limits and rights

The original 77.31 bp QQQ issuer mismatch is not fully identified. A contemporary SEC close, high-precision daily reconstruction and fixed ±100 bp sensitivity bound its effect on the stated conclusions. No prices were changed to force agreement. Live-ETF next-open results begin in 2012; earlier mutual-fund/spot proxies remain monthly-only. Observed bars and theoretical ex-date total-return units do not validate auction fills, payment-date cash, settlement, liquidity or taxes.

`LICENSES.md` reserves rights in owned work and grants no vendor-data license. No additional open-source or Creative Commons license has been selected. Do not upload the private archive. Cite Yudian Pan using `CITATION.cff`; do not invent a DOI or publication status.
