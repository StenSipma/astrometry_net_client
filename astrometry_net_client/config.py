BASE_URL = "http://nova.astrometry.net/api"
login_url = BASE_URL + '/login'
upload_url = BASE_URL + '/upload'


def read_api_key(location):
    with open(location, 'r') as f:
        key = f.read().strip()
    return key
