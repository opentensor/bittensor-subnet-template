from bitcoinrpc.authproxy import AuthServiceProxy
from Crypto.Hash import SHA256, RIPEMD160
import itertools
import base58
import time
import sys


def pubkey_to_address(pubkey: str) -> str:
    # Step 1: SHA-256 hashing on the public key
    sha256_result = SHA256.new(bytes.fromhex(pubkey)).digest()

    # Step 2: RIPEMD-160 hashing on the result of SHA-256 using PyCryptodome
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_result)
    ripemd160_result = ripemd160.digest()

    # Step 3: Add version byte (0x00 for Mainnet)
    versioned_payload = b"\x00" + ripemd160_result

    # Step 4 and 5: Calculate checksum and append to the payload
    checksum = SHA256.new(SHA256.new(versioned_payload).digest()).digest()[:4]
    binary_address = versioned_payload + checksum

    # Step 6: Encode the binary address in Base58
    bitcoin_address = base58.b58encode(binary_address).decode("utf-8")
    return bitcoin_address


class BlockchainSyncStatus:
    def __init__(self, config):
        self.config = config

    def spinner(self):
        spinner_words = itertools.cycle(["Tao", "Bit", "Tensor", "AI"])
        while True:
            yield next(spinner_words)

    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.config["rpc_url"])
        spinner_gen = self.spinner()
        try:
            while True:
                current_block = rpc_connection.getblockcount()
                highest_block = rpc_connection.getblockchaininfo()["blocks"]
                spinner_word = next(spinner_gen)
                sys.stdout.write(
                    f"\rChecking sync status... {spinner_word} {current_block}/{highest_block}"
                )
                sys.stdout.flush()

                # Check if the current block is equal to the highest block
                if current_block == highest_block:
                    sys.stdout.write("\nNode is synced!\n")
                    return True
                else:
                    time.sleep(1)  # Wait a bit before checking again
        except Exception as e:
            sys.stdout.write(f"\nFailed to check sync status: {e}\n")
            return False


"""
# Example usage:
# Assuming you have a valid config dictionary with an RPC URL
config = {
    'rpc_url': 'http://username:password@localhost:8332'
}

blockchain_status = BlockchainSyncStatus(config)
blockchain_status.is_synced()
"""
