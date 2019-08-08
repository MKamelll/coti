# Handle video and Gif
class OtherMediaHandler(object):
    def __init__(self, mime, file_type, file_size,
                 file_name, auth, url, status):
        self.upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
        self.status_update_url = 'https://api.twitter.com/1.1/statuses/update.json'
        self.mime = mime
        self.file_type = file_type
        self.file_size = file_size
        self.file_name = file_name
        self.auth = auth
        self.url = url
        self.status = status
        raise NotImplementedError
