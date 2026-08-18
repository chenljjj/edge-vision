import unittest

from src.geometry import parse_rectangle, point_in_rectangle


class GeometryTests(unittest.TestCase):
    def test_point_in_rectangle_includes_boundary(self) -> None:
        rectangle = (10, 20, 100, 200)
        self.assertTrue(point_in_rectangle((10, 20), rectangle))
        self.assertTrue(point_in_rectangle((100, 200), rectangle))
        self.assertFalse(point_in_rectangle((9, 20), rectangle))

    def test_parse_rectangle_requires_a_valid_rectangle(self) -> None:
        self.assertEqual(parse_rectangle("1,2,30,40"), (1, 2, 30, 40))
        with self.assertRaises(ValueError):
            parse_rectangle("1,2,3")
        with self.assertRaises(ValueError):
            parse_rectangle("30,20,10,40")


if __name__ == "__main__":
    unittest.main()
