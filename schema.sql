-- schema.sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Type ENUM
CREATE TYPE trip_status AS ENUM ('draft', 'planned', 'completed', 'cancelled');

-- ============================================
-- TABLE: users
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    preferred_currency VARCHAR(3) DEFAULT 'EUR',
    language VARCHAR(2) DEFAULT 'fr',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- TABLE: user_preferences
-- ============================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    preferred_budget_range TEXT,
    preferred_travel_style TEXT[],
    dietary_restrictions TEXT[],
    allergies TEXT[],
    mobility_needs TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLE: conversations
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    summary TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    total_messages INT DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.00
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- ============================================
-- TABLE: messages
-- ============================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    model_used VARCHAR(100),
    tokens_input INT,
    tokens_output INT,
    cost_usd DECIMAL(10, 6),
    latency_ms INT,
    tools_called JSONB,
    user_feedback VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    sequence_number INT NOT NULL,
    UNIQUE(conversation_id, sequence_number)
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id, sequence_number);

-- ============================================
-- TABLE: trips
-- ============================================
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    destination VARCHAR(255),
    cities TEXT[],
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INT GENERATED ALWAYS AS (end_date - start_date + 1) STORED,
    budget_total DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    travelers_count INT DEFAULT 1,
    itinerary JSONB,
    status trip_status DEFAULT 'draft',
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CHECK (end_date >= start_date),
    CHECK (budget_total IS NULL OR budget_total >= 0)
);

CREATE INDEX idx_trips_user_id ON trips(user_id);

-- ============================================
-- TABLE: api_cache
-- ============================================
CREATE TABLE api_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    api_provider VARCHAR(100),
    response_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    hit_count INT DEFAULT 0,
    CHECK (expires_at > created_at)
);

CREATE INDEX idx_api_cache_key ON api_cache(cache_key);

-- ============================================
-- TABLE: agent_logs
-- ============================================
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    tool_name VARCHAR(100),
    tool_input JSONB,
    tool_output JSONB,
    execution_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TRIGGERS pour updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trips_updated_at BEFORE UPDATE ON trips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- DONNÉES DE TEST
-- ============================================
INSERT INTO users (email, password_hash, full_name)
VALUES ('test@example.com', crypt('password123', gen_salt('bf')), 'Test User');

INSERT INTO user_preferences (user_id, preferred_budget_range, preferred_travel_style)
SELECT id, 'mid_range', ARRAY['culture', 'nature']
FROM users WHERE email = 'test@example.com';

-- Table pour stocker les documents sources
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source
    source_type VARCHAR(50) NOT NULL, -- 'wikivoyage', 'blog', 'tripadvisor'
    source_url TEXT NOT NULL,
    
    -- Contenu
    destination VARCHAR(255),
    category VARCHAR(100), -- 'attractions', 'restaurants', 'hotels'
    title TEXT NOT NULL,
    content TEXT NOT NULL, -- Texte complet
    
    -- Metadata
    author VARCHAR(255),
    published_at TIMESTAMP,
    language VARCHAR(2) DEFAULT 'en',
    
    -- Scraping info
    scraped_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP,
    
    -- Stats
    chunk_count INT, -- Nombre de chunks créés depuis ce document
    
    UNIQUE(source_url)
);

CREATE INDEX idx_rag_documents_destination ON rag_documents(destination);
CREATE INDEX idx_rag_documents_source ON rag_documents(source_type);


-- Table pour stocker les chunks individuels
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES rag_documents(id) ON DELETE CASCADE,
    
    -- Contenu du chunk
    chunk_text TEXT NOT NULL,
    chunk_index INT NOT NULL, -- Position dans le document
    
    -- ID dans Pinecone
    vector_id VARCHAR(255) UNIQUE, -- "wikivoyage_tokyo_001"
    
    -- Metadata
    token_count INT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_document_chunk UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_rag_chunks_document_id ON rag_chunks(document_id);
CREATE INDEX idx_rag_chunks_vector_id ON rag_chunks(vector_id);