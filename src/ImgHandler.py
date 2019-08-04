# Imports
import requests
import re
import time


class ImgHandler(object):
    '''
        * Handle img uploading
        : mime is the content-type header of the file
          to upload.
        : file_type is img type
        : file_size is the size in bytes
        : file_name is the name formed of the timestamp
        : url to upload
        : status in case the user wants to tweet something 
                 with the img
    '''

    def __init__(self, mime, file_type,
                 file_size, file_name,
                 auth, url, status):

        self.upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        self.status_update_url = 'https://api.twitter.com/1.1/statuses/update.json'
        self.mime = mime
        self.file_type = file_type
        self.file_size = file_size
        self.file_name = file_name
        self.auth = auth
        self.url = url
        self.status = status

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
            self.media_id_string = resp['media_id_string']
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
