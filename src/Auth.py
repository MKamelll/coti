# Imports
from requests_oauthlib import OAuth1Session
import argparse
import json
import sys
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
        self.is_add()

    # Check for reset
    def is_add(self):
        # Check arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--add',
                            help='Reset your creds',
                            action='store_true')
        args, _ = parser.parse_known_args()

        if args.add:
            self.get_token()
            sys.exit(0)
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
            print('You are not registered')
            self.get_token()

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
        self.oauth_token = oauth_tokens.get('oauth_token')
        self.oauth_token_secret = oauth_tokens.get('oauth_token_secret')
        self.screen_name = oauth_tokens.get('screen_name')

        # Save the token
        with open(self.creds_path, 'w') as f:
            json.dump(oauth_tokens, f)

    # Set a client to make the request
    def get_auth(self):
        client = OAuth1Session(self.consumer_key,
                               client_secret=self.consumer_secret,
                               resource_owner_key=self.oauth_token,
                               resource_owner_secret=self.oauth_token_secret)
        return client

    # Return the screen name of the authenticated user
    def get_screen_name(self):
        return self.screen_name
