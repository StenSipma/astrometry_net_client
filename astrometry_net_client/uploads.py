import abc
from typing import Union, cast

from astrometry_net_client.config import upload_url
from astrometry_net_client.request import PostRequest
from astrometry_net_client.session import SessionRequest
from astrometry_net_client.statusables import Submission


class Submitter(abc.ABC):
    """
    Abstract class intended to use as a mixin class with a Request object (and
    hence assumes a `_make_request` method).
    Provides a new `submit` method, similar to `make`, but creates a Submission
    object out of the resulting response (from the subid entry).

    Example
    -------
    >>> upl = FileUpload(filename, session)
    >>> submission = upl.submit()
    """

    @abc.abstractmethod
    def make(self) -> Union[dict, bytes]:
        pass

    def submit(self) -> Submission:
        """
        Submit function, similar to ``make`` but in addition creates and
        returns the resulting submission.

        Returns
        -------
        :py:class:`astrometry_net_client.statusables.Submission`
            The submission which is created by the API. Use this to get the
            status & result(s) of your upload.
        """
        response = cast(dict, self.make())
        return Submission(response["subid"])


class BaseUpload(SessionRequest, PostRequest, Submitter):
    """
    Extends from:

    #. :py:class:`astrometry_net_client.request.AuthorizedRequest`,
    #. :py:class:`astrometry_net_client.request.PostRequest`,
    #. :py:class:`Submitter`

    Base class for uploads to be made with the Astrometry.net API. Combines
    some abstact classes useful for an upload request (e.g. a submit method,
    default post request and authorization)

    Meant as an abstact/base class, not to be called directly.
    """

    pass


class FileUpload(BaseUpload):
    """Request for submitting a file

    Extends from :py:class:`BaseUpload`

    Class for uploading a file to Astrometry.net `upload file`_ endpoint

    .. _upload file: http://astrometry.net/doc/net/api.html#submitting-a-file

    Example
    -------
    >>> s = Session(api_key='XXXXX')
    >>> upl = FileUpload('some/file', session=s)
    >>> submission = upl.submit()

    You can then use the resulting submission to inspect the result of your
    upload.

    Parameters
    ----------
    filename : str
        The path to the file which you want to upload.
    session : :py:class:`astrometry_net_client.session.Session`
        The login session (required by the
        :py:class:`astrometry_net_client.request.AuthorizedRequest`
        class)

    Returns
    -------
    :py:class:`astrometry_net_client.statusables.Submission`
        The submission object, which is created when you upload a file.
    """

    url: str = upload_url

    def __init__(self, filename: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO check if file exists?
        # TODO check if file has the correct type
        self.filename = filename

    def _make_request(self) -> dict:
        with open(self.filename, "rb") as f:
            self.arguments["files"] = {"file": f}
            response = super()._make_request()
        return response

    def __repr__(self):
        msg = "FileUpload(filename={}, session={})"
        return msg.format(self.filename, self.session)


class URLUpload(BaseUpload):
    """
    Extends from :py:class:`BaseUpload`

    Class for making a url upload to Astrometry.net
    http://astrometry.net/doc/net/api.html#submitting-a-url

    Work in progress
    """

    # TODO implement


class SourcesUpload(BaseUpload):
    """
    Extends from :py:class:`BaseUpload`

    Class for uploading a list of sources. (inspired by astroquery
    implementation)
    """

    # TODO: Decide if this is necessary
