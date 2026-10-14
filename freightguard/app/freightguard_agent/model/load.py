import os
from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Amazon Bedrock model client using AWS IAM credentials in ap-south-1."""
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    region_name = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
    return BedrockModel(model_id=model_id, region_name=region_name)
