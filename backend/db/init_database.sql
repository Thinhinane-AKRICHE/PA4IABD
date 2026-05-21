-- ============================================
-- TRAVEL BUDDY - Base de données SIMPLIFIÉE
-- ============================================
-- Focus sur l'essentiel pour personnalisation IA
-- ============================================


-- Table principale des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    telephone VARCHAR(50),
    date_naissance DATE,
    langue_preferee VARCHAR(10) DEFAULT 'fr',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Profil de voyage SIMPLIFIÉ - uniquement l'essentiel
CREATE TABLE IF NOT EXISTS user_travel_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    
    -- Budget (essentiel pour suggestions)
    budget_quotidien_moyen INTEGER,  -- Budget par jour en devise locale
    devise_preferee VARCHAR(3) DEFAULT 'EUR',
    
    -- Style de voyage (guide les suggestions)
    style_voyage VARCHAR(50),  -- 'luxe', 'confort', 'routard', 'equilibre'
    rythme_prefere VARCHAR(50), -- 'relax', 'modéré', 'intense'
    
    -- Préférences alimentaires (crucial pour restaurants)
    regime_alimentaire TEXT[],  -- ['végétarien', 'vegan', 'sans_gluten', etc.]
    cuisines_preferees TEXT[],  -- ['italienne', 'japonaise', 'locale', etc.]
    
    -- Hébergement (filtres principaux)
    etoiles_min_preferees INTEGER CHECK (etoiles_min_preferees BETWEEN 1 AND 5),
    prefere_centre_ville BOOLEAN DEFAULT TRUE,
    
    -- Transport
    modes_transport_preferes TEXT[], -- ['avion', 'train', 'bus', 'voiture']
    
    -- Intérêts (pour activités)
    centres_interet TEXT[], -- ['culture', 'nature', 'gastronomie', 'shopping', 'sport', etc.]
    
    -- Contexte voyage
    voyage_generalement_avec VARCHAR(50), -- 'solo', 'couple', 'famille', 'amis'
    nombre_enfants INTEGER DEFAULT 0,
    
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_travel_profile_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Destinations favorites (apprend des goûts)
CREATE TABLE IF NOT EXISTS user_favorite_destinations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    pays VARCHAR(255) NOT NULL,
    ville VARCHAR(255),
    note INTEGER CHECK (note BETWEEN 1 AND 5),
    deja_visite BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_favorite_destinations_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Destinations à éviter
CREATE TABLE IF NOT EXISTS user_blacklist_destinations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    pays VARCHAR(255) NOT NULL,
    ville VARCHAR(255),
    raison TEXT,
    added_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_blacklist_destinations_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Voyages planifiés
CREATE TABLE IF NOT EXISTS trips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    titre VARCHAR(255) NOT NULL,
    destination_principale VARCHAR(255) NOT NULL,
    pays VARCHAR(255),
    date_debut DATE,
    date_fin DATE,
    duree_jours INTEGER,
    budget_total INTEGER,
    statut VARCHAR(50) DEFAULT 'planification', -- 'planification', 'confirmé', 'en_cours', 'terminé'
    itineraire_detaille JSONB,
    notes_voyage TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_trips_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Hôtels sauvegardés par voyage
CREATE TABLE IF NOT EXISTS trip_hotels (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    nom_hotel VARCHAR(255) NOT NULL,
    adresse TEXT,
    ville VARCHAR(255),
    pays VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    etoiles INTEGER CHECK (etoiles BETWEEN 1 AND 5),
    prix_nuit DECIMAL(10, 2),
    devise VARCHAR(3) DEFAULT 'EUR',
    date_checkin DATE,
    date_checkout DATE,
    nombre_nuits INTEGER,
    hotel_data JSONB, -- Données complètes de l'API
    statut VARCHAR(50) DEFAULT 'wishlist', -- 'wishlist', 'réservé', 'confirmé'
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_trip_hotels_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);


-- Restaurants sauvegardés
CREATE TABLE IF NOT EXISTS trip_restaurants (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    nom_restaurant VARCHAR(255) NOT NULL,
    adresse TEXT,
    ville VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    types_cuisine TEXT[],
    prix_moyen VARCHAR(20), -- '€', '€€', '€€€', '€€€€'
    note_moyenne DECIMAL(3, 2),
    options_vegetariennes BOOLEAN,
    options_vegan BOOLEAN,
    options_sans_gluten BOOLEAN,
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_trip_restaurants_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);


