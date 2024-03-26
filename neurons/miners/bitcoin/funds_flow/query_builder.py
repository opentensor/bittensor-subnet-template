from insights import protocol

import os


class QueryBuilder:
    
    class __InnerQueryBuilder:
        @staticmethod
        def build_search_query(query: protocol.Query) -> str:
            if query.target is None:
                raise Exception(protocol.LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED)
            if query.limit is None:
                raise Exception(protocol.LLM_ERROR_SEARCH_LIMIT_NOT_SPECIFIED)
            if query.limit > os.getenv('QUERY_MAX_LIMIT', 50):
                raise Exception(protocol.LLM_ERROR_SEARCH_LIMIT_EXCEEDED)
            
            if query.where is None:
                query.where = {}
            
            if query.target == 'Transaction':
                cypher_query = 'MATCH'
                cypher_query += ' '

                # from address node
                if "from_address" in query.where:
                    cypher_query += f'(a1:Address{{address: "{query.where["from_address"]}"}})-[s1:SENT]->'

                # main transaction node
                cypher_query += '(t:Transaction{})'.format(f'{{tx_id: "{query.where["tx_id"]}"}}' if 'tx_id' in query.where else '')

                # to address node
                if "to_address" in query.where:
                    cypher_query += f'-[s2:SENT]->(a2:Address{{address: "{query.where["to_address"]}"}})'

                # where clause
                conditionals = []
                if "block_height_range" in query.where:
                    if "from" in query.where["block_height_range"]:
                        conditionals.append(f't.block_height >= {query.where["block_height_range"]["from"]}')
                    if "to" in query.where["block_height_range"]:
                        conditionals.append(f't.block_height <= {query.where["block_height_range"]["to"]}')
                if "amount_range" in query.where:
                    if "from" in query.where["amount_range"]:
                        conditionals.append(f't.out_total_amount >= {query.where["amount_range"]["from"]}')
                    if "to" in query.where["amount_range"]:
                        conditionals.append(f't.out_total_amount <= {query.where["amount_range"]["to"]}')
                if "timestamp_range" in query.where:
                    if "from" in query.where["timestamp_range"]:
                        conditionals.append(f't.timestamp >= {query.where["timestamp_range"]["from"]}')
                    if "to" in query.where["timestamp_range"]:
                        conditionals.append(f't.timestamp <= {query.where["timestamp_range"]["to"]}')
                        
                if len(conditionals) > 0:
                    cypher_query += '\n'
                    cypher_query += 'WHERE ' + ' AND '.join(conditionals)

                cypher_query += '\n'
                cypher_query += f'RETURN t'
                cypher_query += '\n'
                cypher_query += f'LIMIT {query.limit}'
                cypher_query += ';'
                return cypher_query
        
            raise Exception(protocol.LLM_ERROR_SEARCH_TARGET_NOT_SUPPORTED)
    @staticmethod
    def build_query(query: protocol.Query) -> str:
        if query.type is None:
            raise Exception(protocol.LLM_ERROR_TYPE_NOT_SUPPORTED)
        if query.type == protocol.QUERY_TYPE_SEARCH:
            return QueryBuilder.__InnerQueryBuilder.build_search_query(query)
        
        raise Exception(protocol.LLM_ERROR_TYPE_NOT_SUPPORTED)
