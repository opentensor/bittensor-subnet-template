from insights import protocol


class QueryBuilder:
    
    @staticmethod
    def build_query(query: protocol.Query) -> str:
        if query.type is None:
            raise Exception("type must be specified in query")
        if query.type == protocol.QUERY_TYPE_SEARCH:
            return QueryBuilder.build_search_query(query)
        
        raise Exception("unknown query type")

    @staticmethod
    def build_search_query(query: protocol.Query) -> str:
        if query.target is None:
            raise Exception("target must be specified in search query")
        if query.limit is None:
            raise Exception("limit must be specified in search query")
        
        return 'search query'
