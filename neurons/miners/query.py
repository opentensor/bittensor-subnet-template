from neurons.miners.bitcoin.funds_flow.graph_search import (
    GraphSearch as BitcoinGraphSearch,
)
from neurons.miners.bitcoin.funds_flow.graph_indexer import (
    GraphIndexer as BitcoinGraphIndexer,
)
from neurons.miners.bitcoin.balance_tracking.balance_search import (
    BalanceSearch as BitcoinBalanceSearch,
)
from neurons.miners.bitcoin.balance_tracking.balance_indexer import (
    BalanceIndexer as BitcoinBalanceIndexer,
)
from neurons.miners.ethereum.funds_flow.graph_search import (GraphSearch as EthereumGraphSearch)
from neurons.miners.ethereum.funds_flow.graph_indexer import (GraphIndexer as EthereumGraphIndexer)

from insights.protocol import NETWORK_BITCOIN, NETWORK_ETHEREUM, MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING

def get_graph_search(config):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_FUNDS_FLOW: lambda: BitcoinGraphSearch(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
        NETWORK_ETHEREUM: {
            MODEL_TYPE_FUNDS_FLOW: lambda: EthereumGraphSearch(config.graph_db_url, config.graph_db_user, config.graph_db_password),
        },
    }

    return switch[config.network][MODEL_TYPE_FUNDS_FLOW]()
    
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
        return switch[config.network][MODEL_TYPE_FUNDS_FLOW]()
    except:
        raise ValueError(f'Graph Indexer {MODEL_TYPE_FUNDS_FLOW} not found for network {config.network}'
)
        
def get_balance_search(config):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_BALANCE_TRACKING: lambda: BitcoinBalanceSearch(config.db_connection_string),
        },
    }

    return switch[config.network][MODEL_TYPE_BALANCE_TRACKING]()

def get_balance_indexer(config):
    switch = {
        NETWORK_BITCOIN: {
            MODEL_TYPE_BALANCE_TRACKING: lambda: BitcoinBalanceIndexer(config.db_connection_string),
        },
    }

    return switch[config.network][MODEL_TYPE_BALANCE_TRACKING]()


def is_query_only(query_restricted_keywords, cypher_query):
    normalized_query = cypher_query.upper()
    for keyword in query_restricted_keywords:
        if keyword in normalized_query:
            return False
    return True
