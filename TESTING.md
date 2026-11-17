# Verification

Run from the repository root with Python 3.12.

## Validator self-test

```bash
python src/epsa_check.py --selftest
```

Expected: PASS. Each injected-defect fixture must light exactly the intended check. A fixture that lights no check or more than one check is a validator defect.

## Example declaration

```bash
python src/epsa_check.py examples/declaration_epsa_own_visdrone.json
```

Expected at v1.0.0: 19 checks, FAIL 0, WARN 1. The warning is deliberate: it marks a ratio claim whose denominator confidence interval covered zero, so the ratio has no usable interval. It is retained as an example of honest disclosure, not removed to make the output look clean.

Expected at v1.0.0 for `examples/declaration_epsa_own_aitod.json`: the same rule applies; read the printed report rather than assuming all green.

## Repository hygiene

The published repository must contain only code, declarations, documentation and license files. Do not add local environment files, SSH keys, personal correspondence, preprint cover letters, manuscript PDFs containing author identities, or the parent project history.
