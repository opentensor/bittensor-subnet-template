from bitcoinrpc.authproxy import AuthServiceProxy
import itertools
import time
import sys


class BlockchainSyncStatus:
    def __init__(self, config):
        self.config = config


    def spinner(self):
        spinner_words = itertools.cycle(['Tao', 'Bit', 'Tensor', 'AI'])
        while True:
            yield next(spinner_words)


    def is_synced(self):
        rpc_connection = AuthServiceProxy(self.config['rpc_url'])
        spinner_gen = self.spinner()
        try:
            while True:
                current_block = rpc_connection.getblockcount()
                highest_block = rpc_connection.getblockchaininfo()['blocks']
                spinner_word = next(spinner_gen)
                sys.stdout.write(f'\rChecking sync status... {spinner_word} {current_block}/{highest_block}')
                sys.stdout.flush()

                # Check if the current block is equal to the highest block
                if current_block == highest_block:
                    sys.stdout.write('\nNode is synced!\n')
                    return True
                else:
                    time.sleep(1)  # Wait a bit before checking again
        except Exception as e:
            sys.stdout.write(f'\nFailed to check sync status: {e}\n')
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