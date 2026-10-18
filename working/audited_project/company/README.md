# Company-style research presentation

This edition changes communication and visual design, not statistical specifications or results. The independent raw-input/prediction audit passes. Evidence.json is generated from the frozen output tables by exhibits.py. The report and slides share those numbers.

The report contains 12 pages. Slides 1-9 form the main presentation, with slides 10-17 for questions. The current two-page speaking notes contain approximately 850 words for a 5-7 minute talk. The current deck connects the original text index, classifier transfer, source vocabulary findings and economic baseline to the model comparisons.

The main model is multiple linear regression with eight separate predictors and an intercept. The dynamic version adds prior sentiment. The 21-target media experiment is separate from the 81-target long economic exercise.

Research limitations remain unchanged: independent human validation is incomplete, historical vintages are unverified, the media corpus is sparse/selected, and the evaluation period was previously inspected. Better formatting does not resolve those limits. The classmate dashboard could not be read from a Windows-local URL. No peer data, labels, code or results enter this submission.

Rebuild from the extracted working/audited_project folder:

    python analyze_integrated_v7.py
    python make_figures_v7.py
    python audit_final.py
    python company/exhibits.py
    python build_company_report.py
    python company/build_speaking_notes.py
    python build_company_dashboard.py

Outputs go to the extracted company_final folder. The dashboard builder reads the original HTML under working/final_audited and changes its layout while preserving data and interaction logic. Those originals are included to support the build. Files under audit/ retain earlier evidence. Do not use legacy report/deck builders for this company edition.

The editable deck builder, company/deck.mjs, requires the OpenAI primary Artifact Tool runtime and its finalization helpers. Set PROJECT_WORKSPACE to the extracted root directory, link node_modules in this company folder to the runtime node modules, and run in a fresh workspace with a new final output path. These runtime dependencies are not needed to reproduce the analysis or PDFs.

company/results_script.json is the authoritative current nine-slide script. Older notes and deck builders remain as historical source evidence and are superseded. The numerical workflow starts from frozen automated labels, not independently verified human annotations.
