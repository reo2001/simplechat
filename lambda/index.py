import json
import os
import re
import urllib.request

import boto3


MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
EXTERNAL_MODEL_ENDPOINT = os.environ.get("EXTERNAL_MODEL_ENDPOINT")

bedrock_client = None


def extract_region_from_arn(arn):
    """Extract the Lambda region from its ARN."""
    match = re.search(r"arn:aws:lambda:([^:]+):", arn)
    return match.group(1) if match else "us-east-1"


def invoke_bedrock(message, conversation_history, context):
    """Invoke Amazon Bedrock and return the generated text."""
    global bedrock_client

    if bedrock_client is None:
        region = extract_region_from_arn(context.invoked_function_arn)
        bedrock_client = boto3.client("bedrock-runtime", region_name=region)

    messages = conversation_history.copy()
    messages.append({"role": "user", "content": message})

    bedrock_messages = [
        {
            "role": item["role"],
            "content": [{"text": item["content"]}],
        }
        for item in messages
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]

    request_payload = {
        "messages": bedrock_messages,
        "inferenceConfig": {
            "maxTokens": 512,
            "stopSequences": [],
            "temperature": 0.7,
            "topP": 0.9,
        },
    }

    response = bedrock_client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(request_payload),
        contentType="application/json",
    )
    response_body = json.loads(response["body"].read())

    try:
        return response_body["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("No response content was returned by Amazon Bedrock") from error


def invoke_external_model(message):
    """Invoke the optional FastAPI inference endpoint used in the exercise."""
    payload = json.dumps(
        {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        EXTERNAL_MODEL_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read())

    return result["generated_text"]


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": (
                "Content-Type,X-Amz-Date,Authorization,X-Api-Key,"
                "X-Amz-Security-Token"
            ),
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        message = body["message"]
        conversation_history = body.get("conversationHistory", [])

        if EXTERNAL_MODEL_ENDPOINT:
            assistant_response = invoke_external_model(message)
        else:
            assistant_response = invoke_bedrock(message, conversation_history, context)

        messages = conversation_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": assistant_response},
        ]

        return build_response(
            200,
            {
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages,
            },
        )
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Invalid request: {error}")
        return build_response(400, {"success": False, "error": "Invalid request"})
    except Exception as error:
        print(f"Inference error: {error}")
        return build_response(500, {"success": False, "error": "Inference failed"})
