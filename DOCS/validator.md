# Validator Script Documentation

This documentation provides an overview of the validator script, its functionality, requirements, and usage instructions.

## Overview

The validator script is designed to run a validator process and automatically update it whenever a new version is released. This script was adapted from the [original script](https://github.com/macrocosm-os/pretraining/blob/main/scripts/start_validator.py) in the Pretraining Subnet repository.

Key features of the script include:
- **Automatic Updates**: The script checks for updates periodically and ensures that the latest version of the validator is running by pulling the latest code from the repository and upgrading necessary Python packages.
- **Command-Line Argument Compatibility**: The script now properly handles custom command-line arguments and forwards them to the validator (`neurons/validator.py`).
- **Virtual Environment Support**: The script runs within the same virtual environment that it is executed in, ensuring compatibility and ease of use.
- **PM2 Process Management**: The script uses PM2, a process manager, to manage the validator process.

## Prerequisites

### Server requirements

 - 64GB of RAM
 - storage: 500GB, extendable
 - GPU - nVidia RTX, 12GB VRAM (will work without GPU, but slower)

### System requirements

- **Python 3.10 and virtualenv **: The script is written in Python and requires Python 3.10 to run.
- **PM2**: PM2 must be installed and available on your system. It is used to manage the validator process.
- **zip and unzip**

## Installation and Setup

1. **Clone the Repository**: Make sure you have cloned the repository containing this script and have navigated to the correct directory.

2. **Install PM2**: Ensure PM2 is installed globally on your system. If it isn't, you can install it using npm:

```
   npm install -g pm2
```

3. **Set Up Virtual Environment**: If you wish to run the script within a virtual environment, create and activate the environment before running the script:
```
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

4. **Install Required Python Packages**: Install any required Python packages listed in requirements.txt:
```
pip install -r requirements.txt
```


## Usage
To run the validator script, use the following command:
**TODO(DEV): CHANGE THESE VALUES BEFORE THE RELEASE TO MAINNET NETUID!!!**

```
python3 scripts/start_validator.py --wallet.name=my-wallet --wallet.hotkey=my-hotkey --netuid=163

```

## Command-Line Arguments

- `--pm2_name`: Specifies the name of the PM2 process. Default is `"cancer_ai_vali"`.
- `--wallet.name`: Specifies the wallet name to be used by the validator.
- `--wallet.hotkey`: Specifies the hotkey associated with the wallet.
- `--subtensor.network`: Specifies the network name. Default is `"test"`.
- `--netuid`: Specifies the Netuid of the network. Default is `"163"`.
- `--logging.debug`: Enables debug logging if set to `1`. Default is `1`.


## How It Works

1. **Start Validator Process**: The script starts the validator process using PM2, based on the provided PM2 process name.
2. **Periodic Updates**: The script periodically checks for updates (every 5 minutes by default) by fetching the latest code from the git repository.
3. **Handle Updates**: If a new version is detected, the script pulls the latest changes, upgrades the Python packages, stops the current validator process, and restarts it with the updated code.
4. **Local Changes**: If there are local changes in the repository that conflict with the updates, the script attempts to rebase them. If conflicts persist, the rebase is aborted to preserve the local changes.

## Notes

- **Local Changes**: If you have made local changes to the codebase, the auto-update feature will attempt to preserve them. However, conflicts might require manual resolution.
- **Environment**: The script uses the environment from which it is executed, so ensure all necessary environment variables and dependencies are correctly configured.
