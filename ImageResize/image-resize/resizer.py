import json
import requests
from pprint import pprint
import os
import boto3
from urllib.parse import urlsplit, parse_qs
import PIL
from PIL import Image
from io import BytesIO
from slack_helper import post_to_slack

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


def image_resize_worker(event, context):
    pprint(event)

    for record in event['Records']:
        payload = json.loads(record['Sns']['Message'])
        destination_bucket = payload["bucket"]
        channel_id = payload["channel_id"]
        callback_id = payload["callback_id"]
        image_url = payload["image_url"]
        token = payload["token"]
        platform = payload["platform"]


        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }

        data = IMAGE_SIZES[platform]
        r = requests.get(image_url, headers=headers)
        downloaded_image = Image.open(BytesIO(r.content))
        for img_type, size in data.items():
            object_key = "{}/{}_{}.jpeg".format(callback_id, platform, img_type)

            print("Resizing the image to : {} from url : {}".format(size, image_url))
            s3 = boto3.resource('s3')

            obj = s3.Object(
                    bucket_name=destination_bucket,
                    key=object_key,
                )

            img = downloaded_image.resize(size, Image.ANTIALIAS)
            buffer = BytesIO()
            img.save(buffer, 'JPEG', quality=100)
            buffer.seek(0)
            obj.put(ACL='public-read', Body=buffer)
            post_to_slack(channel_id, token, destination_bucket, object_key)

            # Printing to CloudWatch
            print('File saved at {}/{}'.format(
                destination_bucket,
                object_key,
            ))