---
name: statistical-power
description: Plan prospective sample size, statistical power, minimum detectable effect, precision, attrition allowance, and power curves for biomedical, cell, animal, and experimental studies. Use when the user asks how many biological replicates or animals are needed, whether a design is adequately powered, what effect can be detected, or how assumptions change required n. Keep prospective planning separate from post hoc observed-power claims.
---

# Statistical power

## Principle

Base sample-size planning on the intended primary analysis and experimental unit. Power calculations do not rescue an ambiguous primary endpoint, pseudoreplication, or an unrealistic effect-size assumption.

## Workflow

1. Define the primary endpoint, scientific contrast, experimental unit, groups, allocation ratio, sidedness, alpha, target power, and intended statistical model/test.
2. Obtain the effect-size assumption from the strongest defensible source: pilot data with uncertainty, prior comparable experiments, meta-analytic evidence, or a scientifically meaningful minimum effect. Do not default to a conventional small/medium/large effect when a domain-specific effect is available.
3. Specify variability/correlation assumptions on the analysis scale: SD, event rate, within-subject correlation, intraclass correlation, or other parameters required by the planned model.
4. Calculate required analyzable `n` per group or total `n`. Then apply attrition/non-evaluable allowance separately and round according to the randomization structure.
5. Run sensitivity scenarios over plausible effect sizes and variability. Prefer a power curve or `n` table over one falsely precise number when assumptions are uncertain.
6. Record formulas/software/version and every assumption so the calculation can be reproduced.
7. Recalculate if the primary endpoint, analysis model, number of groups, allocation, or multiplicity plan changes.

Read [planning-rules.md](references/planning-rules.md) for animal/cell experiments, repeated measures, pilot studies, and MDE reporting.

## Biological versus technical replication

Power normally concerns independent biological experimental units. Technical replicates improve measurement precision but do not increase biological `n` unless they are independently randomized biological units. For animal experiments, the animal is usually the experimental unit unless treatment is randomized at a different level.

## Attrition

Calculate the analyzable sample size first. Inflate for expected attrition or unusable samples using a transparent rule such as `n_enroll = ceil(n_analyzable / (1 - attrition_fraction))`. Do not reduce the analyzable target after losses simply because the study has already started.

## Minimum detectable effect

When the available sample size is fixed, report the MDE under the stated alpha, power, allocation, variability, and model. MDE is often more informative than retrospective “observed power.”

## Post hoc power

Do not use power computed from the observed effect as an explanation for a nonsignificant result; it is largely a transformation of the p-value and adds little. Report the observed effect and confidence interval instead. Use prospective assumptions or MDE for planning future work.

## Small pilot studies

Treat SD or effect-size estimates from very small pilots as highly uncertain. Show sensitivity across plausible values and avoid claiming that one pilot-derived `n` is definitive. When feasible, use prior external evidence or blinded/internal pilot variance updating with a prespecified rule.

## Clustered and repeated designs

Account for pairing, repeated measurements, litter/cage/batch clustering, multiple lesions per animal, or other hierarchy in the planned analysis and power model. A simple independent-samples formula is invalid when effective sample size is reduced by correlation.

## Outputs

Return the assumed effect and variability, alpha, power, sidedness, allocation, base analyzable `n`, attrition-adjusted `n`, sensitivity scenarios, and a short statement of what would make the estimate invalid. Distinguish exact software output from rough planning approximations.

## External design provenance

This skill was independently designed after reviewing statistical-power patterns in K-Dense-AI/scientific-agent-skills on 2026-10-09.
