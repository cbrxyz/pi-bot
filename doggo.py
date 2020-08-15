import requests
import json

async def getDoggo():
    """Gets a random dog pic!"""
    res = requests.get("https://dog.ceo/api/breeds/image/random")
    res = res.content.decode("UTF-8")
    jso = json.loads(res)
    return jso['message']

async def getShiba():
    """Gets a random shiba pic!"""
    res = requests.get("https://dog.ceo/api/breed/shiba/images/random")
    res = res.content.decode("UTF-8")
    jso = json.loads(res)
    return jso['message']