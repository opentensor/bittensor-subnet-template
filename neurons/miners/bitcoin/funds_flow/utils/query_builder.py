from insights import protocol


class QueryBuilder:
    
    @staticmethod
    def build_query(query: protocol.Query) -> str:
        
        def __build_search_query(query: protocol.Query) -> str:
            if query.target is None:
                raise Exception("target must be specified in search query")
            if query.limit is None:
                raise Exception("limit must be specified in search query")
            if query.where is None:
                query.where = {}
            
            if query.target == 'Transaction':
                cypher_query = 'MATCH'
                cypher_query += ' '
                if "from_address" in query.where:
                    cypher_query += f'(a1:Address{{address: "{query.where["from_address"]}"}})->[s1:SENT]->'
                cypher_query += '(t:Transaction{})'.format(f'{{tx_id: "{query.where["tx_id"]}"}}' if 'tx_id' in query.where else '')
                if "to_address" in query.where:
                    cypher_query += f'->[s2:SENT]->(a2:Address{{address: "{query.where["to_address"]}"}})'
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
