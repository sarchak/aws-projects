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
import uuid

IMAGE_SIZES = {
    'facebook': {
        'profile': (180,180),
        'cover': (851,310),
        'fanpage': (851,312) ,
        'group': (820,428),
        'event': (500,262),
        'posts': (1200,630)
    },
    'instagram': {
        'profile': (150,150),
        'share_square': (1080,1080),
        'share_vertical': (1080,1350),
        'share_horizontal': (1080,566)
    },
    'twitter': {
        'profile': (200,200),
        'cover': (1500,1500),
        'share': (1024,512)
    },
    'google+': {
        'profile': (250,250),
        'cover': (968,545),
        'share': (502,282)
    },
    'linkedin': {
        'profile': (400,400),
        'cover': (1584,396),
        'posts': (520,320)
    },
    'pinterest': {
        'profile': (165,165),
        'pin': (236,450),
        'board': (222,150)
    }
}

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
        write_to_db({"callback_id": callback_id, "image_url": image_url}, table_name='CACHE_TABLE_NAME')
        open_dialog(token, trigger_id, callback_id)
        print("*** Image url : {}".format(image_url))
    else:
        platform = payload['submission']['image_platform']
        table_name = os.environ['CACHE_TABLE_NAME']
        item = app_table.get_item(TableName=table_name, Key={'callback_id':payload['callback_id']})
        image_url = item['Item']['image_url']
        print("*** Post submission Image url : {}".format(image_url))
        handle_submission(token, response_url, platform, channel_id, image_url)

    response = {
        "statusCode": 200,
        "body": ""
    }
    return response

def handle_submission(token, post_url, platform, channel_id, image_url):
    print("***** Submission Accepted ******")
    send_ephemeral_message(token, post_url, "We will send the resized images soon..")
    resize_helper(platform, channel_id, token, image_url)


def resize_helper(platform, channel_id, token, image_url):
    sns = boto3.resource('sns')
    destination_bucket = os.environ['APP_BUCKET']
    if platform == 'all':
        print("Wowwwww!")
    else:
        data = IMAGE_SIZES[platform]
        for img_type, size in data.items():
            object_key = "shrek_{}_{}.jpeg".format(platform, img_type)
            sns = boto3.client('sns')
            params = {
                "bucket": destination_bucket,
                "object_key": object_key,
                "platform": platform,
                "channel_id": channel_id,
                "size": size,
                "token": token,
                "image_url": image_url
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
    code = event['queryStringParameters']['code'];
    clientId = os.environ['SLACK_CLIENT_ID']
    clientSecret = os.environ['SLACK_CLIENT_SECRET']

    oauthURL = 'https://slack.com/api/oauth.access?' + 'client_id='+clientId + '&' + 'client_secret='+clientSecret + '&' + 'code='+code;

    #Authorize Slack
    data = requests.post(oauthURL)
    response = {
        "statusCode": 200,
        "body": "Successfully Authorized!"
    }

    #Store team id and token
    data = make_item(data.json())
    write_to_db(data)

    return response