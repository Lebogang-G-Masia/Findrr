# Roadmap

The project will progress through five major development milestones.
These milestones represent the intended evolution of the application. They must not be confused with individual software releases or development iterations.

## Milestone 1: Core Application Functionality

The primary objective is to establish a functional baseline of Findrr.
The application must use a Command-Line Interface (CLI) during this milestone.
The implementation should establish the essential functionality required to achieve the application's primary objectives.
This includes the relevant core workflows for:
-   Gathering and processing user information.
-   Creating a structured User Profile.
-   Generating relevant job-search titles.
-   Searching for employment opportunities.
-   Extracting and storing job-posting information.
-   Preparing basic application materials where included in the approved core scope.

The application and supporting infrastructure must run locally on the user's laptop.
The user's laptop will act as the application server for model inference.
Any machine learning models required by the approved scope must follow the Kaggle training and server-side inference strategy.
The relevant Kaggle notebooks must be developed and documented.
This milestone is complete only when the approved core functionality has been implemented and tested.

## Milestone 2: Additional Functionality

The primary objective is to implement functionality not classified as essential to the initial application baseline.
The CLI will remain the primary interface.
Potential additions include:
-   Improved User Profile management.
-   Enhanced job-search configuration.
-   Improved relevance assessment.
-   Duplicate job-posting detection.
-   Application management and tracking.
-   Additional document-generation capabilities.
-   Company research.
-   Notifications and reminders.
-   Improved error handling and logging.
-   Additional machine learning capabilities.
-   Improvements to existing models.

These are potential additions, not automatically approved requirements. Their priority must be established through planning and requirements analysis.
All additional machine learning functionality must follow the Kaggle training and server-side inference strategy.

## Milestone 3: User Interface

The primary objective is to develop the user interfaces.
Two interfaces must be developed:
1.  A web interface suitable for desktop devices.
2.  An application interface suitable for mobile devices.

Both interfaces must be designed and approved before implementation.
The interfaces must use mock APIs, simulated responses, or other appropriate mechanisms to simulate server communication.
The focus is on the interfaces rather than integrating them with the actual server that the user will provide during Milestone 4.
Nevertheless, the interfaces must behave as functional interfaces from the user's perspective.
This includes:
-   Form validation.
-   Navigation.
-   User interactions.
-   Loading states.
-   Error states.
-   Empty states.
-   Data presentation.
-   Application workflows.
-   Simulated submission and retrieval of information.

Development and execution must remain local to the user's laptop.
The architecture must anticipate the actual server integration that will take place during Milestone 4.

## Milestone 4: Performance Improvements and Server Integration

The primary objective is to integrate the interfaces developed during Milestone 3 with an actual server that the user will provide.
This milestone must focus on:
-   Integrating desktop and mobile interfaces with the supplied server.
-   Implementing actual API communication.
-   Connecting UI operations to backend functionality.
-   Implementing authentication and authorisation where required.
-   Ensuring reliable communication and data exchange.
-   Handling server-side errors.
-   Improving application performance.
-   Addressing integration issues.
-   Optimising computationally intensive operations.
-   Deploying the required trained model artifacts.
-   Configuring server-side model loading.
-   Verifying model inference.

All models must continue to be trained or fine-tuned through Kaggle notebooks.
Only the resulting trained model artifacts should be transferred to the application server for inference.
This milestone is complete only when:
-   The interfaces communicate successfully with the supplied server.
-   The required application workflows function correctly.
-   The server successfully loads the required trained models.
-   The models execute inference successfully.
-   The integrated system satisfies its acceptance criteria.

Do not assume server specifications, endpoints, authentication mechanisms, infrastructure, or deployment configurations. These must be established from the documentation and information the user provides.

## Milestone 5: Refinement, New Functionality, and Bug Fixes

The primary objective is to improve the reliability, usability, and overall effectiveness of Findrr.
This milestone should focus on:
-   Identifying existing defects.
-   Investigating their causes.
-   Recommending appropriate solutions.
-   Resolving defects upon approval.
-   Improving existing functionality.
-   Optimising performance.
-   Improving usability and accessibility.
-   Improving model inference performance.
-   Evaluating existing model performance.
-   Identifying opportunities for model improvements.
-   Developing updated Kaggle training notebooks where required.
-   Implementing approved new functionality.
-   Addressing security and reliability concerns.

Model retraining or fine-tuning must continue to follow the Kaggle training workflow.
Do not introduce substantial functionality merely because it is technically possible. It must provide a meaningful improvement to Findrr.
