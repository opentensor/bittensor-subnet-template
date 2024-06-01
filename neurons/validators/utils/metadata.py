import bittensor as bt

from typing import List, Dict, Union
from collections import Counter

from protocols.blockchain import get_network_by_id
from neurons.storage import get_miners_metadata

class Metadata:
    hotkeys: List[Dict[str, Union[str, int]]]
    DISTRIBUTION_KEYS = ['network', 'hotkey', 'ip']
    
    def __init__(self, hotkeys: List[Dict[str, Union[str, int]]]) -> None:
        self.hotkeys = hotkeys
        self.distributions = {key: self._distribution_by_key(key) for key in self.DISTRIBUTION_KEYS}
        result = {}
        ck = [x['coldkey'] for x in self.hotkeys]
        for d in self.hotkeys:
            hotkey, coldkey = d['hotkey'], d['coldkey']
            result[hotkey] = ck.count(coldkey)
        
        self.distributions['coldkey'] = result
    
    @classmethod
    def build(cls, metagraph: bt.metagraph, config):
        return cls(cls.retrieve_data(metagraph, config)) 

    @classmethod
    def retrieve_data(cls, metagraph, config) -> List[Dict]:
        miners_metadata = get_miners_metadata(config, metagraph)
        hotkeys_metadata = []
        for neuron in metagraph.neurons:
            miner_metadata = miners_metadata.get(neuron.hotkey)

            network_id, version, end_block_height = None, None, None
            if miner_metadata:
                network_id = miner_metadata.n
                version = miner_metadata.cv
                end_block_height = miner_metadata.lb

            data = dict(
                hotkey = neuron.hotkey,
                coldkey = neuron.coldkey,
                ip = neuron.axon_info.ip,
                network = get_network_by_id(network_id),
                version = version,
                end_block_height = end_block_height
            )
            hotkeys_metadata.append(data)
        return hotkeys_metadata        

    def _distribution_by_key(self, key: str) -> Dict[str, int]:
        data = [hotkey[key] for hotkey in self.hotkeys if hotkey[key] is not None]
        return dict(Counter(data))        
    
    def get_metadata_for_hotkey(self, hotkey: str) -> Dict[str, Union[str, int]]:
        for m in self.hotkeys:
            if m['hotkey'] == hotkey:
                return m
        return None

    @property
    def network_distribution(self):
        return self.distributions['network']

    @property
    def hotkey_distribution(self):
        return self.distributions['hotkey']
    
    @property
    def ip_distribution(self):
        return self.distributions['ip']

    @property
    def coldkey_distribution(self):
        return self.distributions['coldkey']
    
    @property
    def worst_end_block_height(self):
        hotkey =  min(filter(lambda x: x.get('end_block_height') is not None, self.hotkeys), key=lambda x: x['end_block_height'])
        return hotkey['end_block_height']
