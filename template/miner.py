# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Bittensor Miner Template:
# TODO(developer): Rewrite based on protocol and validator defintion.

# Step 1: Import necessary libraries and modules
import os
import time
import template
import argparse
import traceback
import bittensor as bt

# import this repo
import template

# Step 2: Set up the configuration parser
# This function initializes the necessary command-line arguments.
# Using command-line arguments allows users to customize various miner settings.
def parse_config():
    parser = argparse.ArgumentParser()
    # TODO(developer): Adds your custom miner arguments to the parser.
    parser.add_argument('--custom', default='my_custom_value', help='Adds a custom value to the parser.')
    # Adds subtensor specific arguments i.e. --subtensor.chain_endpoint ... --subtensor.network ...
    bt.subtensor.add_args(parser)
    # Adds logging specific arguments i.e. --logging.debug ..., --logging.trace .. or --logging.logging_dir ...
    bt.logging.add_args(parser)
    # Adds wallet specific arguments i.e. --wallet.name ..., --wallet.hotkey ./. or --wallet.path ...
    bt.wallet.add_args(parser)
    # Adds axon specific arguments i.e. --axon.port ...
    bt.axon.add_args(parser)
    # The function returns a merged dictionary of configuration settings.
    return bt.config(parser)

# Activating the parser to read any command-line inputs.
# To print help message, run python3 template/miner.py --help
config = parse_config()

# Step 3: Set up logging directory
# Logging captures events for diagnosis or understanding miner's behavior.
config.full_path = os.path.expanduser(
    "{}/{}/{}/netuid{}/{}".format(
        config.logging.logging_dir,
        config.wallet.name,
        config.wallet.hotkey,
        template.NETUID,
        config.name,
    )
)
# Ensure the directory for logging exists, else create one.
if not os.path.exists(config.full_path): os.makedirs(config.full_path, exist_ok=True)
# Activating Bittensor's logging with the set configurations.
bt.logging(config=config, logging_dir=config.full_path)
# This logs the active configuration to the specified logging directory for review.
bt.logging.info(config)

# Step 4: Initialize Bittensor miner objects
# These classes are vital to interact and function within the Bittensor network.
bt.logging.info("Setting up bittensor objects.")
# Wallet holds cryptographic information, ensuring secure transactions and communication.
wallet = bt.wallet(config=config).create_if_non_existent()
# subtensor manages the blockchain connection, facilitating interaction with the Bittensor blockchain.
subtensor = bt.subtensor(config=config)
# axon handles request processing, allowing validators to send this process requests.
axon = bt.axon(wallet=wallet)
# metagraph provides the network's current state, holding state about other participants in a subnet.
metagraph = subtensor.metagraph(template.NETUID)

# Step 5: Integrate the miner with the network
# This ensures that our miner becomes a recognized entity on the network.
bt.logging.info(f"Registering the miner on subnet: {template.NETUID}")
subtensor.register(wallet=wallet, netuid=template.NETUID)
# Each miner gets a unique identity (UID) in the network for differentiation.
my_subnet_uid = metagraph.hotkeys.index(wallet.hotkey.ss58_address)
bt.logging.info(f"Registered with uid: {my_subnet_uid}")

# Step 6: Set up miner functionalities
# The following functions control the miner's response to incoming requests.
# Each function plays a specific role in this decision process.

# The blacklist function decides if a request should be ignored.
def blacklist_fn( synapse: template.protocol.Dummy ) -> bool:
    # TODO(developer): Define how miners should blacklist requests.
    caller_uid = metagraph.uids[synapse.dendrite.hotkey.ss58_address] if synapse.dendrite.hotkey.ss58_address in metagraph.hotkeys else -1
    # Ignore requests from unrecognized entities.
    if caller_uid == -1: 
        return True
    # Ignore requests from non-validators.
    if not metagraph.validator_permit[ caller_uid ]:
        return True
    # Allow the request to be processed further.
    return False

# The priority function determines the order in which requests are handled.
# More valuable or higher-priority requests are processed before others.
def priority_fn( synapse: template.protocol.Dummy ) -> float:
    # TODO(developer): Define how miners should prioritize requests.
    prirority = float( metagraph.S[ synapse.dendrite.hotkey.ss58_address ] ) 
    return prirority

# This is the core miner function, which decides the miner's response to a valid, high-priority request.
def dummy( synapse: template.protocol.Dummy ) -> template.protocol.Dummy:
    # TODO(developer): Define how miners should process requests.
    # Simple logic: return the input value multiplied by 2.
    synapse.dummy_output = synapse.dummy_input * 2
    return synapse

# Step 8: Link miner functions to the axon.
# This makes sure the axon knows which functions to use when deciding how to respond.
axon.attach(
    fn = dummy,
    blacklist_fn = blacklist_fn,
    priority_fn = priority_fn,
)

# Step 9: Serve the miner network information on the network
# We pass netuid and subtensor connection, which determine which chain and which network to serve on.
# This will update outdated network information if the axon port of external ip have changed.
axon.serve( netuid = template.NETUID, subtensor = subtensor )

# Step 10: Launch the miner
# This starts the miner's axon, making it active on the network.
axon.start()

# Step 10: Keep the miner alive
# This loop maintains the miner's operations until intentionally stopped.
while True:
    try:
        # TODO(developer): Define any additional operations to be performed by the miner.
        # The miner remains operational with minimal overhead.
        time.sleep(1)
    # If someone intentionally stops the miner, it'll safely terminate operations.
    except KeyboardInterrupt:
        axon.stop()
        bt.logging.critical('Miner killed by keyboard interrupt.')
        break
    # In case of unforeseen errors, the miner will log the error and continue operations.
    except Exception as e:
        bt.logging.error(traceback.format_exc())
        continue

