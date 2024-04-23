from neurons.miners.bitcoin.funds_flow.graph_search import (
    GraphSearch as BitcoinGraphSearch,
)
from neurons.miners.bitcoin.funds_flow.graph_indexer import (
    GraphIndexer as BitcoinGraphIndexer,
)
from neurons.miners.ethereum.funds_flow.graph_search import (GraphSearch as EthereumGraphSearch)
from neurons.miners.ethereum.funds_flow.graph_indexer import (GraphIndexer as EthereumGraphIndexer)

from insights.protocol import NETWORK_BITCOIN, NETWORK_ETHEREUM, MODEL_TYPE_FUNDS_FLOW

def get_graph_search(config):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: BitcoinGraphSearch(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
        NETWORK_ETHEREUM: {
            MODEL_TYPE_FUNDS_FLOW: lambda: EthereumGraphSearch(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
    }

    try:
        return switch[config.network][config.model_type]()
    except:
        raise ValueError(f'Graph search {config.model_type} not found for network {config.network}')
    
def get_graph_indexer(config):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: BitcoinGraphIndexer(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
        NETWORK_ETHEREUM: {
            MODEL_TYPE_FUNDS_FLOW: lambda: EthereumGraphIndexer(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
    }

    try:
        return switch[config.network][config.model_type]()
    except:
        raise ValueError(f'Graph Indexer {config.model_type} not found for network {config.network}'
)


def execute_query_proxy(network, model_type, query):
    graph_search = get_graph_search(network, model_type)
    if callable(graph_search):
        return graph_search.execute_query(network, query)
    else:
        return (
            graph_search
        )


def is_query_only(query_restricted_keywords, cypher_query):
    normalized_query = cypher_query.upper()
    for keyword in query_restricted_keywords:
        if keyword in normalized_query:
            return False
    return True










