# AI Development Guide

**Version:** 1.0  
**Status:** Approved  
**Document ID:** STD-007

---

# 1. Purpose

This document defines how AI development agents should interpret and implement the marketplace architecture.

The objective is to ensure that all AI-generated code remains consistent with the project's architecture, business model, and engineering principles.

This document applies to every AI-assisted implementation.

---

# 2. Single Source of Truth

The specification repository is the authoritative source of truth.

AI agents must derive implementation from the specifications.

When implementation and documentation conflict, the documentation takes precedence.

AI agents must not invent architecture that contradicts the specifications.

---

# 3. Architectural Priority

Implementation decisions must follow the architectural hierarchy.

1. Project Vision
2. Product Principles
3. Business Rules
4. Domain Model
5. Architecture Principles
6. Domain Specifications
7. Standards
8. Implementation

Higher-level documents always override lower-level decisions.

---

# 4. Preserve Domain Ownership

Every business capability belongs to exactly one domain.

AI agents must never move business logic across domain boundaries.

Business ownership defined in the Domain Specifications is authoritative.

---

# 5. Respect Aggregate Boundaries

Aggregate invariants must always be enforced.

AI agents must never modify aggregate state externally.

All state changes occur through aggregate behavior.

Repositories persist aggregates.

They do not implement business logic.

---

# 6. Business Logic Placement

Business logic belongs to the Domain layer.

The Application layer coordinates use cases.

Infrastructure implements technical concerns.

Presentation exposes capabilities.

AI agents must preserve this separation.

---

# 7. Infrastructure Independence

The Domain layer must remain independent of:

- databases;
- ORMs;
- messaging technologies;
- storage providers;
- AI providers;
- web frameworks;
- cloud vendors.

Infrastructure adapts to the domain.

The domain never adapts to infrastructure.

---

# 8. Domain Events

Business facts are communicated through Domain Events.

AI agents should never replace Domain Events with direct cross-domain dependencies.

Cross-domain workflows should remain event-driven whenever possible.

---

# 9. State Machines

Lifecycle changes must occur through explicit state transitions.

AI agents must not update lifecycle state by directly assigning values.

Transitions enforce business invariants.

Successful transitions produce Domain Events.

---

# 10. API Implementation

HTTP endpoints expose application capabilities.

Controllers should remain thin.

Controllers should not contain business logic.

Business behavior belongs to the Application and Domain layers.

---

# 11. Persistence

Persistence follows the domain model.

Database schemas are implementation details.

AI agents must never redesign aggregates to simplify persistence.

---

# 12. AI Integration

The AI domain is an independent bounded context.

AI enriches business processes.

AI never owns business entities.

AI never bypasses business rules.

AI recommendations require explicit business evaluation before affecting business state.

---

# 13. Error Handling

Business failures should be represented as business outcomes.

Technical failures should remain infrastructure concerns.

AI agents must not expose internal implementation details through public interfaces.

---

# 14. Validation

Validation occurs at multiple levels.

API validation verifies request structure.

Application validation coordinates workflows.

Domain validation protects business invariants.

AI agents must not duplicate validation unnecessarily.

---

# 15. Security

Security applies throughout the architecture.

Authentication establishes identity.

Authorization determines permissions.

AI-generated code must never bypass security rules.

---

# 16. Simplicity

AI agents should prefer the simplest solution that satisfies all architectural requirements.

Complexity should not be introduced without clear business value.

---

# 17. Extensibility

Solutions should remain open for future extension.

AI agents should avoid assumptions that unnecessarily restrict future business capabilities.

Extensibility must not compromise simplicity.

---

# 18. Technology Neutrality

Specifications intentionally avoid framework-specific implementation details.

AI agents may choose appropriate implementation techniques provided they remain compliant with the architecture.

Technology choices must not alter business behavior.

---

# 19. Existing Code

When modifying existing code, AI agents should:

- preserve established architecture;
- avoid unnecessary refactoring;
- minimize unrelated changes;
- respect existing module boundaries;
- maintain backward compatibility where applicable.

---

# 20. Code Generation Principles

Generated code should be:

- readable;
- deterministic;
- maintainable;
- testable;
- cohesive;
- minimally coupled.

Generated code should prioritize correctness over cleverness.

---

# 21. Testing

Generated functionality should be testable.

Business rules should be verifiable independently of infrastructure.

Tests should focus on observable business behavior.

---

# 22. When Requirements Are Missing

If a required behavior is not explicitly specified:

- infer the simplest solution consistent with the architecture;
- preserve existing design principles;
- avoid inventing new architectural patterns;
- avoid contradicting higher-level specifications.

When uncertainty remains, implementation should minimize assumptions.

---

# 23. Prohibited Behaviors

AI agents must not:

- move business logic into controllers;
- move business logic into repositories;
- violate aggregate boundaries;
- bypass domain validation;
- introduce hidden dependencies between domains;
- implement business rules in the database;
- couple the Domain layer to infrastructure;
- invent undocumented architecture;
- replace explicit business rules with AI decisions.

---

# 24. Success Criteria

An AI-generated implementation is considered successful when it:

- complies with the specification repository;
- preserves domain ownership;
- enforces aggregate invariants;
- maintains architectural boundaries;
- remains technology-independent at the business level;
- minimizes unnecessary complexity;
- produces maintainable code.

---

# 25. Compliance Checklist

Every AI-generated implementation should:

- follow the architectural hierarchy;
- preserve domain boundaries;
- respect aggregate ownership;
- enforce business invariants;
- publish Domain Events appropriately;
- maintain infrastructure independence;
- keep business logic in the Domain layer;
- remain consistent with all approved specifications.