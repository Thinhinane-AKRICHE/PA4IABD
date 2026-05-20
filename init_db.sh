#!/bin/bash
set -e

echo "Initialisation de la base de données Travel Buddy..."

echo "Attente de PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U travelbuddy -d travelbuddy -c '\q'; do
  echo "PostgreSQL non disponible - attente..."
  sleep 2
done

echo "PostgreSQL prêt!"

echo "Exécution du script SQL..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U travelbuddy -d travelbuddy -f /app/db/init_database.sql

echo "Création de l'utilisateur test..."
python /app/core/database.py

echo "Base de données initialisée avec succès!"