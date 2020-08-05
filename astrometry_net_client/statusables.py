import abc

from astrometry_net_client.exceptions import ExhaustedAttemptsException 
from astrometry_net_client.config import BASE_URL
from astrometry_net_client.request import Request


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



