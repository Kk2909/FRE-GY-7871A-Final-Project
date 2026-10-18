# Design freeze: audited final study
Date: 2026-10-17. Earlier evaluation years and v7 results were already inspected. This is an exploratory correction and reproduction, not preregistration or untouched confirmation.

Primary question: Does the original title-tone index add predictive information about Michigan consumer sentiment beyond economic conditions, household pressures, era indicators and prior sentiment?

Primary data: supplied Michigan headline index; raw UNRATE, PCEPI, real GDP quarterly annualized growth, real disposable income; frozen 670 in-scope titles, with all 691 original review decisions preserved. No new outcomes guide labels or inclusion. National NPR, state Colorado Sun and social Hacker News remain fixed. At least three titles per source/month, equal source weights. No missing media interpolation.

Outcome frequency: calendar month. Monthly macro values enter after a 45-day period-end buffer; GDP after 35 days. These are availability assumptions applied to revised snapshots. Do not call this a historical-vintage or real-time forecast. Use media from two calendar months before target at first-of-month origin. Exclude preliminary October from scoring. Rebuild input panel from raw sources instead of using an undocumented intermediate CSV.

M1: unemployment + 12-month PCE inflation + quarterly annualized GDP.
M2: M1 + original direct-AI tone.
M3: M2 + 36-month accumulated PCE prices + annual real-income growth + Democratic-presidency indicator + July-2024 web-era indicator.
Controls-only: M3 without tone. Dynamic pair: add previous calendar-month sentiment to controls-only and M3. Benchmarks: last month unchanged and estimated AR(1). All slopes enter separately with an intercept. No composite factors or tuning.

Use the same complete media-aligned calendar observations for all primary models. Initial training: first 24 finalized observations, then expanding fits. Report sample gaps, parameter count, matrix rank, raw-unit coefficients, calendar-HAC(6) uncertainty, VIF, residual serial correlation, influential observations and coefficient stability. Approximate nominal 90% prediction intervals: Student-t OLS initially, then past-error calibration after 12 evaluated outcomes. No guaranteed coverage under temporal dependence.

Primary forecast metrics: RMSE and MAE on identical finalized target dates. Fixed six paired comparisons as in v7, calendar block bootstrap intervals and Holm correction for approximate HAC loss tests. Inference is exploratory and fragile on roughly 21 targets. Do not declare superiority solely from a p-value or bootstrap endpoint.

Secondary checks fixed now: dictionary and raw NLI measurements, leave-one-source-out tone, three-month media lag, annual seasonal harmonics, first differences on consecutive calendar months, separate Conditions/Expectations, coarse era controls and source composition. Do not promote a favorable alternative after observing it. Lag-one media is not an admissible month-start forecast under the seven-day buffer and is excluded from primary claims.

Gap: observed headline minus expanding economics-only prediction trained on earlier outcomes from 2010. Gap/tone correlations are descriptive. No causal residual-explained share. Generated-gap uncertainty and common omitted causes prevent causal attribution.

Three competing explanations: household experience, media information/framing, model/survey timing. A surviving controlled news association supports only incremental association. The absence of exposure data precludes causal attribution. Text cannot establish reader anchoring, availability or confirmation bias. Matched-release cases assess title wording/units, not corpus-wide bias prevalence.

Known mandatory gaps: no two independent human annotators, no verified historical vintages. Prepare blinded 300-item human annotation forms and evaluator. Do not fill human columns. Direct AI name/source counterfactual audit will be explicitly labeled same-assistant illustrative consistency, not independent accuracy.
