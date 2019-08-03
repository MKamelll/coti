# Imports
from dotenv import load_dotenv
import oauth2 as oauth
from Auth import Auth
import requests
import binascii
import hashlib
import random
import string
import urllib
import base64
import uuid
import time
import hmac
import re
import os
load_dotenv()


# Twitter auth
class Twitter(object):

    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.update_status = 'https://api.twitter.com/1.1/statuses/update.json'
        self.upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        self.redirect_url = 'http://localhost:8000'

        # Handle auth
        client = Auth(self.consumer_key, self.consumer_secret)
        self.auth = client.get_auth()
        self.screen_name = client.get_screen_name()

        # Show the user who is tweeting
        print(f'You are tweeting as, {self.screen_name}')

    # Upload
    def upload(self, url):
        self.url = url
        self.get_file()
        media_id_string = self.init_command()

    # INIT command
    def init_command(self):
        # params = {
        #     'command': 'INIT',
        #     'name': self.file_name,
        #     'total_bytes': self.file_size,
        #     'media_type': self.mime,
        # }

        # print(self.header)
        resp = self.auth.post(self.update_status, params=params)
        print(resp.json(), resp.url)
        return 1

    # Get file
    def get_file(self):
        with requests.get(self.url, stream=True) as stream:
            headers = stream.headers
            headers = dict(headers)
            self.mime = headers['Content-Type']
            self.file_type = re.search(r'/(\w+)',
                                       self.mime).group(1)
            self.file_size = int(headers['Content-Length'])

            # Check if file is larger than twitter max 15MB
            file_size_MB = self.file_size / 1e+6
            if file_size_MB > 15:
                raise Exception('File is larger than 15MB')
            time_stamp = str(int(time.time()))

            self.file_name = f'{time_stamp}.{self.file_type}'


# Run
if __name__ == '__main__':
    url = 'https://preview.redd.it/3jpql4kx5oc31.png?width=640&crop=smart&auto=webp&s=874dc48de6107732704ec03fdd58afad2f411737'
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    Twitter(consumer_key, consumer_secret).upload(url)
