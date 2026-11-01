---
name: new-ml-model
description: Use whenever the application needs a new or changed ML model, to run the lifecycle from model specification through Kaggle training to verified server inference.
---

# Kaggle-to-Server Model Workflow & Iterative Development

Govern the end-to-end development, manual training, artifact transfer, and server-side inference integration for every machine learning model required across Findrr's iterative milestones.

## When to Use

* Following initial planning, requirements analysis, system design, and approval gates (`/bootstrap-1-environment` to `/bootstrap-5-design`).
* When beginning implementation across the five development milestones according to the prioritized product backlog.
* Whenever a machine learning model is required during feature development.
* When developing Kaggle training notebooks, documenting training instructions, and implementing compatible server-side inference pipelines (Module 9).
* When testing model integration with mocks/stubs and verifying actual artifacts once supplied by the user.

---

## 1. 14-Step Kaggle-to-Server Model Lifecycle

For every model requiring training or fine-tuning, you must follow this exact sequence:

1. **Identify Requirement:** Identify the model requirement in the application's specification.
2. **Define Behavior:** Define the model's purpose, inputs, outputs, and expected behavior.
3. **Design Training Approach:** Design the model-training approach (scratch, fine-tuning, or adaptation).
4. **Develop Notebook:** Develop the required Kaggle training notebook.
5. **Store in Repository:** Store the notebook in the project repository.
6. **Document Execution:** Document datasets, configurations, dependencies, and execution instructions.
7. **Manual Transfer:** User manually transfers the notebook to Kaggle.
8. **Manual Execution:** User executes the notebook and trains or fine-tunes the model.
9. **Model Evaluation:** The notebook evaluates the trained model against acceptance criteria.
10. **Export Artifacts:** The notebook exports the required model artifacts.
11. **Artifact Retrieval:** User retrieves resulting artifacts from Kaggle.
12. **Storage Placement:** User provides or places artifacts in the designated server model storage location.
13. **Server Loading:** The Findrr application loads the supplied artifacts (with SHA-256 integrity verification).
14. **Inference Execution:** Relevant application modules use the loaded models for inference (Module 9).

* **Compatibility Responsibility:** You are strictly responsible for ensuring that the training notebook and application inference implementation are mutually compatible (preprocessing parity).

---

## 2. Beginning Iterative Development

Once initial planning, requirements, and design activities have been completed and approved:

* **Incremental Delivery:** Begin implementation according to the prioritized product backlog, working through the five development milestones incrementally while following all mandatory workflow constraints.
* **ML Development Protocol:** Whenever an ML model is required:
  1. Develop its Kaggle training notebook.
  2. Document how the user should train it.
  3. Implement compatible application-side inference functionality (Module 9).
  4. Test integration using controlled mocks/stubs where necessary.
  5. Wait for the user to provide the trained artifacts.
  6. Verify actual model integration once artifacts are supplied.
