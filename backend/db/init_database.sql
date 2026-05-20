-- ============================================
-- TRAVEL BUDDY - Base de données 
-- ============================================
-- 1. PROFIL USER (stable) → guide l'IA pour suggérer
-- 2. VOYAGES (ponctuels) → contexte temporaire
-- ============================================


-- Table principale des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Hash du mot de passe (bcrypt/argon2)
    telephone VARCHAR(50),
    date_naissance DATE,
    nationalite VARCHAR(100),
    langue_preferee VARCHAR(10) DEFAULT 'fr',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Profil de voyage PERMANENT de l'utilisateur
CREATE TABLE IF NOT EXISTS user_travel_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    budget_min_habituel INTEGER,
    budget_max_habituel INTEGER,
    devise_preferee VARCHAR(3) DEFAULT 'EUR',
    types_voyage_preferes TEXT[],
    rythme_prefere VARCHAR(50),    
    duree_voyage_typique INTEGER, 
    periodes_preferees TEXT[],
    regime_alimentaire TEXT[],    
    allergies_alimentaires TEXT[],    
    cuisines_preferees TEXT[],
    categories_hotel_preferees TEXT[],
    etoiles_min_preferees INTEGER CHECK (etoiles_min_preferees BETWEEN 1 AND 5),
    etoiles_max_preferees INTEGER CHECK (etoiles_max_preferees BETWEEN 1 AND 5),
    prefere_centre_ville BOOLEAN DEFAULT TRUE,
    prefere_calme BOOLEAN DEFAULT FALSE,
    prefere_proche_transport BOOLEAN DEFAULT TRUE,
    types_logement_acceptes TEXT[],    
    equipements_essentiels TEXT[],
    equipements_souhaites TEXT[],
    exige_annulation_gratuite BOOLEAN DEFAULT TRUE,
    accepte_paiement_sur_place BOOLEAN DEFAULT TRUE,
    modes_transport_preferes TEXT[],    
    classe_vol_preferee VARCHAR(50),    
    accepte_escales BOOLEAN DEFAULT TRUE,
    voyage_generalement_avec TEXT[],    
    nombre_enfants INTEGER DEFAULT 0,
    ages_enfants INTEGER[],
    contraintes_mobilite TEXT[],    
    climats_preferes TEXT[],    
    types_destinations_preferees TEXT[],    
    centres_interet TEXT[],
    problemes_sante TEXT[],    
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_travel_profile_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS user_favorite_destinations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    pays VARCHAR(255) NOT NULL,
    ville VARCHAR(255),
    raison TEXT, 
    note INTEGER CHECK (note BETWEEN 1 AND 5),
    deja_visite BOOLEAN DEFAULT FALSE,
    aimerait_revisiter BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_favorite_destinations_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

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
    budget_deja_depense INTEGER DEFAULT 0,
    objectif_voyage TEXT,    
    contraintes_speciales TEXT[],
    statut VARCHAR(50) DEFAULT 'planification',
    itineraire_detaille JSONB,
    notes_voyage TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_trips_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trip_hotels (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    hotel_api_id VARCHAR(255),
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
    hotel_data JSONB,
    statut VARCHAR(50) DEFAULT 'wishlist',    
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    raisons_match TEXT[],    
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_trip_hotels_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trip_restaurants (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    nom_restaurant VARCHAR(255) NOT NULL,
    adresse TEXT,
    ville VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    types_cuisine TEXT[],
    prix_moyen VARCHAR(20),
    note_moyenne DECIMAL(3, 2),
    source_note VARCHAR(50),
    options_vegetariennes BOOLEAN,
    options_vegan BOOLEAN,
    options_sans_gluten BOOLEAN,
    reservation_requise BOOLEAN,
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    raisons_match TEXT[],
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_trip_restaurants_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trip_activities (
    id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    nom_activite VARCHAR(255) NOT NULL,
    type_activite VARCHAR(100),
    adresse TEXT,
    ville VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    duree_estimee INTEGER,
    prix DECIMAL(10, 2),
    horaires_ouverture JSONB,
    score_match_profil INTEGER CHECK (score_match_profil BETWEEN 0 AND 100),
    raisons_match TEXT[],
    notes_personnelles TEXT,
    saved_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_trip_activities_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    trip_id INTEGER, 
    query TEXT NOT NULL,
    query_type VARCHAR(50),    
    destination VARCHAR(255),
    results_summary JSONB,
    tools_called TEXT[],
    user_clicked_results JSONB,    
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    searched_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_search_history_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_search_history_trip 
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS weather_cache (
    id SERIAL PRIMARY KEY,
    ville VARCHAR(255) NOT NULL,
    pays VARCHAR(255),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    date_prevision DATE NOT NULL,
    temperature_min DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    precipitation_mm DECIMAL(5, 2),
    conditions VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ville, pays, date_prevision)
);

CREATE TABLE IF NOT EXISTS countries_info (
    id SERIAL PRIMARY KEY,
    code_pays VARCHAR(3) UNIQUE NOT NULL,
    nom_pays VARCHAR(255) NOT NULL,
    capitale VARCHAR(255),
    region VARCHAR(100),
    population BIGINT,
    langues TEXT[],
    devises JSONB,
    country_data JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_documents (
    id SERIAL PRIMARY KEY,
    
    source_type VARCHAR(50),
    source_url TEXT,
    
    destination VARCHAR(255),
    pays VARCHAR(255),
    categorie VARCHAR(100),
    
    contenu_texte TEXT NOT NULL,

    langue VARCHAR(10) DEFAULT 'fr',
    fiabilite INTEGER CHECK (fiabilite BETWEEN 1 AND 5),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    
    embedding_id VARCHAR(255),
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_rag_chunks_document 
        FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);

-- ============================================
-- INDEX
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
CREATE INDEX idx_trip_hotels_ville ON trip_hotels(ville, pays);
CREATE INDEX idx_trip_restaurants_trip ON trip_restaurants(trip_id);
CREATE INDEX idx_trip_activities_trip ON trip_activities(trip_id);

-- Search history
CREATE INDEX idx_search_user_date ON search_history(user_id, searched_at DESC);
CREATE INDEX idx_search_trip ON search_history(trip_id);

-- Cache
CREATE INDEX idx_weather_location ON weather_cache(ville, pays, date_prevision);
CREATE INDEX idx_countries_code ON countries_info(code_pays);

-- RAG
CREATE INDEX idx_rag_docs_destination ON rag_documents(destination);
CREATE INDEX idx_rag_chunks_document ON rag_chunks(document_id);

-- Favorites
CREATE INDEX idx_favorites_user ON user_favorite_destinations(user_id);
CREATE INDEX idx_blacklist_user ON user_blacklist_destinations(user_id);


-- ============================================
-- DONNÉES DE TEST
-- ============================================

-- Utilisateur 1 : Marie Dupont (voyageuse régulière, budget moyen-haut)
-- Mot de passe : "password123" (hash bcrypt)
INSERT INTO users (id, nom, prenom, email, password_hash, telephone, date_naissance, nationalite, langue_preferee) VALUES
(1, 'Dupont', 'Marie', 'marie.dupont@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYNZ0zJ5C', '+33612345678', '1990-05-15', 'France', 'fr')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_travel_profile (
    user_id, 
    budget_min_habituel, 
    budget_max_habituel,
    devise_preferee,
    types_voyage_preferes,
    rythme_prefere,
    duree_voyage_typique,
    periodes_preferees,
    regime_alimentaire,
    cuisines_preferees,
    categories_hotel_preferees,
    etoiles_min_preferees,
    etoiles_max_preferees,
    prefere_centre_ville,
    prefere_calme,
    prefere_proche_transport,
    types_logement_acceptes,
    equipements_essentiels,
    equipements_souhaites,
    exige_annulation_gratuite,
    modes_transport_preferes,
    classe_vol_preferee,
    accepte_escales,
    voyage_generalement_avec,
    nombre_enfants,
    climats_preferes,
    types_destinations_preferees,
    centres_interet
) VALUES (
    1,
    80,
    200,
    'EUR',
    ARRAY['culturel', 'gastronomique', 'city-break'],
    'modéré',
    5,
    ARRAY['printemps', 'automne'],
    ARRAY['végétarien'],
    ARRAY['française', 'italienne', 'japonaise'],
    ARRAY['boutique', 'charme'],
    3,
    5,
    TRUE,
    FALSE,
    TRUE,
    ARRAY['hotel', 'appartement'],
    ARRAY['wifi', 'petit-déjeuner', 'climatisation'],
    ARRAY['spa', 'salle_sport', 'restaurant'],
    TRUE,
    ARRAY['avion', 'train'],
    'économique',
    TRUE,
    ARRAY['en_couple'],
    0,
    ARRAY['tempéré', 'méditerranéen'],
    ARRAY['capitales_européennes', 'villes_historiques'],
    ARRAY['musées', 'gastronomie', 'architecture', 'shopping']
) ON CONFLICT (user_id) DO NOTHING;

-- Destinations favorites de Marie
INSERT INTO user_favorite_destinations (user_id, pays, ville, raison, note, deja_visite, aimerait_revisiter) VALUES
(1, 'Italie', 'Rome', 'Architecture magnifique et cuisine délicieuse', 5, TRUE, TRUE),
(1, 'Espagne', 'Barcelone', 'Culture vibrante et plages', 5, TRUE, FALSE),
(1, 'Japon', 'Tokyo', 'Fascinant mélange tradition/modernité', 4, FALSE, FALSE)
ON CONFLICT DO NOTHING;

-- Blacklist
INSERT INTO user_blacklist_destinations (user_id, pays, raison) VALUES
(1, 'Arabie Saoudite', 'Préférence personnelle')
ON CONFLICT DO NOTHING;

-- Utilisateur 2 : Thomas Martin (backpacker, petit budget)
-- Mot de passe : "password456" (hash bcrypt)
INSERT INTO users (id, nom, prenom, email, password_hash, telephone, date_naissance, nationalite, langue_preferee) VALUES
(2, 'Martin', 'Thomas', 'thomas.martin@example.com', '$2b$12$eUDlKxuNaber8ss7D/StDeNLDqfqeJQRb.PSu4wXnGPi3K0nCZXQC', '+33623456789', '1995-08-22', 'France', 'fr')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_travel_profile (
    user_id,
    budget_min_habituel,
    budget_max_habituel,
    devise_preferee,
    types_voyage_preferes,
    rythme_prefere,
    duree_voyage_typique,
    periodes_preferees,
    cuisines_preferees,
    etoiles_min_preferees,
    etoiles_max_preferees,
    prefere_centre_ville,
    types_logement_acceptes,
    equipements_essentiels,
    modes_transport_preferes,
    classe_vol_preferee,
    accepte_escales,
    voyage_generalement_avec,
    climats_preferes,
    types_destinations_preferees,
    centres_interet
) VALUES (
    2,
    20,
    60,
    'EUR',
    ARRAY['aventure', 'nature', 'backpacking'],
    'intense',
    14,
    ARRAY['été', 'hiver'],
    ARRAY['locale', 'street_food'],
    1,
    3,
    FALSE,
    ARRAY['auberge_jeunesse', 'camping', 'airbnb'],
    ARRAY['wifi'],
    ARRAY['bus', 'train', 'stop'],
    'économique',
    TRUE,
    ARRAY['entre_amis', 'solo'],
    ARRAY['tropical', 'montagnard'],
    ARRAY['pays_exotiques', 'hors_sentiers_battus'],
    ARRAY['randonnée', 'plongée', 'photographie', 'rencontres_locales']
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
    objectif_voyage,
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
    'Découvrir les quartiers romantiques et la gastronomie parisienne',
    'planification'
) ON CONFLICT DO NOTHING;

-- Hotels enregistrés pour le voyage à Paris
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
    score_match_profil,
    raisons_match
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
    92,
    ARRAY['Centre-ville', 'Quartier historique', 'Style boutique', 'Excellent rapport qualité-prix']
) ON CONFLICT DO NOTHING;

-- Restaurants sauvegardés
INSERT INTO trip_restaurants (
    trip_id,
    nom_restaurant,
    adresse,
    ville,
    types_cuisine,
    prix_moyen,
    note_moyenne,
    options_vegetariennes,
    score_match_profil,
    raisons_match
) VALUES (
    1,
    'Le Comptoir du Relais',
    '9 Carrefour de l''Odéon',
    'Paris',
    ARRAY['française', 'bistrot'],
    '€€',
    4.5,
    TRUE,
    88,
    ARRAY['Cuisine française authentique', 'Options végétariennes', 'Quartier Saint-Germain']
) ON CONFLICT DO NOTHING;

-- Activités planifiées
INSERT INTO trip_activities (
    trip_id,
    nom_activite,
    type_activite,
    ville,
    duree_estimee,
    prix,
    score_match_profil,
    raisons_match
) VALUES (
    1,
    'Visite du Musée d''Orsay',
    'culturel',
    'Paris',
    180,
    16.00,
    95,
    ARRAY['Passion pour l''art', 'Impressionnisme', 'Architecture du bâtiment']
),
(
    1,
    'Promenade dans le Marais',
    'découverte',
    'Paris',
    120,
    0.00,
    90,
    ARRAY['Quartier historique', 'Boutiques', 'Cafés charmants']
) ON CONFLICT DO NOTHING;

-- Historique de recherche
INSERT INTO search_history (
    user_id,
    trip_id,
    query,
    query_type,
    destination,
    tools_called
) VALUES (
    1,
    1,
    'Meilleurs restaurants végétariens à Paris',
    'restaurant',
    'Paris',
    ARRAY['search_restaurants', 'filter_by_diet']
),
(
    1,
    NULL,
    'Que faire à Lisbonne en 3 jours',
    'itineraire',
    'Lisbonne',
    ARRAY['get_city_info', 'suggest_activities']
) ON CONFLICT DO NOTHING;

-- Informations pays (cache)
INSERT INTO countries_info (
    code_pays,
    nom_pays,
    capitale,
    region,
    population,
    langues,
    devises
) VALUES (
    'FRA',
    'France',
    'Paris',
    'Europe',
    67000000,
    ARRAY['français'],
    '{"EUR": {"name": "Euro", "symbol": "€"}}'::jsonb
),
(
    'ITA',
    'Italie',
    'Rome',
    'Europe',
    60000000,
    ARRAY['italien'],
    '{"EUR": {"name": "Euro", "symbol": "€"}}'::jsonb
),
(
    'ESP',
    'Espagne',
    'Madrid',
    'Europe',
    47000000,
    ARRAY['espagnol'],
    '{"EUR": {"name": "Euro", "symbol": "€"}}'::jsonb
) ON CONFLICT (code_pays) DO NOTHING;