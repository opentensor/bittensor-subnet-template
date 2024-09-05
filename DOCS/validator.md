# Running validator

## Server requirements

### Minimal 
 - 32GB of RAM
 - storage: 100GB, extendable

### Recommended
 - 64GB of RAM
 - storage: 100GB0, extendable
 - GPU - nVidia RTX, 12GB VRAM

## System requirements

- tested on Ubuntu 22.04
- python 3.10
- virtualenv


## Installation 

- install `unzip` and `zip` commands 

`sudo apt install zip unzip`

- create virtualenv

`virtualenv venv --python=3.10`

- activate it 

`source venv/bin/activate`

- install requirements

`pip install -r requirements.txt`

## Running

Prerequirements 

- make sure you are in base directory of the project
- activate your virtualenv 
- run `export PYTHONPATH="${PYTHONPATH}:./"`

Main command

```bash
python neurons/validator.py \
    --netuid <NETUID> \
    --wallet.name <WALLET NAME> \
    --wallet.hotkey <WALLET HOTKEY NAME> \
    --subtensor.network <test|finney> \
    --logging.debug
```

Example for testnet 

```bash
python neurons/validator.py \
    --netuid 163 \
    --subtensor.network test \
    --wallet.name validator_testnet \
    --wallet.hotkey hotkey1 \
    --logging.debug
```


You can also run validator using auto-restart script, which does the following:
    - detects changes from git  
    - automatically pulls new code or configuration
    - installs new packages if required
    - restarts validator process

You can  use the same configuration switches as above, with one extra command - `--pm2_name`

```bash
python scripts/start_validator.py --pm2_name <PROCESS NAME>
```

