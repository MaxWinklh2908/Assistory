ITEMS = {
    'iron_ore': 1,
    'iron_ingot': 2,
    'iron_rod': 4,
    'iron_plate': 6,
    'screw': 2,
    'reinforced_iron_plate': 120,
    'rotor': 140,
    'smart_plating': 520,

    'copper_ore': 3,
    'copper_ingot': 6,
    'wire': 6,
    'copper_sheet': 24,

}

RECIPES = [
    ('Iron Ingot', {'iron_ore': 1}, {'iron_ingot': 1}),
    ('Iron Plate', {'iron_ingot': 3}, {'iron_plate': 2}),
    ('Iron Rod', {'iron_ingot': 1}, {'iron_rod': 1}),
    ('Screw', {'iron_rod': 1}, {'screw': 4}),
    ('Reinforced Iron Plate', {'iron_plate': 6, 'screw': 12}, {'reinforced_iron_plate': 1}),
    ('Rotor', {'iron_rod': 5, 'screw': 25}, {'rotor': 1}),
    ('Smart Plating', {'rotor': 1, 'reinforced_iron_plate': 1}, {'smart_plating': 1}),

    ('Copper Ingot', {'copper_ore': 1}, {'copper_ingot': 1}),
    ('Wire', {'copper_ingot': 1}, {'wire': 2}),
    ('Copper Sheet', {'copper_ingot': 2}, {'copper_sheet': 1}),

    ('Alternate: Copper Rotor', {'copper_sheet': 6, 'screw': 52}, {'rotor': 3}),


]
