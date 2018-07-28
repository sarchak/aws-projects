#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Webotron helps automate deploying static sites to AWS 
"""

import boto3
import click 
from bucket import BucketManager
from domain import DomainManager
from certificate import CertificateManager
from cdn import DistributionManager

import util
session = None
bucket_manager = None
domain_manager = None
cert_manager = None
dist_manager = None

@click.group()
@click.option('--profile', default=None, help="Provide user profile")
def cli(profile):
    "Webotron deploys websites to AWS"
    global session, bucket_manager, domain_manager, cert_manager, dist_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile        
    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)       
    domain_manager = DomainManager(session)
    cert_manager = CertificateManager(session)
    dist_manager = DistributionManager(session)

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

@cli.command('setup-domain')
@click.argument('domain')
def setup_domain(domain):
    """Setup domain using a given bucket"""
    bucket = bucket_manager.get_bucket(domain)
    zone = domain_manager.find_hosted_zones(domain) or \
           domain_manager.create_hosted_zone(domain)

    endpoint = util.get_endpoint(bucket_manager.get_region_name(bucket))
    a_record = domain_manager.create_s3_domain_record(zone, domain, endpoint)
    print("Domain Configured: http://{}".format(domain))

@cli.command('find-cert')
@click.argument('domain')
def find_cert(domain):
    return cert_manager.find_matching_certificate(domain)

@cli.command('setup-cdn')
@click.argument('domain')
@click.argument('bucket')
def setup_cdn(domain, bucket):
    """Set up CloudFront CDN for DOMAIN pointing to BUCKET."""
    dist = dist_manager.find_matching_dist(domain)

    if not dist:
        cert = cert_manager.find_matching_certificate(domain)
        if not cert:  # SSL is not optional at this time
            print("Error: No matching cert found.")
            return

        dist = dist_manager.create_dist(domain, cert)
        print("Waiting for distribution deployment...")
        dist_manager.await_deploy(dist)

    zone = domain_manager.find_hosted_zones(domain) \
        or domain_manager.create_hosted_zone(domain)

    domain_manager.create_cf_domain_record(zone, domain, dist['DomainName'])
    print("Domain configured: https://{}".format(domain))

    return

if __name__ == '__main__':
    cli()