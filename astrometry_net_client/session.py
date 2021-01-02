import os

from astrometry_net_client.config import login_url, read_api_key
from astrometry_net_client.exceptions import (
    APIKeyError,
    InvalidRequest,
    LoginFailedException,
)
from astrometry_net_client.request import PostRequest


class Session(object):
    """
    Class to hold information on the Astrometry.net API session. Is able to
    read an api key from multiple possible locations, and login to retrieve
    a session key (stored in the id attribute).
    """

    url = login_url

    def __init__(self, api_key=None, key_location=None):
        if api_key is not None:
            self.api_key = api_key.strip()
        elif key_location is not None:
            self.api_key = read_api_key(key_location)
        else:
            self.api_key = os.environ.get("ASTROMETRY_API_KEY")
            if self.api_key is None:
                raise APIKeyError(
                    "No api key found or given. "
                    "Specify an API key using one of: "
                    "1. A direct argument, "
                    "2. A location of a file containing the key, "
                    "3. An environment variable named ASTROMETRY_API_KEY."
                )
        self.logged_in = False

    def login(self, force: bool = False):
        """
        Method used to log-in or start a session with the Astrometry.net API.

        Only sends a request if it is absolutely needed (or forced to).
        If logged_in is True, it assumes the session is still valid (there is
        no way to check if the session is still valid).

        After a successful login, the session key is stored in the `key`
        attribute and `logged_in` is set to `True`.

        Parameters
        ----------
        force: bool
            Forces the login by ignoring the :py:attr:`logged_in` boolean.

        Raises
        ------
        LoginFailedException
            if the login response does not have the status 'success'.
        """
        if not force and self.logged_in:
            return

        r = PostRequest(self.url, data={"apikey": self.api_key})
        try:
            response = r.make()
        except InvalidRequest:
            raise LoginFailedException("The api key given is not valid")

        self.key = response["session"]
        self.logged_in = True
