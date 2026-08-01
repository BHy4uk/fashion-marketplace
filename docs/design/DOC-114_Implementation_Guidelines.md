# DOC-114 — Implementation Guidelines

**Document ID:** DOC-114  
**Title:** Implementation Guidelines  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines how the ARCHIVE Design System must be implemented by developers, AI coding assistants, and automation tools.

Its purpose is to ensure that the final product matches the design system without interpretation or improvisation.

---

# 2. Design System Authority

The Design System is the single source of truth.

Implementation must never override documented design decisions.

If implementation and documentation conflict, documentation takes precedence.

---

# 3. Technology Stack

The preferred UI stack consists of:

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Radix UI
- Lucide Icons
- Motion (motion.dev)

Additional UI frameworks require design review before adoption.

---

# 4. Design Tokens

Every visual property must reference design tokens.

Never use:

- hardcoded colors
- hardcoded spacing
- hardcoded typography
- hardcoded radius
- hardcoded shadows

Preferred:

```tsx
className="px-space-l text-primary rounded-medium"
```

Avoid:

```tsx
className="px-[24px] text-[#111111] rounded-[12px]"
```

---

# 5. Component Reuse

Always reuse existing components.

Before creating a new component:

1. Search existing components.
2. Extend an existing component if appropriate.
3. Create a new component only when no suitable pattern exists.

Component duplication is prohibited.

---

# 6. Component Composition

Build complex interfaces from small reusable components.

Preferred hierarchy:

```
Page

↓

Section

↓

Container

↓

Component

↓

Primitive
```

Avoid deeply nested component trees.

---

# 7. File Structure

Recommended structure:

```
components/

    ui/

    layout/

    marketplace/

    dashboard/

    forms/

    shared/
```

Avoid feature-specific UI duplication.

---

# 8. Naming

Component names should describe purpose.

Examples:

```
ProductCard

ListingGallery

CheckoutSummary

SellerBadge

PriceDisplay

OfferDialog
```

Avoid vague names.

Examples:

```
Card2

ItemBox

PanelNew

Widget

Component
```

---

# 9. Variants

Component variants should remain limited.

Example:

```tsx
<Button
    variant="primary"
    size="medium"
/>
```

Avoid introducing one-off variants.

---

# 10. Styling

Prefer utility classes.

Extract repeated patterns into reusable components.

Avoid component-specific CSS whenever possible.

Avoid inline styles.

---

# 11. State Management

Components should support documented states only.

Required states:

- Default
- Hover
- Active
- Focus
- Disabled
- Loading
- Selected

Avoid undocumented visual states.

---

# 12. Responsive Design

Responsive behavior should follow the Layout System.

Never redesign components for mobile.

Components should adapt—not change identity.

---

# 13. Accessibility

Every component must satisfy DOC-112.

Accessibility testing is required before release.

Accessibility defects are considered functional defects.

---

# 14. Animation

Animation must follow DOC-108.

Never introduce custom animation styles for individual features.

Use the shared motion system.

---

# 15. Icons

Icons must follow DOC-111.

Only Lucide icons are permitted.

Icon size, spacing, and color must remain consistent.

---

# 16. Typography

Typography must use predefined styles only.

Never introduce:

```
font-size: 15.5px

line-height: 23px
```

Use semantic typography tokens.

---

# 17. Colors

Every color must originate from the Color System.

Never define:

```
#F9F9F9

rgb(...)

hsl(...)
```

inside production components.

---

# 18. Layout

Layouts must follow DOC-107.

Do not create page-specific spacing systems.

Reuse layout primitives.

---

# 19. Error Handling

Every user-facing error should include:

- clear explanation
- recovery path
- accessible messaging

Avoid exposing implementation details.

---

# 20. Loading States

Every asynchronous interaction must provide visual feedback.

Preferred order:

- Skeleton
- Inline Loader
- Spinner

Avoid blocking the entire interface.

---

# 21. Empty States

Every data-driven page must define an empty state.

Empty states should:

- explain why nothing is shown
- provide the next action
- preserve page layout

---

# 22. Performance

Target:

First Contentful Paint < 2 seconds

Interaction latency < 100ms

Maintain 60 FPS animations.

Avoid unnecessary re-renders.

Lazy-load heavy components.

---

# 23. AI Coding Assistants

AI tools must:

- reuse existing components
- reuse design tokens
- follow documented patterns
- avoid inventing layouts
- avoid inventing colors
- avoid inventing typography
- avoid inventing spacing

When documentation is unclear, AI should choose the most consistent existing implementation.

---

# 24. Code Review Checklist

Every UI pull request should verify:

- Design tokens only
- Existing components reused
- Responsive behavior
- Accessibility
- Typography
- Color compliance
- Spacing compliance
- Motion compliance
- No hardcoded values
- No duplicated components

---

# 25. Definition of Done

A UI implementation is considered complete only when:

- It follows every applicable design document.
- It passes accessibility validation.
- It uses only approved components.
- It introduces no undocumented visual patterns.
- It is responsive across supported breakpoints.
- It is production-ready without additional visual refinement.

---

# 26. AI Implementation Contract

When implementing or modifying the ARCHIVE interface, AI assistants must follow these rules in order of priority:

1. Reuse existing components.
2. Reuse existing layout patterns.
3. Reuse existing design tokens.
4. Follow the documented interaction model.
5. Maintain visual consistency.
6. Avoid introducing new visual ideas unless explicitly requested.

If documentation is missing, AI must extend the closest existing pattern rather than inventing a new one.

Consistency is always preferred over creativity.

---

# 27. Definition of Success

A successful implementation should be visually indistinguishable from the approved design system.

Developers, designers, and AI assistants should independently produce interfaces that are functionally and visually consistent because they are guided by the same documentation.