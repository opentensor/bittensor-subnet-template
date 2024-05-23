import inspect
import json
import re
import unittest

def build_query(network, start_block, end_block, diff=1):
    import random
    total_blocks = end_block - start_block
    part_size = total_blocks // 8
    range_clauses = []
    for i in range(8):
        part_start = start_block + i * part_size
        if i == 7:
            part_end = end_block
        else:
            part_end = start_block + (i + 1) * part_size - 1
        if (part_end - part_start) > diff:
            sub_range_start = random.randint(part_start, part_end - diff)
        else:
            sub_range_start = part_start
        sub_range_end = sub_range_start + diff
        range_clauses.append(f"range({sub_range_start}, {sub_range_end})")
    combined_ranges = " + ".join(range_clauses)
    final_query = f"""
    WITH {combined_ranges} AS block_heights
    UNWIND block_heights AS block_height
    MATCH p=(sender:Address)-[sent1:SENT]->(t:Transaction)-[sent2:SENT]->(receiver:Address)
    WHERE t.block_height = block_height
    WITH project(p) AS subgraph
    CALL pagerank.get(subgraph) YIELD node, rank
    RETURN round(rank * 1000000) / 1000000 AS roundedRank 
    ORDER BY roundedRank DESC
    LIMIT 1
    """
    query = final_query.strip()
    return query

class BenchmarkQueryRegex(unittest.TestCase):

    def test_something(self):
        function_code = inspect.getsource(build_query) + "\nquery = build_query(network, start_block, end_block, 1)"
        with open('query_script.json', 'w') as file:
            json.dump({"code": function_code}, file)

        query_script = ""
        with open('query_script.json', 'r') as file:
            data = json.load(file)
            query_script = data['code']

        query = build_query('bitcoin', 1, 835000, 1)
        benchmark_query_script_vars = {
            'network': 'bitcoin',
            'start_block': 1,
            'end_block': 835000,
            'diff': 1,
        }

        exec(query_script, benchmark_query_script_vars)
        generated_query = benchmark_query_script_vars['query']
        print(generated_query)

        pattern = "WITH\s+(?:range\(\d+,\s*\d+\)\s*\+\s*)+range\(\d+,\s*\d+\)\s+AS\s+block_heights\s+UNWIND\s+block_heights\s+AS\s+block_height\s+MATCH\s+p=\((sender:Address)\)-\[(sent1:SENT)\]->\((t:Transaction)\)-\[(sent2:SENT)\]->\((receiver:Address)\)\s+WHERE\s+t\.block_height\s+=\s+block_height\s+WITH\s+project\(p\)\s+AS\s+subgraph\s+CALL\s+pagerank\.get\(subgraph\)\s+YIELD\s+node,\s+rank\s+RETURN\s+round\(rank\s*\*\s*1000000\)\s*/\s*1000000\s+AS\s+roundedRank\s+ORDER\s+BY\s+roundedRank\s+DESC\s+LIMIT\s+1"
        print(pattern)

        with open('query_script_regex.json', 'w') as file:
            json.dump({"regex": pattern}, file)

        regex = re.compile(pattern)
        match = regex.fullmatch(generated_query)

        self.assertIsNotNone(match)  # Updated assertion to check if the match is not None

if __name__ == '__main__':
    unittest.main()
