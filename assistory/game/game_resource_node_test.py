import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game import game_resource_node


class TestSchematicFlags(unittest.TestCase):

    def test_resource_node_name(self):
        exp_resource_name = 'Desc_LiquidOil_C'
        exp_fracking = True

        resource_node_name = game_resource_node.get_resource_node_name(
            exp_resource_name,
            exp_fracking
        )
        extraction_method_name = game_resource_node.get_extraction_method_name(
            exp_fracking
        )
        self.assertIn(extraction_method_name, resource_node_name)
        
        resource_name = game_resource_node.get_resource_name(resource_node_name)
        self.assertEqual(exp_resource_name, resource_name)

        fracking = game_resource_node.get_extraction_method(resource_node_name)
        self.assertEqual(exp_fracking, fracking)

    
# Run the tests
if __name__ == '__main__':
    unittest.main()
