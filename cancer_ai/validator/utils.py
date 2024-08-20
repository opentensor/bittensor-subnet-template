from enum import Enum
import os


class ModelType(Enum):
    ONNX = "ONNX"
    TENSORFLOW_SAVEDMODEL = "TensorFlow SavedModel"
    KERAS_H5 = "Keras H5"
    PYTORCH = "PyTorch"
    SCIKIT_LEARN = "Scikit-learn"
    XGBOOST = "XGBoost"
    UNKNOWN = "Unknown format"


def detect_model_format(file_path) -> ModelType:
    _, ext = os.path.splitext(file_path)

    if ext == ".onnx":
        return ModelType.ONNX
    elif ext == ".h5":
        return ModelType.KERAS_H5
    elif ext in [".pt", ".pth"]:
        return ModelType.PYTORCH
    elif ext in [".pkl", ".joblib"]:
        return ModelType.SCIKIT_LEARN
    elif ext in [".model", ".json", ".txt"]:
        return ModelType.XGBOOST

    try:
        with open(file_path, "rb") as f:
            # TODO check if it works
            header = f.read(4)
            if (
                header == b"PK\x03\x04"
            ):  # Magic number for ZIP files (common in TensorFlow SavedModel)
                return ModelType.TENSORFLOW_SAVEDMODEL
            elif header[:2] == b"\x89H":  # Magic number for HDF5 files (used by Keras)
                return ModelType.KERAS_H5

    except Exception:
        return ModelType.UNKNOWN

    return ModelType.UNKNOWN
