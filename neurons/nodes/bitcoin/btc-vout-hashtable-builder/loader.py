from utils import load_hash_table

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Construct a hash table from pickles data.')
    parser.add_argument('--picklepath', type=str, help='Path to the pickle file')
    args = parser.parse_args()

    return args.picklepath

if __name__ == '__main__':
    pickle_path = parse_args()

    if not pickle_path:
        print("Provide pickle path parameter.")
        exit()

    hash_table = load_hash_table(pickle_path)

    print(sum([len(hash_table[sub_key].keys()) for sub_key in hash_table.keys()]))