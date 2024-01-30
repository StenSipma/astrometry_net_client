BASE_URL = "http://nova.astrometry.net/api"
login_url = BASE_URL + "/login"
upload_url = BASE_URL + "/upload"
url_upload_url = BASE_URL + "/url_upload"


def read_api_key(location):
    """
    Reads an api key from a file in the specifies location.

    Parameters
    ----------
    location: str
        Location of the api key file.

    Returns
    -------
    str:
        The resulting api key
    """
    with open(location, "r") as f:
        key = f.read().strip()
    return key
