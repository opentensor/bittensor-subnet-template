import re
import unittest

class BenchmarkQueryRegex(unittest.TestCase):
    def test_something(self):
        # Updated pattern to allow spaces around the arithmetic operators and additional flexibility
        pattern = 'UNWIND range\\((\\d+), (\\d+)\\) AS block_height MATCH \\(p:Transaction\\) WHERE p.block_height = block_height RETURN SUM\\(p.(\\w+)\\+(\\d+)\\)$'
        query = 'UNWIND range(822375, 832375) AS block_height MATCH (p:Transaction) WHERE p.block_height = block_height RETURN SUM(p.in_total_amount+1)'
        regex = re.compile(pattern)
        match = regex.fullmatch(query)

        self.assertIsNotNone(match)  # Updated assertion to check if the match is not None

if __name__ == '__main__':
    unittest.main()