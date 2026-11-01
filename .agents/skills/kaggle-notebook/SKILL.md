---
name: kaggle-notebook
description: Use whenever creating, editing, or reviewing a Kaggle training or fine-tuning notebook, or defining model artifacts and the manifest that the notebook must export.
---

# Kaggle Model Training & Evaluation

Manage the end-to-end lifecycle of machine learning model specifications, Kaggle training notebooks, evaluation metrics, and artifact export procedures for Findrr.

## When to Use

* When identifying, specifying, or selecting model architectures, pretrained options, and training strategies (scratch, fine-tuning, adaptation).
* When creating or updating complete, executable Jupyter notebooks for Kaggle.
* When designing and implementing rigorous evaluation procedures, metric selection, and acceptance criteria verification.
* When documenting reproducibility parameters, dependencies, datasets, and artifact transfer workflows.

## Core Responsibilities & Workflow

1. **Model Specification & Selection:**
   * Identify required machine learning models and establish their purpose and expected behavior.
   * Evaluate appropriate architectures and pretrained models, deciding between training from scratch, fine-tuning, or adaptation.

2. **Kaggle Notebook Development:**
   * Create self-contained, complete Jupyter notebooks designed for Kaggle execution.
   * Ensure notebooks include:
     * Clear explanations of purpose, model, and training task.
     * Required datasets and instructions for attaching them in Kaggle.
     * Dependency specifications and installation commands.
     * Data preprocessing and rigorous procedures to prevent data leakage between train, validation, and test splits.
     * Training/fine-tuning implementation and evaluation procedures.
     * Artifact export steps, descriptions of generated files, and instructions for downloading and transferring artifacts to Findrr's server.

3. **Rigorous Model Evaluation:**
   * Select task-appropriate metrics (e.g., Precision, Recall, F1-score, Accuracy, ROC-AUC, Semantic similarity, Ranking metrics).
   * Verify whether trained models satisfy their approved acceptance criteria before integration.
   * **Important:** Never assume a model is suitable or trained merely because code execution completed successfully.

4. **Reproducibility & Documentation:**
   * Document methodology, configurations, and environment details.
   * Record reproducibility parameters: random seeds, dataset versions, base model versions, training/hyperparameters, dependency versions, training duration, hardware configurations, evaluation metrics, and artifact versions.

## Execution Constraints & Rules

* **Manual Execution Workflow:** The user manually transfers notebooks to Kaggle, executes training/fine-tuning, and retrieves artifacts. Do not assume personal access to execute training on Kaggle or local laptop files.
* **Truthfulness on Training Status:** Never claim a model has been trained successfully unless the user has executed the notebook and supplied the resulting artifacts or explicit evidence of successful training.
* **Security:** Never include private credentials or secrets in notebooks.
* **Evaluation policy:** All model evaluation must follow `docs/ml/evaluation-policy.md`. Select metrics appropriate to each model's purpose; verify acceptance criteria are met before considering a model ready for integration; prevent data leakage between train, validation, and test splits.
* **Data management:** Dataset sourcing, labelling, splits, privacy and versioning follow `docs/ml/data-management.md`. Read it before specifying or attaching any dataset.
* **Kaggle-appropriate paths and dependencies:** Use paths, configurations and dependencies that work in Kaggle (for example `/kaggle/input/...` and `/kaggle/working/...`). Never reference files on the user's local laptop or assume access to them.
* **Run start to end:** Where practical, notebooks must run from beginning to end without manual intervention. The only exceptions are necessary dataset configuration and explicitly documented inputs. The notebook must be complete enough for the user to run it without further development work in Kaggle.
* **No claim of identical results:** Do not claim identical results across training runs unless the implementation and environment support that guarantee (fixed seeds, pinned dependencies and deterministic settings). Otherwise report expected variation.
* **Resource limits:** Evaluate each model choice against the compute available for training (Kaggle) and for inference (the Findrr server). If a proposed model cannot reasonably be trained or fine-tuned within Kaggle's available resources, identify the limitation and present an alternative for the user's approval. Do not move training to another service.
* **Prefer fine-tuning:** Do not assume training from scratch is needed when fine-tuning an existing model would be more appropriate. Do not assume a pretrained model is suitable without evaluating it.
* **Notebook and inference compatibility:** Keep the notebook's preprocessing, tokenizers, label mappings and artifact formats compatible with the inference implementation (`model-inference` skill). Document all model dependencies and runtime requirements.
