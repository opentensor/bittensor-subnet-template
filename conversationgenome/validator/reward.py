# The MIT License (MIT)
# Copyright © 2023 Yuma Rao

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

import torch
import bittensor as bt
from typing import List
import editdistance
import time

from scipy.optimize import linear_sum_assignment

from conversationgenome.protocol import CgSynapse


def get_position_reward(boxA: List[float], boxB: List[float] = None):
    """
    Calculate the intersection over union (IoU) of two bounding boxes.

    Args:
    - boxA (list): Bounding box coordinates of box A in the format [x1, y1, x2, y2].
    - boxB (list): Bounding box coordinates of box B in the format [x1, y1, x2, y2].

    Returns:
    - float: The IoU value, ranging from 0 to 1.
    """
    if not boxB:
        return 0.0

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    intersection_area = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    boxA_area = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxB_area = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = intersection_area / float(boxA_area + boxB_area - intersection_area)

    return iou

def get_text_reward(text1: str, text2: str = None):
    """
    Calculate the edit distance between two strings.

    Args:
    - text1 (str): The first string.
    - text2 (str): The second string.

    Returns:
    - float: The edit distance between the two strings. Normalized to be between 0 and 1.
    """
    if not text2:
        return 0.0

    return 1 - editdistance.eval(text1, text2) / max(len(text1), len(text2))

def get_font_reward(font1: dict, font2: dict = None, alpha_size=1.0, alpha_family=1.0):
    """
    Calculate the distance between two fonts, based on the font size and font family.

    Args:
    - font1 (dict): The first font.
    - font2 (dict): The second font.

    Returns:
    - float: The distance between the two fonts. Normalized to be between 0 and 1.
    """
    if not font2:
        return 0.0

    font_size_score = ( 1 - abs(font1['size'] - font2['size']) / max(font1['size'], font2['size']) )
    font_family_score = alpha_family * float(font1['family'] == font2['family'])
    return (alpha_size * font_size_score + alpha_family * font_family_score) / (alpha_size + alpha_family)

def section_reward(label: dict, pred: dict, alpha_p=1.0, alpha_f=1.0, alpha_t=1.0, verbose=False):
    """
    Score a section of the image based on the section's correctness.
    Correctness is defined as:
    - the intersection over union of the bounding boxes,
    - the delta between the predicted font and the ground truth font,
    - and the edit distance between the predicted text and the ground truth text.

    Args:
    - label (dict): The ground truth data for the section.
    - pred (dict): The predicted data for the section.

    Returns:
    - float: The score for the section. Bounded between 0 and 1.
    """
    reward = {
        'text': get_text_reward(label['text'], pred.get('text')),
        'position': get_position_reward(label['position'], pred.get('position')),
        'font': get_font_reward(label['font'], pred.get('font')),
    }
    print("reward", reward)
    print("alpha", alpha_p,  alpha_f, alpha_t)
    if not alpha_p:
        alpha_p = 1.0
    if not alpha_f:
        alpha_f = 1.0
    if not alpha_t:
         alpha_t = 1.0

    reward['total'] = (alpha_t * reward['text'] + alpha_p * reward['position'] + alpha_f * reward['font']) / (alpha_p + alpha_f + alpha_t)

    if verbose:
        bt.logging.info(', '.join([f"{k}: {v:.3f}" for k,v in reward.items()]))

    return reward

def sort_predictions(labels: List[dict], predictions: List[dict], draw=False) -> List[dict]:
    """
    Sort the predictions to match the order of the ground truth data using the Hungarian algorithm.

    Args:
    - labels (list): The ground truth data for the image.
    - predictions (list): The predicted data for the image.

    Returns:
    - list: The sorted predictions.
    """

    # First, make sure that the predictions is at least as long as the image data
    predictions += [{}] * (len(labels) - len(predictions))
    r = torch.zeros((len(labels), len(predictions)))
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            r[i,j] = section_reward(labels[i], predictions[j])['total']

    # Use the Hungarian algorithm to find the best assignment
    row_indices, col_indices = linear_sum_assignment(r, maximize=True)

    sorted_predictions = [predictions[i] for i in col_indices]

    return sorted_predictions


def reward(self, labels: List[dict], response: CgSynapse) -> float:
    """
    Reward the miner response to the OCR request. This method returns a reward
    value for the miner, which is used to update the miner's score.

    Args:
    - labels (List[dict]): The true data underlying the image sent to the miner.
    - response (CgSynapse): Response from the miner.

    The expected fields in each section of the response are:
    - position (List[int]): The bounding box of the section e.g. [x0, y0, x1, y1]
    - font (dict): The font of the section e.g. {'family': 'Times New Roman', 'size':12}
    - text (str): The text of the section e.g. 'Hello World!'

    Returns:
    - float: The reward value for the miner.
    """
    time.sleep(5)
    return 0.5
    predictions = response.response
    if predictions is None:
        return 0.0

    # Sort the predictions to match the order of the ground truth data as best as possible
    predictions = sort_predictions(labels, predictions)

    alpha_p = self.config.neuron.alpha_position
    alpha_t = self.config.neuron.alpha_text
    alpha_f = self.config.neuron.alpha_font
    alpha_prediction = self.config.neuron.alpha_prediction
    alpha_time = self.config.neuron.alpha_time

    # Take mean score over all sections in document (note that we don't penalize extra sections)
    section_rewards = [
        section_reward(label, pred, verbose=True, alpha_f=alpha_f, alpha_p=alpha_p, alpha_t=alpha_t)
        for label, pred in zip(labels, predictions)
    ]
    prediction_reward = torch.mean(torch.FloatTensor([reward['total'] for reward in section_rewards]))
    time_reward = 1
    #time_reward = max(1 - response.time_elapsed / self.config.neuron.timeout, 0)
    print("TOTALREWARD", alpha_prediction, prediction_reward,  alpha_time, time_reward)
    if not alpha_time:
        alpha_time = 1
    if not  alpha_prediction:
        alpha_prediction = 1
    total_reward = (alpha_prediction * prediction_reward + alpha_time * time_reward) / (alpha_prediction + alpha_time)

    bt.logging.info(f"prediction_reward: {prediction_reward:.3f}, time_reward: {time_reward:.3f}, total_reward: {total_reward:.3f}")
    return total_reward

def get_rewards(
    self,
    labels: List[dict],
    responses: List[CgSynapse],
) -> torch.FloatTensor:
    """
    Returns a tensor of rewards for the given image and responses.

    Args:
    - image (List[dict]): The true data underlying the image sent to the miner.
    - responses (List[CgSynapse]): A list of responses from the miner.

    Returns:
    - torch.FloatTensor: A tensor of rewards for the given image and responses.
    """
    # Get all the reward results by iteratively calling your reward() function.
    return torch.FloatTensor(
        [reward(self, labels, response) for response in responses]
    ).to(self.device)
