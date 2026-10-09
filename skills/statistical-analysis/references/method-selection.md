# Biomedical statistical method selection

| Design / outcome | Common primary route | Key checks |
|---|---|---|
| 2 independent continuous groups | Welch t-test or regression | independence, influential points, estimand |
| paired continuous data | paired t-test or paired regression | correct pairing, difference distribution |
| >=3 independent groups | linear model / ANOVA with contrasts | variance structure, multiplicity |
| repeated measures / longitudinal | mixed-effects or GEE-style model | subject clustering, time structure, missingness |
| ordinal outcome | ordinal model or rank-based method | scale interpretation, ties, dependence |
| binary outcome | logistic/binomial model | events per parameter, separation, effect scale |
| count outcome | Poisson/negative-binomial model | overdispersion, exposure offset |
| continuous predictor-response | regression | functional form, residuals, leverage |
| survival/time-to-event | dedicated survival method | censoring assumptions, proportional hazards when used |

Use this table as routing guidance, not an automatic test selector. The experimental design and scientific estimand control the final choice.
