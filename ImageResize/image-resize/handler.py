import json
import requests
from pprint import pprint
import os
import boto3
from urllib.parse import urlsplit, parse_qs
import PIL
from PIL import Image
from io import BytesIO
from slack_helper import open_dialog, send_ephemeral_message
from resizer import slash_resize
import uuid

def slash(event, context):
    payload = parse_qs(event['body'])
    response_url = payload['response_url'][0]
    team_id = payload['team_id'][0]
    text = payload['text'][0]
    text = text.replace(' ', ',')
    values = text.split(',')
    image_url = values[-1]
    size = [int(x) for x in values[:-1] if len(x) > 0]
    print("Size: ", size)
    print("Image url : ", image_url)
    if (''.join(values[:-1])) == 'help' or image_url == "help":
        help(response_url)
    else:
        slash_resize(size, image_url, response_url, team_id)
    response = {
        "statusCode": 200,
        "body": ""
    }
    return response


def resize(event, context):
    payload = parse_qs(event['body'])
    payload = payload['payload'][0]
    payload = json.loads(payload)

    print(json.dumps(payload, indent=4, sort_keys=True))
    image_url = None

    if "message" in payload:
        print("Payload : {}".format(payload["message"]["files"][0]["url_private"]))
        print("Keys: ", payload["message"]["files"][0].keys())
        image_url = payload["message"]["files"][0]["url_private"]

    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    app_table = dynamodb.Table(table_name)
    item = app_table.get_item(TableName=table_name, Key={'team_id':payload['team']['id']})
    token = item['Item']['access_token']
    response_url = payload['response_url']
    platform = None
    channel_id = payload['user']['id']

    if(payload['type'] == 'message_action'):
        trigger_id = payload['trigger_id']
        callback_id = str(uuid.uuid4())
        write_to_db({"callback_id": callback_id, "image_url": image_url, "team_id":payload['team']['id'], "channel_id": channel_id}, table_name='CACHE_TABLE_NAME')
        open_dialog(token, trigger_id, callback_id)
        print("*** Image url : {}".format(image_url))
    else:
        platform = payload['submission']['image_platform']
        table_name = os.environ['CACHE_TABLE_NAME']
        item = app_table.get_item(TableName=table_name, Key={'callback_id':payload['callback_id']})
        image_url = item['Item']['image_url']
        print("*** Post submission Image url : {}".format(image_url))
        handle_submission(token, response_url, platform, channel_id, image_url, payload['callback_id'], payload['team']['id'])

    response = {
        "statusCode": 200,
        "body": ""
    }
    return response

def helpapi(event, context):
    payload = parse_qs(event['body'])
    response_url = payload['response_url'][0]
    help(response_url)
    response = {
        "statusCode": 200,
        "body": ""
    }
    return response

def help(response_url):
    data = {
        "attachments": [
            {
                "color": "#36a64f",
                "pretext": "How to use menu based triggers?",
                "text": "You can trigger this action for any message which contains an image",
                "image_url": "https://imageresize.xyz/images/feature.png",
                "thumb_url": "https://imageresize.xyz/images/feature.png"
            },
            {
                "color": "#36a64f",
                "pretext": "How to use slash commands?",
                "text": "/image-resize width height image_url"
            }


        ]
    }
    requests.post(response_url, json=data)

def handle_submission(token, post_url, platform, channel_id, image_url, callback_id, team_id):
    print("***** Submission Accepted ******")
    send_ephemeral_message(token, post_url, "We will send the resized images soon..")
    resize_helper(platform, channel_id, token, image_url, callback_id, team_id)


def resize_helper(platform, channel_id, token, image_url, callback_id, team_id):
    sns = boto3.client('sns')
    destination_bucket = os.environ['APP_BUCKET']

    params = {
        "bucket": destination_bucket,
        "platform": platform,
        "channel_id": channel_id,
        "token": token,
        "image_url": image_url,
        "callback_id": callback_id,
        "team_id": team_id
    }
    topic_arn = os.environ['SNS_TOPIC_ARN']
    sns.publish(TopicArn= topic_arn, Message= json.dumps(params))

def make_item(data):
    if isinstance(data, dict):
        return { k: make_item(v) for k, v in data.items() }

    if isinstance(data, list):
        return [ make_item(v) for v in data ]

    if isinstance(data, float):
        return str(data)

    return data


def write_to_db(data, table_name='DYNAMODB_TABLE_NAME'):
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ[table_name]
    app_table = dynamodb.Table(table_name)
    app_table.put_item(Item=data)


def authorization(event, context):

    if 'error' in event['queryStringParameters'] and event['queryStringParameters']['error'] == 'access_denied':
        response = {
            "statusCode": 301,
            "body": "",
            "headers": {
                "Location": "https://imageresize.xyz/denied.html"
            },
        }
        return response

    else:
        code = event['queryStringParameters']['code'];
        clientId = os.environ['SLACK_CLIENT_ID']
        clientSecret = os.environ['SLACK_CLIENT_SECRET']

        oauthURL = 'https://slack.com/api/oauth.access?'+'client_id='+clientId + '&' + 'client_secret='+clientSecret + '&' + 'code='+code;

        #Authorize Slack
        data = requests.post(oauthURL)
        #Store team id and token
        data = make_item(data.json())
        write_to_db(data)
        response = {
            "statusCode": 301,
            "body": "",
            "headers": {
                "Location": "https://imageresize.xyz/thankyou.html"
            },
        }
        return response
