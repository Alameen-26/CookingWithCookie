CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    available INTEGER NOT NULL DEFAULT 1
);
INSERT INTO menu_items (name, description, price)
VALUES (
    'Jollof Rice Plate',
    'Jollof rice, chicken, plantain and salad',
    18.00
);
INSERT INTO menu_items (name, description, price)
VALUES (
    'Fried Rice Plate',
    'Fried rice, chicken, plantain and salad',
    18.00
);
INSERT INTO menu_items (name, description, price)
VALUES (
    'Chicken Shawarma',
    'Chicken wrap with vegetables and sauce',
    15.00
);
-- Example query: list available items.
-- SELECT name, price
-- FROM menu_items
-- WHERE available = 1
-- ORDER BY name;
