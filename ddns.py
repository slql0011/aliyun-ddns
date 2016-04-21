#!/usr/bin/env python

ACCESS_KEY_ID = '<Your access key id>'
ACCESS_KEY_SECURE = '<Your access key secure>'

DOMAIN_NAME = 'shellc.cn'
DOMAIN_RECORD = ['*', '@']
RECORD_TYPE = 'A'
TTL = 600

# You do not need to change this below

import sys
import json

from dns.resolver import Resolver, Answer
from aliyunsdkcore.profile import region_provider
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import RpcRequest

def get_ip():
    '''
    Query specified domain myip.opends.com from resolver1.opendns.com & 
    resolver2.opendns.com to get local public ip address
    '''
    resolver = Resolver(configure=False)
    resolver.nameservers = ['208.67.222.222', '208.67.220.220']
    answers = resolver.query('myip.opendns.com', 'A')
    for rdata in answers:
        return str(rdata)

PROD = 'DNS'
VERSION = '2015-01-09'
REGION_ID = 'cn-beijing'
IP = None

region_provider.modify_point('DNS', REGION_ID, 'dns.aliyuncs.com')
domain = region_provider.find_product_domain(REGION_ID, 'DNS')
client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECURE, REGION_ID)

def get_all_record():
    req = RpcRequest(PROD, VERSION, 'DescribeDomainRecords', 'JSON')
    req.add_query_param('DomainName', DOMAIN_NAME)
    resp = json.loads(client.do_action(req))
    return resp

def get_record(resp, domain_record):
    record_id = None
    record_value = None
    for record in resp['DomainRecords']['Record']:
        if record['RR'] == domain_record:
            record_id = record['RecordId']
            if record['Type'] != RECORD_TYPE:
                raise Exception('The record is already exsits and the type not same.')
            record_value = record['Value']
    return record_id, record_value

def add_record(domain_record, record_value):
    req = RpcRequest(PROD, VERSION, 'AddDomainRecord', 'JSON')
    req.add_query_param('DomainName', DOMAIN_NAME)
    req.add_query_param('RR', domain_record)
    req.add_query_param('Type', RECORD_TYPE)
    req.add_query_param('Value', record_value)
    req.add_query_param('TTL', TTL)

    resp = json.loads(client.do_action(req))
    return resp['RecordId']

def update_record(record_id, domain_record, record_value):
    req = RpcRequest(PROD, VERSION, 'UpdateDomainRecord', 'JSON')
    req.add_query_param('RecordId', record_id)
    req.add_query_param('RR', domain_record)
    req.add_query_param('Type', RECORD_TYPE)
    req.add_query_param('Value', record_value)
    req.add_query_param('TTL', TTL)

    resp = json.loads(client.do_action(req))
    return resp['RecordId']

def process_record(record_id, domain_record, record_value):
    if record_id is None:
        print('The record does not exits, this script will add it first.')
    else:
        print('RecordId: %s, Value: %s'%(record_id, record_value))
        
    changed = True
    if not record_id: # Create a new record 
        add_record(domain_record, IP)
    elif record_value != ip: # Update a new value to the record
        print('Update...')
        update_record(record_id, domain_record, IP)
    else:
        changed = False
   
    # Query the result
    if changed:
        resp = get_all_record()
        record_id, record_value = get_record(resp, domain_record)
        if record_id is None:
            print('FAILED: The record does not exits.')
            return
        
    print('Status: RecordId=%s, Value=%s'%(record_id, record_value))

if __name__ == '__main__':

    print('Begin get all record.')
    resp = get_all_record()
    if resp is None:
        print('Got nothing.')
        sys.exit(1)

    # Get IP address
    IP = get_ip()
    print('The public IP detected is %s.'%ip)
    
    for domain_record in DOMAIN_RECORD:
        record_id, record_value = get_record(resp, domain_record)
        process_record(record_id, domain_record, record_value)
        

