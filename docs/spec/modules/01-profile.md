# Module 1: Onboarding and User Profile Management

## Purpose

Gather information about users, understand their professional backgrounds, and create and maintain their User Profiles.
The User Profile is the central source of professional information used by Findrr.

## Information Collection

Support gathering information from:
-   Onboarding questionnaires and surveys.
-   Uploaded CVs.
-   Other professional documents.
-   LinkedIn profiles, subject to permitted access.
-   GitHub profiles and repositories.
-   Personal portfolio websites.
-   Other user-provided URLs.
-   Manually entered information.

Extract as much relevant information as reasonably possible, subject to technical feasibility, access permissions, and applicable restrictions.

## User Profile Information

The User Profile should be capable of representing:
- Category
- Information
- Personal Information
- Name and relevant contact information.
- Professional Summary
- Professional background and career overview.
- Education
- Qualifications, institutions, and dates.
- Work Experience
- Employers, positions, responsibilities, achievements, and dates.
- Skills
- Technical skills, soft skills, tools, frameworks, and technologies.
- Certifications
- Professional certifications, licences, and credentials.
- Projects
- Personal, academic, and professional projects.
- Portfolio
- Relevant professional profiles, websites, and repositories.
- Career Preferences
- Desired job titles, industries, and career directions.
- Employment Preferences
- Full-time, part-time, contract, internship, and freelance arrangements.
- Location Preferences
- Preferred locations and geographical restrictions.
- Work Arrangement
- Remote, hybrid, or on-site preferences.
- Compensation Preferences
- Desired compensation range and currency, where provided.
- Seniority Preferences
- Desired professional level or experience range.
- Additional Information
- Other relevant professional or employment information.

The SRS must identify mandatory, optional, and conditionally required fields.

Distinguish between:
**Professional suitability:** The types of positions the user may be qualified to perform.
**Employment preferences:** The positions and working conditions the user wants.
These must be represented separately.

## Information Processing

Implement a structured process:
1.  Information collection.
2.  Information extraction.
3.  Data normalisation.
4.  Information reconciliation.
5.  Profile validation.
6.  User review and correction.
7.  Profile approval and storage.

Distinguish extracted information from manually supplied and user-verified information.
Where possible, retain information provenance, including:
-   Source.
-   Collection or extraction date.
-   Verification status.
-   Relevant extraction metadata.

Flag conflicting information for resolution rather than silently choosing an arbitrary value.
Allow users to review and correct their information.
Never treat unverified extracted information as definitively accurate.

## Generalised Job Title

The final step of initial profile creation must identify an appropriate generalised job title for the user.
Examples include:
-   Software Developer.
-   Data Analyst.
-   Business Analyst.
-   Mechanical Engineer.
-   Graphic Designer.

The selected title must represent the user's overall professional suitability rather than simply repeating their latest or preferred job title.
Consider qualifications, skills, experience, projects, and other relevant professional information.
The output should include:
-   Primary generalised job title.
-   Explanation of why it is appropriate.
-   Supporting qualifications and skills.
-   Potential alternative classifications.
-   Uncertainty or limitations.
    
This title serves as the primary reference for the Generate Key Search Terms Module.
