# Discovery Log — Customer Success Digital FTE

## Session 1: Requirements Analysis

### What We Learned
- The business needs 24/7 customer support across 3 channels: Email (Gmail), WhatsApp, and Web Form
- Current support team handles ~200 tickets/day with avg response time of 4 hours
- Most tickets (70%) are routine questions about product features, password resets, and account issues
- A Digital FTE can handle these routine queries autonomously, reducing human workload

### Key Decisions
1. **Agent Framework**: OpenAI Agents SDK (Hackathon 5 requirement)
2. **CRM**: Custom PostgreSQL with pgvector for knowledge base embeddings
3. **Event Streaming**: Apache Kafka for multi-channel message routing
4. **API Layer**: FastAPI for webhooks and web form backend
5. **Web Form**: Next.js/React for the customer-facing support form

### Business Rules Discovered
- Agent must NEVER discuss specific pricing or negotiate discounts
- Agent must NEVER process refunds directly
- Legal mentions trigger immediate escalation
- Angry customers (sentiment < 0.3) get escalated to humans
- WhatsApp has 300-character response limit
- Email responses need formal formatting with ticket reference
- Cross-channel customer identity must be unified (same customer via email and WhatsApp)

## Session 2: Technical Architecture

### Channel Integration Research
- **Gmail**: Use Gmail API v1 + Pub/Sub for push notifications (no polling needed)
- **WhatsApp**: Twilio API with webhook for inbound, REST API for outbound
- **Web Form**: Next.js frontend → FastAPI backend → Kafka → Agent

### Data Model
- Unified `customers` table with cross-channel `customer_identifiers`
- All interactions stored in `messages` table with channel tracking
- Knowledge base uses pgvector for semantic search with text fallback

### Scaling Strategy
- Kafka enables horizontal scaling of message processors
- Kubernetes HPA for auto-scaling based on CPU/memory
- Connection pooling for PostgreSQL (min 5, max 20)

## Session 3: Agent Design

### Tool Design
5 tools following strict workflow order:
1. `create_ticket` — Always first
2. `get_customer_history` — Check cross-channel context
3. `search_knowledge_base` — Find relevant product info
4. `escalate_to_human` — When triggers detected
5. `send_response` — Always last (never respond without this)

### Escalation Rules
- Pricing → escalate with reason "pricing_inquiry"
- Refunds → escalate with reason "refund_request"
- Legal keywords → escalate with reason "legal_threat"
- Profanity/anger → escalate with reason "angry_customer"
- 2 failed searches → escalate with reason "unresolved"
- Customer requests human → escalate with reason "customer_request"

### Quality Guardrails
- Temperature set to 0.3 for consistent, focused responses
- Channel-specific formatting enforced (email=formal, WhatsApp=concise, web=semi-formal)
- Response limits enforced: Email 500 words, WhatsApp 300 chars, Web 300 words
