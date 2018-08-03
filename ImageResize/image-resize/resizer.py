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
import zipfile

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


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            print("Zip : {}, {}".format(root, file))
            ziph.write(os.path.join(root, file), arcname=file)


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

        tmp_dir = "/tmp/{}".format(callback_id)
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)

        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }

        r = requests.get(image_url, headers=headers)
        downloaded_image = Image.open(BytesIO(r.content))
        s3 = boto3.resource('s3')
        platforms = [platform]
        if platform == "all":
            platforms = IMAGE_SIZES.keys()

        for platform in platforms:
            data = IMAGE_SIZES[platform]
            for img_type, size in data.items():
                filepath = "{}/{}_{}.jpeg".format(tmp_dir, platform, img_type)
                img = downloaded_image.resize(size, Image.ANTIALIAS)
                img.save(filepath, 'JPEG', quality=100)
                print(os.listdir(tmp_dir))

        zipfile_name = '{}.zip'.format(callback_id)
        zippath = '{}/{}'.format('/tmp', zipfile_name)
        zipf = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)
        zipdir(tmp_dir, zipf)
        zipf.close()
        obj = s3.Object(
                    bucket_name=destination_bucket,
                    key=zipfile_name,
                )

        obj.put(ACL='public-read', Body=open(zippath, 'rb'))
        post_to_slack(channel_id, token, destination_bucket, zipfile_name)
        print('Zip file uploaded')