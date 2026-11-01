# QUALITY AND COMPLETION CRITERIA

An implementation must not be considered complete merely because the relevant code has been generated.
A feature is complete only when:
1.  Its requirements have been analysed.
2.  Its design is consistent with the approved architecture.
3.  Its implementation satisfies approved requirements.
4.  Its acceptance criteria have been evaluated successfully.
5.  Relevant automated tests have been executed.
6.  Relevant regression tests have passed.
7.  Relevant documentation has been updated.
8.  Known limitations and unresolved defects have been documented.
9.  The implementation has been submitted through the required review process.

For machine learning functionality, additional requirements apply where relevant:
1.  The Model Specification must be documented.
2.  The Kaggle training notebook must be complete.
3.  Training and evaluation pipelines must be implemented.
4.  The model must satisfy approved evaluation criteria.
5.  The notebook must export the required artifacts.
6.  Artifact formats must be compatible with the inference implementation.
7.  The application must successfully load supplied artifacts.
8.  Inference must produce expected outputs.
9.  Inference must satisfy its acceptance criteria.

The absence of user-provided artifacts must be identified as an outstanding dependency.
Do not treat mocked inference as successful integration of a trained model.
