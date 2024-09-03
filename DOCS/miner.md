# Miner 

## Installation 

- `git clone https://github.com/safe-scan-ai/cancer-ai`

- create python virtualenv

`virtualenv venv --python=3.10`

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



`python neurons/miner.py --action evaluate --competition_id <COMPETITION ID> --model_path <NAME OF FILE WITH EXTENSION> `

If flag `--clean-after-run` is supplied, it will delete dataset after evaluating the model

### Upload to HuggingFace

- compresses code provided by --code-path
- uploads model and code to HuggingFace

`python neurons/miner.py --action upload --competition_id melanoma-1 --model_path test_model.onnx --hf_model_name file_name.zip --hf_repo_id repo/id --hf_token TOKEN`
```bash
python neurons/miner.py \
    --action upload \
    --competition_id <COMPETITION ID> \
    --model_path <NAME OF FILE WITH EXTENSION> \
    --code_directory <CODE DIRECTORY WITHOUT DATASETS> \
    --hf_model_name <MODEL NAME WITH EXTENSION> \
    --hf_repo_id <HF REPO ID > \
    --hf_token <HF API TOKEN> \
    --logging.debug
```


### Send model to validators 

- saves model information in metagraph
- validator can get information about your model to test it 

```bash
python neurons/miner.py \
    --action submit \
    --model_path <NAME OF FILE WITH EXTENSION> \
    --competition_id <COMPETITION ID> \
    --hf_code_filename "melanoma-1-piwo.zip" \
    --hf_model_name <MODEL NAME WITH EXTENSION> \
    --hf_repo_id <HF REPO ID> \
    --hf_repo_type model \
    --wallet.name <WALLET NAME> \
    --wallet.hotkey <WALLET HOTKEY NAME> \
    --netuid <NETUID> \
    --subtensor.network <test|finney> \
    --logging.debug 
    ```
