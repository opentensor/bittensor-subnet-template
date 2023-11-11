import os


class BitcoinNodeConfig:
    """
    Configuration for the Bitcoin node.
    """

    def __init__(self, node_rpc_url: str = None):
        """
        Args:
            node_rpc_url:
        """
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("NODE_RPC_URL")
                or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            )
        else:
            self.rpc_url = node_rpc_url

    def __str__(self):
        return f"BitcoinNodeConfig(node_rpc_url={self.node_rpc_url})"


class GraphDatabaseConfig:
    """
    Configuration for the Neo4j/Memgraph graph database.
    """

    def __init__(
        self,
        graph_db_url: str = None,
        graph_db_user: str = None,
        graph_db_password: str = None,
    ):
        """
        Args:
            graph_db_url:
            graph_db_user:
            graph_db_password:
        """
        if graph_db_url is None:
            self.graph_db_url = (
                os.environ.get("GRAPH_DB_URL") or "bolt://localhost:7687"
            )
        else:
            self.graph_db_url = graph_db_url

        if graph_db_user is None:
            self.graph_db_user = os.environ.get("GRAPH_DB_USER") or ""
        else:
            self.graph_db_user = graph_db_user

        if graph_db_password is None:
            self.graph_db_password = os.environ.get("GRAPH_DB_PASSWORD") or ""
        else:
            self.graph_db_password = graph_db_password

    def __str__(self):
        return f"GraphIndexerConfig(graph_db_url={self.graph_db_url}, graph_db_user={self.graph_db_user}, graph_db_password={self.graph_db_password})"


class IndexerConfig:
    """
    Configuration for the indexer.
    Node config is used to connect to the Bitcoin node.
    Graph config is used to connect to the Neo4j graph database.
    """

    def __init__(
        self,
        node_config: BitcoinNodeConfig = None,
        graph_config: GraphDatabaseConfig = None,
    ):
        """
        Args:
            node_config:
            graph_config:
        """
        if node_config is None:
            self.node_config = BitcoinNodeConfig()
        else:
            self.node_config = node_config

        if graph_config is None:
            self.graph_config = GraphDatabaseConfig()
        else:
            self.graph_config = graph_config

    def __str__(self):
        return f"IndexerConfig(node_config={self.node_config}, graph_config={self.graph_config})"
