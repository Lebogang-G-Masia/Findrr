# Module 3: Generate Key Search Terms

## Purpose

Generate alternative job titles and related search terms for discovering appropriate employment opportunities.
Use the generalised job title produced by the Onboarding and User Profile Management Module as the primary reference.

## Generation Process

Use a generative transformer model to generate alternative job titles and search terms.
Use a dual-encoder model to evaluate the semantic similarity of generated titles against the original generalised job title.
Both models must follow the Kaggle training and server-side inference strategy.
Evaluate pretrained models and determine whether fine-tuning or another adaptation approach is necessary.
The validation process must consider:
1.  Semantic similarity to the original title.
2.  Relevance to the user's qualifications and skills.
3.  Consistency with employment preferences.
4.  Similarity to previously accepted titles.

A generated title must not be accepted merely because it is semantically similar. It must also be professionally appropriate.

## Validation and Duplicate Detection

Evaluate each generated title against an established relevance threshold.
Reject titles that fail validation.
Reject titles sufficiently similar to previously accepted titles.
Support exact and similarity-based duplicate detection.
Append accepted, unique titles to the collection available to the Find Postings Module.

## Retry and Failure Handling

Prevent infinite generation loops.
Establish:
-   Maximum generation attempts.
-   Relevance thresholds.
-   Duplicate-detection thresholds.
-   Maximum accepted titles.
-   Appropriate failure-handling procedures.

Where sufficient titles cannot be generated, stop processing, record the outcome, and provide diagnostic information.
Do not invent numerical thresholds without evaluating and documenting their suitability.

## Stored Information

For each generated title, retain:
-   Generated job title.
-   Original job title.
-   Relevance score.
-   Generation date.
-   Model name and version.
-   Validation outcome.
-   Duplicate-detection outcome.
-   Search status.

Distinguish between accepted, rejected, and pending titles where relevant.
