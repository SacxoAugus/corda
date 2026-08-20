# Contributing

The most valuable contribution is a third-party case the compiler's author
did not anticipate.

## Before submitting

1. Use only synthetic or publicly redistributable data.
2. Add input and ground truth as separate files.
3. Declare whether the case is development, validation, regression or holdout.
4. Do not adjust the ground truth after observing the result without
   recording the change.
5. Run:

   ```bash
   python3 scripts/verify_repo.py
   ```

## Claims

- A passing test demonstrates only the contract it executes.
- Review by another agent is not external audit.
- Agreement between modes sharing the same evidence is not corroboration.
- Decisions remain with the human owner.

## Licensing of contributions

Until a CLA is published, contributions are accepted only under the terms of
the Apache License 2.0 (§5): any contribution intentionally submitted for
inclusion is licensed under the same terms as the project, with the
contributor's patent grant it implies.
