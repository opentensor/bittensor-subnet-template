import random

from insights.protocol import get_network_by_id, Challenge, ChallengeInput
from neurons.nodes.bitcoin.node_utils import process_in_memory_txn_for_indexing
from neurons.miners.bitcoin.funds_flow.graph_creator import GraphCreator

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

def count_run_id_per_hotkey(metadata):
    run_id_count = {}
    for hotkey in metadata:
        if hotkey not in run_id_count:
            run_id_count[hotkey] = set()
        run_id_count[hotkey].add(metadata[hotkey].ri)

    # Count the number of unique run_ids for each hotkey
    for hotkey in run_id_count:
        run_id_count[hotkey] = len(run_id_count[hotkey])
    return run_id_count

def count_hotkeys_per_ip(filtered_axons):
    hotkey_count_per_ip = {}

    for axon in filtered_axons:
        ip = axon.ip
        hotkey_count_per_ip[ip] = hotkey_count_per_ip.get(ip, 0) + 1

    return hotkey_count_per_ip

def generate_challenge_to_check(node, start_block_height, last_block_height, k=20):
    blocks_to_check = random.sample(range(start_block_height, last_block_height + 1), k=k)
    txn_ids_to_check = []
    graph_creator = GraphCreator()
    challenge_inputs = []
    
    for block_height in blocks_to_check:
        block_data = node.get_block_by_height(block_height)
        num_transactions = len(block_data["tx"])

        out_total_amount = 0
        while out_total_amount == 0:
            selected_txn = block_data["tx"][random.randint(0, num_transactions - 1)]
            txn_id = selected_txn.get('txid')
        
            txn_data = node.get_txn_data_by_id(txn_id)
            tx = graph_creator.create_in_memory_txn(txn_data)

            in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = process_in_memory_txn_for_indexing(tx, node)
            
        txn_ids_to_check.append(txn_id)
        challenge_inputs.append(ChallengeInput(in_total_amount=in_total_amount, out_total_amount=out_total_amount, tx_id_last_4_chars=txn_id[-4:]))

    challenge = Challenge(inputs=challenge_inputs)
    return challenge, txn_ids_to_check
