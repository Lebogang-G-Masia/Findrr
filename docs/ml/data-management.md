# Machine Learning Data Management

Manage training datasets separately from operational application data.
For each model, identify and document:

-   Dataset sources.
-   Dataset versions.
-   Data formats.
-   Preprocessing.
-   Data cleaning.
-   Feature engineering, where applicable.
-   Training, validation, and test splits.
-   Data leakage prevention.
-   Labelling procedures, where applicable.
-   Data licensing.
-   Privacy considerations.

Training datasets must not automatically contain real users' personal information.
Any use of personal or sensitive information for model training must be specifically evaluated, authorised, and approved.
Prefer appropriate public, synthetic, anonymised, or otherwise authorised datasets.
The inference server must not require training datasets to be present unless an explicitly documented runtime requirement makes them necessary.
