-- CRATE DATABASE IF NOT EXISTS database

CREATE DATABASE database;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
   --- CONSTRAINT valid_email CHECK (email LIKE '%@%.%') -- basic email format validation
    display_name TEXT

);

--- sqllite3 database.db "read schema.sql"