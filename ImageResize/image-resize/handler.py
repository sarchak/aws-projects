import json
import requests
from pprint import pprint
import os
import boto3
from urllib.parse import urlsplit, parse_qs
import PIL
from PIL import Image
from io import BytesIO

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
        'pin': (236,600),
        'board': (222,150)
    }
}

def resize(event, context):  
    pprint(event)
    payload = parse_qs(event['body'])    
    payload = payload['payload'][0]

    print("*****************")
    payload = json.loads(payload)
    if(payload['type'] == 'message_action'):
        open_dialog(payload)
    else:
        handle_submission(payload)  

    response = {
        "statusCode": 200,
        "body": ""
    }        
    return response

def resize_helper(payload):  
    s3 = boto3.resource('s3')
    destination_bucket = os.environ['APP_BUCKET']    
    if payload['submission']['image_platform'] == 'all':
        print("Wowwwww!")
    else:
        data = IMAGE_SIZES[payload['submission']['image_platform']]
        for img_type, size in data.items():
            object_key = "shrek_{}_{}.jpeg".format(payload['submission']['image_platform'], img_type)
            # Uploading the image
            obj = s3.Object(
                bucket_name=destination_bucket,
                key=object_key,
            )    

            r = requests.get('https://i.redd.it/lo1s5x1owyc11.jpg')
            img = Image.open(BytesIO(r.content))
            # img.thumbnail(size)
            print("Resizing the image to : {}".format(size))
            img = img.resize(size)
            buffer = BytesIO()
            img.save(buffer, 'JPEG')
            buffer.seek(0)            
            obj.put(ACL='public-read', Body=buffer)            
            post_to_slack(payload, destination_bucket, object_key)    

            # Printing to CloudWatch
            print('File saved at {}/{}'.format(
                destination_bucket,
                object_key,
            ))



def make_item(data):
    if isinstance(data, dict):
        return { k: make_item(v) for k, v in data.items() }

    if isinstance(data, list):
        return [ make_item(v) for v in data ]

    if isinstance(data, float):
        return str(data)

    return data

def send_message(payload, message):
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    app_table = dynamodb.Table(table_name)
    item = app_table.get_item(TableName=table_name, Key={'team_id':payload['team']['id']})
    token = item['Item']['access_token']
    pprint("Token : {}".format(token))

    # url = 'https://slack.com//api/chat.postMessage'     
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    # data =  {
    #     "text": message,
    #     "channel": payload['user']['id']
    # }
    # requests.post(url, headers=headers, json=data)

    data = {
          "text": "We will be sending the processed images soon...",
          "attachments": [
              {
                  "text":"Platform: {}".format(payload['submission']['image_platform'])
              }
          ],
          "response_type": "ephemeral"
      }
    print("Sending message:!!!!")
    r = requests.post(payload['response_url'], headers=headers, json=data)
    print(r.content)
    
def post_to_slack(payload, destination_bucket, object_key):    
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    app_table = dynamodb.Table(table_name)
    item = app_table.get_item(TableName=table_name, Key={'team_id':payload['team']['id']})
    token = item['Item']['access_token']
    pprint("Token : {}".format(token))

    url = 'https://slack.com//api/chat.postMessage'     
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    data =  {
        "text": "Thank you for using ImageResize.",
        "attachments": [
            {
                "fallback": "Required plain-text summary of the attachment.",
                "title": object_key,
                "title_link": "https://api.slack.com/",
                "text": "",
                "image_url": "https://s3.amazonaws.com/{}/{}".format(destination_bucket, object_key),
                "thumb_url": "https://s3.amazonaws.com/{}/{}".format(destination_bucket, object_key)
            }
        ],
        "channel": payload['user']['id']
    }
    requests.post(url, headers=headers, json=data)
    response = {
        "statusCode": 200,
        "body": "Submission successful"
    }        

    return response

def handle_submission(payload):
    print("***** Submission Accepted ******")
    pprint(payload)
    send_message(payload, "We will send the resized images soon..")
    resize_helper(payload)        

def open_dialog(payload):  
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    app_table = dynamodb.Table(table_name)
    item = app_table.get_item(TableName=table_name, Key={'team_id':payload['team']['id']})
    token = item['Item']['access_token']
    pprint("Token : {}".format(token))

    url = 'https://slack.com//api/dialog.open'     
    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json'
    }
    data =  {
        "callback_id": "ryde-46e2b0",
        "title": "Get Images Resized",
        "submit_label": "Request",
        "elements": [            
            {
                "label": "Select platforms",
                "type": "select",
                "name": "image_platform",
                "options": [
                    {
                    "label": "All",
                    "value": "all"
                    },
                    {
                    "label": "Facebook",
                    "value": "facebook"
                    },
                    {
                    "label": "Instagram",
                    "value": "instagram"
                    },
                    {
                    "label": "Twitter",
                    "value": "twitter"
                    },
                    {
                    "label": "Google+",
                    "value": "google"
                    },
                    {
                    "label": "Linkedin",
                    "value": "linkedin"
                    },
                    {
                    "label": "Pinterest",
                    "value": "pinterest"
                    }
                ]
            }
        ]
        }
    pdata = {
        "token": token,
        "trigger_id": payload['trigger_id'],
        "dialog": data
    }
    pprint(pdata)
    response = requests.post(url, headers=headers, json=pdata)
    print(response.content)


    
def write_to_db(data):
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ['DYNAMODB_TABLE_NAME']
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