-- Activités sauvegardées
CREATE TABLE IF NOT EXISTS trip_activities (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    nom_activite VARCHAR(255) NOT NULL,
    type_activite VARCHAR(100), -- 'musée', 'monument', 'parc', 'excursion', etc.
    adresse TEXT,
    ville VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    duree_estimee INTEGER, -- en minutes
    prix DECIMAL(10, 2),
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_trip_activities_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);


-- Historique de recherche (amélioration continue)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    trip_id INTEGER,
    query TEXT NOT NULL,
    destination VARCHAR(255),
    results_summary JSONB,
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5), -- Feedback utilisateur
    searched_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_search_history_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_search_history_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
);


-- Cache météo
CREATE TABLE IF NOT EXISTS weather_cache (
    id SERIAL PRIMARY KEY,
    ville VARCHAR(255) NOT NULL,
    pays VARCHAR(255),
    date_prevision DATE NOT NULL,
    temperature_min DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    conditions VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(ville, pays, date_prevision)
);


-- Informations pays (cache)
CREATE TABLE IF NOT EXISTS countries_info (
    id SERIAL PRIMARY KEY,
    code_pays VARCHAR(3) UNIQUE NOT NULL,
    nom_pays VARCHAR(255) NOT NULL,
    capitale VARCHAR(255),
    langues TEXT[],
    devise_code VARCHAR(3),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Documents RAG (base de connaissances)
CREATE TABLE IF NOT EXISTS rag_documents (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50), -- 'guide', 'blog', 'officiel', etc.
    destination VARCHAR(255),
    pays VARCHAR(255),
    categorie VARCHAR(100), -- 'hotels', 'restaurants', 'activites', 'conseils'
    contenu_texte TEXT NOT NULL,
    langue VARCHAR(10) DEFAULT 'fr',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Chunks RAG pour embeddings
CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding_id VARCHAR(255), -- ID dans la base vectorielle
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_rag_chunks_document 
        FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);


-- ============================================
-- INDEX OPTIMISÉS
-- ============================================

-- Users & Profile
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_travel_profile_user ON user_travel_profile(user_id);

-- Trips
CREATE INDEX idx_trips_user ON trips(user_id);
CREATE INDEX idx_trips_dates ON trips(date_debut, date_fin);
CREATE INDEX idx_trips_statut ON trips(statut);

-- Trip items
CREATE INDEX idx_trip_hotels_trip ON trip_hotels(trip_id);
CREATE INDEX idx_trip_restaurants_trip ON trip_restaurants(trip_id);
CREATE INDEX idx_trip_activities_trip ON trip_activities(trip_id);

-- Search & Cache
CREATE INDEX idx_search_user_date ON search_history(user_id, searched_at DESC);
CREATE INDEX idx_weather_location ON weather_cache(ville, pays, date_prevision);
CREATE INDEX idx_countries_code ON countries_info(code_pays);

-- RAG
CREATE INDEX idx_rag_docs_destination ON rag_documents(destination, categorie);
CREATE INDEX idx_rag_chunks_document ON rag_chunks(document_id);

-- Favorites
CREATE INDEX idx_favorites_user ON user_favorite_destinations(user_id);
CREATE INDEX idx_blacklist_user ON user_blacklist_destinations(user_id);


-- ============================================
-- DONNÉES DE TEST
-- ============================================

-- Utilisateur 1 : Marie Dupont (voyageuse confort, culture & gastronomie)
INSERT INTO users (id, nom, prenom, email, password_hash, date_naissance, langue_preferee) VALUES
(1, 'Dupont', 'Marie', 'marie.dupont@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYNZ0zJ5C', '1990-05-15', 'fr')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_travel_profile (
    user_id, 
    budget_quotidien_moyen,
    devise_preferee,
    style_voyage,
    rythme_prefere,
    regime_alimentaire,
    cuisines_preferees,
    etoiles_min_preferees,
    prefere_centre_ville,
    modes_transport_preferes,
    centres_interet,
    voyage_generalement_avec,
    nombre_enfants
) VALUES (
    1,
    150, -- 150€/jour
    'EUR',
    'confort',
    'modéré',
    ARRAY['végétarien'],
    ARRAY['française', 'italienne', 'japonaise'],
    3, -- Minimum 3 étoiles
    TRUE,
    ARRAY['avion', 'train'],
    ARRAY['culture', 'gastronomie', 'architecture', 'shopping'],
    'couple',
    0
) ON CONFLICT (user_id) DO NOTHING;

