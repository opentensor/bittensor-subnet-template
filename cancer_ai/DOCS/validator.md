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