-- Exécuté une seule fois, à la première création du volume Postgres.
-- La base "warehouse" (POSTGRES_DB) est déjà créée par l'image.

-- Base de métadonnées d'Airflow, séparée de l'entrepôt de données
CREATE DATABASE airflow;

-- Couche brute (alimentée par Python) ; dbt crée les autres schémas
CREATE SCHEMA IF NOT EXISTS raw;
