# CODE STYLE

**Version:** 1.0

**Status:** Approved

---

# Purpose

This document defines the mandatory coding standards for the ARCHIVE repository.

Every AI assistant must follow these rules when writing, modifying, or refactoring code.

Consistency is more important than personal preference.

---

# General Principles

Code should be:

- Readable
- Predictable
- Maintainable
- Reusable
- Explicit
- Production-ready

Write code for humans first.

---

# Architecture Principles

Follow:

- SOLID
- DRY
- KISS
- YAGNI
- Composition over Inheritance

Avoid unnecessary abstractions.

---

# File Organization

Each file should have a single responsibility.

Avoid files that perform unrelated tasks.

Prefer multiple focused files over one large file.

---

# File Size

Preferred limits:

- Components: ≤ 300 lines
- Hooks: ≤ 200 lines
- Utilities: ≤ 200 lines

Large files should be refactored into smaller modules.

---

# Naming

Names must describe purpose.

Good examples:

```
ProductCard

CheckoutSummary

ListingGallery

UserAvatar

PriceDisplay
```

Avoid:

```
Card2

Widget

Helper

Temp

Data

Utils
```

---

# Components

Component names use PascalCase.

One component per file whenever practical.

Default export is discouraged.

Prefer named exports.

---

# Functions

Function names should describe actions.

Examples:

```
createListing()

calculatePrice()

validateForm()

fetchOrders()
```

Avoid generic names.

Examples:

```
doStuff()

run()

process()

handle()
```

---

# Variables

Variable names should clearly describe their contents.

Prefer:

```
product

seller

cartItems

filteredListings
```

Avoid:

```
obj

data

temp

item1

result2
```

---

# Constants

Constants use UPPER_SNAKE_CASE.

Example:

```
MAX_UPLOAD_SIZE

DEFAULT_PAGE_SIZE

API_TIMEOUT
```

Never use unexplained magic numbers.

---

# Booleans

Boolean names should answer a yes/no question.

Examples:

```
isLoading

hasPermission

canEdit

shouldRender
```

Avoid:

```
loading

permission

flag
```

---

# TypeScript

Use strict typing.

Avoid:

```
any
```

Prefer:

- interfaces
- type aliases
- generics
- discriminated unions

Every public API should be fully typed.

---

# Interfaces

Interfaces should describe business concepts.

Example:

```
Product

Order

Seller

Listing
```

Avoid generic interface names.

---

# Functions

Prefer pure functions.

Functions should:

- perform one task
- return predictable results
- avoid hidden side effects

---

# Component Size

Components should focus on rendering.

Business logic belongs in:

- hooks
- services
- utilities

Avoid embedding complex logic inside JSX.

---

# Hooks

Custom hooks should encapsulate reusable behavior.

Hook names must begin with:

```
use
```

Example:

```
useCart()

useAuth()

useSearch()
```

---

# Imports

Order imports consistently.

1. React

2. External libraries

3. Internal modules

4. Components

5. Hooks

6. Utilities

7. Types

8. Styles

Separate groups with a blank line.

---

# Exports

Prefer named exports.

Avoid anonymous default exports unless required by framework conventions.

---

# Comments

Code should be self-explanatory.

Do not comment obvious code.

Acceptable comments explain:

- business rules
- architectural decisions
- non-obvious behavior

Never explain syntax.

---

# Formatting

Use consistent formatting throughout the repository.

Avoid inconsistent spacing, indentation, or line wrapping.

Formatting should be automated whenever possible.

---

# Conditional Logic

Prefer early returns.

Avoid deeply nested conditions.

Example:

Good

```
if (!user) return null;
```

Avoid

```
if (user) {
    if (user.profile) {
        ...
    }
}
```

---

# Error Handling

Errors should be:

- explicit
- actionable
- user-friendly

Never swallow exceptions silently.

---

# Async Code

Prefer:

```
async / await
```

Avoid chained Promise callbacks unless necessary.

Always handle failures.

---

# Duplication

Never duplicate logic.

Extract shared behavior into:

- hooks
- utilities
- services
- components

---

# Styling

Never hardcode visual values.

Always use:

- Design Tokens
- Tailwind utilities
- shared UI components

---

# Accessibility

Accessibility is required.

Every component should support:

- keyboard navigation
- semantic HTML
- screen readers
- visible focus

---

# Performance

Avoid unnecessary:

- renders
- allocations
- calculations
- re-renders

Optimize only when needed.

---

# Dependencies

Before adding a dependency:

Determine whether existing code already solves the problem.

Prefer fewer dependencies.

---

# Logging

Remove temporary logging before completion.

Avoid:

```
console.log()

console.debug()
```

Production code should not contain debugging statements.

---

# Temporary Code

Never leave:

- TODO
- FIXME
- HACK
- placeholder implementations

Every task should be fully completed.

---

# Refactoring

Refactor only when it:

- improves readability
- removes duplication
- preserves behavior

Avoid unrelated refactoring.

---

# Code Review Checklist

Before completion verify:

✓ Clear naming

✓ Small functions

✓ Small components

✓ Strong typing

✓ No duplication

✓ No magic numbers

✓ No unused code

✓ No debugging statements

✓ No temporary code

✓ Consistent formatting

✓ Existing architecture respected

---

# Final Rule

Every file should be understandable without external explanation.

If another senior engineer opens the file six months later, they should immediately understand its purpose, structure, and behavior.