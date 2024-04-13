import argparse
import getpass
import os
import signal
import time
from random import randint
import bittensor as bt
import yaml

from neurons.setup_logger import setup_logger

shutdown_flag = False

def shutdown_handler(signum, frame):
    global shutdown_flag
    bt.logging.info(
        "Shutdown signal received. Waiting for current indexing to complete before shutting down."
    )
    shutdown_flag = True

original_getpass = getpass.getpass

def my_getpass(prompt='Password: ', stream=None):
    bt.logging.info("Getting password")
    password = os.getenv('WALLET_PASSWORD', None)
    return password

getpass.getpass = my_getpass

def remove_stake(wallet, subtensor):
    threshold = 0.1
    hotkey = wallet.hotkey.ss58_address
    hotkey_stake  = subtensor.get_stake_for_coldkey_and_hotkey(
        hotkey_ss58=hotkey, coldkey_ss58=wallet.coldkeypub.ss58_address
    )
    amount = hotkey_stake.tao
    if amount > threshold:
        ok = subtensor.unstake(
            wallet=wallet,
            hotkey_ss58=hotkey,
            amount=amount,
            wait_for_inclusion=True,
            prompt=False,)
        if ok:
            bt.logging.info(f"Successfully removed {amount} TAO stake from {hotkey}")
        else:
            bt.logging.error(f"Failed to remove {amount} TAO stake from {hotkey}")
    else:
        bt.logging.info(f"Current stake is {amount} TAO, waiting for {threshold} TAO to remove stake")

def transfer(wallet, subtensor):

    target = os.environ.get('WALLET_WITHDRAWAL_ADDRESS', None)
    if target is None:
        bt.logging.error("WALLET_WITHDRAWAL_ADDRESS is not set")
        exit(-1)

    balance  = subtensor.get_balance(wallet.coldkeypub.ss58_address)
    withdrawal_threshold = os.getenv('WALLET_WITHDRAWAL_THRESHOLD', 0.1)

    amount = balance.tao - withdrawal_threshold
    if amount > withdrawal_threshold:
        ok = subtensor.transfer(
            wallet=wallet,
            dest=target,
            amount=amount,
            wait_for_inclusion=True,
            prompt=False,)
        if ok:
            bt.logging.info(f"Successfully transferred {amount} TAO to {target}")
        else:
            bt.logging.error(f"Failed to transfer {amount} TAO to {target}")
    else:
        bt.logging.info(f"Total balance {balance.tao} TAO is below threshold {withdrawal_threshold} TAO")

# Register the shutdown handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action=argparse.BooleanOptionalAction)
    parser.add_argument(
        "--password",
        type=str,
        help="Wallet password",
    )

    parser.add_argument(
        "--hotkeys",
        type=str,
        help="Wallet hotkeys, delimited by comma",
    )

    parser.add_argument(
        "--withdrawal_threshold",
        type=float,
        help="Wallet withdrawal threshold",
    )

    parser.add_argument(
        "--withdrawal_target",
        type=float,
        help="Wallet withdrawal target",
    )

    bt.subtensor.add_args(parser)
    bt.logging.add_args(parser)
    bt.wallet.add_args(parser)
    config = bt.config(parser)

    dev = config.dev
    if dev:
        dev_config_path = "miner_withdrawal.yml"
        if os.path.exists(dev_config_path):
            with open(dev_config_path, 'r') as f:
                dev_config = yaml.safe_load(f.read())
            config.update(dev_config)
            bt.logging.info(f"config updated with {dev_config_path}")

        else:
            with open(dev_config_path, 'w') as f:
                yaml.safe_dump(config, f)
            bt.logging.info(f"config stored in {dev_config_path}")

    return config

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    while not shutdown_flag:
        try:
            config = get_config()
            hotkeys = config.hotkeys.split(',')
            for hotkey in hotkeys:
                #config.wallet['hotkey'] = hotkey
                #wallet = bt.wallet(config=config)
                subtensor = bt.subtensor(config=config)
                remove_stake(wallet, subtensor)

            wallet = bt.wallet(config=config)
            subtensor = bt.subtensor(config=config)
            transfer(wallet, subtensor)
        except Exception as e:
            bt.logging.error(e)
        finally:
            time.sleep(randint(1, 1080))

# WALLET_PASSWORD
# WALLET_WITHDRAWAL_THRESHOLD
# WALLET_WITHDRAWAL_ADDRESS

# miner    # shoulder actual vast embody wait wagon ice story upon scene swap trigger
# default1 # learn believe return butter chest rich almost bar shine cheap during tortoise
# default2 # october duck alley number remain reunion yellow timber message item trick corn

# target # reason truth lobster ramp subway chapter sugar file type venture garden orbit