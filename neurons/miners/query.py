from neurons.miners.bitcoin.funds_flow.graph_search import (
    GraphSearch as BitcoinGraphSearch,
)

from insights.protocol import NETWORK_BITCOIN, MODEL_TYPE_FUNDS_FLOW

def get_graph_search(network, model_type):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: BitcoinGraphSearch(),
        },
    }

    network_switch = switch.get(network, {})
    return network_switch.get(model_type, lambda: "Not found.")()


def execute_query_proxy(network, model_type, query):
    graph_search = get_graph_search(network, model_type)
    if callable(graph_search):
        return graph_search.execute_query(network, query)
    else:
        return (
            graph_search
        )

def is_query_only(cypher_query):
    modification_keywords = ['CREATE', 'SET', 'DELETE', 'DETACH', 'REMOVE', 'MERGE', 'CREATE INDEX', 'DROP INDEX', 'CREATE CONSTRAINT', 'DROP CONSTRAINT']
    normalized_query = cypher_query.upper()
    for keyword in modification_keywords:
        if keyword in normalized_query:
            return False
    return True










