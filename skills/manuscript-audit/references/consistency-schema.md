# Consistency manifest

Create a UTF-8 CSV named `consistency_manifest.csv` with these columns:

`section,item,value,source_location,notes`

Use one row for each repeated factual item. Typical items include:
- animal strain, sex, age;
- group name;
- biological n;
- dose or concentration;
- route and frequency;
- treatment duration;
- induction concentration/duration;
- time point;
- assay name;
- unit;
- statistical test;
- figure/table number.

Normalize trivial formatting differences before entry when they are scientifically equivalent, but do not normalize away meaningful differences. Then run:

`python scripts/check_consistency.py consistency_manifest.csv`

Any conflicting values for the same item are review flags, not automatic proof that one value is wrong.
