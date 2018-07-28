# -*- coding: utf -*-
from pprint import pprint

class CertificateManager:
    def __init__(self, session):
        self.session = session
        self.client = session.client('acm')

    def cert_matches(self, cert_arn, domain_name):
        """Return True if cert matches domain_name."""
        cert_details = self.client.describe_certificate(
                CertificateArn=cert_arn
        )
        print(domain_name)
        alt_names = cert_details['Certificate']['SubjectAlternativeNames']
        print(alt_names)
        for name in alt_names:
            if name == domain_name:
                return True
            if name[0] == '*' and domain_name.endswith(name[1:]):
                return True
        return False

    def find_matching_certificate(self, domain_name):
        paginator = self.client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert in page['CertificateSummaryList']:              
                if self.cert_matches(cert['CertificateArn'], domain_name):
                    return cert
        return None
