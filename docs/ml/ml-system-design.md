# Machine Learning System Design

The architecture must explicitly distinguish between the training and inference environments.
- **Training environment:** Kaggle.
- **Inference environment:** The server hosting Findrr.

The environments must be independent but compatible.
The design must establish:
-   Model architectures.
-   Training and fine-tuning approaches.
-   Dataset requirements.
-   Training and evaluation procedures.
-   Model artifact formats.
-   Required tokenizers and preprocessing artifacts.
-   Model configurations.
-   Model versioning.
-   Artifact storage and transfer.
-   Inference interfaces.
-   Runtime dependencies.
-   Computational requirements.
-   Model loading and failure-handling procedures.

The application must not depend on Kaggle being available during normal operation.
