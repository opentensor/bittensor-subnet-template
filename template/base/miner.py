import copy
import time
import typing
import asyncio
import threading
import traceback

import bittensor as bt

from abc import ABC, abstractmethod

# Sync calls set weights and also resyncs the metagraph.
import template
from template.utils.sync import sync
from template.utils.config import check_config, add_args, config
from template.utils.misc import ttl_get_block

class BaseMinerNeuron(ABC):

    @classmethod
    def check_config(cls, config: "bt.Config"):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    subtensor: "bt.subtensor"
    wallet: "bt.wallet"
    metagraph: "bt.metagraph"

    def __init__(self, config=None):

        base_config = copy.deepcopy(config or BaseMinerNeuron.config())
        print('\nbaseconfig:', base_config)
        self.config = self.config()
        print('\nself.config:', self.config)
        self.config.merge(base_config)
        print('\nmerged config:', self.config)

        # Activating Bittensor's logging with the set configurations.
        bt.logging(config=self.config, logging_dir=self.config.full_path)

        # Warn if allowing incoming requests from anyone.
        if not self.config.blacklist.force_validator_permit:
            bt.logging.warning(
                "You are allowing non-validators to send requests to your miner. This is a security risk."
            )
        if self.config.blacklist.allow_non_registered:
            bt.logging.warning(
                "You are allowing non-registered entities to send requests to your miner. This is a security risk."
            )

        # Step 4: Build Bittensor validator objects
        # These are core Bittensor classes to interact with the network.
        bt.logging.info("Setting up bittensor objects.")

        # The wallet holds the cryptographic key pairs for the validator.
        self.wallet = bt.wallet(config=self.config)
        bt.logging.info(f"Wallet: {self.wallet}")

        # The subtensor is our connection to the Bittensor blockchain.
        self.subtensor = bt.subtensor(config=self.config)
        bt.logging.info(f"Subtensor: {self.subtensor}")

        bt.logging.info(
            f"Running miner for subnet: {self.config.netuid} on network: {self.subtensor.chain_endpoint} with config:"
        )

        # The metagraph holds the state of the network, letting us know about other validators and miners.
        self.metagraph = self.subtensor.metagraph(self.config.netuid)
        bt.logging.info(f"Metagraph: {self.metagraph}")

        bt.logging.info(f"Subtensor: {self.subtensor}")
        if self.wallet.hotkey.ss58_address not in self.metagraph.hotkeys:
            bt.logging.error(
                f"\nYour wallet: {self.wallet} if not registered to chain connection: {self.subtensor} \nRun btcli register and try again. "
            )
            exit(1)
        else:
            # Each miner gets a unique identity (UID) in the network for differentiation.
            self.uid = self.metagraph.hotkeys.index(
                self.wallet.hotkey.ss58_address
            )
            bt.logging.info(f"Running miner on uid: {self.uid}")

        # The axon handles request processing, allowing validators to send this process requests.
        self.axon = bt.axon(wallet=self.wallet, port=self.config.axon.port)

        # Attach determiners which functions are called when servicing a request.
        bt.logging.info(f"Attaching forward function to miner axon.")
        self.axon.attach(
            forward_fn=self.forward,
            blacklist_fn=self.blacklist,
            priority_fn=self.priority,
        )
        bt.logging.info(f"Axon created: {self.axon}")

        # Instantiate runners
        self.should_exit: bool = False
        self.is_running: bool = False
        self.thread: threading.Thread = None
        self.lock = asyncio.Lock()
        self.request_timestamps: Dict = {}

    @abstractmethod
    async def forward(self, synapse: template.protocol.Dummy) -> template.protocol.Dummy:
        ...

    @abstractmethod
    async def blacklist(self, synapse: template.protocol.Dummy) -> typing.Tuple[bool, str]:
        ...

    @abstractmethod
    async def priority(self, synapse: template.protocol.Dummy) -> float:
        ...

    @property
    def block(self):
        return ttl_get_block( self )

    def run(self):
        """
        Initiates and manages the main loop for the miner on the Bittensor network.

        This function performs the following primary tasks:
        1. Check for registration on the Bittensor network.
        2. Attaches the miner's forward, blacklist, and priority functions to its axon.
        3. Starts the miner's axon, making it active on the network.
        4. Regularly updates the metagraph with the latest network state.
        5. Optionally sets weights on the network, defining how much trust to assign to other nodes.
        6. Handles graceful shutdown on keyboard interrupts and logs unforeseen errors.

        The miner continues its operations until `should_exit` is set to True or an external interruption occurs.
        During each epoch of its operation, the miner waits for new blocks on the Bittensor network, updates its
        knowledge of the network (metagraph), and sets its weights. This process ensures the miner remains active
        and up-to-date with the network's latest state.

        Note:
            - The function leverages the global configurations set during the initialization of the miner.
            - The miner's axon serves as its interface to the Bittensor network, handling incoming and outgoing requests.

        Raises:
            KeyboardInterrupt: If the miner is stopped by a manual interruption.
            Exception: For unforeseen errors during the miner's operation, which are logged for diagnosis.
        """
        # --- Check for registration.
        if not self.subtensor.is_hotkey_registered(
            netuid=self.config.netuid,
            hotkey_ss58=self.wallet.hotkey.ss58_address,
        ):
            bt.logging.error(
                f"Wallet: {self.wallet} is not registered on netuid {self.config.netuid}"
                f"Please register the hotkey using `btcli subnets register` before trying again"
            )
            exit()

        # Serve passes the axon information to the network + netuid we are hosting on.
        # This will auto-update if the axon port of external ip have changed.
        bt.logging.info(
            f"Serving axon {self.axon} on network: {self.config.subtensor.chain_endpoint} with netuid: {self.config.netuid}"
        )
        self.axon.serve(netuid=self.config.netuid, subtensor=self.subtensor)

        # Start  starts the miner's axon, making it active on the network.
        bt.logging.info(f"Starting axon server on port: {self.config.axon.port}")
        self.axon.start()

        # --- Run until should_exit = True.
        self.last_epoch_block = ttl_get_block( self )
        bt.logging.info(f"Miner starting at block: {self.last_epoch_block}")

        # This loop maintains the miner's operations until intentionally stopped.
        bt.logging.info(f"Starting miner main loop")
        step = 0
        try:
            while not self.should_exit:
                start_epoch = time.time()

                # --- Wait until next epoch.
                current_block = ttl_get_block( self )
                while (
                    current_block - self.last_epoch_block
                    < self.config.neuron.checkpoint_block_length
                ):
                    # --- Wait for next bloc.
                    time.sleep(1)
                    current_block = ttl_get_block( self )

                    # --- Check if we should exit.
                    if self.should_exit:
                        break

                # --- Update the metagraph with the latest network state.
                self.last_epoch_block = ttl_get_block( self )

                # --- Sync metagraph and potentially set weights.
                sync( self )
                self.step += 1

        # If someone intentionally stops the miner, it'll safely terminate operations.
        except KeyboardInterrupt:
            self.axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            exit()

        # In case of unforeseen errors, the miner will log the error and continue operations.
        except Exception as e:
            bt.logging.error(traceback.format_exc())


    def run_in_background_thread(self):
        """
        Starts the miner's operations in a separate background thread.
        This is useful for non-blocking operations.
        """
        if not self.is_running:
            bt.logging.debug("Starting miner in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            bt.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the miner's operations that are running in the background thread.
        """
        if self.is_running:
            bt.logging.debug("Stopping miner in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            bt.logging.debug("Stopped")

    def __enter__(self):
        """
        Starts the miner's operations in a background thread upon entering the context.
        This method facilitates the use of the miner in a 'with' statement.
        """
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the miner's background operations upon exiting the context.
        This method facilitates the use of the miner in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        self.stop_run_thread()