import json
import logging
from typing import Optional, Union, cast

import requests
from astropy.io import fits

from astrometry_net_client.exceptions import (
    InvalidRequest,
    InvalidSessionError,
    NoSessionError,
    UnkownContentError,
)
from astrometry_net_client.settings import Settings

log = logging.getLogger(__name__)


class Request(object):
    """
    Class to make requests to the Astrometry.net API. Intended use mainly for
    extending / internal class usage.

    Requests are made using the requests library, and is capable of making GET
    and POST requests (controlled by the method argument in the constructor).

    Typical usage (makes a GET request):
     >>> r = Request('some-url')
     >>> response = r.make()

    The constructor prepares the request, but does not yet make it. To send /
    make the request use the method: `r.make()`.

    For a POST request:
     >>> r = Request('some-url', method='post', data=data, settings=settings)
     >>> response = r.make()

    where data and settings are both combined and wrapped into the
    'request-json' form, but are split to allow for some general settings.

    An alternative for not using the "method='post'" is to use the PostRequest
    class

    It is valid to omit specifying a url, if the subclass already has its own
    url attribute.

    The internal _make_request() method can be used to extend the functionality
    of requests (e.g. AuthorizedRequest: by making sure the user is logged in).

    Additional arguments specied in the constructor (which are not directly
    used in this class or any subclass) will be stored and passed to the
    request call.

    The original response (as returned from the requests module call) is stored
    in the `original_response` attribute.
    """

    _allowed_methods = {"post", "get"}
    _raw_content_types = {"application/fits", "image/jpeg", "image/png"}

    def __init__(
        self,
        url: Optional[str] = None,
        method: str = "get",
        data: Optional[dict] = None,
        settings: Optional[Settings] = None,
        **kwargs,
    ):
        self.data = {} if data is None else data.copy()
        self.settings = {} if settings is None else settings.copy()
        self.arguments = kwargs
        if url is not None:
            self.url = url

        # We have to get the attribute like this, otherwise we cannot
        # monkeypatch (e.g. replace requests.get) in the test cases
        if method in self._allowed_methods:
            self.method = getattr(requests, method)
        else:
            err_msg = "Method argument must be one of {}"
            raise ValueError(err_msg.format(self._allowed_methods))

    def _make_request(self) -> Union[dict, bytes]:
        if len(self.data) + len(self.settings) > 0:
            payload = {"request-json": json.dumps({**self.data, **self.settings})}
        else:
            payload = None

        log.debug("Sending {!r} with payload {}".format(self, payload))
        response = self.method(self.url, data=payload, **self.arguments)
        log.debug("Retrieved response: {}".format(response.text))

        self.original_response = response

        if response.status_code != 200:
            response.raise_for_status()

        content_type = response.headers["Content-Type"]

        # case where the response is JSON as text
        if content_type.startswith("text/plain"):
            log.debug("Text response detected")
            response = response.json()
            self.response = response

            # TODO: add complete response checking
            if response.get("status", "") == "error":
                err_msg = response["errormessage"]
                if err_msg == 'no "session" in JSON.':
                    # No session argument provided
                    raise NoSessionError(err_msg)
                if err_msg.startswith("no session with key"):
                    # Invalid / Expired session key provided
                    raise InvalidSessionError(err_msg)

                # fallback exception for a general error
                raise InvalidRequest(err_msg)

        # case where a file is returned, we want to return the raw bytes
        elif content_type in self._raw_content_types:
            log.debug("Raw file response detected")
            self.response = response.content
        else:
            log.error("Unknown response content {}".format(content_type))
            msg = "Request produced a response with unknown content type {}"
            raise UnkownContentError(msg.format(content_type))

        return self.response

    def make(self) -> Union[dict, bytes]:
        """
        Send the actual request to the API.
        returns the response

        This method is mainly for convenience, as to avoid the user unfriendly
        _make_request() method.

        Returns
        -------
        response
            Type depends on the request which is being send. Can be a ``dict``
            but also a binary file (e.g. when expecting a filts file).
        """
        return self._make_request()

    def __repr__(self):
        msg = (
            "Request({self.url}, method={self.method}, data={self.data},"
            " settings={self.settings}, args={self.arguments})"
        )
        return msg.format(self=self)


class PostRequest(Request):
    """
    Makes a POST request instead of the default GET request. It can be used
    as a mixin class, alongside other

    Essentially replaces:
     >>> r = Request(url, method='post', arguments...)

    With
     >>> r = PostRequest(url, arguments...)

    For further usage see the Request class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, method="post", **kwargs)


def file_request(url: str) -> bytes:
    """
    Utility function which makes a request to ``url`` and gets a file in
    response.

    Parameters
    ----------
    url: str
        URL to send the request to.

    Returns
    -------
        the binary contents of this file.
    """
    r = Request(url)
    binary_file = r.make()
    return cast(bytes, binary_file)


def fits_file_request(url: str) -> fits.HDUList:
    """
    Make request to ``url`` and return a FITS file.

    Makes a request to ``url``  and read the binary_fits response into
    an astropy fits file (``astropy.io.fits.HDUList``)

    Parameters
    ----------
    url: str
        URL to send the request to.

    Returns
    -------
        an astropy fits file (``astropy.io.fits.HDUList``)
    """
    binary_fits = file_request(url)
    hdul = fits.HDUList(file=binary_fits)
    return hdul
