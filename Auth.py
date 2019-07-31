# Imports
from requests_oauthlib import OAuth1Session
import argparse
import json
import os


# Get a client
class Auth(object):
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_token_url = 'https://api.twitter.com/oauth/request_token'
        self.access_token_url = 'https://api.twitter.com/oauth/access_token'
        self.authorize_url = 'https://api.twitter.com/oauth/authorize'
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

    # Get an access token
    def get_token(self):
        # Get a request token
        oauth = OAuth1Session(self.consumer_key,
                              client_secret=self.consumer_secret)
        fetch_response = oauth.fetch_request_token(self.request_token_url)
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')

        # Get the temp oauth token and the verifier after authorization
        authorization_url = oauth.authorization_url(self.authorize_url)
        print('Please go to: ', authorization_url)
        redirect_response = input('Paste the full redirect URL here:\n')
        oauth_response = oauth.parse_authorization_response(redirect_response)
        verifier = oauth_response.get('oauth_verifier')

        # Get the actual access token
        oauth = OAuth1Session(self.consumer_key,
                              client_secret=self.consumer_secret,
                              resource_owner_key=resource_owner_key,
                              resource_owner_secret=resource_owner_secret,
                              verifier=verifier)
        oauth_tokens = oauth.fetch_access_token(self.access_token_url)
        resource_owner_key = oauth_tokens.get('oauth_token')
        resource_owner_secret = oauth_tokens.get('oauth_token_secret')
        self.screen_name = oauth_tokens.get('screen_name')
        print(oauth_tokens, self.screen_name)

        # Save the token
        with open(self.creds_path, 'w') as f:
            json.dump(oauth_tokens, f)