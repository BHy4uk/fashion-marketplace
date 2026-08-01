# DOC-108 — Motion System

**Document ID:** DOC-108  
**Title:** Motion System  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Product & Design

---

# 1. Purpose

This document defines the motion language used throughout the ARCHIVE platform.

Motion exists to improve usability, reinforce hierarchy, and communicate relationships between interface elements.

Animation must never exist purely for decoration.

---

# 2. Motion Philosophy

Motion should feel natural.

Motion should feel restrained.

Motion should never demand attention.

Users should notice when motion is missing—not when it is present.

The fastest animation is often no animation.

---

# 3. Core Principles

Every animation must satisfy at least one of the following purposes:

- Explain a transition
- Confirm an action
- Guide attention
- Preserve spatial awareness
- Improve perceived performance

If none apply, remove the animation.

---

# 4. Motion Characteristics

Motion should be:

- Smooth
- Subtle
- Predictable
- Consistent
- Responsive

Avoid dramatic movement.

Avoid theatrical effects.

Avoid unnecessary complexity.

---

# 5. Timing Scale

| Token | Duration |
|--------|---------:|
| Instant | 0ms |
| Fast | 120ms |
| Normal | 180ms |
| Medium | 240ms |
| Slow | 320ms |

Animations longer than 400ms should be extremely rare.

---

# 6. Easing

Default

```css
cubic-bezier(0.2, 0, 0, 1)
```

Exit

```css
cubic-bezier(0.4, 0, 1, 1)
```

Entrance

```css
cubic-bezier(0, 0, 0.2, 1)
```

Use consistent easing across the application.

---

# 7. Fade

Fade is the default transition.

Use for:

- Tooltips
- Menus
- Dropdowns
- Modals
- Notifications

Opacity changes should remain subtle.

---

# 8. Scale

Scale should be minimal.

Recommended range:

98% → 100%

Avoid oversized zoom animations.

Never exceed 105%.

---

# 9. Slide

Use slide transitions only when movement reflects page structure.

Examples:

- Drawers
- Mobile navigation
- Bottom sheets
- Side panels

Avoid long-distance movement.

---

# 10. Page Transitions

Page transitions should preserve context.

Recommended duration:

180–240ms

Avoid cinematic transitions.

Users should never wait for animation to complete.

---

# 11. Hover States

Hover should communicate interactivity.

Recommended effects:

- Background change
- Border change
- Slight opacity adjustment

Avoid:

- Bounce
- Rotation
- Large movement
- Aggressive scaling

---

# 12. Focus States

Focus should be immediate.

No animation is required.

Accessibility takes priority over aesthetics.

---

# 13. Buttons

Buttons may animate:

- Background color
- Border color
- Shadow (if present)

Avoid animated width, height, or position.

Button interactions should feel immediate.

---

# 14. Inputs

Inputs may animate:

- Border color
- Focus ring
- Placeholder opacity

Avoid moving labels unless using a documented floating-label pattern.

---

# 15. Navigation

Navigation should feel stable.

Active states may fade.

Avoid sliding navigation indicators across long distances.

Users should always know where they are.

---

# 16. Cards

Cards should remain visually stable.

Hover effects should be subtle.

Recommended:

- Slight elevation
- Background adjustment
- Soft shadow

Avoid floating or bouncing cards.

---

# 17. Dialogs

Dialogs should:

Fade in

+

Scale from 98% to 100%

Duration:

180ms

Backdrop should fade independently.

---

# 18. Drawers

Drawers should slide from their edge.

Backdrop fades simultaneously.

Motion should reinforce spatial origin.

---

# 19. Notifications

Notifications should appear without interrupting workflow.

Fade + slight vertical movement.

Maximum animation:

180ms

Dismissal should be equally subtle.

---

# 20. Skeleton Loading

Skeletons may use a gentle shimmer.

Animation should remain slow.

Avoid bright moving gradients.

Avoid distracting loading effects.

---

# 21. Progress Indicators

Progress indicators should communicate activity.

Avoid decorative animations.

Loading should appear calm and continuous.

---

# 22. Success Feedback

Success animations should remain understated.

Examples:

- Small fade
- Icon appearance
- Gentle opacity transition

Avoid confetti.

Avoid celebration effects.

Avoid excessive scaling.

---

# 23. Error Feedback

Errors should communicate clearly.

Small shake animations may be used only for invalid input.

Never shake an entire page.

Avoid dramatic effects.

---

# 24. Reduced Motion

The interface must fully support the user's operating system preference for reduced motion.

When reduced motion is enabled:

- Remove non-essential animations
- Reduce movement
- Preserve usability

Accessibility overrides visual polish.

---

# 25. Performance

Animations must maintain 60 FPS on supported devices.

Prefer animating:

- opacity
- transform

Avoid animating:

- width
- height
- top
- left
- margin

unless absolutely necessary.

---

# 26. Consistency

Animations should feel like they belong to one system.

Different pages should not introduce unique animation styles.

Users should develop subconscious expectations about motion.

---

# 27. AI Implementation Rules

AI tools must only use motion patterns defined in this document.

Do not introduce decorative animation libraries or effects without explicit approval.

When uncertain, reduce motion rather than adding more.

Consistency always takes precedence over novelty.

---

# 28. Definition of Success

Motion should quietly support the interface.

Users should feel continuity, clarity, and responsiveness without consciously noticing animation.

The experience should feel polished through restraint rather than spectacle.