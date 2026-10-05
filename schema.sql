-- ============================================================
-- Epic Events CRM - Schéma Initial PostgreSQL (DDL)
-- ============================================================

-- 1. Table des Rôles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- 2. Table des Utilisateurs / Collaborateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    employee_number VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexation des colonnes fréquemment recherchées
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_emp_num ON users(employee_number);

-- 3. Table des Clients
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    company_name VARCHAR(150),
    creation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    commercial_contact_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);

-- 4. Table des Contrats
CREATE TABLE IF NOT EXISTS contracts (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    commercial_contact_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    total_amount FLOAT NOT NULL DEFAULT 0.0,
    amount_due FLOAT NOT NULL DEFAULT 0.0,
    creation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_signed BOOLEAN NOT NULL DEFAULT FALSE
);

-- 5. Table des Événements (Relation 1-à-N avec contrats)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    event_date_start TIMESTAMP WITH TIME ZONE NOT NULL,
    event_date_end TIMESTAMP WITH TIME ZONE NOT NULL,
    support_contact_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    location VARCHAR(255) NOT NULL,
    attendees INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

-- Données initiales des rôles par défaut
INSERT INTO roles (name, description) VALUES
    ('COMMERCIAL', 'Département commercial - Démarchage clients et création événements'),
    ('SUPPORT', 'Département support - Organisation et déroulé des événements'),
    ('GESTION', 'Département gestion - Gestion collaborateurs, contrats et attribution support')
ON CONFLICT (name) DO NOTHING;
