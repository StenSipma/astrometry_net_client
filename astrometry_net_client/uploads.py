import abc
from astrometry_net_client.config import upload_url
from astrometry_net_client.statusables import Submission
from astrometry_net_client.request import AuthorizedRequest, PostRequest


class Submitter(abc.ABC):
    """
    Abstract class intended to use as a mixin class with a Request object (and
    hence assumes a `_make_request` method).
    Provides a new `submit` method, similar to `make`, but creates a Submission
    object out of the resulting response (from the subid entry).

    An example usage is the FileUpload class:
     >>> upl = FileUpload(filename, session)
     >>> submission = upl.submit()
    """

    @abc.abstractmethod
    def _make_request(self):
        pass

    def submit(self):
        response = self._make_request()
        return Submission(response["subid"])


class BaseUpload(AuthorizedRequest, PostRequest, Submitter):
    """
    Base class for uploads to be made with the Astrometry.net API. Combines
    some abstact classes useful for an upload request (e.g. a submit method,
    default post request and authorization)
    
    Meant as an abstact class, not to be called directly.
    """

    pass


class FileUpload(BaseUpload):
    """
    Class for uploading a file to Astrometry.net
    http://astrometry.net/doc/net/api.html#submitting-a-file
    """

    url = upload_url

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO check if file exists?
        self.filename = filename

    def _make_request(self):
        with open(self.filename, "rb") as f:
            self.arguments["files"] = {"file": f}
            response = super()._make_request()
        return response


class URLUpload(BaseUpload):
    """
    Class for making a url upload to Astrometry.net
    http://astrometry.net/doc/net/api.html#submitting-a-url
    """

    pass


class SourcesUpload(BaseUpload):
    """
    Class for uploading a list of sources. (inspired by astroquery implementation)
    """

    # TODO: Decide if this is necessary
    pass
