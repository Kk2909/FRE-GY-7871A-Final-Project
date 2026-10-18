# 300-title annotation export

One automated label set covering the exact 300 task titles. Tone labels are retained from the frozen source corpus. Literal rules supply wording proxies. Factual status remains not_checked. The export supplies no independent human validation or inter-rater reliability. Main model results are unchanged. Full field definitions appear in the workbook Method sheet.

Rebuild from project root: python working/audited_project/company/prepare_title_labels.py, then run company/title_labels.mjs using the primary Artifact Tool Node runtime. The Excel builder uses the intermediate work/title_annotations_payload.json and writes to company_final.
