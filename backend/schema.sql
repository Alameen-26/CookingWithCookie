-- Cooking with Cookie menu database (schema version 2).
--
-- ingredients, allergens and recipe_steps come from TYPICAL recipes for each
-- dish, not from Cooking with Cookie's own recipes. They are marked as
-- unverified (ingredients_verified = 0, allergens_verified = 0) until the
-- owner checks them. calories is NULL (unknown) until the owner adds it.
-- Prices are prototype placeholders and stay hidden while SHOW_PRICES is off.
PRAGMA user_version = 2;
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,                                -- CAD, placeholder
    available INTEGER NOT NULL DEFAULT 1,
    ingredients TEXT,                                   -- comma-separated
    ingredients_verified INTEGER NOT NULL DEFAULT 0,    -- 0 = typical recipe
    calories INTEGER,                                   -- per serving, NULL = unknown
    allergens TEXT,                                     -- comma-separated
    allergens_verified INTEGER NOT NULL DEFAULT 0,      -- 0 = likely, not verified
    recipe_steps TEXT                                   -- one step per line
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Jollof Rice & Peppered Chicken',
    'Smoky party-style jollof rice with spicy peppered chicken.',
    20.00,
    'Long-grain parboiled rice, tomatoes, red bell peppers, scotch bonnet peppers, onions, tomato paste, vegetable oil, chicken, stock cubes, curry powder, dried thyme, bay leaves, garlic, ginger',
    'Wheat, Soy (possible, from stock cubes)',
    '1. Season chicken with onion, garlic, ginger, thyme, curry and stock cubes; boil until tender and keep the stock.
2. Fry or grill the chicken until golden, then toss it in a quick sauce of blended scotch bonnet, onion and a little oil for peppered chicken.
3. Blend tomatoes, red bell peppers, scotch bonnet and onion.
4. Fry sliced onions and tomato paste in oil for a few minutes, add the blend and cook until thick and the oil rises (20-30 minutes).
5. Season with curry, thyme, bay leaves and stock cubes, add the chicken stock, then stir in washed parboiled rice.
6. Cover tightly and cook on low heat until the rice is tender, adding small splashes of stock if needed. Letting the bottom toast slightly gives the smoky party flavour.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Fried Rice',
    'Nigerian fried rice with mixed vegetables, shrimp and a hint of curry.',
    20.00,
    'Long-grain parboiled rice, carrots, green beans, peas, sweet corn, green bell pepper, onions, shrimp, chicken stock, stock cubes, curry powder, dried thyme, vegetable oil, butter',
    'Shellfish (shrimp), Milk (butter), Wheat, Soy (possible, from stock cubes)',
    '1. Parboil the rice in chicken stock with curry powder and thyme until almost cooked, then drain and spread out to cool.
2. Dice the carrots, green beans and green pepper; have the peas and sweet corn ready.
3. Lightly fry the shrimp in a little butter or oil and set aside.
4. Fry the rice in small batches over high heat with oil or butter, onions and the vegetables.
5. Season with curry, thyme and stock cubes, then fold in the shrimp. Serve hot.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Nigerian Shawarma',
    'A Nigerian-style wrap with spiced chicken or beef, sausage, cabbage and creamy sauce.',
    16.00,
    'Flatbread (shawarma bread), chicken or beef, sausage, cabbage, carrots, cucumber, onions, mayonnaise, ketchup, spices, vegetable oil',
    'Wheat (gluten), Eggs (mayonnaise), Soy, Milk, Mustard (possible, from bread, sauces and sausage)',
    '1. Marinate thin strips of chicken or beef with spices, garlic and a little oil, then pan-fry or grill.
2. Grill the sausages and slice them lengthwise.
3. Shred cabbage and carrots, and slice cucumber and onion.
4. Mix mayonnaise and ketchup for the sauce.
5. Warm the flatbread, spread the sauce, add the vegetables, meat and sausage, then roll it up tightly.
6. Toast the wrap in a dry pan or on a grill until crisp on both sides.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Puff-Puff',
    'Soft, golden fried dough balls with a light nutmeg sweetness.',
    15.00,
    'Wheat flour, yeast, sugar, nutmeg, salt, warm water, vegetable oil for frying',
    'Wheat (gluten)',
    '1. Mix the flour, sugar, yeast, nutmeg and a pinch of salt.
