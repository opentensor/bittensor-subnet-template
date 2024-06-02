import bittensor as bt
from substrateinterface import SubstrateInterface

def get_weights_min_stake(substrate: SubstrateInterface):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    weight_min_stake = substrate.query(
        module="SubtensorModule", storage_function="WeightsMinStake", params=[]
    )
    bt.logging.debug(f"get_weights_min_stake() {weight_min_stake}")

    # Convert Rao to Tao
    return int(float(weight_min_stake.value) * 10**-9)
