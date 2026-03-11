CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    store VARCHAR(20) NOT NULL,
    name TEXT NOT NULL,
    price INT NOT NULL,
    image_url TEXT,
    is_promo BOOLEAN DEFAULT FALSE,
    promotion_type VARCHAR(20),
    is_new BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uniq_item UNIQUE (store, name, promotion_type)
);
