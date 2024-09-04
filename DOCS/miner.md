# Miner Script Documentation

This documentation provides an overview of the miner script, its functionality, requirements, and usage instructions.

## Overview

The miner script is designed to manage models, evaluate them locally, and upload them to HuggingFace, as well as submit models to validators within a specified network.

Key features of the script include:
- **Local Model Evaluation**: Allows you to evaluate models against a dataset locally.
- **HuggingFace Upload**: Compresses and uploads models and code to HuggingFace.
- **Model Submission to Validators**: Saves model information in the metagraph, enabling validators to test the models.

## Prerequisites

- **Python 3.10**: The script is written in Python and requires Python 3.10 to run.
- **Virtual Environment**: It's recommended to run the script within a virtual environment to manage dependencies.

## Installation

1. **Create a Virtual Environment**
Set up a virtual environment for the project:

   ```bash
   virtualenv venv --python=3.10
   source venv/bin/activate
   ```

## Install Required Python Packages
Install any required Python packages listed in `requirements.txt`:

```
pip install -r requirements.txt
```

## Usage

### Prerequisites

Before running the script, ensure the following:

- You are in the base directory of the project.
- Your virtual environment is activated.
- Run the following command to set the `PYTHONPATH`:

```
export PYTHONPATH="${PYTHONPATH}:./"
```

### Evaluate Model Locally
This mode performs the following tasks:

- Downloads the dataset.
- Loads your model.
- Prepares data for execution.
- Logs evaluation results.

To evaluate a model locally, use the following command:

```
python neurons/miner.py --action evaluate --competition_id <COMPETITION ID> --model_path <NAME OF FILE WITH EXTENSION>
```

If flag `--clean-after-run` is supplied, it will delete dataset after evaluating the model

### Upload to HuggingFace

This mode compresses the code provided by `--code-path` and uploads the model and code to HuggingFace.

To upload to HuggingFace, use the following command:

```
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

### Submit Model to Validators

This mode saves model information in the metagraph, allowing validators to retrieve information about your model for testing.

To submit a model to validators, use the following command:

```
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

## Notes
- **Environment**: The script uses the environment from which it is executed, so ensure all necessary environment variables and dependencies are correctly configured.
- **Model Evaluation**: The `evaluate` action downloads necessary datasets and runs the model locally; ensure that your local environment has sufficient resources.
