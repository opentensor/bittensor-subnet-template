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
- logs evaluation results 



`python neurons/miner.py --action evaluate --competition-id <COMPETITION ID> --model-path <NAME OF FILE WITH EXTENSION> `

If flag `--clean-after-run` is supplied, it will delete dataset after evaluating the model

### Upload to HuggingFace

- compresses code provided by --code-path
- uploads model and code to HuggingFace

`python neurons/miner.py --action upload --competition-id melanoma-1 --model-path test_model.onnx --hf-model-name file_name.zip --hf-repo-id repo/id --hf-token TOKEN`
```bash
python neurons/miner.py \
    --action upload \
    --competition-id <COMPETITION ID> \
    --model-path <NAME OF FILE WITH EXTENSION> \
    --code-directory <CODE DIRECTORY WITHOUT DATASETS> \
    --hf-model-name <MODEL NAME WITH EXTENSION> \
    --hf-repo-id <HF REPO ID > \
    --hf-token <HF API TOKEN> \
    --logging.debug
```


### Send model to validators 

- saves model information in metagraph
- validator can get information about your model to test it 

```bash
python neurons/miner.py \
    --action submit \
    --model-path <NAME OF FILE WITH EXTENSION> \
    --competition-id <COMPETITION ID> \
    --hf-code-filename "melanoma-1-piwo.zip" \
    --hf-model-name <MODEL NAME WITH EXTENSION> \
    --hf-repo-id <HF REPO ID> \
    --hf-repo-type model \
    --wallet.name <WALLET NAME> \
    --wallet.hotkey <WALLET HOTKEY NAME> \
    --netuid <NETUID> \
    --subtensor.network <test|finney> \
    --logging.debug 
    ```