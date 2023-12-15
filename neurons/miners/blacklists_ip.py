import os
import subprocess
import time
import argparse
import traceback
import bittensor as bt
from neurons.miners.blacklists import load_blacklist_config

SLEEP_TIME = 60

def main(config):
    bt.logging.info(
        f"Running ip blocker for subnet: {config.netuid} on network: {config.subtensor.chain_endpoint}"
    )

    bt.logging.info("Setting up bittensor objects.")
    wallet = bt.wallet(config=config)
    bt.logging.info(f"Wallet: {wallet}")
    subtensor = bt.subtensor(config=config)
    bt.logging.info(f"Subtensor: {subtensor}")
    metagraph = subtensor.metagraph(config.netuid)
    bt.logging.info(f"Metagraph: {metagraph}")
    if wallet.hotkey.ss58_address not in metagraph.hotkeys:
        bt.logging.error(
            f"\nYour miner: {wallet} is not registered to chain connection: {subtensor} \nRun btcli register and try again. "
        )
        exit()

    my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
    metagraph = subtensor.metagraph(config.netuid)
    bt.logging.info(f"Running ip blocker on uid: {my_subnet_uid}")

    while True:
        try:

            WHITELISTED_KEYS, BLACKLISTED_KEYS, STAKE_THRESHOLD, MAX_REQUESTS, MIN_REQUEST_PERIOD = load_blacklist_config('blacklist_discovery.json')

            bt.logging.info(f"🔄 Syncing metagraph")
            metagraph.sync(subtensor = subtensor)
            bt.logging.info(f"✅ Synced")
            bt.logging.info(f"Checking for blacklisted hotkeys")

            needs_refresh = False

            for hotkey in BLACKLISTED_KEYS:
                for _uid, _axon in enumerate(metagraph.axons):
                    if _axon.hotkey == hotkey:
                        if _axon.ip is None or _axon.ip == "0.0.0.0":
                            continue

                        uid = _uid
                        neuron = metagraph.neurons[uid]

                        axon_ip = _axon.ip

                        result = subprocess.run(["iptables", "-L", "INPUT", "-v", "-n"], capture_output=True, text=True)
                        if axon_ip not in result.stdout:
                            subprocess.run(["iptables", "-A", "INPUT", "-s", axon_ip, "-j", "DROP"], check=True)
                            bt.logging.info(f"🚫💻 Blocked {hotkey} at {axon_ip}")
                            needs_refresh = True
                        else:
                            bt.logging.info(f"ℹ️ IP {axon_ip} already blocked")

            if needs_refresh:
                subprocess.run(["iptables-save"], check=True)
                bt.logging.info(f"Refreshed ip tables")
            else:
                bt.logging.info(f"✅ No new blacklisted hotkeys found")


            bt.logging.info(f"Sleeping for {SLEEP_TIME} seconds")
            time.sleep(SLEEP_TIME)

        except KeyboardInterrupt:
            bt.logging.success("Ip blocker killed by keyboard interrupt.")
            break
        except Exception as e:
            bt.logging.error(traceback.format_exc())
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--netuid", type=int, default=15, help="The chain subnet uid.")

    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    bt.axon.add_args(parser)

    config = bt.config(parser)
    config.full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            config.netuid,
            "ip blocker",
        )
    )
    if not os.path.exists(config.full_path):
        os.makedirs(config.full_path, exist_ok=True)

    bt.logging(config=config, logging_dir = config.full_path)

    config.wallet.name = "miner"
    config.wallet.hotkey = "default"

    main(config)