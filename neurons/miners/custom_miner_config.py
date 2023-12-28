import json

class CustomMinerConfig:
    """Class to read custom miner configuration from a JSON file."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CustomMinerConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.json_file = 'custom_miner_config.json'
        self.blacklisted_hotkeys = []
        self._load_config_from_file()

    def _load_config_from_file(self):
        """Loads configuration from the specified JSON file."""
        try:
            with open(self.json_file, 'r') as file:
                data = json.load(file)
                self.blacklisted_hotkeys = data.get('blacklisted_hotkeys', [])
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            raise
        except FileNotFoundError as e:
            print(f"The file {self.json_file} was not found: {e}")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

# Example usage
# config_reader = CustomMinerConfig()
# print(config_reader.blacklisted_hotkeys)


