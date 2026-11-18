# EPSA-MRS v1.0.0

EPSA-MRS (Evaluation Protocol and Sensitivity Audit — Minimum Reporting Standard) is a machine-checkable reporting profile and validator for object-detection evaluation protocols. It checks whether a declaration contains the fields needed to recompute a reported average precision (AP) value.

## Purpose

A reported AP depends on evaluation conventions that are often omitted: engine identity, candidate budget and its unit, IoU threshold list, AP integration rule, class aggregation, area-tier definition, prediction source, tie-breaking, image joining, uncertainty unit, claim type, ratio statistics and seed dispersion. EPSA-MRS turns these into a JSON declaration and a deterministic validator.

The software does not propose a new AP definition and does not claim that using the profile improves detector accuracy. Its purpose is to make protocol differences visible before AP numbers are compared.

## Installation

Python 3.12 is recommended. From a clone of this repository:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows Git Bash: source .venv/Scripts/activate
pip install -e .
```

Core dependencies are `numpy` and `pycocotools`. The validator itself does not require a GPU.

## Usage

Validate a declaration:

```bash
python src/epsa_check.py examples/declaration_epsa_own_visdrone.json --strict --json
```

Verify the instrument with injected-defect fixtures:

```bash
python src/epsa_check.py --selftest
```

The self-test fixtures are generated inside `src/epsa_check.py`. Each intentionally broken declaration must light exactly one intended check; a fixture that lights no check or multiple checks is a validator defect, not a declaration defect.

## Repository layout

- `src/` — source code, including `epsa_check.py`
- `examples/` — declaration files for two illustrative benchmarks and a seven-paper motivation pilot
- `results/e7_check/` — measured join-effect sidecar read by the validator
- `docs/` — schema notes and field-to-evidence mapping

## Declaration fields

The profile contains thirteen field groups, M1–M13. Each group is justified by an independently measured protocol effect; the mapping is documented in `docs/field_evidence.md`. A field missing from a declaration is reported as FAIL or WARN depending on whether it is unconditional or conditional on the reported layer.

## Verification

See `TESTING.md` for the self-test command and the expected WARN in the example declaration.

## Data and reproducibility

Example declarations and metadata sidecars are archived at Zenodo: `doi:10.5281/zenodo.24036122`. Large prediction files are not redistributed; their generating scripts and metadata sidecars are included so that the examples can be regenerated locally.

## Known limitations

- EPSA-MRS checks declaration completeness and consistency; it does not verify that the declared numbers are truthful.
- External behavioural effects (downloads, independent adoption, error-rate reduction) have not been measured.
- The current field set was developed on aerial small-object benchmarks; other domains may require additions.

## License

Apache License 2.0. See `LICENSE.txt` and `Licence.txt`.

## Contact

[To be completed by the corresponding author before submission.]
