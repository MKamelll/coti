# Imports
from dotenv import load_dotenv
import oauth2 as oauth
import argparse
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
import json
import os
import re
load_dotenv()


# Twitter auth
class Twitter(object):

    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_token_url = 'https://api.twitter.com/oauth/request_token'
        self.access_token_url = 'https://api.twitter.com/oauth/access_token'
        self.authorize_url = 'https://api.twitter.com/oauth/authorize'
        self.update_status = 'https://api.twitter.com/1.1/statuses/update.json'
        self.upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        self.redirect_url = 'http://localhost:8000'
        self.creds_path = os.path.join(os.path.curdir, 'creds.json')
        self.is_reset()

    # Check for reset
    def is_reset(self):
        # Check arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--reset',
                            help='Reset your creds',
                            action='store_true')
        args = parser.parse_args()
        if args.reset:
            self.get_token()
        else:
            self.is_already_user()

    # Already a user
    def is_already_user(self):
        if os.path.exists(self.creds_path):
            with open(self.creds_path, 'r') as f:
                cred_file = json.load(f)
                self.oauth_token = cred_file['oauth_token']
                self.oauth_token_secret = cred_file['oauth_token_secret']
                self.screen_name = cred_file['screen_name']
        else:
            self.get_token()

        print(f'You are tweeting as, {self.screen_name}')

    # Twitter token
    def get_token(self):
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        self.client = oauth.Client(consumer)

        resp, content = self.client.request(self.request_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response {}".format(resp['status']))

        request_token = dict(urllib.parse.parse_qsl(content.decode("utf-8")))
        oauth_token = request_token['oauth_token']

        # Prompt for permission
        print('Go to this in your browser:')
        print(f'{self.authorize_url}?oauth_token={oauth_token}')
        after_redirect = input('Paste the url after redirect: ')

        # Parse the redirect for oauth_token and verifier
        after_redirect_parsed = urllib.parse.parse_qsl(after_redirect)
        oauth_token = after_redirect_parsed[0][1]
        oauth_verifier = after_redirect_parsed[1][1]

        # Sign get the actual request token
        token = oauth.Token(request_token['oauth_token'],
                            request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)

        # New Client to make requests through
        self.client = oauth.Client(consumer, token)
        resp, content = self.client.request(self.access_token_url, "POST")
        access_token = dict(urllib.parse.parse_qsl
                            (content.decode("utf-8")))

        self.oauth_token = access_token['oauth_token']
        self.oauth_token_secret = access_token['oauth_token_secret']
        self.screen_name = access_token['screen_name']

        # Save the token
        with open(self.creds_path, 'w') as f:
            json.dump(access_token, f)

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
        params = {
            'status': 'What u doing, stupid!'
        }
        self.oauth_add('POST', params)

        # Set Authorization header
        headers = {
            'Authorization': self.header,
        }
        # print(self.header)
        resp = requests.post(self.update_status,
                             params=params, headers=headers)
        print(resp.json(), resp.url)
        return 1

    # Oauth additional requirements
    def oauth_add(self, method, params):
        self.oauth_nonce = self.get_nonce()
        self.oauth_signature_method = 'HMAC-SHA1'
        self.oauth_version = '1.0'
        self.time_stamp_req = str(int(time.time()))
        self.oauth_signature = self.get_signature(method, params)
        self.header = self.build_header()
        print(self.oauth_signature)

    # Get random string for nonce
    def get_nonce(self):
        return uuid.uuid4().hex

    # Get signature
    def get_signature(self, method, params):
        # Add the rest of params to the object
        params_copy = dict(params)
        params_copy['oauth_timestamp'] = self.time_stamp_req
        params_copy['oauth_version'] = self.oauth_version
        params_copy['oauth_nonce'] = self.oauth_nonce
        params_copy['oauth_signature_method'] = self.oauth_signature_method
        params_copy['oauth_token'] = self.oauth_token
        params_copy['oauth_consumer_key'] = self.consumer_key
        params_copy['oauth_callback'] = self.redirect_url

        # Iterate the param object an percent encode keys and values
        params_percent_encoded = []
        for param, value in params_copy.items():
            param_encoded = urllib.parse.quote_plus(str(param))
            value_encoded = urllib.parse.quote_plus(str(value))
            param_and_value_encoded = param_encoded + '=' + value_encoded
            params_percent_encoded.append(param_and_value_encoded)

        # Sort params alpha.
        params_percent_sorted = sorted(params_percent_encoded)
        param_string = '&'.join(params_percent_sorted)

        # Add the method and url to string
        method_and_url = method.upper() + '&' + \
            urllib.parse.quote_plus(self.upload_url) + '&'
        signature_base_string = urllib.parse.quote_plus(
            method_and_url) + urllib.parse.quote_plus(param_string)

        # Encode both consumer secret and oauth_token_secret
        consumer_secret_encoded = urllib.parse.quote_plus(
            self.consumer_secret)
        oauth_secret_encoded = urllib.parse.quote_plus(
            self.oauth_token_secret)
        signing_key = consumer_secret_encoded + '&' + oauth_secret_encoded
        signing_key = urllib.parse.quote_plus(signing_key)

        # Hashing function
        digester = hmac.new(signing_key.encode('utf-8'),
                            signature_base_string.encode('utf-8'),
                            hashlib.sha1)

        signature = binascii.b2a_base64(digester.digest())[:-1].decode('utf-8')
        return signature

    # Build auth header
    def build_header(self):
        header = ''
        header += 'OAuth '
        all_pars = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': self.oauth_nonce,
            'oauth_signature': self.oauth_signature,
            'oauth_signature_method': self.oauth_signature_method,
            'oauth_timestamp': self.time_stamp_req,
            'oauth_token': self.oauth_token,
            'oauth_version': self.oauth_version
        }
        for parm, value in all_pars.items():
            header += urllib.parse.quote_plus(str(parm))
            header += '='
            header += '"'
            header += urllib.parse.quote_plus(str(value))
            header += '"'
            header += ','
        return header[:-1]

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
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    url = 'https://preview.redd.it/3jpql4kx5oc31.png?width=640&crop=smart&auto=webp&s=874dc48de6107732704ec03fdd58afad2f411737'
    Twitter(consumer_key, consumer_secret).upload(url)
