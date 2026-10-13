# Decisions and resumable state

## Scientific decisions, 13 October 2026

1. Preserve R/M specifications and every supplied historical observation. Recompute the baseline before editing claims.
2. Correct a prior release audit: `python reproduce.py core` previously exited 2 because `core` was not an accepted mode. Unchanged files were not evidence of a rerun. Retain that log and replace the runner with explicit tested modes.
3. Freeze new controls in `protocol_extensions.json` before running them. Retrospective status remains explicit because the history was already inspected.
4. Add mean-holdings and validation-volatility controls, a fixed ten-month trend rule, every completed five-/ten-year January start, and block-length sensitivity. Do not promote a new winner after observing results.
5. Acquire authentic official vintage matrices. Determine eligibility from as-of data alone; assert that the latest comparison covers it. Do not use future missingness to define actionable eligibility.
6. Correct the SIC/NAICS conflation. Compare vintage versus latest within SIC; retain the legacy revised-NAICS branch separately.
7. Add outcome-bounded classifier and macro forecast-loss diagnostics. The classifier's original 120-origin window included 2026 outcomes; the bounded evaluation has 118 origins. This diagnostic addition occurred after the initial extension protocol and is exploratory.
8. Increase the inherited conditional bootstrap to 20,000 draws. Retain 100 process reconstructions as coarse descriptive sensitivity, not a precision claim or rerun of all historical research selection.
9. Preserve newly discovered early QQQ discrepancies. Aggregate endpoint evidence cannot identify an honest replacement monthly history.
10. Reframe the main contribution around downside protection, opportunity cost, start-date dependence, and the lack of consistent benefit from complexity.

## Evidence placement and editorial decisions

| Result | Role | Placement |
|---|---|---|
| Full-history protection, later underperformance | Central finding and boundary | Abstract and main Results |
| Simple trend exceeds R/M later | Conclusion-changing adverse evidence | Main Results and Conclusion |
| Average-exposure and validation-risk controls | Necessary attribution evidence | Main Results, full CSV |
| Rolling starts | Time-period heterogeneity | Main figure and appendix table |
| Classifier failure and macro MSE | Bound predictive claims | Main Results; exact horizons in appendix |
| Solver bounds, serial scaling, costs | Technical support | Methods and appendices |
| External discrepancy and execution gap | Claim boundary | Data, Limits, appendix, release report |
| Tool versions and process history | Provenance | Audit/docs, outside scholarly narrative |

The revision removes brokerage-operating advice, repetitive audit chronology, and outdated claims that vintage files were unavailable. It replaces generic future-work proposals with completed controls and named unresolved requirements. `audit/word_counts.json` records approximate before/after counts: main text about 4,660 words; full text including appendices about 7,110, excluding imported table cells and bibliography. The Results section grows because the unfavorable controls materially change interpretation; total prose contracts.

Terminology: R = state allocation rule; M = simple-forecast optimizer; MR = price-only ridge optimizer; RM = ridge plus uncertainty/state controls; PM = probability-driven control; as-of macro = conservatively dated SIC/CPI extension; legacy macro = inherited revised-NAICS branch. CAGR is geometric growth; log-growth differences belong to paired tests. MDD is a positive loss magnitude; plotted drawdowns are negative. Water means high-to-recovery elapsed months, not trough-to-recovery.

## Earlier release queue (superseded)

The original broad research and declaration queue is retained in the private historical checkpoints. The bounded follow-up below supersedes it. Broker certification and unrestricted data redistribution are not Working Paper prerequisites.

## Follow-up decisions, 13 October 2026

The finite protocol in `protocol_followup.json` is authoritative for the new tests. No original raw observation or R/M coefficient was changed. The QQQ issuer mismatch is closed as a bounded research limitation after endpoint corroboration, a full QQQ source substitution and 26 fixed perturbations. The cause is not claimed fully identified. Thirty-two observed-bar scenarios now test next-open timing; early proxies remain monthly only. Daily drawdowns and the loss of Trend10 drawdown dominance over R are reported, not suppressed. Costs of 25 bp are anticipated by M and can change its weights; no improved branch is adopted.

Restricted commercial data does not have to be made public to publish a paper. Raw data, normalized/derived full histories and figure source-data CSVs are excluded from the public candidate; own code, input/access documentation and a wholly fictional core demo supply the conventional reproduction route. No blanket vendor or derivative license is inferred. Three release levels replace the former universal next-open/publication blockade. The research stage is closed; the author subsequently confirmed all required declarations and approved the 33-page Working Paper.

## Final author approval, 13 October 2026

All author declarations have been supplied and are integrated without changing data, models, parameters or research conclusions. Publication is limited to GitHub Working Paper release; SSRN, arXiv and journals are deferred. The approved 33-page PDF/source checkpoint is preserved under `audit/publication/approved_checkpoint/`.
