import gspread
import json
import os
from dotenv import load_dotenv

def getWorksheet():
    """Returns the Pi-Bot Administrative Sheet, accessible to Pi-Bot administrators."""
    return discordSheet

def buildServiceAccount():
    """Builds the service account used to access the administrative sheet."""
    load_dotenv()
    devMode = os.getenv('DEV_MODE') == "TRUE"
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

async def sendVariables(dataArr):
    """Sends variable backups to the Administrative Sheet."""
    sheet = getWorksheet()
    varSheet = sheet.worksheet("Variable Backup")
    varSheet.update("C3:C7", dataArr)
    print("Stored variables in Google Sheet.")

async def getVariables():
    """Gets the previous variables, so that when Pi-Bot is restarted, the ping information is not lost."""
    sheet = getWorksheet()
    varSheet = sheet.worksheet("Variable Backup")
    dataArr = varSheet.get("C3:C7")
    for row in dataArr:
        row[0] = json.loads(row[0])
    return dataArr

buildServiceAccount()
gc = gspread.service_account(filename="service_account.json")
discordSheet = gc.open("Pi-Bot Administrative Sheet")
print("Initialized gspread.")