from insights.protocol import NETWORK_BITCOIN, NETWORK_DOGE
from neurons.nodes.bitcoin.node import BitcoinNode
from neurons.nodes.dogecoin.node import DogecoinNode


def get_node(network):
    if network == NETWORK_BITCOIN:
        return BitcoinNode()
    elif network == NETWORK_DOGE:
        return DogecoinNode()
    return None
