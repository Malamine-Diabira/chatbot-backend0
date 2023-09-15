from rest_framework import serializers


class CreateAccount(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class SendMessage(serializers.Serializer):
    token = serializers.CharField()
    message = serializers.CharField()


class ClearChat(serializers.Serializer):
    token = serializers.CharField()
