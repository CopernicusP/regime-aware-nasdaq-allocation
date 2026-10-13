# Targeted methodological toolkit audit

Access date: 13 October 2026. Six repositories were inspected at immutable commits. Only relevant text, scripts, templates, and their dependencies/notices were copied. No installer, paid service, recursive team, or external reviewer was used. The user's single-agent instruction overrides toolkit team orchestration and repeated intake prompts. These are methodological aids, not certification.

| Repository | Commit | License | Applied workflow and evidence |
|---|---|---|---|
| Imbad0202/academic-research-skills | a3ef8c79d888b90aaaaecce7f42fbc3fd082d5ab | CC BY-NC 4.0; Cheng-I Wu | Reproducibility and skeptical-review checklists; separate data authentication from computation; preserve failed prior rerun; documented unresolved gates. No simulated independent peer review. |
| K-Dense-AI/scientific-agent-skills | a1043ef544e3a100c28e70a736b6cf32554d0677 | MIT; K-Dense | Executed claim-evidence validator and statistical reproducibility auditor with pinned `_common.py`. Fourteen claims structurally valid; 22-item statistical checklist explicitly retains seven partial items. Structural validity does not establish scientific truth. |
| WUBING2023/PaperSpine | f7e3dabaf499b2aef1eabdd1cd5d64f173d7dcc3 | MIT; PaperSpine contributors | Executed `latex_guard.py`; zero errors. Two reference warnings arise because the static parser does not recognize labels created by the custom table macro. Actual LaTeX references resolve. Full PaperSpine runtime was not installed. |
| SNL-UCSB/paper-writing-skill | 676f8520bba54208eb4fe1d41620e365d9af6a24 | MIT; Arpit Gupta | Audited section roles, claim placement, terminology, word counts and sentence-level flags; removed filler and unsupported adjectives. Technical negation, robust optimization, and precise passive methods descriptions retain documented exceptions. No blanket zero-passive or journal-style claim. |
| Yuan1z0825/nature-skills | 473e8d7b1b918fe37208d3a5e143a3ac9af4c91b | Apache 2.0 | Applied nature-figure claim contracts, nature-polishing section discipline and shared consistency/ethics resources. Ran actual source, PDF text and strict collision scripts on five figures. Python plotting is explicitly permitted by the task; no R conversion or generated scientific imagery. |
| Kiterlin/anti-defensive-writing | c7edf8fc91ae9c4f7e58345bd12934bb4cf41c46 | MIT; Kiterlin | Consolidated repeated operational cautions and removed rhetorical defenses. Retained evidence-based data, execution, selection, and inference limits. |

## Actual figure gate

Five single-panel figures have editable vector PDF/SVG, 600-dpi PNG/TIFF, exact CSV source observations, and recorded claim/transformation/sample contracts. The PDF audit enforces an 8-point floor, stronger than the upstream 5-point default. Strict collision checks use unchanged upstream geometric tolerances. The source validator retains a warning for 165 mm width, because its generic defaults are 89/183 mm. The chosen width fits the working paper's 6.5-inch text area; the warning is documented rather than hidden. No Nature layout compliance is asserted. Multi-panel alignment is inapplicable to these single-panel figures. Color and grayscale were inspected visually; automated glyph/collision checks alone cannot certify accessibility.

Run `python code/figure_qa.py` in the private archive to repeat the upstream audits. `code/validate_artifacts.py` independently compares source CSV values against numerical outputs and checks figure dimensions and fonts. The source validator is run without strict mode specifically to retain its documented layout warning; all exported-PDF collision checks run in strict mode.

## Writing and statistical gates

`audit/mechanical_writing_audit.json` lists every mechanical candidate; `audit/writing_candidate_decisions.csv` records its retained scientific context. Approximate main prose is 4,660 words; full prose is 7,118, excluding imported table cells and bibliography. The post-edit total is smaller than the supplied source, while Results expands to accommodate unfavorable controls. Imported tables, exact mathematical statements and references are not discarded to meet an arbitrary count.

The statistical auditor reports `VALID_WITH_REVIEW_GAPS`: fixed-sample precision, previous selection, unresolved assumptions/data, coarse process uncertainty, public data access, provenance, and author governance remain partly documented. Specialist review in econometrics and market-data provenance is appropriate but has not occurred. No self-review output is described as independent human peer review.

`audit/toolkit_file_inventory.csv` hashes every retained upstream file. Retrieval manifests preserve URLs and pins. `audit/latex_guard.json`, `claim_structure.json`, `statistics_structure.json`, and `figure-qa/` preserve the actual outputs, including warnings. The local public candidate excludes third-party toolkit copies; reusing them separately requires respecting each license.
