# DOC-107 — Layout System

**Document ID:** DOC-107  
**Title:** Layout System  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines how pages, sections, and layouts are structured throughout the ARCHIVE platform.

A consistent layout system creates familiarity, trust, and visual rhythm.

Every screen must follow these structural rules.

---

# 2. Layout Philosophy

Layouts should feel architectural.

The interface should never appear assembled from independent blocks.

Every page should feel intentional.

Whitespace is part of the layout.

Content should always have room to breathe.

---

# 3. Content Hierarchy

Every page follows the same hierarchy:

1. Global Navigation
2. Page Header
3. Primary Content
4. Secondary Content
5. Supporting Actions
6. Footer (when applicable)

Never invert this hierarchy.

---

# 4. Maximum Width

Application

1440px

Dashboard

1600px

Reading Content

760px

Forms

720px

Authentication

480px

Ultra-wide layouts should increase margins instead of stretching content.

---

# 5. Page Structure

Every page consists of:

Header

↓

Hero (optional)

↓

Primary Content

↓

Supporting Sections

↓

Footer

The order should remain predictable.

---

# 6. Page Header

Every page header contains:

- Page title
- Optional description
- Primary action (if applicable)

Avoid placing secondary controls above the page title.

---

# 7. Hero Sections

Hero sections are reserved for:

Home

Collections

Campaigns

Editorial pages

Landing pages

Do not use hero sections inside management interfaces.

---

# 8. Section Structure

Every section contains:

Optional section label

↓

Heading

↓

Supporting text (optional)

↓

Content

↓

Section spacing

Maintain consistent spacing across all sections.

---

# 9. Primary Content

Primary content should receive maximum visual emphasis.

Examples:

Product Gallery

Product Details

Checkout

Order Summary

Analytics

Messaging

Never allow secondary content to dominate.

---

# 10. Secondary Content

Examples:

Recommendations

Seller Information

Related Products

Recently Viewed

Help

Policies

Secondary content should support—not interrupt—the primary task.

---

# 11. Sidebar Rules

Sidebars are optional.

Use them only when they improve navigation or workflow.

Recommended width:

320px

Avoid multiple sidebars on the same page.

---

# 12. Two-Column Layout

Preferred ratio:

65 / 35

or

70 / 30

Examples:

Product + Seller

Checkout + Summary

Analytics + Filters

Never create perfectly equal columns unless content demands it.

---

# 13. Three-Column Layout

Reserved for:

Desktop product discovery

Editorial collections

Large dashboards

Avoid three-column layouts on tablet.

Avoid four-column content layouts outside product grids.

---

# 14. Dashboard Layout

Dashboard pages follow:

Page Header

↓

KPI Row

↓

Charts

↓

Tables

↓

Supporting Information

Avoid mixing unrelated metrics.

---

# 15. Forms

Forms should remain visually narrow.

Inputs should align vertically.

Avoid multiple columns unless comparison is necessary.

Long forms should be divided into logical sections.

---

# 16. Product Detail Page

Recommended structure:

Product Gallery

↓

Product Information

↓

Purchase Actions

↓

Seller Information

↓

Description

↓

Specifications

↓

Recommendations

Photography should remain the dominant element.

---

# 17. Checkout

Checkout must minimize distractions.

Recommended structure:

Checkout Form

↓

Delivery

↓

Payment

↓

Order Summary

↓

Confirmation

Avoid promotional content during checkout.

---

# 18. Lists

Lists should maintain consistent spacing.

Avoid dense rows.

Group related information together.

Separate unrelated information using whitespace.

---

# 19. Filters

Desktop

Persistent sidebar.

Tablet

Collapsible drawer.

Mobile

Bottom sheet or drawer.

Filters should never dominate product discovery.

---

# 20. Search Results

Search bar

↓

Applied filters

↓

Sorting

↓

Results

↓

Pagination or infinite scroll

Users should immediately understand where they are.

---

# 21. Empty Pages

Maintain the same layout structure even when no content exists.

Never collapse page spacing because data is missing.

---

# 22. Mobile Layout

Content should stack naturally.

Avoid horizontal scrolling.

Avoid reducing typography to fit more information.

Preserve hierarchy before density.

---

# 23. Responsive Behaviour

Layouts adapt progressively.

Do not redesign page structure between breakpoints.

Navigation patterns should remain familiar.

Users should recognize the same page regardless of device.

---

# 24. Alignment Rules

All page elements align to the same grid.

Do not manually offset components to create visual interest.

Alignment should appear effortless and consistent.

---

# 25. Density

ARCHIVE favors low-density layouts.

Avoid placing too much information above the fold.

Allow users to scroll naturally.

Scrolling is preferable to visual clutter.

---

# 26. Progressive Disclosure

Show essential information first.

Reveal complexity gradually.

Advanced functionality should never overwhelm first-time users.

---

# 27. Visual Balance

Every layout should have one dominant focal point.

Avoid multiple competing visual centers.

The user's eye should naturally move through the page.

---

# 28. Reuse

New pages should reuse existing layout patterns whenever possible.

Avoid inventing page structures for isolated use cases.

Consistency strengthens usability.

---

# 29. AI Implementation Rules

AI tools must compose pages using the layout patterns defined in this document.

Do not invent new page structures when an existing one satisfies the requirement.

Favor consistency over originality.

---

# 30. Definition of Success

Users should instinctively understand every page without learning a new structure.

Layouts should feel calm, balanced, and predictable.

The architecture of the interface should become invisible while guiding users effortlessly through every task.