import json
import abc
import os

import requests

from astrometry_net_client.config import BASE_URL, login_url, upload_url, read_api_key
from astrometry_net_client.exceptions import APIKeyError, InvalidRequest, NoSessionError, ExhaustedAttemptsException, InvalidSessionError, LoginFailedException

__all__ = ['Session', 'Submission', 'Job']

class Session(object):
    """
    Class to hold information on the Astrometry.net API session. Is able to
    read an api key from multiple possible locations, and login to retrieve
    a session key (stored in the id attribute).
    """
    url = login_url

    def __init__(self, api_key=None, key_location=None):
        if api_key is not None:
            self.api_key = api_key
        elif key_location is not None:
            self.api_key = read_api_key(key_location)
        else: 
            try:
                self.api_key = os.environ.get('ASTROMETRY_API_KEY')
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
        """
        Method used to log-in or start a session with the Astrometry.net API.

        Only sends a request if it is absolutely needed (or forced to). 
        If logged_in is True, it assumes the session is still valid (there is no
        way to check if the session is still valid).

        After a successful login, the session key is stored in the `key` attribute
        and `logged_in` is set to `True`.

        Raises LoginFailedException if the login response does not have the 
        status 'success'.
        """
        if not force and self.logged_in:
            return

        r = PostRequest(self.url, data={'apikey': self.api_key})
        response = r.make()

        if response.get('status') != 'success':
            raise LoginFailedException(str(response))

        self.key = response['session']
        self.logged_in = True


class Statusable(abc.ABC):
    @abc.abstractmethod
    def _make_status_request(self):
        pass

    @abc.abstractmethod
    def _is_final_status(self):
        pass

    def status(self, max_retries=10):
        if not self._is_final_status():
            attempt = 0
            while attempt < max_retries:
                try:
                    self.response = self._make_status_request()
                except Exception as e:
                    print('Failed with exception', e)
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
        response = r.make()
        self.response = response

        # TODO verify which of these entries are valid in the response
        self.processing_started = response['processing_started']
        self.processing_finished = response['processing_finished']
        self.user_images = response['user_images']
        self.images = response['images']
        self.job_calibrations = response['job_calibrations']

        self.jobs = [Job(job_id) for job_id in response['jobs']]
        return response

    def _is_final_status(self):
        try:
            fin = self.processing_finished
        except AttributeError:
            return False
        else:
            print(fin)
            return not fin


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
        return response

    def _is_final_status(self):
        try:
            return self.response['status'] in {'success', 'failure'}
        except AttributeError:
            return False

    
