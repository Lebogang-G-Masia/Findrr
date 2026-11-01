"""Smoke test to verify test harness and package import."""

import unittest

import findrr


class TestSmoke(unittest.TestCase):
    def test_package_metadata(self):
        self.assertEqual(findrr.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
