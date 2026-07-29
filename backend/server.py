"""Fashion Marketplace — Modular Monolith API host.

Assembles all module routers (each module keeps its own domain/application/
infrastructure/api layers). Wires the transactional-outbox relay and a
notifications-lite event handler at startup. See docs/adr/0001.
"""
from dotenv import load_dotenv

load_dotenv()

import asyncio
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from buildingblocks.domain import DomainError
from buildingblocks.mongo import get_db
from buildingblocks import outbox
from modules.administration.router import router as taxonomy_router
from modules.identity.router import auth_router, users_router
from modules.listings.router import router as listings_router
from modules.offers.router import router as offers_router
from modules.offers.service import OfferService
from modules.orders.router import router as orders_router
from modules.orders import handlers as order_handlers
from modules.listings import handlers as listing_handlers
from modules.offers import handlers as offer_handlers
from modules.payments.router import router as payments_router
from modules.payments import handlers as payment_handlers
from modules.payments.service import PaymentService
from modules.shipping.router import router as shipping_router
from modules.shipping import handlers as shipping_handlers
from modules.shipping.service import ShippingService
from modules.reviews.router import router as reviews_router
from modules.identity import handlers as identity_handlers
from modules.messaging.router import router as messaging_router, ws_router as messaging_ws_router
from modules.notifications.router import router as notifications_router
from modules.notifications import handlers as notification_handlers
from seed import ensure_indexes, seed_admin_and_demo, seed_taxonomy

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = FastAPI(title="Fashion Marketplace API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in
                   os.environ.get("CORS_ORIGINS", os.environ.get("FRONTEND_URL", "*")).split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError):
    return JSONResponse(status_code=exc.http_status,
                        content={"error_code": exc.code, "detail": exc.message})


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "fashion-marketplace"}


# ---- Notifications-lite: consume domain events from the outbox (demonstrates
# event-driven cross-domain communication; a full Notifications module is Phase 9). ----
async def _on_event(doc: dict):
    log.info("[event] %s aggregate=%s", doc["event_type"], doc["aggregate_id"])


for _evt in ("UserRegistered", "ListingPublished", "OfferAccepted", "OrderCreated",
             "PaymentCaptured", "ShipmentCreated", "ShipmentDispatched",
             "ShipmentDelivered", "ReviewPublished"):
    outbox.subscribe(_evt, _on_event)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(listings_router)
app.include_router(offers_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(shipping_router)
app.include_router(reviews_router)
app.include_router(messaging_router)
app.include_router(messaging_ws_router)
app.include_router(notifications_router)
app.include_router(taxonomy_router)

# Register cross-domain event subscribers (choreography). Order matters only for
# clarity; all dispatch happens asynchronously via the outbox relay.
order_handlers.register()
listing_handlers.register()
offer_handlers.register()
payment_handlers.register()
shipping_handlers.register()
identity_handlers.register()
notification_handlers.register()


async def _offer_expiration_sweeper(db):
    """Async expiration of stale offers (DOMAIN-004 §12, §19)."""
    while True:
        try:
            n = await OfferService(db).expire_due()
            if n:
                log.info("[offers] expired %d stale offers", n)
        except Exception:  # noqa: BLE001
            log.exception("offer expiration sweep error")
        await asyncio.sleep(60)


async def _escrow_release_sweeper(db):
    """Release seller payouts whose escrow hold window has elapsed (DOMAIN-006, Q3)."""
    while True:
        try:
            n = await PaymentService(db).release_due()
            if n:
                log.info("[payments] released %d escrow payouts", n)
        except Exception:  # noqa: BLE001
            log.exception("escrow release sweep error")
        await asyncio.sleep(60)


async def _shipment_tracking_sweeper(db):
    """Poll the carrier for in-flight shipments and advance their state (DOMAIN-007).
    For real carriers this auto-detects delivery; the sandbox reports in-transit and
    delivery is finalized by the buyer's confirmation."""
    while True:
        try:
            n = await ShippingService(db).sweep_tracking()
            if n:
                log.info("[shipping] advanced %d shipments", n)
        except Exception:  # noqa: BLE001
            log.exception("shipment tracking sweep error")
        await asyncio.sleep(120)


@app.on_event("startup")
async def startup():
    db = get_db()
    await ensure_indexes(db)
    await seed_taxonomy(db)
    await seed_admin_and_demo(db)
    asyncio.create_task(outbox.run_relay(db))
    asyncio.create_task(_offer_expiration_sweeper(db))
    asyncio.create_task(_escrow_release_sweeper(db))
    asyncio.create_task(_shipment_tracking_sweeper(db))
    log.info("startup complete")
