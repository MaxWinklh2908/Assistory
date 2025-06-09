import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game.game_schematic import SchematicFlags


class TestSchematicFlags(unittest.TestCase):

    def test_get_buildings_unlocked(self):
        schematics_unlocked = SchematicFlags()
        buildings_unlocked = schematics_unlocked.get_buildings_unlocked()
        self.assertNotIn('Desc_Packager_C', buildings_unlocked)

        schematics_unlocked = SchematicFlags({'Schematic_5-4_C'})
        buildings_unlocked = schematics_unlocked.get_buildings_unlocked()
        self.assertIn('Desc_Packager_C', buildings_unlocked)

    def test_get_recipes_unlocked(self):
        schematics_unlocked = SchematicFlags()
        recipes_unlocked = schematics_unlocked.get_recipes_unlocked()
        self.assertNotIn('Recipe_UnpackageAlumina_C', recipes_unlocked)

        schematics_unlocked = SchematicFlags({'Schematic_5-4_C'})
        recipes_unlocked = schematics_unlocked.get_recipes_unlocked()
        self.assertIn('Recipe_UnpackageAlumina_C', recipes_unlocked)

    
# Run the tests
if __name__ == '__main__':
    unittest.main()
