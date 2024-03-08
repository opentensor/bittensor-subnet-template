from abc import ABC, abstractmethod

import concurrent

class Node(ABC):
    def __init__(self):
       pass


    @abstractmethod
    def get_current_block_height(self):
        ...

    @abstractmethod
    def get_block_by_height(self, block_height):
        ...

    @abstractmethod
    def create_challenge(self, start_block_height, last_block_height):
        ...

    def validate_data_sample(self, data_sample):
        block_data = self.get_block_by_height(data_sample['block_height'])
        is_valid = len(block_data["tx"]) == data_sample["transaction_count"]
        return is_valid

    def validate_all_data_samples(self, data_samples, blocks_to_check):
        if len(data_samples) != len(blocks_to_check):
            return False
        
        for sample in data_samples:
            if sample['block_height'] not in blocks_to_check:
                return False

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.validate_data_sample, sample) for sample in data_samples]

            for future in concurrent.futures.as_completed(futures):
                if not future.result():
                    return False
        return True 
