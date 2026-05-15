-- =============================================================================
-- CUSTOMER SUCCESS FTE - CRM/TICKET MANAGEMENT SYSTEM
-- =============================================================================
-- PostgreSQL schema serving as the complete CRM system for tracking:
-- - Customers (unified across all channels)
-- - Conversations and message history
-- - Support tickets and their lifecycle
-- - Knowledge base for AI responses
-- - Performance metrics and reporting
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Customers table (unified across channels) - YOUR CUSTOMER DATABASE
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Customer identifiers (for cross-channel matching)
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,  -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'resolved', 'escalated', 'closed'
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- Messages table (with channel tracking)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    direction VARCHAR(20) NOT NULL,  -- 'inbound', 'outbound'
    role VARCHAR(20) NOT NULL,  -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),  -- External ID (Gmail message ID, Twilio SID)
    delivery_status VARCHAR(50) DEFAULT 'pending'  -- 'pending', 'sent', 'delivered', 'failed'
);

-- Tickets table
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'processing', 'resolved', 'escalated', 'closed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

-- Knowledge base entries
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding VECTOR(1536),  -- For semantic search (OpenAI text-embedding-3-small)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Channel configurations
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB NOT NULL,
    response_template TEXT,
    max_response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent performance metrics
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50),
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_channel ON conversations(initial_channel);
CREATE INDEX idx_conversations_started ON conversations(started_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_created ON tickets(created_at);
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_metrics_name ON agent_metrics(metric_name);
CREATE INDEX idx_metrics_recorded ON agent_metrics(recorded_at);

-- =============================================================================
-- SEED CHANNEL CONFIGURATIONS
-- =============================================================================
INSERT INTO channel_configs (channel, enabled, config, response_template, max_response_length) VALUES
('email', true, '{"provider": "gmail", "polling_interval_seconds": 30}',
 'Dear {{customer_name}},\n\nThank you for reaching out to TechCorp Support.\n\n{{response}}\n\nIf you have any further questions, please don''t hesitate to reply.\n\nBest regards,\nTechCorp AI Support Team\n---\nTicket Reference: {{ticket_id}}', 2000),
('whatsapp', true, '{"provider": "twilio", "sandbox_mode": true}',
 '{{response}}\n\nReply for more help or type ''human'' for live support.', 1600),
('web_form', true, '{"cors_origins": ["http://localhost:3000"]}',
 '{{response}}\n\n---\nNeed more help? Reply to this message or visit our support portal.', 1000);
