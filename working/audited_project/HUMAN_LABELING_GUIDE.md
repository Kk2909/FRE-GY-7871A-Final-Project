# Independent human validation

The professor requires at least 300 items with two independent human annotators. No human labels are completed in this package. Do not describe AI labels or completed templates as human work.

## Procedure

Give Human_Annotation_Rater_A.csv and Human_Annotation_Rater_B.csv to two different humans. Each person labels all 300 items without consulting the other person or AI predictions. Keep the sealed mapping hidden during initial tone/framing coding. Preserve each rater's unchanged file and actual rater ID. Keep personal information out of submitted IDs.

Use -1 for an explicit adverse economic direction, 0 for mixed/no clear direction, and +1 for an explicit favorable direction. Label what the title asserts, not whether its assertion is true. Job growth with rising unemployment is mixed unless one direction clearly dominates. Policy announcements without a stated economic welfare consequence are neutral. A negative factual report is still negative tone, not automatically bias.

Record these dimensions separately:

| Field | Allowed values / rule |
|---|---|
| relevant_US | yes / no / uncertain. Title or context must concern US economic conditions or US households. |
| tone | -1 / 0 / +1. Do not substitute an opinion about the publisher. |
| emotional_wording | yes / no / uncertain. Identify affective/intensifying wording in evidence. |
| topics | Separate with semicolons: prices; labor; housing; growth; debt; policy; other. Multiple topics allowed. |
| price_frame | level / rate / both / neither / uncertain. Level describes cumulative/remaining expense, rate describes change speed. |
| time_frame | current / forecast / both / unspecified. |
| political_actor | Named actor or none. Preserve the exact wording. |
| attribution | credit / blame / mention_only / none / mixed. Mention alone does not assign credit or blame. |
| numeric_claim | Copy the narrow numerical clause or none. |
| factual_status | not_checked / supported / contradicted / ambiguous_unit / unverifiable. |
| evidence | Quote the short title phrase that determines the label. After factual review, add benchmark URL/date/definition. |
| rater_id | Actual anonymous human identifier, constant within each file and different across raters. |

After the blinded semantic stage, provide dates, links and source metadata from the sealed mapping joined to outputs/coded_corpus.csv. For numerical claims, identify the official release available on that publication date. Match observation period, geography, adjustment, units, annualization and estimate vintage. Do not use today's revised number as the original truth. A correct number without a necessary unit can remain ambiguous. Do not score an entire article from its title alone.

Calculate agreement before adjudication. Then discuss disagreements under the codebook, preserving both original labels. Record the reason and final label in a separate adjudicated file with item_id and tone. A third reviewer is preferable for unresolved cases. Do not silently replace one rater's work with the other rater's labels.

Run:

    python evaluate_human_annotations.py completed_A.csv completed_B.csv adjudicated.csv

The evaluator rejects blank/invalid tone labels and identical rater IDs. It calculates tone agreement, Cohen's kappa and AI classification precision/recall/F1 by class and source. Those checks cannot prove that the humans worked independently. Document independence separately. Use a similar dimension-specific evaluation for the other coded categories before treating those categories as validated measures.

If human evaluation exposes material errors, review the measurement and rerun the monthly indices, regressions, report and slides. Keep that revision exploratory and record every change. Do not report the current forecasts as human-validated before this work is complete.
