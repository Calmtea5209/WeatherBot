# Create your views here.
from django.shortcuts import render
 
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
import requests, json, time, statistics

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
                    if '雷達' in mtext:
                        message=ImageSendMessage(original_content_url='https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-001.png', preview_image_url='https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-001.png')
                        line_bot_api.reply_message(event.reply_token,message)
                    else:
                        message=TextSendMessage(text=mtext)
                        line_bot_api.reply_message(event.reply_token,message)
                        
                elif event.message.type == 'location':
                    message = TextSendMessage(text=event.message.address + '\n\n' + get_weather(event.message.address) + '\n' + get__AQI(event.message.address))
                    try:
                        url = 'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0038-001?Authorization=CWB-82D657F9-72A7-4A96-A0E1-88A7B340315E&downloadType=WEB&format=JSON'
                        data = requests.get(url)
                        data_json = data.json()
                        weather_map_url = data_json['cwbopendata']['dataset']['resource']['uri']
                        weather_map = ImageSendMessage(original_content_url=weather_map_url, preview_image_url=weather_map_url)
                        line_bot_api.reply_message(event.reply_token,[message,weather_map])
                    except:
                        line_bot_api.reply_message(event.reply_token,message)

 
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

def get_weather(address):
    area_list= {}
    msg = "查無天氣資料"
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
                temp = f"氣溫 : {area_list[i]['temp']} 度" 
                humd = f"相對濕度 : {area_list[i]['humd']}%" 
                r24 = f"累積雨量 : {area_list[i]['r24']}mm" 
                ret = f'{temp}\n{humd}\n{r24}'
                break
        return ret
    
    try:
        get_data()
        msg = get_msg(msg)   
        return msg
    except:
        return msg

def get__AQI(address):
    city_list, site_list = {}, {}
    msg = "查無空氣品質資料"
    def get_data():
        url = 'https://data.epa.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=ImportDate%20desc&format=JSON'
        data = requests.get(url)
        data_json = data.json()
        for i in data_json['records']:
            city = i['county']
            if city not in city_list:
                city_list[city] = []
            site = i['sitename']
            aqi = i['aqi']
            status = i['status']
            site_list[site] = {'aqi':aqi, 'status':status}
            city_list[city].append(aqi)
        print("T")
    
    try:
        get_data()
        for i in city_list:
            if i in address:
                aqi_avg = 0.0
                for k in city_list[i]:
                    aqi_avg += int(k)
                aqi_avg = round(aqi_avg,0)
                
                aqi_status = ''
                if aqi_avg<=50: aqi_status = "良好"
                elif aqi_avg>50 and aqi_avg<=100: aqi_status = "普通"
                elif aqi_avg>100 and aqi_avg<=150: aqi_status = "對敏感族群不健康"
                elif aqi_avg>150 and aqi_avg<=200: aqi_status = "對所有族群不健康"
                elif aqi_avg>200 and aqi_avg<=300: aqi_status = "非常不健康"
                else: aqi_status = "危害"
                msg = f'空氣品質{aqi_status} (AQI {aqi_avg})'
                break
        for i in site_list:
            if i in address:
                msg = f"空氣品質{site_list[i]['status']} (AQI {site_list[i]['aqi']})"
                break

        return msg
    except:
        return msg
