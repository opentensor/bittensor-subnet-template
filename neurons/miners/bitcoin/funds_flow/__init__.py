from neurons.protocol import OutputMetadata, MODEL_TYPE_FUNDS_FLOW

MODEL_VERSION = 1
MODEL_TYPE = MODEL_TYPE_FUNDS_FLOW
MODEL_SCHEMA = """
               """
OUTPUT_METADATA = (
    OutputMetadata(
        network="BITCOIN",
        assets=["BTC"],
        model_type=MODEL_TYPE,
        model_version=MODEL_VERSION,
    ),
)
