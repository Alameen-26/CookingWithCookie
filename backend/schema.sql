-- Cooking with Cookie menu database.
-- calories and allergens are left NULL until the owner confirms them.
-- The chatbot will say "not confirmed" for any NULL value.
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    available INTEGER NOT NULL DEFAULT 1,
    ingredients TEXT,
    calories INTEGER,   -- per serving, NULL = not confirmed
    allergens TEXT      -- comma-separated, NULL = not confirmed
);
INSERT INTO menu_items (name, description, price, ingredients)
VALUES (
    'Jollof Rice Plate',
    'Jollof rice, chicken, plantain and salad',
    18.00,
    'Jollof rice, chicken, plantain and salad'
);
INSERT INTO menu_items (name, description, price, ingredients)
VALUES (
    'Fried Rice Plate',
    'Fried rice, chicken, plantain and salad',
    18.00,
    'Fried rice, chicken, plantain and salad'
);
INSERT INTO menu_items (name, description, price, ingredients)
VALUES (
    'Chicken Shawarma',
    'Chicken wrap with vegetables and sauce',
    15.00,
    'Chicken wrap with vegetables and sauce'
);
-- Example query: list available items.
-- SELECT name, price
-- FROM menu_items
-- WHERE available = 1
-- ORDER BY name;
