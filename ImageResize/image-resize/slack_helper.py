import json
import requests
from pprint import pprint
import os
import boto3
from urllib.parse import urlsplit, parse_qs
import PIL
from PIL import Image
from io import BytesIO
import uuid
def send_ephemeral_message(token, post_url, message):
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    data = {
          "text": message,
          "response_type": "ephemeral"
      }
    r = requests.post(post_url, headers=headers, json=data)
    return r.content

def post_to_slack(channel_id, token, destination_bucket, object_key):
    url = 'https://slack.com//api/chat.postMessage'
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    data =  {
        "text": "Thank you for using ImageResize.",
        "attachments": [
            {
                "fallback": "Required plain-text summary of the attachment.",
                "title": object_key.split('/')[-1],
                "title_link": "https://api.slack.com/",
                "text": "",
                "image_url": "https://s3.amazonaws.com/{}/{}".format(destination_bucket, object_key),
                "thumb_url": "https://s3.amazonaws.com/{}/{}".format(destination_bucket, object_key)
            }
        ],
        "channel": channel_id
    }
    requests.post(url, headers=headers, json=data)
    response = {
        "statusCode": 200,
        "body": "Submission successful"
    }
    return response

def open_dialog(token, trigger_id, callback_id):
    url = 'https://slack.com//api/dialog.open'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json'
    }
    data =  {
        "callback_id": callback_id,
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
        "trigger_id": trigger_id,
        "dialog": data
    }

    response = requests.post(url, headers=headers, json=pdata)


