# Code Agent Guide
## Automatic Open-Source Library Discovery and Integration

This document defines how the coding agent should discover, evaluate, and integrate open-source libraries before writing custom implementations.

The goal is to ensure the agent behaves like an experienced engineer who prioritizes reliable libraries over reinventing solutions.

---

# Core Principle

Always check whether a reliable open-source library already exists before writing custom code.

The agent should prefer mature libraries rather than implementing complex functionality from scratch.

Only implement custom solutions when no suitable library exists.

---

# When to Search for Libraries

Always search for libraries when implementing functionality related to:

- UI components
- data visualization
- machine learning
- parsing or data transformation
- networking
- authentication
- database access
- symbolic regression
- image processing
- file processing
- workflow engines
- agent frameworks

If the feature belongs to one of these domains, library search must occur before coding.

---

# Standard Workflow

The agent must follow the workflow below:

User Request  
↓  
Task Planning  
↓  
Search Open Source Libraries  
↓  
Evaluate Candidate Libraries  
↓  
Select Best Library  
↓  
Read Documentation  
↓  
Generate Integration Code  
↓  
Install Dependency  
↓  
Test Implementation  

---

# Library Search Strategy

The agent should search common registries:

GitHub repositories  
npm packages  
PyPI packages  

Example queries:

react chat ui  
symbolic regression python  
nodejs chart library  

Returned information should include:

- repository name
- stars
- description
- language
- last update

---

# Library Evaluation Criteria

Libraries should be evaluated using the following criteria.

Prefer libraries that meet most of these conditions:

- stars > 1000
- active development within the last 12 months
- clear documentation
- examples available
- active issue resolution

Avoid libraries that:

- have no documentation
- have not been updated in years
- appear experimental

---

# Decision Process

The agent should rank candidate libraries and choose the most reliable option.

Example:

Feature: chat interface

Candidates:
assistant-ui (4200 stars)
chat-ui-kit (1100 stars)

Selected:
assistant-ui

Reason:
better documentation and stronger ecosystem adoption.

---

# Documentation Reading

Before integration the agent must read the documentation.

Key information to extract:

- installation commands
- API usage
- minimal example

Primary source should be the README or official documentation.

---

# Dependency Installation

The agent should install the selected library using the correct package manager.

Examples:

npm install assistant-ui

pip install pysr

The agent must ensure the dependency installs successfully.

---

# Integration Code

The agent should generate minimal integration code first.

Example:

import { AssistantProvider } from "assistant-ui";

function App() {
  return (
    <AssistantProvider>
      <Chat />
    </AssistantProvider>
  );
}

The goal is to produce a working minimal example before expanding functionality.

---

# Verification

After integration the agent should verify the implementation.

Checks include:

- project compiles
- dependencies installed
- example runs
- no runtime errors

Possible actions:

run tests  
start dev server  
compile project  

---

# Decision Log

Every library selection must generate a decision log.

Example:

Library Decision Log

Task:
implement chat interface

Search Query:
react chat ui

Candidates:
assistant-ui
chat-ui-kit

Selected:
assistant-ui

Reason:
best documentation and community support

---

# Fallback Strategy

If no suitable library exists:

1. implement a minimal custom solution
2. design the implementation modularly
3. allow future library replacement

---

# Coding Style Expectations

When integrating external libraries:

- prefer minimal configuration
- follow official examples
- avoid unnecessary abstraction
- keep integration readable

---

# Summary

The coding agent must follow this philosophy:

Search before building.  
Reuse before reinventing.  
Document decisions.  
Verify integrations.

This workflow ensures maintainable and production-quality software.