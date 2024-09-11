from cancer_ai.validator.model_manager import ModelInfo
 
def get_mock_hotkeys_with_models():
    return {
        # good model
        "hfsss_OgEeYLdTgrRIlWIdmbcPQZWTdafatdKfSwwddsavDfO": ModelInfo(
            hf_repo_id="Kabalisticus/test_bs_model",
            hf_model_filename="good_test_model.onnx",
            hf_repo_type="model",
        ),
        # Model made from image, extension changed
        "hfddd_OgEeYLdTgrRIlWIdmbcPQZWTfsafasftdKfSwwvDf": ModelInfo(
            hf_repo_id="Kabalisticus/test_bs_model",
            hf_model_filename="false_from_image_model.onnx",
            hf_repo_type="model",
        ),
        # Good model with wrong extension
        "hf_OgEeYLdTslgrRfasftdKfSwwvDf": ModelInfo(
            hf_repo_id="Kabalisticus/test_bs_model",
            hf_model_filename="wrong_extension_model.onx",
            hf_repo_type="model",
        ),
        # good model on safescan
        "wU2LapwmZfYL9AEAWpUR6sasfsaFoFvqHnzQ5F71Mhwotxujq": ModelInfo(
            hf_repo_id="safescanai/test_dataset",
            hf_model_filename="best_model.onnx",
            hf_repo_type="dataset",
        ),
    }