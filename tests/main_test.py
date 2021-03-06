import json
import pytest
from src.main import handle
from datetime import datetime
from pytz import timezone
from types import SimpleNamespace
from unittest.mock import ANY


#TODO: fix the dates, just for good measure

@pytest.fixture()
def mock_table(mocker):
    mock_table = mocker.Mock()
    mock_table.query.return_value = {
        'Items' : [
            {
            'id': 'SMSXXXXXXXXXXXXXXXX',
            'status': 'queued',
            'from': '+15058675309',
            'to': '+12813308004',
            'send_at': '2020-01-01 12:30:00',
            'message': 'Join Earth\'s mightiest heroes, like Kevin Bacon.',
            'created_at': '2020-10-17T11:01:36.650877-06:00'
            },
        ],
        'Count': 123,
        'ScannedCount': 123
    } 
    yield mock_table


@pytest.fixture
def mock_dynamodb(mocker, mock_table):
    mock_dynamodb = mocker.Mock()
    mock_dynamodb.Table.return_value = mock_table
    yield mock_dynamodb



@pytest.fixture(autouse=True)
def mock_boto(mocker, mock_dynamodb):
    mock_boto = mocker.patch('src.main.boto3')
    mock_boto.resource.return_value = mock_dynamodb


@pytest.fixture
def mock_now():
    yield datetime.now(tz=timezone('America/Denver'))


@pytest.fixture(autouse=True)
def mock_datetime(mocker, mock_now):
    mock_datetime = mocker.patch('src.main.datetime')
    mock_datetime.now.return_value = mock_now


@pytest.fixture()
def mock_twilio_create_message_response(mocker):
    data = (
        '''
        {
            "account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "api_version": "2010-04-01",
            "body": "Join Earth's mightiest heroes. Like Kevin Bacon.",
            "date_created": "Thu, 30 Jul 2015 20:12:31 +0000",
            "date_sent": "Thu, 30 Jul 2015 20:12:33 +0000",
            "date_updated": "Thu, 30 Jul 2015 20:12:33 +0000",
            "direction": "outbound-api",
            "error_code": null,
            "error_message": null,
            "from": "+15017122661",
            "messaging_service_sid": "MGXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "num_media": "0",
            "num_segments": "1",
            "price": null,
            "price_unit": null,
            "sid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "status": "sent",
            "subresource_uris": {
                "media": "/2010-04-01/Accounts/ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Messages/SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Media.json"
            },
            "to": "+15558675310",
            "uri": "/2010-04-01/Accounts/ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/Messages/SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.json"
        }
        '''
    )
    # parse JSON into an object with attributes corresponding to dict keys
    yield json.loads(data, object_hook=lambda d: SimpleNamespace(**d))


@pytest.fixture()
def mock_create_message(mocker, mock_twilio_create_message_response):
    mock_create_message = mocker.patch('src.main.Client.messages')
    mock_create_message.create.return_value = mock_twilio_create_message_response
    yield mock_create_message



def test_handle(mocker, mock_dynamodb, mock_now, mock_create_message):
    handle()
  
    assert mock_create_message.mock_calls == [
        mocker.call.create(
            body="Join Earth's mightiest heroes, like Kevin Bacon.", 
            from_='+15058675309', 
            to='+12813308004'
        )
    ]

    assert mock_dynamodb.mock_calls == [
        mocker.call.Table('test-table'),
        mocker.call.Table().query(KeyConditionExpression=ANY),
        mocker.call.Table('test-table'),
        mocker.call.Table().update_item(
            Key={
                'id': 'SMSXXXXXXXXXXXXXXXX'
            },
            AttributeUpdates={
                'processed_at': {
                    'Value': mock_now.isoformat(),
                    'Action': 'PUT'
                },
                'status': {
                    'Value': 'sent',
                    'Action': 'PUT'
                },
                'twilio_sid': {
                    'Value': 'SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
                    'Action': 'PUT'
                }
            }
        ),
    ]