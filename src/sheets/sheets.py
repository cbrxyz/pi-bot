import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import asyncio
from datetime import datetime
from aioify import aioify
from dotenv import load_dotenv

SHEET_NAME = "Pi-Bot Administrative Sheet"

def get_creds():
    return ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json",
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

aios = aioify(obj=os, name='aios')

async def getWorksheet():
    """Returns the Pi-Bot Administrative Sheet, accessible to Pi-Bot administrators."""
    agc = await agcm.authorize()
    return await agc.open(SHEET_NAME)

async def buildServiceAccount():
    """Builds the service account used to access the administrative sheet."""
    load_dotenv()
    devMode = await aios.getenv('DEV_MODE') == "TRUE"
    if devMode:
        data = {
            "type": "service_account",
            "project_id": os.getenv('GCP_PROJECT_ID'),
            "private_key_id": os.getenv('GCP_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GCP_PRIVATE_KEY'),
            "client_email": os.getenv('GCP_CLIENT_EMAIL'),
            "client_id": os.getenv('GCP_CLIENT_ID'),
            "auth_uri": os.getenv('GCP_AUTH_URI'),
            "token_uri": os.getenv('GCP_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GCP_AUTH_PROVIDER_X509'),
            "client_x509_cert_url": os.getenv('GCP_CLIENT_X509_CERT_URL')
        }
    else:
        data = {
            "type": "service_account",
            "project_id": os.getenv('GCP_PROJECT_ID'),
            "private_key_id": os.getenv('GCP_PRIVATE_KEY_ID'),
            "private_key": f"{os.getenv('GCP_PRIVATE_KEY')}".encode().decode('unicode_escape'),
            "client_email": os.getenv('GCP_CLIENT_EMAIL'),
            "client_id": os.getenv('GCP_CLIENT_ID'),
            "auth_uri": os.getenv('GCP_AUTH_URI'),
            "token_uri": os.getenv('GCP_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GCP_AUTH_PROVIDER_X509'),
            "client_x509_cert_url": os.getenv('GCP_CLIENT_X509_CERT_URL')
        }
    with open("service_account.json",'w+') as f:
        json.dump(data, f)
    print("Service account built.")

async def sendVariables(dataArr, type):
    """Sends variable backups to the Administrative Sheet."""
    agc = await agcm.authorize()
    ss = await agc.open(SHEET_NAME)
    if type == "variable":
        varSheet = await ss.worksheet("Variable Backup")
        await varSheet.batch_update([{
            'range': "C3:C7",
            'values': dataArr
        }])
        print("Stored variables in Google Sheet.")
    elif type == "store":
        storedVarSheet = await ss.worksheet("Stored Variable Backup")
        await storedVarSheet.append_row([str(datetime.now())] + [v[0] for v in dataArr])
        print("Stored variables in the long-term area.")

async def getVariables():
    """Gets the previous variables, so that when Pi-Bot is restarted, the ping information is not lost."""
    agc = await agcm.authorize()
    ss = await agc.open(SHEET_NAME)
    varSheet = await ss.worksheet("Variable Backup")
    dataArr = await varSheet.batch_get(["C3:C7"])
    dataArr = dataArr[0]
    for row in dataArr:
        row[0] = json.loads(row[0])
    return dataArr

async def getStarted():
    await buildServiceAccount()
    agc = await agcm.authorize()
    ss = await agc.open("Pi-Bot Administrative Sheet")
    print("Initialized gspread.")

async def getRawCensor():
    ss = await getWorksheet()
    eventSheet = await ss.worksheet("Censor Management")
    words = await eventSheet.batch_get(["B3:C1000"])
    return words

async def updateWikiPage(title):
    ss = await getWorksheet()
    varSheet = await ss.worksheet("Variable Backup")
    await varSheet.update_acell('C8', title)

async def getWikiPage():
    ss = await getWorksheet()
    varSheet = await ss.worksheet("Variable Backup")
    res = await varSheet.batch_get(["C8"])
    return res[0][0][0]

event_loop = asyncio.get_event_loop()
asyncio.ensure_future(getStarted(), loop = event_loop)