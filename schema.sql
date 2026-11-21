CREATE DATABASE IF NOT EXISTS lifelink_ai
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE lifelink_ai;

-- The backend's SQLAlchemy models create the same initial tables on startup.
-- This SQL is also provided for database setup and inspection.

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','hospital','blood_bank','donor') NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_email (email)
);

CREATE TABLE IF NOT EXISTS hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  name VARCHAR(180) NOT NULL,
  address TEXT NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  CONSTRAINT fk_hospital_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_hospital_city (city)
);

CREATE TABLE IF NOT EXISTS blood_banks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  name VARCHAR(180) NOT NULL,
  license_number VARCHAR(100) NOT NULL UNIQUE,
  address TEXT NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_bank_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_bank_city (city)
);

CREATE TABLE IF NOT EXISTS donors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  blood_group VARCHAR(3) NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  consent_to_alerts BOOLEAN NOT NULL DEFAULT FALSE,
  available_for_contact BOOLEAN NOT NULL DEFAULT FALSE,
  last_donation_date DATETIME NULL,
  CONSTRAINT fk_donor_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_donor_group_city (blood_group, city)
);

CREATE TABLE IF NOT EXISTS blood_units (
  id INT AUTO_INCREMENT PRIMARY KEY,
  blood_bank_id INT NOT NULL,
  unit_code VARCHAR(80) NOT NULL UNIQUE,
  blood_group VARCHAR(3) NOT NULL,
  component VARCHAR(40) NOT NULL,
  quantity_ml INT NOT NULL DEFAULT 450,
  collection_date DATETIME NOT NULL,
  expiry_date DATETIME NOT NULL,
  screening_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  status VARCHAR(30) NOT NULL DEFAULT 'quarantined',
  CONSTRAINT fk_unit_bank FOREIGN KEY (blood_bank_id) REFERENCES blood_banks(id),
  INDEX idx_unit_search (blood_group, component, status, expiry_date)
);

CREATE TABLE IF NOT EXISTS blood_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hospital_id INT NOT NULL,
  blood_group VARCHAR(3) NOT NULL,
  component VARCHAR(40) NOT NULL,
  units_required INT NOT NULL,
  urgency VARCHAR(20) NOT NULL DEFAULT 'normal',
  city VARCHAR(100) NOT NULL,
  clinical_reference VARCHAR(100) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_request_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
  INDEX idx_request_status_city (status, city)
);

CREATE TABLE IF NOT EXISTS notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(180) NOT NULL,
  message TEXT NOT NULL,
  channel VARCHAR(30) NOT NULL DEFAULT 'in_app',
  status VARCHAR(30) NOT NULL DEFAULT 'queued',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_notification_user (user_id, created_at)
);
CREATE TABLE IF NOT EXISTS blood_bank_responses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  request_id INT NOT NULL,
  blood_bank_id INT NOT NULL,
  response_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  units_offered INT NOT NULL DEFAULT 0,
  response_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  responded_at DATETIME NULL,
  CONSTRAINT fk_response_request
    FOREIGN KEY (request_id) REFERENCES blood_requests(id),
  CONSTRAINT fk_response_bank
    FOREIGN KEY (blood_bank_id) REFERENCES blood_banks(id),
  CONSTRAINT uq_request_blood_bank
    UNIQUE (request_id, blood_bank_id),
  INDEX idx_response_request (request_id),
  INDEX idx_response_bank (blood_bank_id)
);