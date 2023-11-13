from neurons.miners.bitcoin.funds_flow.graph_search import (
    GraphSearch as BitcoinGraphSearch,
)
from neurons.miners.litecoin.funds_flow.graph_search import (
    GraphSearch as LitecoinGraphSearch,
)
from neurons.protocol import NETWORK_BITCOIN, MODEL_TYPE_FUNDS_FLOW, NETWORK_LITECOIN


def get_graph_search(network, model_type):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: BitcoinGraphSearch(),
        },
        NETWORK_LITECOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: LitecoinGraphSearch(),
        },
    }

    network_switch = switch.get(network, {})
    return network_switch.get(model_type, lambda: "Not found.")()


def execute_query_proxy(network, asset, model_type, query):
    graph_search = get_graph_search(network, model_type)
    if callable(graph_search):
        return graph_search.execute_query(network, asset, query)
    else:
        return (
            graph_search  # This will be "Not found." if the graph_search is not found.
        )
