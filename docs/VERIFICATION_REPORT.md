# Research Verification and Release Assessment

**Yudian Pan — Regime-Aware Nasdaq Allocation — 13 October 2026**

**Decision:** The scientific working-paper issues have been handled to a reasonable, bounded standard. The project now has a concrete 33-page revised manuscript, finite QQQ sensitivity analysis, observed daily execution-clock tests, a restricted-data reproduction route, and formal submission preparation. The author has now supplied truthful funding and possible personal-interest disclosures, accepted responsibility and explicitly approved public GitHub Working Paper release. The remaining operation is publication using the authenticated account; no further research or author approval is required. Broker-grade implementation and open redistribution of all data are not preconditions for the working paper.

## QQQ discrepancy: contained, not falsely explained

The inherited fiscal-year return ending September 2009 is 9.183065%; the SEC-hosted issuer report says 8.41%, a 77.3065 bp difference. Schwarz, Walter and Weiss (2026, JFQA, DOI 10.1017/S0022109026102774) explain why CRSP SIZ month-end and CIZ ex-date reinvestment yield different monthly returns. That general mechanism was tested against this specific episode rather than presumed to explain it.

SEC Release 34-58943, page 4, independently records the September 30, 2008 QQQQ close of $38.91. The daily vendor gives the same start and an ending close of $42.25. Price-only return is already 8.583912%, above the reported market total return. Daily ex-date reconstruction gives 9.160773%, month-end reinvestment 9.154197%, and adjusted-close ratio 9.160788%. Dividend timing contributes about 0.66 bp, not 77 bp. The frozen versus daily difference is only 2.23 bp, consistent with the fixed two-decimal endpoint interval of 9.151886%–9.214254%. The remaining issuer gap is about 75.08 bp.

The issuer's 2010 prospectus explicitly describes consolidated closing prices and ex-date reinvestment. NAV endpoints of $39.20 and $42.29 belong to a different basis and are not a valid market-price correction. No split occurs in the comparison window. Payment dates were not fabricated. An issuer endpoint-field inconsistency or report error is possible but unproven. No observation was back-solved to match a desired return.

The complete QQQ daily-adjusted replacement changes full-period CAGR for QQQ/R/M from 8.8167/9.1733/11.0682% to 8.8265/9.1800/11.0648%. The pre-recorded ±100 bp fiscal-year-return perturbations, uniformly distributed or located in each of twelve months, produce 26 scenarios and 78 strategy runs. R's full-period CAGR stays between 9.1626% and 9.1835%; M between 11.0551% and 11.1357%. Their original maximum drawdowns are unchanged in these localized stresses. This bounds the identified discrepancy's impact; it does not certify every early proxy observation. The exact cause remains disclosed and the finite research issue is closed.

## Execution: a real daily test with a narrower claim

The audit evaluated CRSP/WRDS and IBKR access. An institutional registration route exists, but no authenticated CRSP entitlement or broker market-data subscription was available or assumed. Public Yahoo chart requests succeeded this time without login or circumvention. Six ETF series each cover all 3,708 expected common sessions from December 30, 2011 through September 30, 2026. Dates, duplicates, positive prices, OHLC bounds and corporate actions were checked. Raw vendor opens are retained separately from the adjusted total-return-unit transform.

Thirty-two scenarios compare four unchanged methods over 2012–September 2026 and 2016–2025, at boundary close or next observed open, and at 10/25 bp per traded dollar. All decisions are frozen at the prior completed month-end; existing holdings bear the overnight move. BIL replaces modeled reserve returns consistently in both daily branches. No opening prices are manufactured for early mutual-fund or indicative spot proxies.

For 2016–2025 at 10 bp, next-open CAGR is QQQ 19.68%, R 12.88%, M 14.86%, and Trend10 16.74%. Their month-end maximum drawdowns are 32.58%, 13.53%, 27.77%, and 15.66%. The simpler trend rule therefore loses its original month-end drawdown advantage over R under this execution clock. Daily-close maximum drawdowns are materially larger: 35.12%, 25.61%, 29.32%, and 28.56%. The revised body explicitly reports this changed comparison instead of generalizing the original monthly dominance claim.

The 25 bp scenario changes the cost M anticipates in its objective; allocation changes can outweigh higher fees, so it is not described as a pure fee deduction. No improved branch is selected. All follow-up solver-failure counts are zero. The initial open of a buy-and-hold portfolio can also change CAGR positively or negatively; delay is not mechanically assumed to reduce every result.

