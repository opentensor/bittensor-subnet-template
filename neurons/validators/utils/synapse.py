from insights.protocol import Discovery, DiscoveryMetadata, DiscoveryOutput, get_model_types, get_networks


def is_discovery_response_valid(discovery_output: Discovery) -> bool:
    if discovery_output is None:
        return False
    
    output: DiscoveryOutput = discovery_output.output
    if output is None:
        return False
    if output.start_block_height < 0 or output.block_height < 0:
        return False
    if output.start_block_height >= output.block_height:
        return False
    if output.start_block_height == 0:
        return False
    
    metadata: DiscoveryMetadata = output.metadata
    
    if metadata.network is None or metadata.network not in get_networks():
        return False
    return True
    