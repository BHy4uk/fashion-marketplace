# 07 — Future Roadmap (Post-MVP Milestones)

Ordered milestones; each exists to advance a specific mission objective (DOC-000 §2) or success metric (DOC-000 §11). Aligned with Product_Requirements §5 Phase 2/3 and the per-domain "Extension Points".

---

## M1 — AI Seller Assistant (Phase 2 core)  *why: reduce manual work; listing < 1 min*
- Image → structured attributes (brand/category/color/material/condition) with confidence.
- AI title + description generation; category/brand suggestion; duplicate & prohibited-item detection.
- All **advisory & editable**; nothing auto-published (BR-101/103). Versioned prompts, audited executions.
- **KPI:** median listing-creation time, listing completeness/quality score.

## M2 — Intelligent Discovery  *why: improve product discovery & search relevance*
- Semantic search + natural-language queries (pgvector embeddings).
- Visual / image-based search ("find similar").
- Personalized recommendations (recently viewed, similar, trending, for-you).
- Saved-search alerts, collections, follow sellers (F05).
- **KPI:** search→listing CTR, discovery time, recommendation accuracy.

## M3 — Trust & Safety 2.0  *why: trust above everything*
- AI-assisted moderation signals & case prioritization; fraud/risk scoring; trust badges.
- Appeals workflow; authenticity verification track (aligns with StockX-style trust, adapted).
- Dispute resolution flow layered on Orders/Payments/Messaging.
- **KPI:** fraud rate, dispute resolution time, chargeback rate.

## M4 — European Expansion  *why: the core long-term vision (DOC-000 §4, §12)*
- Activate additional countries: multi-currency checkout, per-country tax/VAT, EU carriers (DHL/DPD/InPost via aggregator), EU payment routing (Adyen/Mangopay), localized languages.
- Cross-border shipping, customs docs, regional moderation policies, GDPR data-residency review.
- **KPI:** new-market GMV, cross-border transaction success rate.

## M5 — Seller Growth & Analytics  *why: seller retention (a primary metric)*
- Seller analytics dashboards, pricing intelligence (historical price data as an asset — DOC-001 §3.23), listing performance insights.
- Bulk listing tools, inventory sync, seller tiers.
- **KPI:** seller retention, repeat-seller rate, listings/seller.

## M6 — Notifications & Engagement Depth  *why: transaction success without vanity metrics*
- Push (FCM), Telegram (high relevance in Ukraine), SMS; digesting, smart delivery windows, cross-device sync.
- **KPI:** notification→action conversion (not open-rate vanity).

## M7 — Payments & Money Features  *why: broaden commerce, preserve auditability*
- Multi-provider routing, split payments, store credit, gift cards, installments; enhanced payout scheduling.
- **KPI:** payment success rate, payout SLA.

## M8 — Native Mobile  *why: mobile-first majority (DOC-001 §3.10)*
- React Native apps reusing web feature layer; push-first; camera-first listing.
- **KPI:** mobile conversion, app retention.

## M9 — Platform Scale & Extraction  *why: growth via infra, not redesign (DOC-001 §3.20)*
- Extract highest-load modules (Search, Notifications, AI, Media) into services using existing `*.Contracts`; introduce broker (Kafka/RabbitMQ); dedicated search cluster; ClickHouse analytics.
- **KPI:** p99 latency under load, cost per transaction.

## M10 — New Bounded Contexts (only if justified)  *why: extension over redesign (DOC-004 §15)*
- Candidates: Loyalty, Subscriptions (seller pro), Enterprise Seller, Ads (guarded by DOC-000 §13 "never prioritize advertising over usability"), Warehouse/consignment.
- Each added as a **new module**, never by modifying existing domains.

---

### Sequencing rationale
M1→M2 deliver the "AI-first" differentiation the vision promises, on top of a proven transactional core. M3 protects trust as volume grows. M4 unlocks the actual business vision (Europe) once the single-market engine is validated. M5–M8 deepen retention & reach. M9–M10 are scale/structure milestones triggered by measured load, not speculation (DOC-005 §21).
