CREATE TABLE IF NOT EXISTS listing_master (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    business_name VARCHAR(255) NOT NULL,
    category VARCHAR(120) NOT NULL,
    city VARCHAR(120) NOT NULL,
    address VARCHAR(512) NOT NULL,
    phone VARCHAR(64) NULL,
    source VARCHAR(80) NOT NULL,
    source_url VARCHAR(1024) NOT NULL,
    source_id VARCHAR(512) NOT NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_listing_source_id (source, source_id),
    KEY idx_listing_city (city),
    KEY idx_listing_category (category),
    KEY idx_listing_source (source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
