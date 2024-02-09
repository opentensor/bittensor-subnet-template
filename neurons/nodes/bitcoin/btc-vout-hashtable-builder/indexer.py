from utils import initialize_hash_table, index_hash_table, save_hash_table, load_hash_table
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

    hash_table = initialize_hash_table()

    if new:
        user_input = input("Are you going to create a new pickle file? (yes/no)").strip().lower()
        if not user_input in ["yes", "y"]:
            exit()
        else:
            hash_table = initialize_hash_table()
    else:
        hash_table = load_hash_table(target_path)

    index_hash_table(hash_table, csv_file, n_threads=64)
    save_hash_table(hash_table, target_path)