-- RFID-KVC Base User Category Mappings Seed Data
-- Version: 2025-09-26-v1-ai-agent-installation-seed
-- Purpose: Base category mappings for equipment rental classes
-- Usage: AI agent automated installation seed data
--
-- This file provides base user category mappings derived from cats.pdf analysis
-- and existing system patterns for the RFID-KVC bedrock architecture.
--
-- INSTALLATION NOTES FOR AI AGENT:
-- 1. Execute this AFTER creating user_rental_class_mappings table
-- 2. These are baseline mappings - user can override via web interface
-- 3. Store codes: 001=Wayzata, 002=Brooklyn Park, 003=Fridley, 004=Elk River
-- 4. Import priority: User overrides > This seed data > PDF defaults

-- Clear existing mappings (for fresh installation)
DELETE FROM user_rental_class_mappings WHERE store_code IS NULL OR store_code = 'default';

-- Core Table & Chair Equipment
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, store_code) VALUES
('6001', 'Tables', 'Round Tables', '60" Round Table', 'default'),
('6002', 'Tables', 'Round Tables', '72" Round Table', 'default'),
('8001', 'Tables', 'Rectangle Tables', '6ft Rectangle Table', 'default'),
('8002', 'Tables', 'Rectangle Tables', '8ft Rectangle Table', 'default'),
('2001', 'Chairs', 'Folding Chairs', 'White Folding Chair', 'default'),
('2002', 'Chairs', 'Folding Chairs', 'Brown Folding Chair', 'default'),
('2101', 'Chairs', 'Chiavari Chairs', 'Gold Chiavari Chair', 'default'),
('2102', 'Chairs', 'Chiavari Chairs', 'Silver Chiavari Chair', 'default'),

-- Rectangle Linen Categories (High-volume items)
('L6012', 'Rectangle Linen', '60X120 Linen', '60X120 White Linen', 'default'),
('L6013', 'Rectangle Linen', '60X120 Linen', '60X120 Black Linen', 'default'),
('L6014', 'Rectangle Linen', '60X120 Linen', '60X120 Ivory Linen', 'default'),
('L9015', 'Rectangle Linen', '90X156 Linen', '90X156 White Linen', 'default'),
('L9016', 'Rectangle Linen', '90X156 Linen', '90X156 Black Linen', 'default'),

-- Round Linen Categories
('LR12001', 'Round Linen', '120" Round Linen', '120" White Round Linen', 'default'),
('LR12002', 'Round Linen', '120" Round Linen', '120" Black Round Linen', 'default'),
('LR13201', 'Round Linen', '132" Round Linen', '132" White Round Linen', 'default'),
('LR13202', 'Round Linen', '132" Round Linen', '132" Black Round Linen', 'default'),

-- Tableware Categories
('T5001', 'Tableware', 'Flatware Spoons', 'Flatware Spoon, Tablespoon (10 Pack)', 'default'),
('T5002', 'Tableware', 'Flatware Forks', 'Flatware Fork, Dinner (10 Pack)', 'default'),
('T5003', 'Tableware', 'Flatware Knives', 'Flatware Knife, Dinner (10 Pack)', 'default'),
('T6001', 'Tableware', 'Glassware', 'Water Glass (10 Pack)', 'default'),
('T6002', 'Tableware', 'Glassware', 'Wine Glass (10 Pack)', 'default'),
('T7001', 'Tableware', 'China Plates', 'Dinner Plate (10 Pack)', 'default'),
('T7002', 'Tableware', 'China Plates', 'Salad Plate (10 Pack)', 'default'),

-- Tent & Canopy Equipment
('TC2001', 'Tents & Canopies', '20x20 Tents', '20x20 Frame Tent', 'default'),
('TC2002', 'Tents & Canopies', '20x30 Tents', '20x30 Frame Tent', 'default'),
('TC4001', 'Tents & Canopies', '40x40 Tents', '40x40 Frame Tent', 'default'),
('TC4080', 'Tents & Canopies', '40x80 Tents', '40x80 Frame Tent', 'default'),

-- Lighting Equipment
('LT001', 'Lighting', 'String Lights', 'Bistro String Lights (100ft)', 'default'),
('LT002', 'Lighting', 'Chandeliers', 'Crystal Chandelier', 'default'),
('LT003', 'Lighting', 'Market Lights', 'Market String Lights (50ft)', 'default'),
('LT101', 'Lighting', 'Up Lighting', 'LED Up Light (Color Changing)', 'default'),

-- Heater & Climate Equipment
('H001', 'Heaters', 'Propane Heaters', 'Propane Patio Heater', 'default'),
('H002', 'Heaters', 'Electric Heaters', 'Electric Space Heater', 'default'),
('F001', 'Fans', 'Pedestal Fans', 'Industrial Pedestal Fan', 'default'),
('F002', 'Fans', 'Misting Fans', 'Misting Fan System', 'default'),

-- Bar & Beverage Equipment
('B001', 'Bar Equipment', 'Portable Bars', '6ft Portable Bar', 'default'),
('B002', 'Bar Equipment', 'Portable Bars', '8ft Portable Bar', 'default'),
('B101', 'Bar Equipment', 'Bar Stools', 'Black Bar Stool', 'default'),
('B102', 'Bar Equipment', 'Bar Stools', 'White Bar Stool', 'default'),

-- Dance Floor & Staging
('DF001', 'Dance Floors', '12x12 Dance Floor', '12x12 Parquet Dance Floor', 'default'),
('DF002', 'Dance Floors', '16x16 Dance Floor', '16x16 Parquet Dance Floor', 'default'),
('DF003', 'Dance Floors', '20x20 Dance Floor', '20x20 Parquet Dance Floor', 'default'),
('S001', 'Staging', '4x8 Stage', '4x8 Stage Deck (2ft high)', 'default'),
('S002', 'Staging', '4x8 Stage', '4x8 Stage Deck (3ft high)', 'default'),

