# Miner 

## Installation 

- create virtualenv

`virtualenv venv --python=3.10

- activate it 

`source venv/bin/activate`

- install requirements

`pip install -r requirements.txt`

## Run

Prerequirements 

- make sure you are in base directory of the project
- activate your virtualenv 
- run `export PYTHONPATH="${PYTHONPATH}:./"`


### Evaluate model localy

This mode will do following things
- download dataset 
- load your model
- prepare data for executing
- prints evaluation results 



`python neurons/miner.py --action evaluate --competition-id melanoma-1 --model-path test_model.onnx `

If flag `--clean-after-run` is supplied, it will delete dataset after evaluating the model

### Upload to HuggingFace

- compresses code provided by --code-path
- uploads model and code to HuggingFace

`python neurons/miner.py --action upload --competition-id melanoma-1 --model-path test_model.onnx --hf-model-name file_name --hf-repo-id repo/id --hf-token TOKEN`



### Send model to validators 

- saves model information in metagraph