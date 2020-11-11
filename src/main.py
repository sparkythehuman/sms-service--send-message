import boto3
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime
from datetime import timedelta
from pytz import timezone
from twilio.rest import Client


dynamodb = boto3.resource('dynamodb')
message = dynamodb.Table('message')
contact = dynamodb.Table('contact')

def _get_queued_messages(date_range, status='queued'):
    response = message.query(
        IndexName='status-send_at-index',
        KeyConditionExpression=Key('status').eq(status) & Key('send_at').between(date_range[0], date_range[1])
    )
    return response['Items']


def _get_phone_numbers_from_contact_list(contact_list_id):
    response = contact.query(
        IndexName='contact_list_id-index',
        KeyConditionExpression=Key('contact_list_id').eq(contact_list_id)
    )
    
    return response['Items']
    

def _send_message(**kwargs):
    twilio = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    sms = twilio.messages\
        .create(
            body=kwargs['body'], 
            from_=os.environ['FROM_PHONE_NUMBER'],
            to=kwargs['to']
        )
    
    return sms.sid


def _update_sms_item(id, twilio_sid, status='sent'): 
    message.update_item(
      Key={'id': id},
      AttributeUpdates={
        'processed_at': {
            'Value': datetime.now(tz=timezone('America/Denver')).isoformat(),
            'Action': 'PUT'
        },
        'status': {
            'Value': status,
            'Action': 'PUT'
        },
        'twilio_sid': {
            'Value': twilio_sid,
            'Action': 'PUT'
        }
      }
    )


def handle(event, context):
    # five minutes ago to now
    date_range = (
        (datetime.now(tz=timezone('America/Denver')) - timedelta(minutes=5)).isoformat(),
        datetime.now(tz=timezone('America/Denver')).isoformat()
    )
    for queued_message in _get_queued_messages(date_range):
        for to_number in _get_phone_numbers_from_contact_list(queued_message['contact_list_id']):
            twilio_sid = _send_message(
                body=queued_message['message'], 
                to=to_number['phone_number']
            )
            _update_sms_item(queued_message['id'], twilio_sid)