import json
import abc
import os

import requests

from astrometry_net_client.config import BASE_URL, login_url, upload_url, read_api_key
from astrometry_net_client.exceptions import APIKeyError, InvalidRequest, NoSessionError, ExhaustedAttemptsException, InvalidSessionError



class Request(object):
    _method_dict = {'post': requests.post, 'get': requests.get}

    def __init__(self, url=None, method='get', data=None, settings=None, **kwargs):
        self.data = {} if data is None else data.copy()
        self.settings = {} if settings is None else settings.copy()
        self.arguments = kwargs
        if url is not None:
            self.url = url
        self.method = self._method_dict[method]
        self.response = None

    def _make_request(self):
        payload = {'request-json': json.dumps({**self.data, **self.settings})}
        response = self.method(self.url, data=payload, **self.arguments)
        response = response.json()
        self.response = response

        # TODO add complete response checking
        if response['status'] == 'error':
            err_msg = response['errormessage']
            if err_msg == 'no "session" in JSON.':
                # No session argument provided
                raise NoSessionError(err_msg)
            if err_msg.startswith('no session with key'):
                # Invalid / Expired session key provided
                raise InvalidSessionError(err_msg)

            # fallback exception for a general error
            raise InvalidRequest(err_msg)

        return self.response

    def make(self):
        return self._make_request()

    @property
    def success(self):
        # TODO: maybe raise exception if request has not been made yet?
        # TODO: not sure if all requests have a status
        try:
            return self.response['status'] == 'success'
        except AttributeError:
            return False


class AuthorizedRequest(Request):
    def __init__(self, session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        session.login()
        self.session = session

    def _make_request(self):
        try:
            return super()._make_request()
        except InvalidSessionError:
            print('Session expired, loggin in again')
            self.session.login(force=True)

        return super()._make_request()


class Session(object):
    """
    Contains information about the current session. Mainly the session ID.
    Also should take care of loggin in using the API key.
    IDEA: maybe use it as a context manager?
    ISSUE: avoid having to login multiple times.
    """
    url = login_url

    def __init__(self, api_key=None, key_location=None):
        if api_key is not None:
            self.key = api_key
        elif key_location is not None:
            self.key = read_api_key(key_location)
        else: 
            try:
                self.key = os.environ.get('ASTROMETRY_API_KEY')
            except KeyError:
                raise APIKeyError(
                        'No api key found or given. '
                        'Specify an API key using one of: '
                        '1. A direct argument, '
                        '2. A location of a file containing the key, '
                        '3. An environment variable named ASTROMETRY_API_KEY.'
                        )
        self.logged_in = False

    def login(self, force=False):
        if not force and self.logged_in:
            return
        r = Request(self.url, data={'apikey': self.key})
        response = r.make()
        self.id = response['session']
        self.username = response['authenticated_user']
        self.logged_in = True


class Submitter(abc.ABC):
    @abc.abstractmethod
    def _make_request(self):
        pass

    def submit(self):
        response = self._make_request()
        return Submission(response['subid'])


class BaseUpload(AuthorizedRequest, Submitter):
    """
    Base class for uploads to be made with the Astrometry.net api
    
    Meant as an abstact class, not to be used.
    Excpects the implementer to have a url attribute
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, method='post', **kwargs)



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
        with open(filename, 'rb') as f:
            self.arguments['files'] = {'file': f}
            response = super()._make_request()
        return response


class URLUpload(BaseUpload):
    """
    Class for making a url upload to Astrometry.net
    http://astrometry.net/doc/net/api.html#submitting-a-url
    """
    pass


class SourcesUpload(BaseUpload):
    pass



class Statusable(abc.ABC):
    @abc.abstractmethod
    def _make_status_request(self):
        pass

    @abc.abstractmethod
    def _is_final_status(self):
        pass

    @property
    def status(self, max_retries=10):
        if not self._is_final_status():
            attempt = 0
            while attempt < max_retries:
                try:
                    self.response = self._make_status_request()
                except:
                    attempt += 1
                else:
                    break
            else:
                msg = 'Connection could not be made after {} attempts.'
                raise ExhaustedAttemptsException(msg.format(max_retries))

        return self.response


class Submission(Statusable):
    """
    Represents a single submission from Astrometry.net.
    A submission is the result of any of the "upload or upload_url"
    A submission contains a list with jobs (TODO: when are there multiple jobs?)
    If the job_calibrations list is nonempty, the image is solved.
    """
    url = BASE_URL + '/submissions/{submission.id}'

    def __init__(self, submission_id):
        self.id = submission_id
        self.url = self.url.format(submission=self)

    def _make_status_request(self):
        r = Request(self.url)
        self.response = r.make()

        # TODO verify which of these entries are valid in the response
        self.processing_started = response['processing_started']
        self.processing_finished = response['processing_finished']
        self.user_images = response['user_images']
        self.job_calibrations = response['job_calibrations']

        self.jobs = [Job(job_id) for job_id in response['jobs']]

    def _is_final_status(self):
        return hasattr(self, 'processing_finished')


class Job(Statusable):
    """
    Represents a single job from Astrometry.net.
    It can either still be running, or be finished.
    When finished, results can be queried using the appropriate methods.
    """
    url = BASE_URL + '/jobs/{job.id}'
    def __init__(self, job_id):
        self.id = job_id
        self.url = self.url.format(job=self)

    def _make_status_request(self):
        r = Request(self.url)
        response = r.make()
        self.result = response['status']

    def _is_final_status(self):
        try:
            return self.response['status'] in {'success', 'failure'}
        except AttributeError:
            return False
