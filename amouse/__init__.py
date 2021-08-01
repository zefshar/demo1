# aiohttp module for authentication on some servers
# 1. Google API:
# AuthMouse(client_id='', client_secret='', scope=[], user_agent='', oauth_displayname='').client(aiohttp.ClientSession()).get('https://api.google.com/drive')

from .auth_mouse import *
from .sugar import *
