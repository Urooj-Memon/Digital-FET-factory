# Customer Success FTE — Technical Specification

## Overview
The Customer Success Digital FTE is an AI-powered employee that autonomously handles customer support for TechCorp's TechFlow SaaS product across three channels: Gmail, WhatsApp, and Web Form.

## Architecture

```
                    ┌──────────────┐
                    │   Gmail API  │──Pub/Sub──┐
                    └──────────────┘            │
                    ┌──────────────┐            ▼
                    │   Twilio     │──Webhook─►┌──────────┐    ┌─────────┐    ┌───────────┐
                    │  (WhatsApp)  │           │  FastAPI  │───►│  Kafka  │───►│  Worker   │
                    └──────────────┘           │   API     │    │ Topics  │    │ (Agent)   │
                    ┌──────────────┐           └──────────┘    └─────────┘    └─────┬─────┘
                    │  Next.js     │──POST──►       │                               │
                    │  Web Form    │                │                               ▼
                    └──────────────┘                │                        ┌───────────┐
                                                   │                        │ OpenAI    │
                                                   ▼                        │ Agents SDK│
                                            ┌──────────┐                    └─────┬─────┘
                                            │PostgreSQL│◄────────────────────────┘
                                            │+ pgvector│
                                            └──────────┘
```

## Components

### 1. Agent (OpenAI Agents SDK)
- **Model**: gpt-4o (configurable via env)
- **Temperature**: 0.3
- **System Prompt**: Channel-aware with context variable injection
- **Tools**: create_ticket, get_customer_history, search_knowledge_base, escalate_to_human, send_response

### 2. API Layer (FastAPI)
- `POST /api/support/submit` — Web form submissions
- `GET /api/support/ticket/{id}` — Ticket status check
- `POST /webhooks/gmail` — Gmail Pub/Sub notifications
- `POST /webhooks/whatsapp` — Twilio WhatsApp webhook
- `GET /api/metrics` — Performance metrics
- `GET /health` — K8s health check

### 3. Database (PostgreSQL + pgvector)
- **Tables**: customers, customer_identifiers, conversations, messages, tickets, knowledge_base, channel_configs, agent_metrics
- **Vector Search**: 1536-dimension embeddings with IVFFlat index
- **Connection Pool**: asyncpg with min=5, max=20

### 4. Event Streaming (Kafka)
- **Topics**: fte.tickets.incoming, fte.channels.{email|whatsapp|webform}.{inbound|outbound}, fte.escalations, fte.metrics, fte.dlq
- **Consumer Group**: fte-message-processor

### 5. Web Form (Next.js)
- React form with validation
- Category and priority selection
- Ticket status checking
- Proxied API calls to FastAPI backend

## Tool Workflow (Strict Order)
```
Customer Message → create_ticket → get_customer_history → search_knowledge_base → send_response
                                                                                    ↗
                                                   (if triggers detected) → escalate_to_human
```

## Escalation Matrix
| Trigger | Reason Code | SLA |
|---------|-------------|-----|
| Pricing discussion | pricing_inquiry | 1 hour |
| Refund request | refund_request | 2 hours |
| Legal keywords | legal_threat | 30 minutes |
| Angry customer | angry_customer | 1 hour |
| Failed KB search (2x) | unresolved | 2 hours |
| Customer requests human | customer_request | 1 hour |
| Billing dispute | billing_dispute | 2 hours |

## Channel Response Limits
| Channel | Max Length | Format |
|---------|-----------|--------|
| Email | 500 words | Formal with greeting/signature |
| WhatsApp | 300 chars | Concise, conversational |
| Web Form | 300 words | Semi-formal |

## Deployment
- **Docker Compose**: Local development with Postgres, Kafka, API, Worker, Web Form
- **Kubernetes**: Production with HPA (2-10 API pods, 2-8 worker pods), auto-scaling at 70% CPU

## Performance Targets
- Response time: < 30 seconds for WhatsApp, < 2 minutes for email/web
- Availability: 99.9% uptime
- Throughput: 500+ tickets/hour across all channels
