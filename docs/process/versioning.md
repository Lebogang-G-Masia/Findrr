# Software Versioning

The project must use Semantic Versioning.

Software releases must follow:

`vMAJOR.MINOR.PATCH`

The version components represent:

-   **MAJOR:** Incompatible changes that are not backward-compatible with previous releases.
    
-   **MINOR:** New functionality introduced in a backward-compatible manner.
    
-   **PATCH:** Backward-compatible bug fixes, security patches, and maintenance changes.
    

Development milestones must not be confused with software release versions.

The actual release number must reflect the nature of the changes introduced.

The project plan must establish the initial release strategy, including pre-release versioning where appropriate.

Each release must have corresponding release notes.

Model versions must also be tracked independently from application software versions.

Any change to a trained model, model architecture, training dataset, tokenizer, preprocessing pipeline, or model configuration must be appropriately documented and versioned.

The application must be able to identify which model version it is loading.