2. Add warm water gradually and mix into a smooth, thick, slightly stretchy batter.
3. Cover and leave in a warm place for 45-60 minutes until doubled and bubbly.
4. Heat oil to about 175°C (350°F).
5. Drop small balls of batter into the oil with your hand or a spoon and fry, turning, until golden all over.
6. Drain on paper towels and serve warm.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Meat Pie',
    'Buttery pastry filled with seasoned minced beef, potato and carrot.',
    15.00,
    'Wheat flour, butter or margarine, eggs, baking powder, salt, minced beef, potatoes, carrots, onions, stock cubes, curry powder, dried thyme',
    'Wheat (gluten), Milk (butter), Eggs, Soy (possible, from stock cubes)',
    '1. Rub butter into the flour, baking powder and salt until crumbly, add a beaten egg and cold water to form a dough, then chill it for 30 minutes.
2. Brown the minced beef with onions, season with curry, thyme and stock cubes, add diced potatoes, carrots and a little water, thicken with a spoon of flour mixed with water, and let it cool.
3. Roll out the dough and cut it into circles.
4. Spoon filling onto each circle, fold over and seal the edges with a fork.
5. Brush with egg wash and bake at 180°C (350°F) for 30-40 minutes until golden.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Jollof Spaghetti',
    'Spaghetti cooked in a rich, peppery jollof tomato sauce.',
    17.00,
    'Spaghetti, tomatoes, red bell peppers, scotch bonnet peppers, onions, tomato paste, vegetable oil, stock cubes, curry powder, dried thyme',
    'Wheat (gluten), Soy (possible, from stock cubes)',
    '1. Blend tomatoes, red bell peppers, scotch bonnet and onion.
2. Fry tomato paste and onions in oil, add the blend and cook until thick (20-30 minutes).
3. Season with curry, thyme and stock cubes, then add stock or water.
4. Break in the spaghetti and cook it in the sauce, stirring now and then, until tender and the sauce is absorbed.
5. Add a protein of your choice if you like, and serve.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Beef Stir-fry Spaghetti',
    'Spaghetti tossed with tender beef strips and colourful stir-fried vegetables.',
    19.00,
    'Spaghetti, beef strips, bell peppers, carrots, onions, garlic, ginger, soy sauce, stock cubes, vegetable oil',
    'Wheat (gluten), Soy (soy sauce)',
    '1. Boil the spaghetti until al dente, drain and toss with a little oil.
2. Marinate thin beef strips with soy sauce, garlic, ginger and a crumbled stock cube.
3. Stir-fry the beef in a very hot pan until browned, then remove it.
4. Stir-fry sliced onions, bell peppers and carrots for 2-3 minutes so they stay crunchy.
5. Return the beef, add the spaghetti and toss everything with soy sauce and seasoning until hot.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Dirty Rice',
    'Rustic native-style rice cooked in palm oil with peppers, crayfish and smoked fish.',
    18.00,
    'Long-grain rice, palm oil, onions, scotch bonnet peppers, ground crayfish, locust beans (iru), smoked fish, stock cubes, leafy greens',
    'Crustaceans (crayfish), Fish (smoked fish), Wheat, Soy (possible, from stock cubes)',
    '1. Heat the palm oil gently (don''t let it smoke) and fry chopped onions.
2. Add blended or chopped scotch bonnet, locust beans (iru) and ground crayfish and fry for a few minutes.
3. Add stock, stock cubes and flaked smoked fish, and bring to a boil.
4. Stir in washed rice, cover and cook on low heat until tender.
5. Fold in chopped leafy greens at the end and let them wilt before serving.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Stew (Beef)',
    'Classic Nigerian tomato and pepper stew with tender beef.',
    20.00,
    'Tomatoes, red bell peppers, scotch bonnet peppers, onions, vegetable oil, beef, stock cubes, curry powder, dried thyme, garlic, ginger, bay leaves',
    'Wheat, Soy (possible, from stock cubes)',
    '1. Blend tomatoes, red bell peppers, scotch bonnet and onion, then boil the blend to reduce the water.
