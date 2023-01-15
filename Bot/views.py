# Create your views here.
from django.shortcuts import render
 
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
 
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
 
@csrf_exempt #callback()=csrf_exempt(callback()) #防止跨站請求偽造的事情發生
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
 
        try:
            events = parser.parse(body, signature) #處理line傳過來的訊息(json格式)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
 
        for event in events:
            if isinstance(event, MessageEvent):
                mtext=event.message.text
                message=TextSendMessage(text=mtext) #設定回傳的文字
                line_bot_api.reply_message(event.reply_token,message)
 
        return HttpResponse()
    else:
        return HttpResponseBadRequest()
