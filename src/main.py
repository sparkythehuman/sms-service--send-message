import boto3
import os
from datetime import datetime
from pytz import timezone
from twilio.rest import Client


def get_sms_items_from_db():
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table(os.environ['TABLE_NAME'])
  #TODO: get items in date range
    

def send_message(data):
  twilio = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
  message = twilio.messages.create(
                                body=data['message'],
                                from_=data['from'],
                                to=data['to']
                            )

  return message.sid


def update_sms_item(key, twilio_sid, status='sent'): 
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    table.update_item(
      Key={'id': key},
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
  for sms_data in get_sms_items_from_db():
    twilio_sid = send_message(sms_data)
    update_sms_item(sms_data['id'], twilio_sid)