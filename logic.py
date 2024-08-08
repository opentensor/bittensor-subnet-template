from datetime import datetime
from time import sleep


import schedule

database = {} # validator database 
dataset_path = "/dataset"

models_db = {}

class Validator:

    def __init__(self, config=None, validator_hotkey):
        self.config = config
        self.dataset_refresh_date = datetime.now()
        self.validator_hotkey = validator_hotkey

    async def forward(self):
        pass

    async def reward(self):
        pass

    def receive_model(self, miner, model_url):
        """Get axon from miner"""
        return self.save_model(miner, model_url)
    
    def save_model(self, miner, model_url):
        """Save information about miner's models to database for later """
        database[miner.hotkey] = {
            "model_url":model_url,
            "timestamp": datetime.now()
        }

    def download_new_dataset(dataset_url):
        while True:
            if new_dataset_available:
                download_dataset()
                self.dataset_refresh_date = datetime.now()
            else:
                # if it's not available yet, wait for 60 seconds
                sleep(60)
                
    def download_save_model(self, hotkey, url):
        models_db[hotkey] = download_model(url["model_url"])

    def test_model(self, model) -> score:
        return get_model_accuracy(model)

    def test_models(self):
        for hotkey in models_db:
            self.download_save_model(hotkey, models_db[hotkey])

        for hotkey in models_db:
            result = self.test_model()
            save_result_to_wandb(self.validator_hotkey,hotkey, result)


    

validator = Validator()

schedule.every.day.at("18:00").do(validator.download_new_dataset)

    
            

    
