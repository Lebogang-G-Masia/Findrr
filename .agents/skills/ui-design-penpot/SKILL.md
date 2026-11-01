---
name: ui-design-penpot
description: Use when designing or implementing any user interface.
---

# UI/UX Design & Penpot Workflow

Manage the complete UI/UX design, prototyping, and approval lifecycle for Findrr using the connected Penpot MCP. **No UI implementation may begin without explicit user approval of the relevant design.**

## When to Use

* When designing new user interfaces, user flows, wireframes, or components during Milestones 3, 4, and 5.
* When utilizing the Penpot MCP to create information architecture, layouts, and interactive states.
* When structuring dashboards, profile management views, job opportunity explorers, and application tracking interfaces.

---

## 1. UI/UX Design Approval Process

* **Mandatory Design Phase:** All user interfaces must be designed before code implementation.
* **Penpot Integration:** Use the connected **Penpot MCP** to create required designs covering:
  * Information architecture & user flows
  * Wireframes & page layouts
  * Interactive states & component designs
  * Desktop layouts, mobile layouts, and responsive behavior
  * Error, loading, empty, and success states
* **Approval Gate:** Present proposed designs for review. **Do not implement the UI until the user has explicitly approved the relevant design.**
* **Tool Limitations:** If the Penpot MCP is unavailable or lacks required permissions, report the limitation immediately and request access or an approved alternative.

---

## 2. Core Design Principles

The full UI requirements are in `docs/spec/ui.md`. Read it before designing or implementing any screen. It is the source for the principles and views below, and these notes do not replace it.

Prioritize the following characteristics across all interfaces:
* Modern, visually appealing design with a rich yet minimal user experience.
* Clear information hierarchy and consistent visual language.
* Intuitive navigation, responsive layouts, and accessible interaction patterns.
* Appropriate handling of loading, empty, success, and error states.
* Strong prioritization of usability and efficient employment-search management.

---

## 3. UI Scope & Functional Layouts

Ensure designs accommodate the following core product views and capabilities (full requirements in `docs/spec/ui.md`):

### 3.1 Comprehensive Dashboard
Provide an overview and quick navigation to:
* Discovered, saved, and unapplied opportunities
* Applications being prepared, submitted, or awaiting responses
* Upcoming interviews, assessments, offers, and rejections

### 3.2 Professional Profile Management
Allow users to view and manage user profiles, including:
* Reviewing extracted information, correcting errors, and adding missing details
* Updating employment preferences and managing professional links
* Reviewing generalized job titles and generated search titles

### 3.3 Job Opportunities
Allow users to inspect discovered opportunities, including:
* Job descriptions, company information, location, employment conditions, and posting availability
* Relevance information and application links
* Saving opportunities and launching application-preparation functionality

### 3.4 Application Preparation and Management
Support tools and records for:
* Generating and editing tailored CVs and cover letters
* Accessing company research
* Managing application records, updating statuses, and recording notes
