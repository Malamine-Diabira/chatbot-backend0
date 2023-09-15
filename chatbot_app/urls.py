from django.urls import path

from chatbot_app.views import create_account, login, send_message, clear_chat, get_history

urlpatterns = [
    path('create_account', create_account, name='create_account'),
    path('login', login, name='login'),
    path('send_message', send_message, name='send_message'),
    path('clear_chat', clear_chat, name='clear_chat'),
    path('get_history', get_history, name='get_history'),
]
