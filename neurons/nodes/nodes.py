from insights.protocol import NETWORK_BITCOIN
from neurons.nodes.bitcoin.node import BitcoinNode
from insights.protocol import NETWORK_ETHEREUM
from neurons.nodes.evm.ethereum.node import EthereumNode

def get_node(network):
    if network == NETWORK_BITCOIN:
        return BitcoinNode()
    elif network == NETWORK_ETHEREUM:
        return EthereumNode()
    return None