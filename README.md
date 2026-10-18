# Economic news and consumer sentiment

Khushi Khanna · FRE-GY 7871A · Final submission · October 18, 2026

**Question:** Does economic news add information about US consumer sentiment beyond economic conditions and previous sentiment?

The original text analysis uses **670 economic titles**: NPR 220, Colorado Sun 223, and Hacker News 227. Equal source weights produce 47 balanced media months. Timing and finalized outcomes leave 45 usable observations, with 24 initial training observations and 21 shared forecast targets. This selected corpus measures available content, not representative opinion or audience exposure.

## Final deliverables

| File | Contents |
| --- | --- |
| [Research report](company_final/Consumer_Sentiment_Report.pdf) | 12-page report with methods, results, limitations, and references |
| [Presentation](company_final/Consumer_Sentiment_Presentation.pptx) | Nine main slides plus eight appendix slides, with speaker notes |
| [Speaking script](company_final/Presentation_Speaking_Notes.pdf) | Current two-page script, approximately 850 words |
| [Dashboard](company_final/Monitoring_Dashboard.html) | Self-contained interactive HTML; download and open locally |
| [Dashboard data](company_final/Monitoring_Data.json) | Data used for dashboard export/import |
| [Annotation subset](company_final/Title_Annotations_300.csv) | 300 automated labels, also supplied as XLSX |
| [Requirements audit](working/audited_project/audit/REQUIREMENTS_AUDIT.md) | Assignment requirements and outstanding gaps |
| [Codebook](working/audited_project/audit/DIRECT_AI_CODEBOOK_V7.md) | Label definitions and boundaries |

GitHub displays the README and source code directly. Download the PPTX and HTML to use the slides and dashboard. The current speaking script is Presentation_Speaking_Notes.pdf; historical scripts and builders elsewhere in the source tree are superseded.

## Main findings

Forecast errors are RMSE in Michigan sentiment index points, on the same 21 finalized targets:

| Comparison | Without original tone | With original tone |
| --- | ---: | ---: |
| Three-indicator economic model | 12.07 | 10.82 |
| Broader economic and household controls | 5.82 | 6.06 |
| Broader controls plus previous sentiment | 3.98 | 4.32 |

The last-month benchmark gives 4.09. The narrow model's observed improvement is uncertain. The original tone measure does not improve the matched broader comparisons. A dictionary measure gives a favorable exploratory sensitivity result (3.55). Findings do not identify a causal media effect. The separate long economic baseline evaluates 81 months and must not be pooled with the 21-target text exercise.

## Reproduce the analysis

Python 3.12 was used. From the extracted repository root:

```bash
python -m venv .venv
# Activate .venv using the command appropriate for your operating system.
python -m pip install -r working/audited_project/requirements.txt
cd working/audited_project
python analyze_integrated_v7.py
python make_figures_v7.py
python audit_final.py
python prepare_review_materials.py
python company/exhibits.py
python build_company_report.py
python company/build_speaking_notes.py
python build_company_dashboard.py
```

Run commands sequentially. Numerical reproduction uses included source snapshots and frozen labels, with no network or API key. The final builders write into company_final. The speaking-script builder uses DejaVu Sans font files from /usr/share/fonts/truetype/dejavu; on other systems, update those two font paths. The PowerPoint builder, company/deck.mjs, additionally requires the OpenAI Artifact Tool runtime and finalization helpers. See company/README.md for those dependencies. Editing the distributed PPTX in PowerPoint does not require that runtime.

## Sources and evidence

working/audited_project/data contains the supplied workbook and downloaded economic and archive snapshots. outputs/coded_corpus.csv contains all retained titles, source identifiers, dates, URLs and calculated text fields. outputs includes monthly measures, individual predictions, coefficients, diagnostics, uncertainty and robustness tables. audit contains the original assignment, requirements audit, design critique/freeze, collection and labeling history. validation contains independent numerical checks. FILE_MANIFEST.csv records source file sizes and hashes.

Michigan sentiment is the survey outcome. BLS and BEA economic series are supplied through official/FRED snapshots. The published San Francisco Fed news index is a benchmark, separate from the original title measure. Original labels, supplied data, downloaded sources and calculated outputs are distinguished in the report and source documentation. Third-party material retains its original ownership; this repository does not grant a new license over source articles or supplied course materials.

## Material limitations

The required two independent human annotations of 300 titles remain incomplete. Blank rater forms and a labeling guide are supplied, but the automated subset does not fulfill that requirement. Independent label accuracy remains unverified. The analysis uses revised historical inputs with assumed availability buffers, rather than a historical-vintage real-time backtest. Sparse selected coverage, small monthly samples and previously inspected evaluation dates limit inference. The report discloses these issues. The package is the final available submission, with these requirements visibly outstanding.

## Upload to GitHub

Extract the ZIP and upload its **contents**, retaining this README at the repository root. Do not upload only the ZIP. For a new empty GitHub repository, the equivalent local commands are:

```bash
git init
git add .
git commit -m "Add final consumer sentiment analysis and submission"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace YOUR_REPOSITORY_URL with the destination repository URL. If that repository already contains files, clone it first and copy this package into the clone instead of initializing a separate history.
