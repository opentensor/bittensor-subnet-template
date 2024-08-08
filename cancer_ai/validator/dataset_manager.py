from datetime import datetime
from time import sleep
from huggingface_hub import HfApi

import schedule

database = {} # validator database 
dataset_path = "/dataset"
model_basepath = "./models"
models_db = {}

class DatasetManager:
    def __init__(self, config) -> None:
        self.config = config
        self.api = HfApi()
        self.hotkey_store = {}
        
    def get_model_state(self):
        return self.hotkey_store
    
    def load_model_state(self, hotkey_models: dict):
        self.hotkey_store = hotkey_models

    def sync_hotkeys(self, hotkeys: list):
        for hotkey in hotkeys:
            if hotkey not in self.hotkey_store:
                self.delete_model(hotkey)

    def download_miner_model(self, hotkey) -> str:
        """Downloads newest model from Hugging Face and save to disk
        Returns:
            str: path to downloaded model
        """
        return self.api.hf_hub_download(self.hotkey_store[hotkey]["repo_id"], self.hotkey_store[hotkey]["filename"], cache_dir=model_basepath,repo_type="space")
    
    def add_model(self,hotkey, repo_id, filename) -> None:
        """Saves locally information about new model
        """
        self.hotkey_store[hotkey] = {
            "repo_id": repo_id,
            "filename": filename
        }
    
    def delete_model(self, hotkey):
        print("Deleting model: ", hotkey)
        del self.hotkey_store[hotkey]


if __name__ == "__main__":
    dataset_manager = DatasetManager({})
    dataset_manager.add_model("wojtek", "vidhiparikh/House-Price-Estimator", "model_custom.pkcls")
    print(dataset_manager.download_miner_model("wojtek"))
