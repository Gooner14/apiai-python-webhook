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
    if req.get("result").get("action") != "PollForecast":
        return {}
    #baseurl = "https://query.yahooapis.com/v1/public/yql?"
    result = req.get("result")
    parameters = result.get("parameters")
    #import ipgetter
    #import requests

    #IP = ipgetter.myip()
    #url = 'http://freegeoip.net/json/'+IP
    #r = requests.get(url)
    #js = r.json()
    city = parameters.get("geo-city")
    #day=parameters.get("dat")
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
    lati=geo_json['latitude']
    longi=geo_json['longitude']
    print(lati)
    print(longi)
    print (city)
    #app.wsgi_app = ProxyFix(app.wsgi_app)       
    lati=str(lati)
    longi=str(longi)
    aqi_url="https://api.breezometer.com/baqi/?lat="+lati+"&lon="+longi+"&key=e89840e7891c4a81a95e10156c1d9dcf"+"&format=json"
    print(aqi_url)
    result = urllib.urlopen(aqi_url).read()
    aqi_req = requests.get(aqi_url)
    print("aqi result: ")
    print(result)

    data = json.loads(result)
    res = makeWebhookResult2(data)
    #res = makeWebhookResult1(data,city)
    return res
    

def makeWebhookResult2(data):
    # aqi=data.get('breezometer_aqi')
    print(json.dumps(item, indent=4))

    recommendations=data.get('random_recommendations')
    dom=data.get('dominant_pollutant_canonical_name')

    speech = data.get('dominant_pollutant_text')+" with Air quality index of "
    



    print("Response:")
    print(speech)
    
    slack_message = {
        "text": speech,
    }



    print(json.dumps(slack_message))

    return {
        "speech": speech,
        "displayText": speech,
        "data": {"slack": slack_message},
        # "contextOut": [],
        "source": "apiai-pollution"
    }
    
    
  

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print ("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
