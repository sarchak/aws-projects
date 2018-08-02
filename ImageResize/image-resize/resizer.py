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

def image_resize_worker(event, context):
    pprint(event)

    for record in event['Records']:
        payload = json.loads(record['Sns']['Message'])
        destination_bucket = payload["bucket"]
        object_key = payload["object_key"]
        channel_id = payload["channel_id"]
        image_url = payload["image_url"]
        token = payload["token"]
        size = payload["size"]

        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        print("Resizing the image to : {} from url : {}".format(size, image_url))
        s3 = boto3.resource('s3')
        r = requests.get(image_url, headers=headers)
        img = Image.open(BytesIO(r.content))
        obj = s3.Object(
                bucket_name=destination_bucket,
                key=object_key,
            )


        img = img.resize(size)
        buffer = BytesIO()
        img.save(buffer, 'JPEG')
        buffer.seek(0)
        obj.put(ACL='public-read', Body=buffer)
        post_to_slack(channel_id, token, destination_bucket, object_key)

        # Printing to CloudWatch
        print('File saved at {}/{}'.format(
            destination_bucket,
            object_key,
        ))