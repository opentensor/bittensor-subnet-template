from insights.protocol import get_network_by_id

def get_miner_distributions(miners_metadata, network_importance_keys):
    miner_distribution = {}
    for network in network_importance_keys:
        miner_distribution[network] = 0

    for hotkey in miners_metadata:
        metadata = miners_metadata[hotkey]
        network = get_network_by_id(metadata.n)
        if network in network_importance_keys:
            miner_distribution[network] += 1

    return miner_distribution

def count_hotkeys_per_ip(filtered_axons):
    hotkey_count_per_ip = {}

    for axon in filtered_axons:
        ip = axon.ip
        hotkey_count_per_ip[ip] = hotkey_count_per_ip.get(ip, 0) + 1

    return hotkey_count_per_ip

