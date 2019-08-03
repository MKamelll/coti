# Imports
from dotenv import load_dotenv
from Auth import Auth
import requests
import base64
import time
import os
import re
load_dotenv()


# Twitter auth
class Twitter(object):

    def __init__(self, consumer_key, consumer_secret, status=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        self.status_update_url = 'https://api.twitter.com/1.1/statuses/update.json'
        self.status = status

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
        self.media_id_string = self.init_command()
        self.append()
        self.finialize()

    # Get file details
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

            # A unique thing for the file name as required
            # by the api
            time_stamp = str(int(time.time()))
            self.file_name = f'{time_stamp}.{self.file_type}'

    # INIT command
    def init_command(self):
        # Build params for INIT endpoint
        params = {
            'command': 'INIT',
            'name': self.file_name,
            'total_bytes': self.file_size,
            'media_type': self.mime,
        }

        # Make the request with the oauth object
        try:
            resp = self.auth.post(self.upload_url, params=params)
            resp = resp.json()
            return resp['media_id_string']
        except Exception as s:
            raise Exception('Problem at init command, {}'.format(s))

    # Append to the init id
    def append(self):
        # Build params for the APPEND endpoint
        files = {
            'command': 'APPEND',
            'name': self.file_name,
            'media_id': self.media_id_string,
        }

        # Count the chunk numbers as it is required by
        # twitter append endpoint
        segment_index = 0

        # Chunk size of 1 MB as the largest will mostly be
        # arround 15 MB
        chunk_size = int(1e+6)

        # Request the url and get the response as an iterator
        # with specified chunk size
        with requests.get(self.url, stream=True) as stream:
            for chunk in stream.iter_content(chunk_size=chunk_size):
                if chunk:
                    # Add the media which is the raw bytes
                    files['media'] = chunk
                    files['segment_index'] = segment_index
                    resp = self.auth.post(self.upload_url,
                                          files=files)

                    # Match the response code to anything other than 2xx
                    # is probably an error but it is not gonna say what's wrong hehe
                    if not re.match(r'2\d+', str(resp.status_code)):
                        raise Exception(('Could not append file with status code, {}'
                                         .format(resp.status_code)))

                    # A little break to not hammer the server
                    time.sleep(1)

    # Finalize the upload
    def finialize(self):
        # Build the params for the FINALIZE endpoint
        params = {
            'name': self.file_name,
            'command': 'FINALIZE',
            'media_id': self.media_id_string
        }

        # Send
        resp = self.auth.post(self.upload_url, params=params)

        # Errors
        if not re.match(r'2\d+', str(resp.status_code)):
            raise Exception('Could not finalize, {}'.format(resp.status_code))

        # If the response has a processing_info in it then it
        # is not finished processing and it needs to check later
        # after processing_info.check_after_secs
        resp = resp.json()
        if not 'processing_info' in resp:
            self.tweet()

    # Tweet the media after finishing uploading
    def tweet(self):
        # Build params for update status endpoint
        params = {
            'media_ids': self.media_id_string
        }

        # Add status if present
        if self.status:
            params['status'] = str(self.status)

        # Update
        resp = self.auth.post(self.status_update_url, params=params)

        # Errors
        if not re.match(r'2\d+', str(resp.status_code)):
            raise Exception('Could not tweet, {}'.format(resp.status_code))

        # Validation
        resp = resp.json()
        print(f"You tweeted {resp['id_str']} at {resp['created_at']}")


# Run
if __name__ == '__main__':
    url = 'https://preview.redd.it/3jpql4kx5oc31.png?width=640&crop=smart&auto=webp&s=874dc48de6107732704ec03fdd58afad2f411737'
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    Twitter(consumer_key, consumer_secret).upload(url)
