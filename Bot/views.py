# Create your views here.
from django.shortcuts import render
 
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
import requests, json, time
 
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
                if event.message.type == 'text':
                    mtext=event.message.text
                    if mtext == '雷達回波圖':
                        message=ImageSendMessage(original_content_url='https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-001.png', preview_image_url='https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-001.png')
                    else:
                        message=TextSendMessage(text=mtext)
                        
                elif event.message.type == 'location':
                    message = TextSendMessage(text=get_weather(event.message.address))

                line_bot_api.reply_message(event.reply_token,message)
 
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

def get_weather(address):
    area_list= {}
    msg = "查無資料"
    def get_data():
        url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization=CWB-82D657F9-72A7-4A96-A0E1-88A7B340315E&downloadType=WEB&format=JSON'
        data = requests.get(url)
        data_json = data.json()
        location = data_json['cwbopendata']['location']
        for i in location:
            name = i['locationName']                                                      #測站
            area = i['parameter'][2]['parameterValue']                                    #行政區
            temp = i['weatherElement'][3]['elementValue']['value']                        #氣溫
            humd = round(float(i['weatherElement'][4]['elementValue']['value'] )*100 ,1)  #相對濕度
            r24 = i['weatherElement'][6]['elementValue']['value']                         #累積雨量
            if area not in area_list:
                area_list[area] = {'name':name, 'temp':temp, 'humd':humd, 'r24':r24} 

    def get_msg(msg):
        ret = msg
        for i in area_list:
            if i in address:  #檢查地址裡有否行政區的名子
                name = f"測站 : {area_list[i]['name']} " 
                temp = f"氣溫 : {area_list[i]['temp']} 度" 
                humd = f"相對濕度 : {area_list[i]['humd']}%" 
                r24 = f"累積雨量 : {area_list[i]['r24']}mm" 
                ret = f'{name}\n{temp}\n{humd}\n{r24}'
                break
        return ret
    
    try:
        get_data()
        msg = get_msg(msg)   
        msg = f'{address}\n{msg}'
        return msg
    except:
        return msg