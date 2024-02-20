import os

from neurons.nodes.bitcoin.node_utils import initialize_tx_out_hash_table
from utils import index_hash_table, save_hash_table
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Construct a hash table from vout csv data.')

    parser.add_argument('--csvfile', type=str, help='Path to the CSV file')
    parser.add_argument('--targetpath', type=str, help='Path to the target pickle file')
    parser.add_argument('--new', action='store_true', help='Create new pickle file')
    args = parser.parse_args()

    return args.csvfile, args.targetpath, args.new


if __name__ == '__main__':
    csv_file, target_path, new = parse_args()

    if not csv_file or not target_path:
        print("Provide csvfile and targetpath parameter.")
        exit()

    if os.path.exists(target_path):
        os.remove(target_path)

    hash_table = initialize_tx_out_hash_table()
    n_threads = int(os.environ.get("INDEXING_THREADS", 64))
    index_hash_table(hash_table, csv_file, n_threads=n_threads)
    save_hash_table(hash_table, target_path)