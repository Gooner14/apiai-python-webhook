#!/usr/bin/env python

import urllib
import json
import os
import requests
import geocoder

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    #print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print ("started processing")
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    result = req.get("result")
    parameters = result.get("parameters")
    #import ipgetter
    #import requests

    #IP = ipgetter.myip()
    #url = 'http://freegeoip.net/json/'+IP
    #r = requests.get(url)
    #js = r.json()
    city = parameters.get("geo-city")
    day=parameters.get("dat")
    if len(city)<3:
        """newlink = "https://api.ipdata.co/city?api-key=1ad57590c9de8df36fae6f8693b934d2ca8d6228e6f5f5ab8e7cc6b7"
        newf = requests.get(newlink)
        city=newf.text"""
        """g = geocoder.ip('me')
        print(g.city)
        city=g.city"""
        send_url = "http://api.ipstack.com/check?access_key=e4bc9f0507a494f428e34e9bdad24e95&format=1curl%20freegeoip.net/json"
        geo_req = requests.get(send_url)
        geo_json = json.loads(geo_req.text)
        city = geo_json['city']
        print (city)
    #app.wsgi_app = ProxyFix(app.wsgi_app)    
    if len(day) <3:
        yql_query = makeYqlQuery2(req,city)
    else:    
        yql_query = makeYqlQuery1(req,city)
    print ("yql query created")
    if yql_query is None:
        print("yqlquery is empty")
        return {}
    yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
    print(yql_url)

    result = urllib.urlopen(yql_url).read()
    print("yql result: ")
    print(result)

    data = json.loads(result)
    if len(day) < 3:
        res = makeWebhookResult2(data,city)
    else:
        res = makeWebhookResult1(data,city)
    return res


def makeYqlQuery1(req,city):
    result = req.get("result")
    parameters = result.get("parameters")
    #city = parameters.get("geo-city")
    print("in makeyqlquery")
    print(city)
    day=parameters.get("dat")
    if city is None:
        return None    
    #return "select * from weather.forecast where (woeid in (select woeid from geo.places(1) where text='" + city + "') and item.forecast.day='" + day + "') limit 1"
    return "select units,location,title, lastBuildDate,description,ttl,link, wind, atmosphere, astronomy, image, item.link,item.lat,item.long,item.pubDate, item.forecast,item.language, item.title,item.condition,item.description,item.guid from weather.forecast where (woeid in (select woeid from geo.places(1) where text='" + city + "') and item.forecast.day='" + day + "') and u =' c' limit 1"


def makeYqlQuery2(req,city):
    result = req.get("result")
    parameters = result.get("parameters")
    #city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u= ' c'"

def makeWebhookResult1(data,city):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
        
    if condition is None:
        return {}

    forecast=item.get('forecast')   
    # print(json.dumps(item, indent=4))
    
    

    speech = "Weather in " + location.get('city') + " on "+ forecast.get('date')+ ": "+forecast.get('text')+", with a high of " + forecast.get('high') +" "+units.get('temperature')+ \
             " and a low of " + forecast.get('low') +" "+ units.get('temperature')

    print("Response:")
    print(speech)

    slack_message = {
        "text": speech,
        "attachments": [
            {
                "title": channel.get('title'),
                "title_link": channel.get('link'),
                "color": "#36a64f",

                "fields": [
                    {
                        "title": "Condition",
                        "value": "Temp " + condition.get('temp') +
                                 " " + units.get('temperature'),
                        "short": "false"
                    },
                    {
                        "title": "Wind",
                        "value": "Speed: " + channel.get('wind').get('speed') +
                                 ", direction: " + channel.get('wind').get('direction'),
                        "short": "true"
                    },
                    {
                        "title": "Atmosphere",
                        "value": "Humidity " + channel.get('atmosphere').get('humidity') +
                                 " pressure " + channel.get('atmosphere').get('pressure'),
                        "short": "true"
                    }
                ],

                "thumb_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif"
            }
        ]
    }

    facebook_message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": channel.get('title'),
                        "image_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif",
                        "subtitle": speech,
                        "buttons": [
                            {
                                "type": "web_url",
                                "url": channel.get('link'),
                                "title": "View Details"
                            }
                        ]
                    }
                ]
            }
        }
    }

    print(json.dumps(slack_message))

    return {
        "speech": speech,
        "displayText": speech,
        "data": {"slack": slack_message, "facebook": facebook_message},
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }

def makeWebhookResult2(data,city):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    lati=item.get('lat')
    longi=item.get('long')
    lati=str(lati)
    longi=str(longi)
    aqi_url="https://api.breezometer.com/baqi/?lat="+lati+"&lon="+longi+"&key=e89840e7891c4a81a95e10156c1d9dcf&fields=breezometer_aqi"
    aqi_req = requests.get(aqi_url)
    aqi_json = json.loads(aqi_req.text)
    aqi = aqi_json['breezometer_aqi']
    print("aqi is")
    print(aqi)
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}
    
    # print(json.dumps(item, indent=4))

    speech = "Today in " + location.get('city') + ": " + aqi_json.get('breezometer_aqi') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature') + " aqi is "

    print("Response:")
    print(speech)

    slack_message = {
        "text": speech,
        "attachments": [
            {
                "title": channel.get('title'),
                "title_link": channel.get('link'),
                "color": "#36a64f",

                "fields": [
                    {
                        "title": "Condition",
                        "value": "Temp " + condition.get('temp') +
                                 " " + units.get('temperature'),
                        "short": "false"
                    },
                    {
                        "title": "Wind",
                        "value": "Speed: " + channel.get('wind').get('speed') +
                                 ", direction: " + channel.get('wind').get('direction'),
                        "short": "true"
                    },
                    {
                        "title": "Atmosphere",
                        "value": "Humidity " + channel.get('atmosphere').get('humidity') +
                                 " pressure " + channel.get('atmosphere').get('pressure'),
                        "short": "true"
                    }
                ],

                "thumb_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif"
            }
        ]
    }

    facebook_message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": channel.get('title'),
                        "image_url": "http://l.yimg.com/a/i/us/we/52/" + condition.get('code') + ".gif",
                        "subtitle": speech,
                        "buttons": [
                            {
                                "type": "web_url",
                                "url": channel.get('link'),
                                "title": "View Details"
                            }
                        ]
                    }
                ]
            }
        }
    }

    print(json.dumps(slack_message))

    return {
        "speech": speech,
        "displayText": speech,
        "data": {"slack": slack_message, "facebook": facebook_message},
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print ("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
