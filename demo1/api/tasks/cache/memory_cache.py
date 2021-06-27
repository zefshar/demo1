import os
import json
import pickle
from googleapiclient.discovery_cache.base import Cache
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

GOOGLE_TOKEN_PICKLE = 'google_token.pickle'

def google_creds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(GOOGLE_TOKEN_PICKLE):
        with open(GOOGLE_TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # https://developers.google.com/sheets/api/quickstart/python
            google_client_config = json.loads('''
{"installed":{"client_id":"{google.com.client-id}","project_id":"cryptonic-23-1600411684532",
"auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token",
"auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"{google.com.client-secret}",
"redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}'''
                                                .replace('{google.com.client-id}', credentials.get('default', 'google.com.client-id'))
                                                .replace('{google.com.client-secret}', credentials.get('default', 'google.com.client-secret')))
            flow = InstalledAppFlow.from_client_config(google_client_config,
                                                        ['https://www.googleapis.com/auth/spreadsheets'])
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(GOOGLE_TOKEN_PICKLE, 'wb') as token:
                pickle.dump(creds, token)
    return creds