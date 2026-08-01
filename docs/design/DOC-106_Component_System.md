# DOC-106 — Component System

**Document ID:** DOC-106  
**Title:** Component System  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines the component philosophy and usage rules for the ARCHIVE design system.

Components exist to create consistency.

Every component should feel like part of one coherent system rather than an individual design.

No component should establish its own visual identity.

---

# 2. Design Philosophy

Components should be quiet.

They support content.

They never compete with content.

Products, photography, typography, and information always receive visual priority.

---

# 3. General Principles

Every component must be:

- Predictable
- Consistent
- Accessible
- Minimal
- Timeless
- Responsive

Avoid novelty.

Prefer familiarity.

---

# 4. Component Hierarchy

Visual hierarchy should originate from content—not from the component itself.

Priority order:

1. Photography
2. Headings
3. Prices
4. Primary actions
5. Supporting metadata
6. Secondary actions

Components should reinforce this hierarchy.

---

# 5. Corners

Border Radius Scale

| Token | Radius |
|--------|--------|
| Small | 8px |
| Medium | 12px |
| Large | 16px |
| XL | 20px |

Default Radius

12px

Avoid perfectly square components.

Avoid extremely rounded ("pill") components unless functionally appropriate.

---

# 6. Borders

Default Border

1px

Border color must originate from the Color System.

Never increase border thickness for emphasis.

Hierarchy should not rely on borders.

---

# 7. Shadows

Default state:

No shadow.

Use subtle elevation only when necessary:

- Dialogs
- Menus
- Dropdowns
- Floating panels

Cards should rarely require shadows.

---

# 8. Buttons

Buttons communicate actions.

They do not decorate the interface.

Button hierarchy:

Primary

Secondary

Ghost

Danger

Only one Primary button should exist within a logical section.

Avoid multiple competing primary actions.

---

# 9. Button Sizes

| Size | Height |
|-------|--------|
| Small | 36px |
| Medium | 44px |
| Large | 52px |

Default button height:

44px

---

# 10. Button Labels

Use verbs.

Examples:

Save

Publish

Continue

Checkout

Submit Offer

Pay

Cancel

Avoid vague labels.

Avoid unnecessary words.

---

# 11. Inputs

Inputs should feel calm and spacious.

Always include:

- Label
- Placeholder (when helpful)
- Validation message (if needed)

Do not rely solely on placeholder text.

---

# 12. Selects

Dropdowns should visually match text inputs.

Avoid custom visual treatments.

Searchable selects should appear identical until activated.

---

# 13. Checkboxes

Checkboxes represent multiple independent selections.

Use only where multiple values may be selected.

Avoid replacing switches with checkboxes.

---

# 14. Radio Buttons

Radio buttons represent exclusive choices.

Never use radio buttons for binary settings.

Prefer switches when enabling or disabling a feature.

---

# 15. Switches

Switches represent immediate state changes.

Examples:

Notifications

Dark Mode (future)

Email Preferences

Availability

Avoid confirmation dialogs after switch interactions whenever possible.

---

# 16. Cards

Cards should feel almost invisible.

Cards group related content.

Cards should not become decorative containers.

Avoid excessive nesting of cards.

Maximum recommended nesting depth:

One level.

---

# 17. Badges

Badges communicate concise status information.

Examples:

New

Sold

Verified

Pending

Draft

Premium

Badges should never become primary visual elements.

---

# 18. Chips

Chips represent:

Filters

Tags

Categories

Selections

Chips should remain lightweight.

Avoid large filled chips.

---

# 19. Tooltips

Tooltips explain.

They never replace labels.

Keep under two sentences.

Never require users to discover essential information via tooltip.

---

# 20. Dialogs

Dialogs interrupt workflow.

Use them sparingly.

Dialogs should appear only when:

- confirmation is required
- important information must be acknowledged
- focused interaction is needed

Avoid using dialogs as ordinary pages.

---

# 21. Drawers

Drawers should be preferred when users need additional context without losing page state.

Examples:

Product preview

Filters

Messaging

Order details

---

# 22. Menus

Menus should remain compact.

Avoid long scrolling menus.

Group related actions.

Separate destructive actions.

---

# 23. Tabs

Tabs separate related content.

Maximum recommended tabs:

Six

If more sections exist, consider another navigation pattern.

---

# 24. Accordions

Use accordions only when progressive disclosure improves comprehension.

Never hide critical information inside collapsed sections.

---

# 25. Tables

Tables prioritize readability.

Avoid unnecessary borders.

Prefer whitespace.

Numeric values should align consistently.

---

# 26. Pagination

Prefer infinite scrolling for product discovery.

Prefer pagination for:

Admin

Analytics

Orders

Reports

Management interfaces

---

# 27. Skeleton Loaders

Skeletons should mimic final layouts.

Avoid animated placeholder gimmicks.

Loading should feel calm.

---

# 28. Empty States

Every empty state should contain:

- Short title
- Supporting explanation
- Primary action (if appropriate)

Avoid illustrations that dominate the layout.

---

# 29. Error States

Errors should explain:

- What happened
- Why it happened (if known)
- How to recover

Never blame the user.

Avoid technical language unless appropriate.

---

# 30. Success States

Success messages should be brief.

Examples:

Saved

Published

Offer Sent

Payment Received

Avoid celebratory language.

---

# 31. Responsive Behaviour

Components should resize naturally.

Avoid creating mobile-only component variants unless absolutely necessary.

Interaction patterns should remain consistent across devices.

---

# 32. Accessibility

Every interactive component must support:

- Keyboard navigation
- Visible focus state
- Screen readers
- WCAG AA contrast
- Touch targets of at least 44×44px

Accessibility is a baseline requirement.

---

# 33. AI Implementation Rules

AI tools must build new interfaces exclusively from existing components.

If a suitable component already exists, it must be reused.

Do not redesign existing components unless the design system is explicitly updated.

Avoid introducing one-off component variations.

---

# 34. Definition of Success

A successful component system is one where every screen feels like it belongs to the same product.

Users should recognize interaction patterns immediately without needing to learn them again.

Components should quietly disappear behind the content while remaining reliable, consistent, and predictable.
```