"""Small dependency-free contract check for the offline preparation boundary."""

import unittest


class FinalizationContract(unittest.TestCase):
    def test_empty_language_is_rejected_instead_of_publishing_an_approved_list(self):
        from multilang.services.vocabulary_finalization import consolidate

        with self.assertRaises(ValueError):
            consolidate([], language="de")


if __name__ == "__main__":
    unittest.main()
