# Release Deployment

Reference for releasing completed increments. Used at release time, not during routine iterations. Versioning rules are in `docs/process/versioning.md`.

## Objective

Make completed software increments available to their intended users in a controlled and reliable manner.

## Activities

You must:

- Prepare and validate the release candidate.
- Configure the target environment.
- Deploy application components.
- Perform database migrations where necessary.
- Deploy required model artifacts.
- Configure the application to load the appropriate model versions.
- Verify model loading and inference.
- Verify deployment success.
- Establish monitoring and logging.
- Establish backup and recovery mechanisms where required.
- Document operational procedures.
- Record release changes.
- Collect relevant feedback.

Deployment may occur after individual iterations or after several increments have been grouped into a release.

The model deployment procedure must not require Kaggle to remain available.

## Primary Deliverable

A **Deployed Software Increment**, supported by:

- Release notes.
- Deployment documentation.
- Model deployment documentation.
- Configuration documentation.
- Operational procedures.
- Verification and test results.

---

## Release checklist

Complete every item, and verify it, before declaring a release done. Do not claim a deployment, migration, or model load succeeded without evidence.

### Before release

- [ ] All included increments satisfy their acceptance criteria.
- [ ] Automated and regression tests pass; results recorded in the test report.
- [ ] Known limitations and unresolved defects documented.
- [ ] Documentation reviewed and up to date.
- [ ] Release version chosen per SemVer (`vMAJOR.MINOR.PATCH`); milestone is not the version.
- [ ] Release scope approved by the user.

### Environment and deployment

- [ ] Target environment configured. (Do not assume server specs, networking, or deployment configuration; take them from the user's documentation.)
- [ ] Configuration documented; no secrets committed.
- [ ] Application components deployed.
- [ ] Database migrations performed and verified, with a backup taken first where required.
- [ ] Deployment success verified.

### Models

- [ ] Required model artifacts supplied by the user and placed in the configured model-artifact location (not committed to Git).
- [ ] Artifact integrity verified (checksums or equivalent).
- [ ] Application configured to load the intended model versions.
- [ ] Model loading verified.
- [ ] Inference verified with the real artifacts, not mocks. If only mocked inference was tested, record the model integration as **unverified**.
- [ ] Model deployment documented, and confirmed not to require Kaggle.

### Operations

- [ ] Monitoring and logging established.
- [ ] Backup and recovery mechanisms established where required.
- [ ] Operational procedures documented.

### After release

- [ ] Release notes written (changes, model versions, migrations, configuration changes, known issues).
- [ ] Release tagged in Git.
- [ ] Feedback collected and recorded for the next iteration's planning.
- [ ] `docs/STATUS.md` and the product backlog updated.

---

## Release notes template

Store as `docs/releases/vX.Y.Z.md`.

```markdown
# Release vX.Y.Z

- **Date:** YYYY-MM-DD
- **Milestone:** <current milestone>
- **Pre-release:** yes / no

## Summary
## Requirements addressed
<FR / NFR / ML IDs>

## Changes
## Model versions
<model name, version, verification status: real inference verified / mocked only>

## Database migrations and configuration changes
## Known issues and limitations
## Deployment and rollback notes
## Test results
<link to test report>
```
