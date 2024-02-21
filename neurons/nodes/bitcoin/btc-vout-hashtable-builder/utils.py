import os
import pickle
import time

import multiprocessing
from functools import partial

from neurons.nodes.bitcoin.node_utils import initialize_tx_out_hash_table, get_tx_out_hash_table_sub_keys


def calculate_chunk_positions(csv_file, n_threads=64):
    positions = []

    # open csv file in read mode
    with open(csv_file, 'r', newline='') as file:
        # calculate file size and chunk size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        chunk_size = file_size // n_threads

        # calculate correct chunk positions
        for i in range(n_threads):
            pos = i * chunk_size
            if pos == 0: positions.append(pos)
            else:
                file.seek(pos)
                file.readline()
                positions.append(file.tell())

    # return pairs of start_pos and end_pos
    result = []
    for i in range(len(positions)):
        start_pos = positions[i]
        end_pos = positions[i + 1] if i < len(positions) - 1 else -1
        result.append((start_pos, end_pos))
    return result


# Process logic for each thread
def process_lines(pos_range, csv_file):
    start_pos = pos_range[0]
    end_pos = pos_range[1]
    hash_table = initialize_tx_out_hash_table()
    with open(csv_file, 'r') as file:
        file.seek(start_pos)
        i = 0
        while True:
            i += 1
            line = file.readline()

            # Break if end of file
            if not line:
                break

            # Process line
            columns = line.split(';')
            txid = columns[0].strip()
            vout = columns[1].strip()
            value = columns[2].strip()
            address = columns[4].strip()
            hash_table[txid[:3]][(txid, vout)] = (address, value)

            # Break if processed all rows of the chunk
            if end_pos > -1 and file.tell() >= end_pos:
                break
    return hash_table


def index_hash_table(hash_table, csv_file, n_threads=64, debug=1):
    start_time = time.time()
    print("Indexing started.")

    chunk_positions = calculate_chunk_positions(csv_file, n_threads)

    # Create and start threads
    pool = multiprocessing.Pool()
    new_hash_tables = pool.map(partial(process_lines, csv_file=csv_file), chunk_positions)

    # Close the pool of proceses
    pool.close()
    pool.join()

    end_time = time.time()
    print(f"Indexing completed in {end_time - start_time} seconds.")

    print("Merging started.")
    time1 = time.time()
    merge_hash_tables(hash_table, new_hash_tables)
    time2 = time.time()
    print(f"Merging completed in {time2 - time1} seconds.")


def merge_hash_tables(hash_table, new_hash_tables):
    sub_keys = get_tx_out_hash_table_sub_keys()
    for new_hash_table in new_hash_tables:
        for sub_key in sub_keys:
            hash_table[sub_key].update(new_hash_table[sub_key])


def save_hash_table(hash_table, target_path, debug=1):
    print("Saving started.")
    time1 = time.time()

    with open(target_path, 'wb') as file:
        pickle.dump(hash_table, file)

    time2 = time.time()
    print(f"Saving completed in {time2 - time1} seconds.")


def load_hash_table(pickle_path, debug=1):
    print("Loading started")
    time1 = time.time()

    with open(pickle_path, 'rb') as file:
        hash_table = pickle.load(file)
        time2 = time.time()
        print(f"Loading completed in {time2 - time1} seconds.")
        return hash_table