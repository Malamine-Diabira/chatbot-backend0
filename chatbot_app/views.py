import json
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response

from chatbot_app.serializers import CreateAccount, SendMessage, ClearChat

from pyairtable import Table
from pyairtable.formulas import match

from hashlib import md5

import uuid

import openai

from env import AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, OPENAI_API_KEY


@api_view(['POST'])
def create_account(request):
    try:
        serializer = CreateAccount(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        hash_password = md5(password.encode()).digest()

        token = str(uuid.uuid4())

        user = create_account_db(
            email,
            str(hash_password),
            token
        )

        if user:
            return Response(
                {
                    'code': 100,
                    'message': 'User created successfully',
                    'token': token
                }
            )

        else:
            return Response(
                {
                    'code': 101,
                    'message': 'User already exists',
                }
            )

    except Exception as e:
        return Response(
            {
                'error': str(e),
                'code': 102,
                'message': 'An error occurred'
            }
        )


@api_view(['POST'])
def login(request):
    try:
        serializer = CreateAccount(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        hash_password = md5(password.encode()).digest()

        user = get_account_db(
            email,
        )

        if user:
            if f'{hash_password}' == user['fields']['HashPassword']:
                return Response(
                    {
                        'code': 100,
                        'message': 'User logged successfully',
                        'token': user['fields']['Token'],
                    }
                )

            else:
                return Response(
                    {
                        'code': 101,
                        'message': 'Invalid password'
                    }
                )

        else:
            return Response(
                {
                    'code': 102,
                    'message': 'Can not find user'
                }
            )

    except Exception as e:
        return Response(
            {
                'error': str(e),
                'code': 103
            }
        )


@api_view(['POST'])
def clear_chat(request):
    try:
        serializer = ClearChat(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        source = Table(
            AIRTABLE_TOKEN,
            AIRTABLE_BASE_ID,
            AIRTABLE_TABLE_NAME
        )

        user = source.first(
            formula=match(
                {
                    'Token': token
                }
            )
        )

        _id = user['id']

        source.update(
            _id,
            {
                'Messages': str([])
            }
        )

        return Response(
            {
                'code': 100,
                'message': 'Chat cleared'
            }
        )

    except Exception as e:
        return Response(
            {
                'code': 101,
                'error': str(e)
            }
        )


@api_view(['GET'])
def get_history(request):
    try:
        serializer = ClearChat(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        source = Table(
            AIRTABLE_TOKEN,
            AIRTABLE_BASE_ID,
            AIRTABLE_TABLE_NAME
        )

        user = source.first(
            formula=match(
                {
                    'Token': token
                }
            )
        )

        return Response(
            {
                'code': 100,
                'history': json.loads(user['fields']['Messages'])
            }
        )

    except Exception as e:
        return Response(
            {
                'code': 101,
                'error': str(e)
            }
        )


@api_view(['POST'])
def send_message(request):
    try:
        serializer = SendMessage(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        message = serializer.validated_data['message']

        answer = ask_gpt(token, message)

        save_message_db(
            message,
            answer,
            token
        )

        return Response(
            {
                'answer': answer,
                'code': 100
            }
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {
                'message': 'An error occurred',
                'code': 101,
                'error': str(e)
            }
        )


def create_account_db(email, hash_password, token):
    source = Table(
        AIRTABLE_TOKEN,
        AIRTABLE_BASE_ID,
        AIRTABLE_TABLE_NAME
    )

    user = source.first(
        formula=match(
            {
                'Email': email
            }
        )
    )

    if not user:
        source.create(
            {
                'Email': email,
                'HashPassword': hash_password,
                'Token': token,
                'Messages': str([])
            }
        )
        return True

    else:
        return False


def get_account_db(email,):
    source = Table(
        AIRTABLE_TOKEN,
        AIRTABLE_BASE_ID,
        AIRTABLE_TABLE_NAME
    )

    try:
        user = source.first(
            formula=match(
                {
                    'Email': email,
                }
            )
        )

        return user

    except:
        return None


def ask_gpt(token, message):
    source = Table(
        AIRTABLE_TOKEN,
        AIRTABLE_BASE_ID,
        AIRTABLE_TABLE_NAME
    )

    messages = source.first(
        formula=match(
            {
                'Token': token
            }
        )
    )['fields']['Messages']

    messages = json.loads(messages)

    if len(messages) < 8:
        history = messages

    else:
        history = messages[-8:]

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]

    for i in history:
        messages.append(i)

    messages.append(
        {"role": "user", "content": f"{message}"}
    )

    openai.api_key = OPENAI_API_KEY

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages
    )

    return completion.choices[0].message.content


def save_message_db(message, answer, token):
    source = Table(
        AIRTABLE_TOKEN,
        AIRTABLE_BASE_ID,
        AIRTABLE_TABLE_NAME
    )

    user = source.first(
        formula=match(
            {
                'Token': token
            }
        )
    )

    _id = user['id']
    messages = user['fields']['Messages']

    messages = json.loads(messages)

    messages.append(
        {"role": "user", "content": message}
    )

    messages.append(
        {"role": "assistant", "content": answer}
    )

    source.update(
        _id,
        {
            "Messages": json.dumps(messages)
        }
    )

