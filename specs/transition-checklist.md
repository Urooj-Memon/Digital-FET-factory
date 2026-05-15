# Transition Checklist — From Incubation to Specialization

## Stage 1: Incubation (Claude Code + MCP)

### Setup
- [x] Define company context (company-profile.md)
- [x] Create product documentation (product-docs.md)
- [x] Design sample tickets (sample-tickets.json)
- [x] Establish escalation rules (escalation-rules.md)
- [x] Define brand voice guidelines (brand-voice.md)

### MCP Server Testing
- [ ] Expose tools via MCP for Claude Code testing
- [ ] Test each tool individually with sample inputs
- [ ] Test complete workflow: ticket → history → search → respond
- [ ] Test escalation scenarios (pricing, legal, angry customer)
- [ ] Validate cross-channel customer identification

### Prompt Refinement
- [ ] Test email channel responses (formal tone, greeting, signature)
- [ ] Test WhatsApp responses (concise, under 300 chars)
- [ ] Test web form responses (semi-formal, balanced)
- [ ] Verify hard constraints are respected (no pricing, no refunds)
- [ ] Test cross-channel continuity acknowledgment

## Stage 2: Specialization (OpenAI Agents SDK)

### Agent Development
- [x] Create system prompt with channel awareness
- [x] Implement all @function_tool definitions
- [x] Build channel-specific formatters
- [x] Configure Agent with tools and model settings
- [x] Implement agent runner with conversation history

### Channel Integration
- [x] Gmail API + Pub/Sub handler
- [x] Twilio WhatsApp webhook handler
- [x] Web form FastAPI endpoints
- [x] Kafka event streaming for all channels
- [x] Message processor worker (unified pipeline)

### Database & Infrastructure
- [x] PostgreSQL CRM schema with pgvector
- [x] Database access layer (asyncpg)
- [x] Knowledge base seeder
- [x] Docker Compose for local development
- [x] Kubernetes manifests for production

### Testing
- [ ] Unit tests for agent tools
- [ ] Channel handler tests
- [ ] End-to-end conversation flow tests
- [ ] Load testing (target: 500 tickets/hour)
- [ ] Escalation scenario tests

## Pre-Launch Verification

### Environment
- [ ] All environment variables configured (.env)
- [ ] OpenAI API key valid and quota sufficient
- [ ] Gmail API credentials and Pub/Sub topic created
- [ ] Twilio account with WhatsApp sandbox activated
- [ ] PostgreSQL running with schema applied

### Functional Tests
- [ ] `docker-compose up` starts all services
- [ ] Health check passes at http://localhost:8000/health
- [ ] Web form accessible at http://localhost:3000
- [ ] Submit web form → ticket created → AI responds
- [ ] Swagger docs at http://localhost:8000/docs
- [ ] Email inbound → Gmail webhook → AI responds via email
- [ ] WhatsApp inbound → Twilio webhook → AI responds via WhatsApp

### Quality Gates
- [ ] Response accuracy verified against knowledge base
- [ ] Escalation triggers working correctly
- [ ] Response formatting correct per channel
- [ ] Cross-channel customer identity working
- [ ] Metrics being recorded
- [ ] Dead letter queue catching errors
