from neurons import protocol
from neurons.miners.bitcoin.funds_flow.graph_search import GraphSearch
from neurons.miners.configs import GraphDatabaseConfig
from neurons.protocol import NETWORK_BITCOIN


def get_data_to_verify_by_validator(network):
    switch = {
        NETWORK_BITCOIN: lambda: GraphSearch(
            config=GraphDatabaseConfig()
        ).verify_random_block_transaction(),
    }

    method = switch.get(network, lambda: "Not found.")()
    return method
