# Current edition: company-style research assessment

Use company_final/Consumer_Sentiment_Report.pdf and Consumer_Sentiment_Presentation.pptx at the extracted repository root. The current presentation uses slides 1-9 for the main talk, with slides 10-17 as appendices. Read company/README.md for the current reproduction commands. Statistical findings are unchanged.

# Economic narratives and consumer sentiment: audited project

Author: Khushi Khanna. Economic cutoff: October 16, 2026. Processing: October 17, 2026.

Read the report and Presentation_Speaking_Notes.pdf first. The current edition has nine main slides and eight appendices. The current two-page script has approximately 850 words. Earlier editions are superseded for presentation use.

## What this version establishes

The original 670-title AI index feeds monthly regressions directly. All primary forecasts share 21 finalized target months. The index improves the narrow economic point estimate but worsens matched static and dynamic controlled comparisons. The dictionary sensitivity gives conflicting exploratory evidence. No national causal media effect is identified.

The assignment is not fully rubric-compliant. Two independent humans have not labeled the required 300 items. Exact historical release vintages are not reconstructed. Do not rename AI-reference labels as human labels, claim a real-time backtest, or hide these gaps. The report states them on its first page.

## Reproduce offline

Python 3.12 was used. Install the packages in requirements.txt, then run these commands in this folder:

    python analyze_integrated_v7.py
    python make_figures_v7.py
    python audit_final.py
    python prepare_review_materials.py
    python company/exhibits.py
    python build_company_report.py
    python company/build_speaking_notes.py
    python build_company_dashboard.py

The wording_proxies.py module regenerates all literal text fields from titles for independent inspection.

The scripts retain descriptive legacy filenames, but outputs belong to this audited edition. They use raw source snapshots and frozen labels. Outputs are regenerated in outputs/. The current report, notes and dashboard builders write to company_final at the extracted repository root. The editable PowerPoint builder is company/deck.mjs and requires the OpenAI Artifact Tool runtime. A standard Python environment can reproduce the analysis, figures, PDFs, notes, and dashboard without that runtime. Legacy builders under presentation_source/ and audit/ are superseded.

No API key, model runtime or network is necessary for numerical reproduction. Numerical reproduction starts from frozen assistant labels. The exact assistant model snapshot and sampling settings are unavailable, so identical future labeling is not promised. The rejected automated-model scores are supplied as frozen comparison measurements, not recreated by the default pipeline.

## Files and provenance

- data/: supplied workbook, official BLS/BEA series via FRED, Michigan component and group snapshots, published SF Fed benchmark, original public archive metadata and model manifests.
- outputs/coded_corpus.csv: 670 retained titles. Direct_AI_Coding_Audit.csv retains all 691 selection/review decisions. The monthly_media.csv index uses equal source weights and preserves gaps.
- outputs/*forecasts.csv: every prediction and actual. Metrics, coefficient estimates, parameter counts, influence checks, VIF, paired uncertainty tests and sensitivities accompany them.
- audit/: assignment PDF, requirements matrix, design freeze, original retrieval/coding scripts and prompts, and sealed human-sample mapping. Legacy scripts in audit/ are historical evidence, not default entrypoints. Raw model weights are not bundled.
- validation/: independent raw-unit numerical checks, source hashes, and final review. The 63 coefficient/uncertainty checks use a separate LAPACK and pairwise-calendar calculation.
- Human_Annotation_Rater_A.csv and B.csv: blank 300-item forms, 100 per source, selected without financial outcomes. HUMAN_LABELING_GUIDE.md explains independent coding and adjudication.
- evaluate_human_annotations.py: rejects missing ratings and evaluates real completed files. It does not manufacture human labels.

Original raw filenames can reflect earlier versions. The saved manifest records current file hashes and sizes. Collection timestamps are unavailable for some earlier raw macro snapshots. Treat their retrieval cutoff as inherited project provenance, not a verified historical vintage. URLs and period columns identify series and observation periods. Do not confuse source publication dates with assumed availability columns.

The supplied PCE rate differs from the formula applied to downloaded PCE index levels. The report discloses the unresolved difference. The unreleased supplied Q3 GDP value does not enter the analysis. Missing October 2025 unemployment is not imputed. The latest nonmissing buffered value is used with its source period visible.

## Dashboard updates

Open Monitoring_Dashboard.html locally. It runs without external scripts. Model and year selectors change the view. Export/import uses Monitoring_Data.json schema_version 1. The import must contain baseline, forecasts, media, factual, events arrays, cutoff and processed strings. Forecast records require period, model, actual, predicted and preliminary. Media records use calendar month and numeric or null tone_score. Preserve nulls for missing text indices. Imported predictions are supplied values; the page recalculates score summaries but does not estimate coefficients.

For new data, append official observations and archived metadata, preserve timestamps/vintages, finalize new labels, update the explicit end date in build_inputs.py and analysis filters, then rerun. Save forecasts before outcomes. Automated collection of new data and independent human annotation are not implemented by pressing import.

## Writing preference

The user requests plain English for future work, following https://github.com/AminBlg/SimpleEnglish. Use short sentences, define technical terms, and avoid decorative language. Preserve statistical uncertainty and necessary technical definitions. This preference is recorded with the project; this file does not configure unrelated future chats.
