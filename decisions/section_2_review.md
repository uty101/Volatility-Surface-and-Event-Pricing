# Decisions from the Section 2 review (instruction 03, part A)

One line per item: the option chosen and the reviewer's reason. Options are as written in `decisions/OPEN.md`.

- **O-29** (a). `ok`, `american_fail`, `european_fail`, `both_fail`; on any failure both vols and the premium are blank. No reason given.
- **O-30** (a). The `book_greeks` total row carries `expiry = total` and follows that underlying's expiry rows. No reason given.
- **Status 5** (small interpretations). All accepted.
- **Status 4** (negative premiums from the tree). A real flaw, caused by the reviewer's spec: a 200-step tree IV against a closed-form BSM IV mixes the early exercise premium with the tree's discretisation error (up to 0.07 vol points on 3 SPY puts). Fixed in instruction 03 step 3.0, where the European IV is solved on CRR European at `n_prod`.
- **Status 3** (SPY sanity check). Composition, not an error: the SPY ITM put bins mix very different expiries, and the deep ITM call values come from rows with almost no vega. Instruction 03 step 3.0 blanks those rows (`low_vega`).
