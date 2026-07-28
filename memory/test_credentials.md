# Test Credentials — Fashion Marketplace

All accounts are auto-activated (MVP skips email verification enforcement).

## Admin
- email: `admin@archivemarket.co`
- password: `Admin12345`
- role: admin

## Seed Seller (owns the 6 demo listings)
- email: `seller@archivemarket.co`
- password: `Seller12345`
- role: user

## Auth endpoints (JWT via httpOnly cookies; Bearer header also accepted)
- POST `/api/auth/register`  { email, password (min 8), display_name }
- POST `/api/auth/login`     { email, password }
- POST `/api/auth/logout`    (auth)
- GET  `/api/auth/me`        (auth)
- POST `/api/auth/refresh`
- POST `/api/auth/forgot-password` { email }
- POST `/api/auth/reset-password`  { token, password }

## Key marketplace endpoints
- GET  `/api/listings` (search: q, brand, category, condition, size, min_price, max_price, sort, page, page_size) -> {items,total,facets}
- GET  `/api/listings/mine` (auth)
- GET  `/api/listings/{id_or_slug}`
- POST `/api/listings` (auth) -> create draft
- POST `/api/listings/{id}/publish` (auth, owner)
- PATCH `/api/listings/{id}/price` (auth, owner) { amount }
- DELETE `/api/listings/{id}` (auth, owner) -> archive
- GET  `/api/taxonomy/categories | /brands | /meta`
- GET  `/api/health`

Note: prices are in MINOR units (kopiykas). e.g. amount 420000 = ₴4,200.
