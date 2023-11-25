from insights.protocol import NETWORK_BITCOIN
from neurons.nodes.bitcoin.node import BitcoinNode


def get_node(network):
    if network == NETWORK_BITCOIN:
        return BitcoinNode()
    return None