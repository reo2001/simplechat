# lambda/index.py
import json
import urllib.request

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # API Gatewayから来たリクエストボディを読み取る
        body = json.loads(event["body"])
        user_message = body["message"]  # "message"をそのまま使う

        # FastAPIサーバーに送るリクエストペイロード
        payload = json.dumps({
            "prompt": user_message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://ea30-34-106-241-73.ngrok-free.app/predict",
            data=payload,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as res:
            response_body = res.read()
            result = json.loads(response_body)

        # FastAPI応答から generated_text を取り出す
        generated_text = result["generated_text"]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "candidates": [
                    {
                        "role": "assistant",
                        "content": generated_text
                    }
                ]
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "error": str(error)
            })
        }
