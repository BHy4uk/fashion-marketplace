# TASK WORKFLOW

**Version:** 1.0

**Status:** Approved

---

# Purpose

This document defines the mandatory workflow for every AI task performed within the ARCHIVE repository.

No implementation may bypass this workflow.

---

# Core Principle

Think before coding.

Analyze before changing.

Reuse before creating.

Validate before finishing.

---

# Standard Workflow

Every task MUST follow this sequence.

```
Receive Task
        ↓
Understand Requirements
        ↓
Read Documentation
        ↓
Analyze Project
        ↓
Analyze Existing Implementation
        ↓
Identify Reusable Code
        ↓
Create Implementation Plan
        ↓
Validate Plan
        ↓
Implement
        ↓
Self Review
        ↓
Complete
```

Never skip steps.

---

# Step 1 — Understand the Task

Before making changes:

- Read the entire request.
- Identify the objective.
- Identify constraints.
- Identify expected outcome.
- Identify affected areas.

Never begin implementation before understanding the request.

---

# Step 2 — Read Documentation

Read all relevant documentation before coding.

Priority:

1. `/docs/ai`
2. `/docs/design`
3. `/docs/architecture`

Documentation always takes precedence over implementation.

---

# Step 3 — Analyze the Project

Before modifying code, identify:

- project structure
- application architecture
- routing
- shared layouts
- shared components
- hooks
- providers
- contexts
- utilities
- design tokens
- styling conventions

Understand the existing architecture before making changes.

---

# Step 4 — Analyze Existing Implementation

Identify:

- current behavior
- reusable logic
- reusable components
- duplicated code
- inconsistencies
- technical debt
- accessibility issues

Do not redesign blindly.

---

# Step 5 — Search Before Creating

Always search for:

- existing components
- existing hooks
- existing utilities
- existing helpers
- existing layouts
- existing styles

Reuse existing solutions whenever possible.

---

# Step 6 — Create an Implementation Plan

Before coding, determine:

- what will change
- what will remain unchanged
- what can be reused
- what requires refactoring
- possible risks

Keep the plan as small as possible.

---

# Step 7 — Validate the Plan

Confirm that the implementation:

- follows documentation
- respects architecture
- preserves behavior
- minimizes risk
- avoids duplication

Only then begin implementation.

---

# Step 8 — Implement

Implement only the approved plan.

Do not introduce unrelated improvements.

Do not modify unrelated files.

Keep commits logically focused.

---

# Step 9 — Refactor Carefully

Safe refactoring is encouraged when it:

- removes duplication
- improves readability
- increases maintainability
- preserves behavior

Do not perform unrelated refactoring.

---

# Step 10 — Validate

After implementation verify:

- functionality
- accessibility
- responsiveness
- consistency
- type safety
- performance

Every change must be verified.

---

# Step 11 — Self Review

Before considering the task complete, verify:

✓ Documentation followed

✓ Existing components reused

✓ Existing patterns respected

✓ Design Tokens used

✓ No duplicated code

✓ No unnecessary complexity

✓ Accessibility preserved

✓ Responsive behavior preserved

✓ No regressions introduced

---

# Decision Rules

When multiple solutions exist:

1. Reuse
2. Extend
3. Compose
4. Create

Always choose the least complex solution.

---

# Scope Control

Only modify code required for the requested task.

Avoid:

- unnecessary cleanup
- unrelated refactoring
- architectural rewrites
- dependency changes

Stay focused.

---

# Handling Missing Documentation

If documentation is incomplete:

Stop.

Explain what is missing.

Request clarification.

Do not invent requirements.

---

# Handling Conflicts

If implementation conflicts with documentation:

Documentation wins.

Do not silently follow existing code.

---

# Error Recovery

If an implementation introduces risk:

Reduce the scope.

Prefer incremental improvements.

Avoid large speculative changes.

---

# Completion Criteria

A task is complete only when:

- Requirements are satisfied.
- Documentation has been followed.
- Existing architecture is respected.
- Code is production-ready.
- Accessibility requirements are met.
- No temporary solutions remain.
- No TODO comments remain.
- No placeholders remain.

---

# Final Rule

Every task should leave the codebase in a better state than it was found, without introducing unnecessary complexity or inconsistency.