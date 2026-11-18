# EPSA-MRS field evidence notes

This document maps the thirteen top-level declaration fields to the measurement observations that motivated them. It is a public summary. Detailed derivations and raw sidecars are in the Zenodo deposit: `doi:10.5281/zenodo.24036122`.

| Field group | Required content | Observation that motivated it |
|---|---|---|
| M1 engine | name, version, commit or release | Identical boxes produced AP differences of 2.7e-3 and 1.4e-3 between the project engine and the framework validation path. The implementation must be named. |
| M2 max_det | evaluation value, unit, export value | Two meanings of the candidate budget produced a 0.0093 AP difference on AI-TOD. The export-side cap also bounds the measurable window. |
| M2c export cap | cap share and sensitivity | Holding the stated protocol fixed and changing the export cap moved AP by +0.002098/+0.001634 on VisDrone and +0.000424/+0.000642 on AI-TOD. |
| M3 protocol | expanded IoU list and named matcher | Writing a range instead of an expanded list does not identify the evaluation grid. |
| M4 integration | interpolation rule and recall-beyond-max rule | The choice of zero-fill versus last-value fill moved AP by about 0.05 on small objects. |
| M5 aggregation | named mode and per-class ground-truth counts | Macro and ground-truth-weighted aggregation moved AP by +0.0736 on VisDrone and +0.0656 on AI-TOD. |
| M6 area tiers | tier definition and thresholds | Absolute-pixel and relative-area definitions do not identify the same object set. |
| M6b tier details | size measure, boundary rule, filter scope | Literal published tier definitions admitted thirteen readings; APvt varied by up to 0.082. |
| M7 predictions | confidence threshold, source path, source detail | Validation and prediction paths produced model-dependent shifts up to 1.28e-2 under the same weights. |
| M8 tie-break | named rule | About 35% of detections shared a score with their successor in a sampled curve, so order is part of the measurement. |
| M9 join | image counts, joined-image counts, zero-detection handling | A join-key coercion dropped 41 images and 971 ground-truth objects on AI-TOD and inflated AP by 0.0028--0.0034. |
| M10 uncertainty | resampling unit, cluster definition, resamples | Image-level and video-segment bootstrap changed standard errors by 1.08--1.97 times. |
| M11 claims | claim kind label | Pooling unlike estimator configurations produced a spurious second-ranked risk factor. |
| M12 ratios | numerator, denominator, interval, denominator sign | A published ratio claim was withdrawn because its denominator interval covered zero. |
| M13 seed dispersion | seed count, pooled sd, interval, cell count | Pooled seed sd was 0.001215 on VisDrone and 0.001715 on AI-TOD; single-seed spread cannot support 1e-3-level claims. |

The validator reports PASS, WARN or FAIL for each required field. A complete declaration is not automatically sufficient for every downstream use; EPSA-MRS checks completeness under this profile, not the truthfulness of declared values.
