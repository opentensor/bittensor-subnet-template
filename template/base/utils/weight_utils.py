import numpy as np
from typing import Tuple, List, Union, Any
import bittensor
from numpy import ndarray, dtype, floating, complexfloating

U32_MAX = 4294967295
U16_MAX = 65535


def normalize_max_weight(
        x: np.ndarray, limit: float = 0.1
) -> np.ndarray:
    r"""Normalizes the numpy array x so that sum(x) = 1 and the max value is not greater than the limit.
    Args:
        x (:obj:`np.ndarray`):
            Array to be max_value normalized.
        limit: float:
            Max value after normalization.
    Returns:
        y (:obj:`np.ndarray`):
            Normalized x array.
    """
    epsilon = 1e-7  # For numerical stability after normalization

    weights = x.copy()
    values = np.sort(weights)

    if x.sum() == 0 or len(x) * limit <= 1:
        return np.ones_like(x) / x.size
    else:
        estimation = values / values.sum()

        if estimation.max() <= limit:
            return weights / weights.sum()

        # Find the cumulative sum and sorted array
        cumsum = np.cumsum(estimation, 0)

        # Determine the index of cutoff
        estimation_sum = np.array(
            [(len(values) - i - 1) * estimation[i] for i in range(len(values))]
        )
        n_values = (estimation / (estimation_sum + cumsum + epsilon) < limit).sum()

        # Determine the cutoff based on the index
        cutoff_scale = (limit * cumsum[n_values - 1] - epsilon) / (
                1 - (limit * (len(estimation) - n_values))
        )
        cutoff = cutoff_scale * values.sum()

        # Applying the cutoff
        weights[weights > cutoff] = cutoff

        y = weights / weights.sum()

        return y


def convert_weights_and_uids_for_emit(
        uids: np.ndarray, weights: np.ndarray
) -> Tuple[List[int], List[int]]:
    r"""Converts weights into integer u32 representation that sum to MAX_INT_WEIGHT.
    Args:
        uids (:obj:`np.ndarray,`):
            Array of uids as destinations for passed weights.
        weights (:obj:`np.ndarray,`):
            Array of weights.
    Returns:
        weight_uids (List[int]):
            Uids as a list.
        weight_vals (List[int]):
            Weights as a list.
    """
    # Checks.
    uids = np.asarray(uids)
    weights = np.asarray(weights)

    # Get non-zero weights and corresponding uids
    non_zero_weights = weights[weights > 0]
    non_zero_weight_uids = uids[weights > 0]

    # Debugging information
    bittensor.logging.debug(f"weights: {weights}")
    bittensor.logging.debug(f"non_zero_weights: {non_zero_weights}")
    bittensor.logging.debug(f"uids: {uids}")
    bittensor.logging.debug(f"non_zero_weight_uids: {non_zero_weight_uids}")

    if np.min(weights) < 0:
        raise ValueError(
            "Passed weight is negative cannot exist on chain {}".format(weights)
        )
    if np.min(uids) < 0:
        raise ValueError("Passed uid is negative cannot exist on chain {}".format(uids))
    if len(uids) != len(weights):
        raise ValueError(
            "Passed weights and uids must have the same length, got {} and {}".format(
                len(uids), len(weights)
            )
        )
    if np.sum(weights) == 0:
        bittensor.logging.debug("nothing to set on chain")
        return [], []  # Nothing to set on chain.
    else:
        max_weight = float(np.max(weights))
        weights = [
            float(value) / max_weight for value in weights
        ]  # max-upscale values (max_weight = 1).
        bittensor.logging.debug(f"setting on chain max: {max_weight} and weights: {weights}")

    weight_vals = []
    weight_uids = []
    for i, (weight_i, uid_i) in enumerate(list(zip(weights, uids))):
        uint16_val = round(
            float(weight_i) * int(U16_MAX)
        )  # convert to int representation.

        # Filter zeros
        if uint16_val != 0:  # Filter zeros
            weight_vals.append(uint16_val)
            weight_uids.append(uid_i)
    bittensor.logging.debug(f"final params: {weight_uids} : {weight_vals}")
    return weight_uids, weight_vals


