#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Webotron helps automate deploying static sites to AWS 
"""

import boto3
import click 
from bucket import BucketManager

session = None
bucket_manager = None
@click.group()
@click.option('--profile', default=None, help="Provide user profile")
def cli(profile):
    "Webotron deploys websites to AWS"
    global session, bucket_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile        
    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)       

@cli.command('list-buckets')
def list_buckets():
    "List all s3 buckets"
    for bucket in bucket_manager.s3.buckets.all():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    "List files in a buckets"
    for file in bucket_manager.all_objects(bucket):
        print(file)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and configure s3 bucket"    
    s3_bucket = bucket_manager.init_bucket(bucket) 
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    "Sync contents of PATHNAME to BUCKET"    
    bucket_manager.sync(pathname, bucket)
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket)))

if __name__ == '__main__':
    cli()