# Imports
from ImgHandler import ImgHandler
from OtherMediaHandler import OtherMediaHandler
from dotenv import load_dotenv
from Auth import Auth
import requests
import time
import sys
import os
import re
load_dotenv()


# Twitter auth
class Twitter(object):

    def __init__(self, consumer_key, consumer_secret, status=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.status = status

        # Handle auth
        client = Auth(self.consumer_key, self.consumer_secret)
        self.auth = client.get_auth()
        self.screen_name = client.get_screen_name()

        # Show the user who is tweeting
        print(f'You are tweeting as, {self.screen_name}')

    # Upload
    def upload(self, url):
        '''
            * Handle uploading media by first
              checking the type and calling the appropriate
              class.

            :url the url to upload
            :return None
        '''
        self.url = url
        mime, file_type, file_size, file_name = self.get_file()

        # Check file type
        if not self.is_it_img(file_type):
            OtherMediaHandler(mime, file_type, file_size,
                              file_name, self.auth, self.url, self.status)

        # Handle img
        img = ImgHandler(mime, file_type, file_size,
                         file_name, self.auth, self.url, self.status)
        img.init_command()
        img.append()
        img.finialize()

    # Get file details
    def get_file(self):
        '''
            Gets all the file details from the headers.

            :return 
                :file_type
                :mime
                :file_size in bytes
                :file_size_MB in megabytes to check against
                :the tweet max
                :file_name using the timestamp
        '''
        with requests.get(self.url, stream=True) as stream:
            headers = stream.headers
            headers = dict(headers)
            mime = headers['Content-Type']
            file_type = re.search(r'/(\w+)',
                                  mime).group(1)
            file_size = int(headers['Content-Length'])

            # Check if file is larger than twitter max 15MB
            file_size_MB = file_size / 1e+6
            if file_size_MB > 15:
                raise Exception('File is larger than 15MB')

            # A unique thing for the file name as required
            # by the api
            time_stamp = str(int(time.time()))
            file_name = f'{time_stamp}.{file_type}'

            # Return
            return mime, file_type, file_size, file_name

    def is_it_img(self, file_type):
        ''' 
            Checks if the current file is an img because
            different file types have different implentations
            in the api.

            :return True if it's an img
                    False otherwise
        '''
        supported_img_exts = ['png', 'jpg', 'jpeg']
        for ext in supported_img_exts:
            if file_type.lower() == ext:
                return True

        return False


# main
def main():
    if len(sys.argv) >= 2:
        url = sys.argv[1]
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')
        Twitter(consumer_key, consumer_secret).upload(url)
    else:
        print('----------------> USE tweet ["URL"] <----------------')
        sys.exit(0)


# Run
if __name__ == '__main__':
    main()