def process_weights_for_netuid(
        uids,
        weights: np.ndarray,
        netuid: int,
        subtensor: "bittensor.subtensor",
        metagraph: "bittensor.metagraph" = None,
        exclude_quantile: int = 0,
) -> Union[tuple[ndarray[Any, dtype[Any]], Union[
    Union[ndarray[Any, dtype[floating[Any]]], ndarray[Any, dtype[complexfloating[Any, Any]]]], Any]], tuple[
    ndarray[Any, dtype[Any]], ndarray], tuple[Any, ndarray]]:
    bittensor.logging.debug("process_weights_for_netuid()")
    bittensor.logging.debug("weights", weights)
    bittensor.logging.debug("netuid", netuid)
    bittensor.logging.debug("subtensor", subtensor)
    bittensor.logging.debug("metagraph", metagraph)

    # Get latest metagraph from chain if metagraph is None.
    if metagraph is None:
        metagraph = subtensor.metagraph(netuid)

    # Cast weights to floats.
    if not isinstance(weights, np.ndarray) or weights.dtype != np.float32:
        weights = weights.astype(np.float32)

    # Network configuration parameters from an subtensor.
    # These parameters determine the range of acceptable weights for each neuron.
    quantile = exclude_quantile / U16_MAX
    min_allowed_weights = subtensor.min_allowed_weights(netuid=netuid)
    max_weight_limit = subtensor.max_weight_limit(netuid=netuid)
    bittensor.logging.debug("quantile", quantile)
    bittensor.logging.debug("min_allowed_weights", min_allowed_weights)
    bittensor.logging.debug("max_weight_limit", max_weight_limit)

    # Find all non zero weights.
    non_zero_weight_idx = np.argwhere(weights > 0).squeeze()
    non_zero_weight_uids = uids[non_zero_weight_idx]
    non_zero_weights = weights[non_zero_weight_idx]
    if non_zero_weights.size == 0 or metagraph.n < min_allowed_weights:
        bittensor.logging.warning("No non-zero weights returning all ones.")
        final_weights = np.ones(metagraph.n) / metagraph.n
        bittensor.logging.debug("final_weights", final_weights)
        return np.arange(len(final_weights)), final_weights

    elif non_zero_weights.size < min_allowed_weights:
        bittensor.logging.warning(
            "No non-zero weights less then min allowed weight, returning all ones."
        )
        weights = (
                np.ones(metagraph.n) * 1e-5
        )  # creating minimum even non-zero weights
        weights[non_zero_weight_idx] += non_zero_weights
        bittensor.logging.debug("final_weights", weights)
        normalized_weights = normalize_max_weight(
            x=weights, limit=max_weight_limit
        )
        return np.arange(len(normalized_weights)), normalized_weights

    bittensor.logging.debug("non_zero_weights", non_zero_weights)

    # Compute the exclude quantile and find the weights in the lowest quantile
    max_exclude = max(0, len(non_zero_weights) - min_allowed_weights) / len(
        non_zero_weights
    )
    exclude_quantile = min([quantile, max_exclude])
    lowest_quantile = np.quantile(non_zero_weights, exclude_quantile)
    bittensor.logging.debug("max_exclude", max_exclude)
    bittensor.logging.debug("exclude_quantile", exclude_quantile)
    bittensor.logging.debug("lowest_quantile", lowest_quantile)

    # Exclude all weights below the allowed quantile.
    non_zero_weight_uids = non_zero_weight_uids[lowest_quantile <= non_zero_weights]
    non_zero_weights = non_zero_weights[lowest_quantile <= non_zero_weights]
    bittensor.logging.debug("non_zero_weight_uids", non_zero_weight_uids)
    bittensor.logging.debug("non_zero_weights", non_zero_weights)

    # Normalize weights and return.
    normalized_weights = normalize_max_weight(
        x=non_zero_weights, limit=max_weight_limit
    )
    bittensor.logging.debug("final_weights", normalized_weights)

    return non_zero_weight_uids, normalized_weights