-- Audio Visual Equipment
('AV001', 'Audio Visual', 'Microphones', 'Wireless Handheld Microphone', 'default'),
('AV002', 'Audio Visual', 'Speakers', 'Portable PA Speaker System', 'default'),
('AV003', 'Audio Visual', 'Projectors', 'HD Projector with Screen', 'default'),
('AV101', 'Audio Visual', 'TVs', '55" LED TV with Stand', 'default'),

-- Cooking & Catering Equipment
('C001', 'Cooking Equipment', 'Grills', 'Propane BBQ Grill', 'default'),
('C002', 'Cooking Equipment', 'Warmers', 'Chafing Dish (Full Size)', 'default'),
('C003', 'Cooking Equipment', 'Coolers', 'Large Event Cooler', 'default'),
('C101', 'Cooking Equipment', 'Coffee Service', 'Coffee Urn (100 cup)', 'default'),

-- Game & Entertainment Equipment
('G001', 'Games & Entertainment', 'Lawn Games', 'Giant Jenga Set', 'default'),
('G002', 'Games & Entertainment', 'Lawn Games', 'Cornhole Set', 'default'),
('G003', 'Games & Entertainment', 'Casino Games', 'Blackjack Table', 'default'),
('G004', 'Games & Entertainment', 'Casino Games', 'Poker Table', 'default'),

-- Specialty Decor & Accessories
('D001', 'Decor & Accessories', 'Centerpieces', 'Gold Candelabra', 'default'),
('D002', 'Decor & Accessories', 'Centerpieces', 'Silver Candelabra', 'default'),
('D003', 'Decor & Accessories', 'Arches', 'Wedding Arch (White)', 'default'),
('D101', 'Decor & Accessories', 'Pedestals', 'Acrylic Pedestal (Clear)', 'default'),

-- Lounge & Furniture
('LF001', 'Lounge Furniture', 'Cocktail Tables', '30" Cocktail Table', 'default'),
('LF002', 'Lounge Furniture', 'Cocktail Tables', '36" Cocktail Table', 'default'),
('LF101', 'Lounge Furniture', 'Lounge Seating', 'White Leather Lounge Chair', 'default'),
('LF102', 'Lounge Furniture', 'Lounge Seating', 'Black Leather Sofa', 'default'),

-- Restroom & Sanitation
('R001', 'Restroom Facilities', 'Portable Restrooms', 'Standard Portable Restroom', 'default'),
('R002', 'Restroom Facilities', 'Luxury Restrooms', 'Luxury Restroom Trailer', 'default'),
('R101', 'Sanitation', 'Hand Wash Stations', 'Portable Hand Wash Station', 'default'),

-- Transportation & Setup
('TR001', 'Transportation', 'Delivery', 'Local Delivery Service', 'default'),
('TR002', 'Transportation', 'Setup Service', 'Full Setup & Breakdown', 'default'),
('TR101', 'Labor', 'Event Staff', 'Event Coordinator (per hour)', 'default');

-- Store-specific overrides (examples for each location)
-- Wayzata (001) - Lake area events, more upscale items
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, store_code) VALUES
('6001', 'Tables', 'Round Tables', '60" Premium Round Table', '001'),
('2101', 'Chairs', 'Chiavari Chairs', 'Gold Chiavari Chair (Premium)', '001'),
('LR13201', 'Round Linen', '132" Round Linen', '132" Premium White Round Linen', '001');

-- Brooklyn Park (002) - Industrial/construction, more utility items
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, store_code) VALUES
('8001', 'Tables', 'Rectangle Tables', '6ft Utility Table', '002'),
('2001', 'Chairs', 'Folding Chairs', 'Commercial Folding Chair', '002'),
('TC4080', 'Tents & Canopies', '40x80 Tents', '40x80 Commercial Frame Tent', '002');

-- Fridley (003) - Broadway Tent & Event, performance/entertainment focus
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, store_code) VALUES
('S001', 'Staging', '4x8 Stage', '4x8 Performance Stage (2ft)', '003'),
('AV002', 'Audio Visual', 'Speakers', 'Professional PA System', '003'),
('LT002', 'Lighting', 'Chandeliers', 'Theater Crystal Chandelier', '003');

-- Elk River (004) - Rural/agricultural, outdoor focus
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, store_code) VALUES
('TC4001', 'Tents & Canopies', '40x40 Tents', '40x40 Agricultural Tent', '004'),
('C001', 'Cooking Equipment', 'Grills', 'Large Propane BBQ Grill', '004'),
('G002', 'Games & Entertainment', 'Lawn Games', 'Deluxe Cornhole Set', '004');

-- Add performance indexes for better query speed
CREATE INDEX IF NOT EXISTS ix_mappings_category_store ON user_rental_class_mappings(category, store_code);
CREATE INDEX IF NOT EXISTS ix_mappings_rental_class ON user_rental_class_mappings(rental_class_id, store_code);

-- Validation query to verify seed data loaded correctly
-- AI AGENT VERIFICATION COMMAND:
-- SELECT category, subcategory, COUNT(*) as item_count,
--        COUNT(CASE WHEN store_code = 'default' THEN 1 END) as default_count,
--        COUNT(CASE WHEN store_code != 'default' THEN 1 END) as store_specific_count
-- FROM user_rental_class_mappings
-- GROUP BY category, subcategory
-- ORDER BY category, subcategory;

-- Expected result: Should show ~100+ base mappings with store-specific overrides