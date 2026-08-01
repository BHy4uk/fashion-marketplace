# DOC-113 — Design Tokens

**Document ID:** DOC-113  
**Title:** Design Tokens  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines the design tokens used across the ARCHIVE platform.

Design tokens are the single source of truth for visual properties.

Every interface implementation must consume these tokens rather than defining values directly.

Hardcoded visual values are prohibited.

---

# 2. Principles

Design tokens provide:

- Consistency
- Scalability
- Maintainability
- Themeability
- Predictability

Every visual decision should map to an existing token.

If a required token does not exist, the design system should be updated instead of introducing one-off values.

---

# 3. Naming Convention

All tokens follow the format:

```
category.role.state
```

Examples

```
color.text.primary

color.border.default

space.l

radius.medium

shadow.surface

motion.fast
```

Names must describe purpose rather than appearance.

---

# 4. Color Tokens

## Background

```text
color.background.canvas
color.background.surface
color.background.subtle
color.background.overlay
color.background.inverse
```

---

## Text

```text
color.text.primary
color.text.secondary
color.text.muted
color.text.disabled
color.text.inverse
```

---

## Border

```text
color.border.default
color.border.subtle
color.border.focus
color.border.disabled
```

---

## Interactive

```text
color.action.primary
color.action.primary-hover
color.action.primary-active

color.action.secondary
color.action.secondary-hover

color.action.ghost-hover
```

---

## Status

```text
color.success
color.warning
color.error
color.info
```

---

# 5. Typography Tokens

```text
font.family.primary

font.weight.light

font.weight.regular

font.weight.medium

font.weight.semibold

font.weight.bold
```

---

Typography Scale

```text
font.display-xl

font.display-lg

font.h1

font.h2

font.h3

font.h4

font.body-lg

font.body

font.body-sm

font.caption

font.label

font.overline
```

---

# 6. Spacing Tokens

```text
space.xs

space.s

space.m

space.l

space.xl

space.2xl

space.3xl

space.4xl

space.5xl
```

Spacing tokens are the only permitted spacing values.

---

# 7. Radius Tokens

```text
radius.small

radius.medium

radius.large

radius.xl
```

Component-specific border radius values are prohibited.

---

# 8. Shadow Tokens

```text
shadow.none

shadow.surface

shadow.dialog

shadow.dropdown
```

New shadow values should not be introduced.

---

# 9. Border Tokens

```text
border.width.default

border.width.focus

border.style.default
```

Borders should remain consistent throughout the product.

---

# 10. Motion Tokens

Duration

```text
motion.instant

motion.fast

motion.normal

motion.medium

motion.slow
```

Easing

```text
motion.easing.default

motion.easing.enter

motion.easing.exit
```

---

# 11. Opacity Tokens

```text
opacity.disabled

opacity.overlay

opacity.loading

opacity.hover
```

Opacity should always be tokenized.

---

# 12. Z-Index Tokens

```text
z.base

z.dropdown

z.sticky

z.drawer

z.modal

z.toast

z.tooltip
```

Never use arbitrary z-index values.

---

# 13. Layout Tokens

```text
layout.max-width

layout.dashboard-width

layout.form-width

layout.reading-width
```

---

# 14. Grid Tokens

```text
grid.columns.desktop

grid.columns.tablet

grid.columns.mobile

grid.gutter.desktop

grid.gutter.tablet

grid.gutter.mobile
```

---

# 15. Component Tokens

Buttons

```text
button.height.small

button.height.medium

button.height.large
```

Cards

```text
card.padding

card.radius

card.border
```

Inputs

```text
input.height

input.padding

input.radius
```

Navigation

```text
navigation.height

navigation.item-gap
```

Dialogs

```text
dialog.padding

dialog.radius

dialog.max-width
```

---

# 16. Breakpoint Tokens

```text
breakpoint.mobile

breakpoint.tablet

breakpoint.laptop

breakpoint.desktop

breakpoint.wide
```

Breakpoints should be shared across the application.

---

# 17. State Tokens

Every interactive component should support the following states:

```text
default

hover

active

focus

disabled

loading

selected
```

Every state should reference existing design tokens.

---

# 18. Semantic Tokens

Component implementations should reference semantic tokens instead of primitive values.

Preferred

```text
color.text.primary
```

Avoid

```text
#111111
```

Preferred

```text
space.l
```

Avoid

```text
24px
```

Semantic naming improves maintainability.

---

# 19. Implementation Example

Preferred

```css
padding: var(--space-l);

border-radius: var(--radius-medium);

color: var(--color-text-primary);

background: var(--color-background-surface);

transition: var(--motion-normal);
```

Avoid

```css
padding: 24px;

border-radius: 12px;

color: #111111;

background: #ffffff;

transition: 180ms;
```

---

# 20. Token Ownership

Only the Design System may introduce or modify tokens.

Application teams should consume tokens.

Individual features must not create private token sets.

---

# 21. Versioning

Token changes should be versioned.

Breaking changes require:

- Documentation
- Migration guide
- Component updates
- Design review

Backward compatibility should be preserved whenever practical.

---

# 22. AI Implementation Rules

AI tools must always consume existing design tokens.

If a requested value has no matching token, the implementation must stop and request a design system update instead of inventing a new token.

No hardcoded visual values may appear inside production components.

---

# 23. Definition of Success

Every screen in the application should be visually constructed from the same shared token system.

Developers, designers, AI tools, and design software should all reference the same design language.

A design token should represent intent—not merely a numeric value.