from .set_weights import set_weights

def resync_metagraph(metagraph, subtensor, scores):
    """Resyncs the metagraph and updates moving averages based on the new metagraph."""
    bt.logging.info("resync_metagraph()")

    # Copies state of metagraph before syncing.
    previous_metagraph = copy.deepcopy(metagraph)

    # Sync the metagraph.
    metagraph.sync(subtensor=subtensor)

    # Check if the metagraph axon info has changed.
    metagraph_axon_info_updated = previous_metagraph.axons != metagraph.axons

    if metagraph_axon_info_updated:
        bt.logging.info(
            "Metagraph updated, re-syncing hotkeys, dendrite pool and moving averages"
        )

        # Zero out all hotkeys that have been replaced.
        for uid, hotkey in enumerate(previous_metagraph.hotkeys):
            if hotkey != metagraph.hotkeys[uid]:
                scores[uid] = 0  # hotkey has been replaced

        # Check to see if the metagraph has changed size.
        # If so, we need to add new hotkeys and moving averages.
        if len(hotkeys) < len(metagraph.hotkeys):
            # Update the size of the moving average scores.
            new_moving_average = torch.zeros((metagraph.n))
            min_len = min(len(hotkeys), len(scores))
            new_moving_average[:min_len] = scores[:min_len]
            scores = new_moving_average

    return metagraph, scores