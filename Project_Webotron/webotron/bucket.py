# -*- coding: utf -*-
from botocore.exceptions import ClientError
import mimetypes
from pathlib import Path

""" Class for s3 buckets."""
class BucketManager: 
    """Manage an S3 Bucket."""
    def __init__(self, session):
        """Create a bucket Manager object"""
        self.s3 = session.resource('s3')

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

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
    def upload_file(bucket, path, key):
        """Upload path to s3 bucket at key."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        return bucket.upload_file(path, key, ExtraArgs={'ContentType': content_type})

    def sync(self, pathname, bucket_name):
        bucket = self.s3.Bucket(bucket_name)
        root = Path(pathname).expanduser().resolve()
        def handle_directory(target):
            for p in target.iterdir():
                if p.is_dir(): handle_directory(p)
                if p.is_file():
                    print("Path: {} \t Key: {}".format(p, p.relative_to(root)))
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)