-- Destinations favorites
INSERT INTO user_favorite_destinations (user_id, pays, ville, note, deja_visite) VALUES
(1, 'Italie', 'Rome', 5, TRUE),
(1, 'Espagne', 'Barcelone', 5, TRUE),
(1, 'Japon', 'Tokyo', 4, FALSE)
ON CONFLICT DO NOTHING;

-- Blacklist
INSERT INTO user_blacklist_destinations (user_id, pays, raison) VALUES
(1, 'Arabie Saoudite', 'Préférence personnelle')
ON CONFLICT DO NOTHING;


-- Utilisateur 2 : Thomas Martin (backpacker, aventure & nature)
INSERT INTO users (id, nom, prenom, email, password_hash, date_naissance, langue_preferee) VALUES
(2, 'Martin', 'Thomas', 'thomas.martin@example.com', '$2b$12$eUDlKxuNaber8ss7D/StDeNLDqfqeJQRb.PSu4wXnGPi3K0nCZXQC', '1995-08-22', 'fr')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_travel_profile (
    user_id,
    budget_quotidien_moyen,
    devise_preferee,
    style_voyage,
    rythme_prefere,
    cuisines_preferees,
    etoiles_min_preferees,
    prefere_centre_ville,
    modes_transport_preferes,
    centres_interet,
    voyage_generalement_avec,
    nombre_enfants
) VALUES (
    2,
    40, -- 40€/jour
    'EUR',
    'routard',
    'intense',
    ARRAY['locale', 'street_food'],
    1,
    FALSE, -- Préfère hors du centre
    ARRAY['bus', 'train', 'stop'],
    ARRAY['nature', 'aventure', 'randonnée', 'photographie'],
    'solo',
    0
) ON CONFLICT (user_id) DO NOTHING;


-- Voyage planifié pour Marie : Week-end à Paris
INSERT INTO trips (
    user_id,
    titre,
    destination_principale,
    pays,
    date_debut,
    date_fin,
    duree_jours,
    budget_total,
    statut
) VALUES (
    1,
    'Week-end romantique à Paris',
    'Paris',
    'France',
    '2026-06-15',
    '2026-06-17',
    3,
    600,
    'planification'
) ON CONFLICT DO NOTHING;


-- Hôtel sauvegardé pour Paris
INSERT INTO trip_hotels (
    trip_id,
    nom_hotel,
    adresse,
    ville,
    pays,
    latitude,
    longitude,
    etoiles,
    prix_nuit,
    date_checkin,
    date_checkout,
    nombre_nuits,
    statut,
    score_match_profil
) VALUES (
    1,
    'Hôtel Le Marais Boutique',
    '12 Rue des Archives',
    'Paris',
    'France',
    48.859180,
    2.357200,
    4,
    180.00,
    '2026-06-15',
    '2026-06-17',
    2,
    'wishlist',
    92
) ON CONFLICT DO NOTHING;


-- Restaurant sauvegardé
INSERT INTO trip_restaurants (
    trip_id,
    nom_restaurant,
    adresse,
    ville,
    types_cuisine,
    prix_moyen,
    note_moyenne,
    options_vegetariennes,
    score_match_profil
) VALUES (
    1,
    'Le Comptoir du Relais',
    '9 Carrefour de l''Odéon',
    'Paris',
    ARRAY['française', 'bistrot'],
    '€€',
    4.5,
    TRUE,
    88
) ON CONFLICT DO NOTHING;


-- Activités planifiées
INSERT INTO trip_activities (
    trip_id,
    nom_activite,
    type_activite,
    ville,
    duree_estimee,
    prix,
    score_match_profil
) VALUES (
    1,
    'Visite du Musée d''Orsay',
    'musée',
    'Paris',
    180,
    16.00,
    95
),
(
    1,
    'Promenade dans le Marais',
    'découverte',
    'Paris',
    120,
    0.00,
    90
) ON CONFLICT DO NOTHING;


-- Informations pays
INSERT INTO countries_info (code_pays, nom_pays, capitale, langues, devise_code) VALUES
('FRA', 'France', 'Paris', ARRAY['français'], 'EUR'),
('ITA', 'Italie', 'Rome', ARRAY['italien'], 'EUR'),
('ESP', 'Espagne', 'Madrid', ARRAY['espagnol'], 'EUR'),
('JPN', 'Japon', 'Tokyo', ARRAY['japonais'], 'JPY')
ON CONFLICT (code_pays) DO NOTHING;