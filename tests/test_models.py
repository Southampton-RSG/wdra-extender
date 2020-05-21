import unittest

from wdra_extender.extract import models


class ExtractTest(unittest.TestCase):
    def test_constructor(self):
        extract = models.Extract(email="test@example.com")
