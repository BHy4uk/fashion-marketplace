# DOC-110 — Interaction Patterns

**Document ID:** DOC-110  
**Title:** Interaction Patterns  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines how users interact with the ARCHIVE platform.

Interaction patterns must remain consistent across all devices, pages, and features.

Users should never have to relearn how the interface behaves.

---

# 2. Principles

Every interaction must be:

- Predictable
- Fast
- Forgiving
- Discoverable
- Accessible
- Consistent

The interface should always behave exactly as users expect.

---

# 3. Progressive Disclosure

Present only the information required for the current task.

Reveal additional controls only when they become relevant.

Never overwhelm users with advanced functionality by default.

---

# 4. Recognition Over Recall

Users should recognize available actions immediately.

Avoid requiring memorization.

Frequently used actions should remain visible.

Rare actions may be placed inside contextual menus.

---

# 5. Primary Actions

Each screen should contain one clearly identifiable primary action.

Examples:

- Publish Listing
- Checkout
- Save Changes
- Send Offer

Multiple competing primary actions should be avoided.

---

# 6. Secondary Actions

Secondary actions should remain available without competing for attention.

Examples:

- Cancel
- Save Draft
- Share
- Report

Their visual weight must always remain lower than the primary action.

---

# 7. Destructive Actions

Destructive actions must be visually separated.

Examples:

- Delete Listing
- Remove Account
- Cancel Order
- Reject Offer

Confirmation is required before irreversible actions.

---

# 8. Navigation

Navigation should remain stable across the application.

Primary navigation should never change position between pages.

Users should always know:

- Where they are
- Where they came from
- Where they can go next

---

# 9. Search

Search should be available wherever users are expected to discover content.

Search should provide:

- Instant feedback
- Typo tolerance
- Relevant suggestions
- Recent searches
- Popular searches (optional)

Search results should update without unnecessary page reloads.

---

# 10. Filters

Filters should update results immediately whenever possible.

Selected filters must remain visible.

Users should always understand why results changed.

Provide a clear option to reset all filters.

---

# 11. Sorting

Sorting controls should remain simple.

Recommended options:

- Recommended
- Newest
- Price: Low to High
- Price: High to Low
- Most Popular

Avoid overwhelming users with excessive sorting options.

---

# 12. Forms

Forms should guide users naturally.

Validation should occur as early as possible without interrupting typing.

Preserve entered data whenever possible.

Never force users to repeat completed work.

---

# 13. Validation

Validation messages should:

- Explain the issue
- Explain how to fix it
- Appear near the relevant field

Avoid technical terminology.

---

# 14. Saving

Whenever appropriate, save changes automatically.

If manual saving is required, clearly communicate:

- Unsaved changes
- Save progress
- Successful completion

Users should never wonder whether their work was saved.

---

# 15. Loading

Users should receive feedback immediately after initiating an action.

Preferred loading states:

- Skeletons
- Inline progress
- Button loading indicators

Avoid full-screen blocking loaders whenever possible.

---

# 16. Empty States

Every empty state should answer three questions:

- Why is this empty?
- What can I do next?
- How do I get started?

Empty states should encourage action rather than simply report absence.

---

# 17. Error Recovery

Errors should always provide recovery paths.

Examples:

- Retry
- Edit
- Contact Support
- Return

Users should never reach a dead end.

---

# 18. Confirmation

Confirmation messages should appear only when they provide value.

Avoid confirming routine actions unnecessarily.

Confirmation should never interrupt user flow.

---

# 19. Notifications

Notifications should inform.

They should never become the center of attention.

Notifications must:

- Be concise
- Be dismissible when appropriate
- Disappear automatically if non-critical

---

# 20. Undo

Whenever technically feasible, destructive actions should support Undo.

Undo is preferable to confirmation dialogs for reversible actions.

---

# 21. Drag and Drop

Drag and drop should remain optional.

Every drag interaction must have an accessible alternative.

Dragging should feel smooth and responsive.

---

# 22. Keyboard Support

Every important workflow should support keyboard navigation.

Essential shortcuts should remain consistent.

Examples:

- Enter
- Escape
- Tab
- Shift + Tab

Custom shortcuts should be documented.

---

# 23. Touch Interaction

Touch targets must be at least:

44 × 44 px

Avoid placing interactive elements too closely together.

Touch interactions should require minimal precision.

---

# 24. Infinite Scroll

Use infinite scrolling for exploration.

Examples:

- Marketplace
- Search Results
- Collections

Provide clear loading feedback.

Preserve scroll position when returning.

---

# 25. Pagination

Use pagination for structured management tasks.

Examples:

- Orders
- Listings
- Analytics
- Admin Panels

Users should always know how much content remains.

---

# 26. Context Menus

Context menus should contain only relevant actions.

Group related actions.

Separate destructive actions.

Avoid very long menus.

---

# 27. Hover Behaviour

Hover should reveal additional information—not essential functionality.

Users on touch devices must have an equivalent interaction.

---

# 28. Focus Management

Focus should move logically throughout the interface.

Dialogs must trap focus while open.

Closing overlays should restore focus to the triggering element.

---

# 29. Accessibility

Interaction patterns must support:

- Keyboard navigation
- Screen readers
- Reduced motion
- WCAG AA compliance
- Clear focus indicators

Accessibility is part of every interaction—not an enhancement.

---

# 30. AI Implementation Rules

AI tools must implement interactions using the patterns defined in this document.

Do not invent new interaction models when an existing pattern already satisfies the requirement.

Favor predictability over innovation.

---

# 31. Definition of Success

Users should complete tasks naturally without thinking about the interface itself.

Interactions should feel obvious, responsive, and consistent throughout the entire product.

Every action should build confidence through clarity rather than surprise.