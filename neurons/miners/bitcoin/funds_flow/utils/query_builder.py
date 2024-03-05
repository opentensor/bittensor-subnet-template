from insights import protocol


class QueryBuilder:
    
    @staticmethod
    def build_query(query: protocol.Query) -> str:
        
        def __build_search_query(query: protocol.Query) -> str:
            if query.target is None:
                raise Exception("target must be specified in search query")
            if query.limit is None:
                raise Exception("limit must be specified in search query")
            
            cypher_query = 'MATCH (t:{}{})'.format(query.target, f'{{tx_id: "{query.tx_id}"}}' if 'tx_id' in query else '')
            cypher_query += '\n'
            cypher_query += f'RETURN t'
            cypher_query += '\n'
            cypher_query += f'LIMIT {query.limit}'
            cypher_query += ';'
            return cypher_query
        
        if query.type is None:
            raise Exception("type must be specified in query")
        if query.type == protocol.QUERY_TYPE_SEARCH:
            return __build_search_query(query)
        
        raise Exception("unknown query type")
