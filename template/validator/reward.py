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
import numpy as np
from typing import Dict, List
import bittensor as bt


def reward(task: Dict[str, str], response_payload: Dict[str, str]) -> float:
    """
    Reward the miner response to the inference request. This method returns a
    reward value for the miner, which is used to update the miner's score.

    Returns:
    - float: The reward value for the miner.
    """
    expected = task["expected"].strip().lower()
    normalized_response = (
        response_payload.get("response", "").strip().lower()
    )
    bt.logging.info(
        "In rewards, task id: "
        f"{task['id']}, response: {normalized_response}, expected: {expected}"
    )
    return 1.0 if normalized_response == expected else 0.0


def get_rewards(
    self,
    task: Dict[str, str],
    responses: List[Dict[str, str]],
) -> np.ndarray:
    """
    Returns an array of rewards for the given task and responses.

    Args:
    - task (Dict[str, str]): The task sent to the miner, including the expected answer.
    - responses (List[Dict[str, str]]): A list of miner payloads.

    Returns:
    - np.ndarray: An array of rewards for the given query and responses.
    """
    # Get all the reward results by iteratively calling your reward() function.

    return np.array([reward(task, response) for response in responses])