Observed bars do not establish auction participation, fill size, actual spreads/impact, distribution payment-date liquidity, settlement, whole shares or taxes. Ex-date adjusted units are a research accounting convention. This is an empirical timing sensitivity; executable-investment status remains unverified. Early proxy history remains monthly simulation.

## Reproduction and public-data scope

Journal of Finance and JFQA policies recognize code plus documented restricted-data access and fictional test inputs when commercial raw data cannot be shared. Their policies do not confer vendor permissions. The package now includes an entirely fictional, deterministic demonstration that executes the unchanged core in isolation, and a provider-neutral validator for a legally obtained daily export. Neither silently downloads data, changes original research inputs or claims to reproduce empirical findings from fictional observations. The demo exercises the core rather than every macro/statistical stage; universal journal code-policy compliance is not claimed.

Digrin's October 1, 2026 terms and Yahoo's provider notice were reviewed. No blanket raw/derivative redistribution license is assumed. The public research package excludes raw histories, normalized empirical panels, full monthly paths, figure source-data CSVs, standalone SVGs, third-party full texts/workbooks, correspondence and private author fields. The scholarly paper contains original analysis and research graphics; it is not offered as a reusable vendor database. Owned code, aggregate results, identifiers, exact schemas, source hashes and acquisition instructions are retained. Rights are reserved; choosing MIT/CC is optional and not a publication gate. A broader dataset distribution would require its own source-specific authorization.

## Three release levels

**Public Working Paper / Preprint:** scientific accuracy, reasonable treatment of important uncertainty, clear limits, scoped copyright handling and truthful author statements. The data and execution questions now have adequate bounded treatment. Funding, possible personal financial interests and author responsibility are now explicitly confirmed by the author. There is no further open-ended optimization requirement.

**Journal Submission:** working-paper requirements plus actual platform/profile information, target-journal presentation, biography, reviewer access and submission authorization. Journal of Asset Management is the principal applied target. Anonymous double-spaced manuscript and separate supplement are prepared from the canonical source. Final house-style formatting, profile details and a separate submission instruction belong to this stage; the author has expressly deferred all platform and journal submissions. No submission or acceptance is claimed.

**Executable Investment Strategy:** authenticated trading data and execution, realistic size-dependent costs, distributions/settlement, share/cash constraints and prospective validation. Daily-bar testing is meaningful progress but does not complete this level. Its remaining work does not block a qualified preprint.

## Platform and author preparation

Official SSRN guidance updated August 3, 2026 requires a complete author profile, current affiliation/valid email, English title/abstract/PDF, relevant rights and AI disclosure with both abstract and PDF. The revised paper includes first-page and full substantive AI disclosures. arXiv offers a perpetual nonexclusive license as an alternative to broader CC licenses, may require endorsement, and moderates scope and originality. No license choice, account status or endorsement is invented.

JAM currently asks for 3,000–6,000 words, double spacing, a short abstract, up to six keywords, editable figures/tables, double-blind review and an approximately 100-word biography; its formatting section allows LaTeX plus PDF. A separate main review copy and supplement are prepared. Springer Nature permits preprints without treating them as prior publication. Simultaneous journal review is a different issue. Full source URLs and operational requirements appear in `docs/VENUE_ASSESSMENT.md`.

All named deliverables use Yudian Pan. The author explicitly confirms review of the 33-page revised manuscript, accepts responsibility for its content and disclosed AI assistance, and authorizes public GitHub Working Paper release. The research had no external funding or commercial sponsorship; possible personal ETF/security holdings are disclosed without claiming a blanket absence of conflicts. No institutional affiliation, endorsement, ORCID or personal code-by-code checking is invented. `docs/AUTHOR_COMPLETION.md` records the confirmed declarations. SSRN, arXiv and journal submissions are deferred by explicit author instruction.

## Verification and remaining limits

The original nine raw input files match the preceding private-archive manifest byte for byte. The prior 31 checks plus four focused execution checks pass: independent same-panel close accounting, observed-opening buy-and-hold identity, no use of future open in target formation and self-financing costs. The fictional demo runs without vendor input. Numerical table generation reads executed follow-up outputs directly. The final audit records PDF/source consistency, anonymous-file checks, package exclusions, checksums and source-only compilation.

The inherited full computation and resampling findings remain intact: no established positive growth outperformance after the stated adjustments, weak loss classification, small macro forecast gains, and substantial dependence on start date and exposure. No model retuning or new winning policy was introduced. This is single-agent computational and source review, not independent human peer review, legal certification or journal approval. The research queue is closed at the documented scope; new primary evidence can be incorporated later without reopening the approved Working Paper release.
