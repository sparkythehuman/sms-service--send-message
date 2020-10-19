import boto3
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime
from datetime import timedelta
from pytz import timezone
from twilio.rest import Client



def get_sms_items_from_db(date_range, status='queued'):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    response = table.query(
        KeyConditionExpression=Key('status').eq(status)& Key('send_at').between(date_range[0], date_range[1])
    )
    return response['Items']
    

def send_message(data):
    twilio = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    message = twilio.messages\
        .create(
            body=data['message'], 
            from_=data['from'],
            to=data['to']
        )
    
    return message.sid


def update_sms_item(id, twilio_sid, status='sent'): 
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    table.update_item(
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


def handle():
    # five minutes ago to now
    date_range = (
        (datetime.now(tz=timezone('America/Denver')) - timedelta(minutes=5)).isoformat(),
        datetime.now(tz=timezone('America/Denver')).isoformat()
    )
    for sms_data in get_sms_items_from_db(date_range):
        twilio_sid = send_message(sms_data)
        update_sms_item(sms_data['id'], twilio_sid)