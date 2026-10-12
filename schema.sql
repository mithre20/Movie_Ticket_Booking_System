-- ====================================================================
-- CineMithresh Cinema Booking System - Production MySQL Database Schema
-- Compatible with MySQL 8.0+ and MariaDB 10.4+
-- ====================================================================

CREATE DATABASE IF NOT EXISTS cinemithresh_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cinemithresh_db;

-- 1. Users & Authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    cine_points INT DEFAULT 450,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Movies Catalog
CREATE TABLE IF NOT EXISTS movies (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    genre VARCHAR(100) NOT NULL,
    language VARCHAR(100) NOT NULL,
    rating DECIMAL(3,1) DEFAULT 8.0,
    votes VARCHAR(20) DEFAULT '10K',
    duration VARCHAR(20) NOT NULL,
    certificate VARCHAR(20) NOT NULL,
    poster VARCHAR(255) NOT NULL,
    backdrop VARCHAR(255) NOT NULL,
    synopsis TEXT,
    cast TEXT,
    director VARCHAR(100),
    trailer_url VARCHAR(255),
    formats VARCHAR(150) DEFAULT 'Dolby Atmos 7.1',
    status VARCHAR(20) DEFAULT 'now_showing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_movie_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Screens / Theaters
CREATE TABLE IF NOT EXISTS screens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    features VARCHAR(255) DEFAULT '4K Laser & Dolby Atmos',
    total_seats INT DEFAULT 80
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Seat Definitions Master (80 seats in total: rows A-H, 10 seats each)
CREATE TABLE IF NOT EXISTS seat_definitions (
    id VARCHAR(10) PRIMARY KEY,
    row_label VARCHAR(2) NOT NULL,
    seat_number INT NOT NULL,
    tier VARCHAR(20) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_vip BOOLEAN DEFAULT FALSE,
    INDEX idx_seat_tier (tier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Shows Schedule
CREATE TABLE IF NOT EXISTS shows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id VARCHAR(50) NOT NULL,
    screen_id INT NOT NULL,
    show_date VARCHAR(40) NOT NULL,
    show_time VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE,
    UNIQUE KEY uq_show_slot (movie_id, screen_id, show_date, show_time),
    INDEX idx_show_movie (movie_id),
    INDEX idx_show_date (show_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Temporary Seat Holds (Concurrency control with TTL expiry)
CREATE TABLE IF NOT EXISTS seat_holds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT NOT NULL,
    seat_id VARCHAR(10) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    user_id INT DEFAULT NULL,
    held_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES seat_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uq_show_seat_hold (show_id, seat_id),
    INDEX idx_hold_expiry (expires_at),
    INDEX idx_hold_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Bookings Master
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_ref VARCHAR(50) NOT NULL UNIQUE,
    user_id INT DEFAULT NULL,
    show_id INT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(150) NOT NULL,
    customer_phone VARCHAR(20) DEFAULT NULL,
    ticket_subtotal DECIMAL(10,2) NOT NULL,
    snacks_subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    convenience_fee DECIMAL(10,2) NOT NULL DEFAULT 30.00,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    promo_code VARCHAR(30) DEFAULT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'completed',
    payment_method VARCHAR(40) DEFAULT 'TEST_SANDBOX_GATEWAY',
    payment_ref VARCHAR(100) DEFAULT NULL,
    qr_token VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE RESTRICT,
    INDEX idx_booking_user (user_id),
    INDEX idx_booking_email (customer_email),
    INDEX idx_booking_ref (booking_ref)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Booked Seats (Strict Unique Constraint prevents double-booking)
CREATE TABLE IF NOT EXISTS booked_seats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    show_id INT NOT NULL,
    seat_id VARCHAR(10) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES seat_definitions(id) ON DELETE RESTRICT,
    UNIQUE KEY uq_show_seat_booked (show_id, seat_id),
    INDEX idx_booked_show (show_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Snacks Master
CREATE TABLE IF NOT EXISTS snacks (
    id VARCHAR(30) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '🍿',
    price DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Booking Snacks Detail
CREATE TABLE IF NOT EXISTS booking_snacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    snack_id VARCHAR(30) NOT NULL,
    quantity INT NOT NULL,
    price_per_item DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (snack_id) REFERENCES snacks(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Audience Reviews
CREATE TABLE IF NOT EXISTS reviews (
    id VARCHAR(50) PRIMARY KEY,
    movie_id VARCHAR(50) NOT NULL,
    user_id INT DEFAULT NULL,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL,
    likes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_review_movie (movie_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Promotional Coupons
CREATE TABLE IF NOT EXISTS coupons (
    code VARCHAR(30) PRIMARY KEY,
    discount_percent DECIMAL(5,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    description VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Legacy CGI compatibility tables
CREATE TABLE IF NOT EXISTS login_page (
    id INT AUTO_INCREMENT PRIMARY KEY,
    UserName VARCHAR(100),
    Email VARCHAR(150),
    Password VARCHAR(255),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Movie VARCHAR(150),
    Seats VARCHAR(50),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100),
    Email VARCHAR(150),
    rate VARCHAR(50),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
