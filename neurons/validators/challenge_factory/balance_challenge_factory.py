import time
import threading
from typing import List, Tuple
import random

from insights.protocol import Challenge

class BalanceChallengeFactory:
    """
    BalanceChallengeFactory generates challenges for balance tracking model periodically
    It has several tiers and generate one challenge for each tier
    It caches generated challenges and provides them to validators
    """
    def __init__(self, node, interval=300, tier_gap=100000):
        self.node = node # blockchain node
        self.interval = interval  # seconds between updates
        self.tier_gap = tier_gap # a block height gap between tiers
        self.last_generated_tier = -1
        self.challenges: List[Tuple[Challenge, int]] = [] # list of generated challenges and expected results, each element corresponding to each tier
        self.lock = threading.Lock()  # Lock for synchronizing access to 'challenges'
        self.running = True  # Control the thread activity
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

    def update(self):
        while self.running:
            # Use the lock to ensure safe update of the variable
            # TODO: generate challenge logic here
            block_height = 0
            latest_block_height = self.node.get_current_block_height() - 6
            new_tier = self.last_generated_tier + 1
            if new_tier * self.tier_gap < latest_block_height:
                block_height = random.randint(new_tier * self.tier_gap, min(latest_block_height, (new_tier + 1) * self.tier_gap - 1))
            else:
                new_tier = 0
            challenge, expected_output = self.node.create_balance_challenge(block_height)

            with self.lock:
                if new_tier > len(self.challenges) - 1:
                    self.challenges.append((challenge, expected_output))
                else:
                    self.challenges[new_tier] = (challenge, expected_output)
                
            self.last_generated_tier = new_tier
            time.sleep(self.interval)  # Wait for the specified interval

    def get_challenge(self, block_height: int) -> Tuple[Challenge, int]:
        with self.lock:
            max_tier = min(block_height // self.tier_gap, len(self.challenges) - 1)
            random_tier = random.randint(0, max_tier)
            return self.challenges[random_tier]

    def stop(self):
        self.running = False
        self.thread.join()  # Wait for the thread to finish
