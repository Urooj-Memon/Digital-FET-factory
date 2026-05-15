"""FastAPI application - main API for the Customer Success Digital FTE."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.kafka_client import FTEKafkaProducer, TOPICS
from src.database.queries import (
    get_db_pool,
    close_db_pool,
    get_ticket_by_id,
    find_customer_by_email,
    get_channel_metrics,
)
from src.channels.gmail_handler import process_gmail_notification
from src.channels.whatsapp_handler import (
    process_whatsapp_message,
    validate_twilio_request,
)
from src.channels.web_form_handler import WebFormSubmission, handle_web_form_submission

logger = logging.getLogger(__name__)

kafka_producer = FTEKafkaProducer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    try:
        await get_db_pool()
        logger.info("Database connection pool created")
    except Exception as e:
        logger.warning(f"Database not available – {e}")
    try:
        await kafka_producer.start()
        logger.info("FTE API started - database and Kafka connected")
    except Exception as e:
        logger.warning(f"Kafka not available – {e}")


    yield
    # Shutdown
    try:
        await kafka_producer.stop()
    except Exception as e:
        logger.warning(f"Kafka stop failed – {e}")
    await close_db_pool()
    logger.info("FTE API shut down")


app = FastAPI(
    title="Customer Success Digital FTE",
    description="AI-powered customer support across Email, WhatsApp, and Web Form channels",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Next.js web form
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check ---

@app.get("/health")
async def health_check():
    """Health check endpoint for K8s probes."""
    try:
        pool = await get_db_pool()
        # Acquire a connection without using async context manager (compatible with simple AsyncMock)
        conn = await pool.acquire()
        await conn.fetchval("SELECT 1")
        # Release the connection if possible
        release = getattr(conn, "release", None) or getattr(conn, "close", None)
        if release:
            await release()
        return {"status": "healthy", "service": "fte-api", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)},
        )

# --- Web Form Endpoints ---

@app.post("/api/support/submit")
async def submit_support_request(submission: WebFormSubmission):
    """Receive a support request from the Next.js web form."""
    try:
        result = await handle_web_form_submission(submission, kafka_producer)
        return result
    except Exception as e:
        logger.error(f"Error in support submission endpoint: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while processing request."
        )

@app.get("/api/support/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Check the status of a support ticket."""
    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket["id"],
        "status": ticket["status"],
        "subject": ticket.get("subject", ""),
        "category": ticket.get("category", ""),
        "priority": ticket.get("priority", ""),
        "created_at": str(ticket.get("created_at", "")),
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "channel": m["channel"],
                "created_at": str(m["created_at"]),
            }
            for m in ticket.get("messages", [])
        ],
    }

# --- Gmail Webhook ---

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
    """Receive Gmail Pub/Sub push notifications."""
    try:
        body = await request.json()
        await process_gmail_notification(body, kafka_producer)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process notification")

# --- WhatsApp Webhook ---

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Receive WhatsApp messages via Twilio webhook."""
    form_data = await request.form()
    form_dict = dict(form_data)

    # Validate Twilio signature
    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    request_url = str(request.url)
    if not validate_twilio_request(request_url, form_dict, twilio_signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    await process_whatsapp_message(form_dict, kafka_producer)
    return {"status": "ok"}

# --- Metrics Endpoint ---

@app.get("/api/metrics")
async def get_metrics():
    """Get FTE performance metrics across all channels."""
    metrics = await get_channel_metrics()
    return {
        "status": "ok",
        "channels": metrics,
    }

# --- Customer Lookup ---

@app.get("/api/customers/lookup")
async def lookup_customer(email: str):
    """Look up a customer by email."""
    customer = await find_customer_by_email(email)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "customer_id": str(customer["id"]),
        "name": customer.get("name", ""),
        "email": customer.get("email", ""),
    }
