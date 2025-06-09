import unittest
import sys, os

print('Add', os.getcwd(), 'to path')
sys.path.append(os.getcwd())
from assistory.game.base_types import Flags, Values


class FlagsTest(unittest.TestCase):

    def test_flag_check(self):
        flags = Flags({'x'}, ['x', 'y'])
        with self.assertRaises(ValueError):
            Flags({'z'}, ['x', 'y'])

        flags.add('y')
        with self.assertRaises(ValueError):
            flags.add('z')

        flags.update({'y'})
        with self.assertRaises(ValueError):
            flags.update({'z'})

    def test_logic(self):
        flags1 = Flags(set(), ['x', 'y'])
        flags2 = Flags(set(), ['x', 'z'])
        with self.assertRaises(ValueError):
            flags1 & flags2
        with self.assertRaises(ValueError):
            flags1.__and__(flags2)
        with self.assertRaises(ValueError):
            flags1 | flags2
        with self.assertRaises(ValueError):
            flags1.__or__(flags2)

    def test_array(self):
        flags = Flags({'x'}, ['x', 'y'])
        flags2 = Flags._from_array(flags.as_array(), ['x', 'y'])
        self.assertEqual(flags, flags2)


class ProducableItemsTest(unittest.TestCase):

    def test_key_check(self):

        values = Values({'x': 1}, ['x', 'y'])
        with self.assertRaises(ValueError):
            Values({'z': 1}, ['x', 'y'])

        values['y'] = 1
        with self.assertRaises(ValueError):
            values['z'] = 1

        values.update({'y': 2})
        with self.assertRaises(ValueError):
            values.update({'z': 2})

    def test_as_dict_ignoring(self):
        values = Values({'x': 1, 'y': 0}, ['x', 'y'])
        self.assertEqual(
            {'x': 1},
            values.as_dict_ignoring(ignore_value=0)
        )

    def test_clear(self):
        values = Values({'x': 1}, ['x', 'y'])
        self.assertEqual(0, values['y'])

        values.clear()
        self.assertEqual(0, values['x'])

        values = Values({'x': 1}, ['x', 'y'], default_value=1)
        self.assertEqual(1, values['y'])
    
        values.clear()
        self.assertEqual(1, values['x'])

    def test_copy(self):
        values = Values({'x': 1}, ['x', 'y'], default_value=1)
        values2 = values.copy()
        values2.clear()
        self.assertEqual(1, values2['x'])
        self.assertEqual(1, values2['y'])

    def test_array(self):
        values = Values({'x': 1}, ['x', 'y'])
        values2 = Values._from_array(values.as_array(), ['x', 'y'])
        self.assertEqual(values, values2)


class ValuesTest(unittest.TestCase):

    def setUp(self):
        self.A = Values({'a': 1}, omega=['a', 'b'])
        self.B = Values({'a': 4}, omega=['a', 'b'])

    def test_mul(self):
        self.assertEqual(self.A * 4, self.B)

    def test_rmul(self):
        self.assertEqual(0.25 * self.B, self.A)

    def test_imul(self):
        B = Values({'a': 1}, omega=['a', 'b'])
        B *= 4
        self.assertEqual(B, self.B)

    def test_mul_does_not_modify_original(self):
        B = self.A * 4
        self.assertEqual(self.A,  Values({'a': 1}, omega=['a', 'b']))
        self.assertEqual(B, self.B)

    def test_rounding(self):
        v = Values({'a': 1.001}, omega=['a', 'b'])
        v_out = v.round(2)
        self.assertEqual(1, v_out['a'])

        v_out = v.round(None)
        self.assertEqual(int, type(v_out['a']))

# Run the tests
if __name__ == '__main__':
    unittest.main()
