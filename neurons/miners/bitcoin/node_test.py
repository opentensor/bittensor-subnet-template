import unittest

from neurons.miners.bitcoin.funds_flow.graph_creator import GraphCreator
from neurons.miners.bitcoin.node import BitcoinNode


class MyTestCase(unittest.TestCase):
    def test_something(self):
        node = BitcoinNode(node_rpc_url="http://jezus667:jezus.jest.tu667@194.163.162.94:8332")
        block = node.get_block_by_height(818250)
        total_value = node.sum_vout_values(block)
        total_value_count = node.sum_vout_values_count(block)
        print(total_value)
        print(total_value_count)

        gc = GraphCreator()
        in_memory_graph = gc.create_in_memory_graph_from_block(block)
        # print(in_memory_graph)

        value_satoshi = 0;
        value_satoshi_count = 0;
        block1 = in_memory_graph['block']

        for transaction in block1.transactions:
            for vout in transaction.vouts:
                value_satoshi += vout.value_satoshi
                value_satoshi_count += 1

        print(value_satoshi_count)
        print(value_satoshi)

if __name__ == '__main__':
    unittest.main()
