# Canonical manuscript

`paper.tex` is the canonical source. `paper_review.tex` includes the same source with double spacing. Numerical macros and table fragments are generated from archived outputs; vector figures retain editable text.

Verified build from this directory:

```bash
latexmk -xelatex -bibtex -interaction=nonstopmode -halt-on-error -outdir=build paper.tex
```

Requirements: XeLaTeX, BibTeX, latexmk, standard LaTeX packages, and distribution fonts (Latin Modern; STIX Two when present). Biber is not required. The delivered PDF matches the canonical source and the supplied table/figure assets. No external data or internet access is necessary to compile it.

For Overleaf, upload the ZIP, select `paper.tex` as the main document and XeLaTeX as the compiler. Use TeX Live 2023 for the checked environment. The fonts fall back to Latin Modern when STIX Two is unavailable; a different TeX installation may change line breaks. All tables, figure PDFs, bibliography and numerical macros needed for offline compilation are included.

The optional review wrapper supports later editorial preparation; this archive is not a submitted or author-approved journal submission. See the verification report for the publication boundary.

Follow-up revision: the named working paper now has 33 pages. `followup_appendix.tex` and four generated table fragments contain the executed QQQ/timing tests. `paper_review.tex` now also activates anonymous metadata and author suppression. `code/prepare_submission.py` compiles this wrapper and splits at Appendix A into main manuscript and supplement; it does not submit anything. Source CSVs and editable SVGs remain in the complete private research archive rather than the public-safe LaTeX ZIP. The included vector PDFs reproduce the paper without raw data.
