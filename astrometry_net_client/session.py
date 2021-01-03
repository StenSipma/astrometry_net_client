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
    read an API key from multiple possible locations, and login to retrieve
    a session key (stored in the id attribute).

    Attributes
    ----------
    logged_in : bool
        Boolean indicating if a :py:func:`login` has happened successfully
        since creation of the class. Does not guarentee that the session
        :py:attr:`key` is (still) valid.
    api_key : str
        The API key used to log in.
    key : str
        The session key (not the :py:attr:`api_key`) which is given by the API
        after a valid :py:func:`login`.

    Examples
    --------
    There are multiple ways of giving your api key. You can just give it as
    a plain string (not very safe):

    >>> session_1 = Session(api_key='the api key')

    You can enter it in a separate private file and give the path to it. This
    file should only contain the key, nothing else.

    >>> session_2 = Session(key_location='path/to/file/with/key')

    You can specify the key as an environment variable named 
    `ASTROMETRY_API_KEY`.

    >>> session_3 = Session()

    If you do not specify any of the above, an exception will be thrown:

    >>> Session()
    APIKeyError

    Raises
    ------
    :py:exc:`APIKeyError`
        When no API key is specified (see examples)
    """

    url = login_url

    def __init__(self, api_key: str = None, key_location: str = None):
        """
        Some documentation
        """
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
        If :py:attr:`logged_in` is True, it assumes the session is still valid (there is
        no way to check if the session is still valid).

        After a successful login, the session key is stored in the :py:attr:`key`
        attribute and :py:attr:`logged_in` is set to `True`.

        Parameters
        ----------
        force: bool
            Forces the login by ignoring the :py:attr:`logged_in` boolean.

        Raises
        ------
        LoginFailedException
            If the login response does not have the status 'success'.
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
