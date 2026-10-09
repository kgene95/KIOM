# Power-planning rules for experimental biomedicine

## Animal studies

Define the randomized experimental unit explicitly. If animals are housed, treated, or randomized by cage/litter, account for clustering when it affects independence. Base `n` on the primary endpoint rather than trying to power every secondary marker simultaneously.

## Cell experiments

Distinguish independent biological experiments/cultures from wells or repeated measurements within one experiment. Technical wells are subsamples. Plan biological replicate count around the primary biological comparison.

## Repeated measures

Use the planned within-unit correlation and covariance structure or a justified approximation. Repeated measurements can improve precision, but only if the analysis model uses the correlation correctly.

## Multiple groups

If the primary claim is an omnibus group effect, power that test. If the primary claim is one or more specific contrasts, power those contrasts and account for multiplicity when confirmatory.

## Reporting

State where effect-size and variance assumptions came from. Provide at least one sensitivity scenario when assumptions are uncertain. Avoid wording such as “G*Power determined n=8” without the input parameters and effect definition.