2. Season the beef with onion, garlic, ginger, thyme and stock cubes and cook until tender (keep the stock), then fry or grill it.
3. Fry sliced onions in oil, add the reduced pepper blend and fry for 20-30 minutes, stirring, until the oil rises to the top.
4. Add the stock, curry, thyme, bay leaves and stock cubes, then simmer for 10 minutes.
5. Add the beef, simmer a few more minutes and adjust the salt. Serve with rice, yam or plantain.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Stew (Chicken)',
    'Classic Nigerian tomato and pepper stew with chicken.',
    19.00,
    'Tomatoes, red bell peppers, scotch bonnet peppers, onions, vegetable oil, chicken, stock cubes, curry powder, dried thyme, garlic, ginger, bay leaves',
    'Wheat, Soy (possible, from stock cubes)',
    '1. Blend tomatoes, red bell peppers, scotch bonnet and onion, then boil the blend to reduce the water.
2. Season the chicken with onion, garlic, ginger, thyme and stock cubes and cook until tender (keep the stock), then fry or grill it.
3. Fry sliced onions in oil, add the reduced pepper blend and fry for 20-30 minutes, stirring, until the oil rises to the top.
4. Add the stock, curry, thyme, bay leaves and stock cubes, then simmer for 10 minutes.
5. Add the chicken, simmer a few more minutes and adjust the salt. Serve with rice, yam or plantain.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Stew (Fish)',
    'Classic Nigerian tomato and pepper stew with fried fish.',
    22.00,
    'Tomatoes, red bell peppers, scotch bonnet peppers, onions, vegetable oil, fish (such as mackerel or tilapia), stock cubes, curry powder, dried thyme, garlic, ginger, bay leaves',
    'Fish, Wheat, Soy (possible, from stock cubes)',
    '1. Blend tomatoes, red bell peppers, scotch bonnet and onion, then boil the blend to reduce the water.
2. Season the fish pieces with salt and stock cube, then fry or grill until firm and golden.
3. Fry sliced onions in oil, add the reduced pepper blend and fry for 20-30 minutes, stirring, until the oil rises to the top.
4. Add a little water or stock, curry, thyme, bay leaves, garlic, ginger and stock cubes, then simmer for 10 minutes.
5. Add the fish gently and simmer for a few minutes without stirring hard so it doesn''t break. Serve with rice, yam or plantain.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Egusi',
    'Rich melon-seed soup with leafy greens, palm oil, meat and fish.',
    22.00,
    'Ground egusi (melon seeds), palm oil, spinach or bitter leaf, beef and assorted meat, stockfish or dried fish, ground crayfish, locust beans (iru), scotch bonnet peppers, onions, stock cubes',
    'Fish (stockfish, dried fish), Crustaceans (crayfish), Seeds (melon seeds), Wheat, Soy (possible, from stock cubes)',
    '1. Season and boil the beef and assorted meat with onions and stock cubes until tender, keeping the stock. Soak and rinse the stockfish or dried fish.
2. Mix the ground egusi with a little water (or blended onion) into a thick paste.
3. Heat palm oil, add the egusi paste in small lumps and fry gently for 5-10 minutes, stirring now and then.
4. Add the meat stock, peppers, crayfish, locust beans, meat and fish, and simmer for 10-15 minutes.
5. Stir in washed, chopped spinach or bitter leaf and cook for a few minutes. Serve with pounded yam, eba or rice.'
);
INSERT INTO menu_items (name, description, price, ingredients, allergens, recipe_steps)
VALUES (
    'Beans Porridge',
    'Slow-cooked black-eyed beans in a savoury palm-oil and pepper sauce.',
    16.00,
    'Black-eyed beans, palm oil, onions, scotch bonnet peppers, ground crayfish, stock cubes, salt',
    'Crustaceans (crayfish), Legumes (black-eyed beans), Wheat, Soy (possible, from stock cubes)',
    '1. Rinse the black-eyed beans (soaking them for an hour shortens cooking), then boil until soft, topping up with water as needed.
2. Add chopped onions, blended scotch bonnet, ground crayfish and stock cubes.
3. Pour in the palm oil and simmer for 10-15 minutes until the beans are creamy and slightly mashed.
4. Optional: add diced ripe plantain for the last 10 minutes.
5. Adjust the salt and serve.'
);
