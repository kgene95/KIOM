---
name: statistical-analysis
description: Design, run, review, or interpret statistical analyses for biomedical and experimental data, including assumption checks, effect sizes, confidence intervals, t-tests, ANOVA, repeated-measures and mixed models, nonparametric tests, regression, categorical outcomes, multiplicity control, and Bayesian alternatives when appropriate. Use when the statistical method or inference itself is a central task. Do not use for prospective sample-size or power calculations; use statistical-power instead.
---

# Statistical analysis

## Start with the data-generating design

Before choosing a test, identify the experimental unit, biological versus technical replicates, grouping, pairing/repeated measures, hierarchy/nesting, time structure, endpoint type, missingness, exclusions, censoring, and whether the analysis was prespecified or exploratory. Do not let spreadsheet row count substitute for biological `n`.

## Analysis workflow

1. State the estimand or scientific comparison before selecting a test.
2. Inspect data quality and distributions without using normality tests as a mechanical gate.
3. Choose a model matching design and outcome, then assess assumptions relevant to that model.
4. Report effect estimates with uncertainty; p-values are secondary to effect size and interval interpretation.
5. Address multiplicity when multiple confirmatory hypotheses or post hoc comparisons are tested.
6. Use sensitivity analyses when conclusions depend strongly on distributional assumptions, outliers, missing-data choices, or model specification.
7. Keep exploratory analyses clearly labeled and do not rewrite them as prespecified.
8. Preserve code, package versions, random seeds, exclusions, transformed variables, model formulas, and output tables when analysis is executed.

Read [method-selection.md](references/method-selection.md) for common biomedical designs and decision rules.

## Core method rules

- Two independent groups: compare the target estimand with an appropriate two-sample model; use Welch's t-test by default over equal-variance t-test unless equal variance is justified.
- Paired data: use paired analysis or a model that retains subject pairing; never analyze paired observations as independent.
- More than two groups: prefer ANOVA/regression-family models with planned contrasts over many pairwise tests.
- Repeated time points or nested measurements: use repeated-measures/mixed models or another model that represents within-unit correlation.
- Ordinal or strongly non-Gaussian outcomes: choose a model/test suited to the scale and estimand; a nonparametric test does not automatically solve dependence or heteroscedasticity.
- Binary/count outcomes: use an appropriate generalized model rather than forcing them into ordinary least squares.
- Correlation: distinguish association from agreement and from causal effect. Report scatter/data structure and avoid correlation on pooled repeated measures without accounting for subjects.

## Assumptions

Check assumptions using design knowledge, residuals, influence diagnostics, and data scale. Do not choose a test solely because Shapiro-Wilk is above or below 0.05. For small `n`, normality tests have weak power; for large `n`, trivial deviations become significant.

## Effect sizes and uncertainty

Report the effect on a scientifically interpretable scale whenever possible: mean/median difference, standardized difference, ratio, odds/risk ratio, regression coefficient, or another relevant estimand, with confidence/credible interval. Explain what the interval means without claiming that a frequentist 95% CI contains the true value with 95% probability.

## Multiplicity and transparency

Separate confirmatory primary comparisons from exploratory secondary comparisons. Use a justified family definition and correction method when multiplicity control is needed. Do not hide unadjusted exploratory analyses; label them.

## Bayesian analysis

Use Bayesian models when scientifically justified and when priors, likelihood, diagnostics, and sensitivity can be documented. Report priors and posterior uncertainty explicitly. Do not use Bayesian output as a cosmetic replacement for weak design.

## Boundaries

This skill does not invent missing raw data or reconstruct exact p-values from figures. If only summary statistics are available, restrict analysis to methods valid for those summaries and state the limitation. For prospective `n`, MDE, or power curves, use `statistical-power`.

## External design provenance

This skill was independently designed after reviewing statistical-analysis patterns in K-Dense-AI/scientific-agent-skills on 2026-10-09. Preserve design-based inference and local biomedical safeguards over generic test-selection recipes.
