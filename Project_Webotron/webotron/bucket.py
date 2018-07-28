# -*- coding: utf -*-
from botocore.exceptions import ClientError
import mimetypes
from pathlib import Path
import util
from hashlib import md5
from functools import reduce
import boto3

""" Class for s3 buckets."""
class BucketManager: 
    """Manage an S3 Bucket."""
    CHUNK_SIZE = 8388608
    def __init__(self, session):
        """Create a bucket Manager object"""
        self.s3 = session.resource('s3')
        self.manifest = {}
        self.transfer_config =  boto3.s3.transfer.TransferConfig(
            multipart_chunksize = self.CHUNK_SIZE,
            multipart_threshold = self.CHUNK_SIZE
        )

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def get_region_name(self, bucket):
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)
        return bucket_location["LocationConstraint"] or 'us-east-1'

    def get_bucket_url(self, bucket):
        return "http://{}.{}".format(bucket.name, util.get_endpoint(self.get_region_name(bucket)).host)
         
    def all_objects(self, bucket):
        """Get an iterator for all files"""
        return self.s3.Bucket(bucket).objects.all()

    def init_bucket(self, bucket_name):
        bucket = None
        try:
            bucket = self.s3.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print("You own the bucket!!!")
            else:
                raise(e)
        return bucket

    def get_bucket(self, bucket_name):
        return self.s3.Bucket(bucket_name)
        
    def set_policy(self, bucket):
        policy = """
        {
            "Version":"2012-10-17",
            "Statement":[{
                "Sid":"PublicReadGetObject",
                    "Effect":"Allow",
                "Principal": "*",
                "Action":["s3:GetObject"],
                "Resource":["arn:aws:s3:::%s/*"]               
            }]
        }
        """ % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)
    

    def configure_website(self, bucket):
        ws = bucket.Website()
        ws.put(WebsiteConfiguration = {
            'ErrorDocument': { 'Key': 'error.html'},
            'IndexDocument': { 'Suffix': 'index.html'}
        })

    @staticmethod
    def hash_data(data):
        hash = md5()
        hash.update(data)
        return hash

    def gen_etag(self, path):
        hashes = []
        with open(path, 'rb') as f:
            while(True):
                data = f.read(self.CHUNK_SIZE)
                if not data:
                    break
                hashes.append(self.hash_data(data))
            if not hashes:
                return
            elif len(hashes) == 1:
                return '"{}"'.format(hashes[-1].hexdigest())
            else:
                hash = self.hash_data(reduce(lambda x, y: x+y, (h.digest() for h in hashes)))
                return '"{}-{}"'.format(hash.hexdigest(), len(hashes))

    def load_manifest(self, bucket):
         paginator = self.s3.meta.client.get_paginator('list_objects_v2')
         for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag'] 


    def upload_file(self, bucket, path, key):
        """Upload path to s3 bucket at key."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.gen_etag(path)
        if self.manifest.get(key, '') == etag:
            print("Skipping {}, etags match".format(key))
            return

        return bucket.upload_file(path, key, ExtraArgs={'ContentType': content_type}, Config=self.transfer_config)

    def sync(self, pathname, bucket_name):
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)
        root = Path(pathname).expanduser().resolve()
        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir(): handle_directory(p)
                if p.is_file():
                    print("Path: {} \t Key: {}".format(p, p.relative_to(root)))
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)