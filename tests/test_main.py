import unittest

from src.main import build_parser, format_status


class MainTests(unittest.TestCase):
    def test_headless_arguments(self) -> None:
        args = build_parser().parse_args(["--headless", "--log-interval", "2.5"])
        self.assertTrue(args.headless)
        self.assertEqual(args.log_interval, 2.5)

    def test_status_format_with_region_count(self) -> None:
        self.assertEqual(format_status(12.34, 3, 2), "status fps=12.3 objects=3 in_region=2")

    def test_status_format_without_region_count(self) -> None:
        self.assertEqual(format_status(12.34, 3, None), "status fps=12.3 objects=3")


if __name__ == "__main__":
    unittest.main()
