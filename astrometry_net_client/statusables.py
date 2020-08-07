import abc
from functools import wraps

from astropy.io import fits

from astrometry_net_client.exceptions import (
    ExhaustedAttemptsException,
    StillProcessingException,
)
from astrometry_net_client.config import BASE_URL
from astrometry_net_client.request import (
    Request,
    fits_file_request,
    file_request,
)


def cache_response(func):
    """
    Wrapper around a function to cache its result in an attribute of the object.
    Name of the attribute is: _<funcname>_result
    """
    # TODO can the result be cached in a closure variable instead of an attribute?
    func_name = func.__name__
    result_attr = "_{}_result".format(func_name)

    @wraps(func)
    def wrapper(self, *args, force=False, **kwargs):
        if not force and hasattr(self, result_attr):
            return getattr(self, result_attr)
        result = func(self, *args, **kwargs)
        setattr(self, result_attr, result)
        return result

    return wrapper


def ensure_status(func):
    """
    Decorator for a method to enforce it only being called when the 
    statusable is finished.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.status()
        if not self._is_final_status():
            raise StillProcessingException()
        result = func(self, *args, **kwargs)
        return result

    return wrapper


class Statusable(abc.ABC):
    @abc.abstractmethod
    def _make_status_request(self):
        pass

    @abc.abstractmethod
    def _is_final_status(self):
        pass

    @abc.abstractmethod
    def _status_success(self):
        pass

    def status_success(self):
        return self._is_final_status() and self._status_success()

    def status(self, max_retries=3):
        if not self._is_final_status():
            # TODO evaluate if retrying here is needed
            attempt = 0
            while attempt < max_retries:
                try:
                    self.stat_response = self._make_status_request()
                except Exception as e:
                    print("Failed with exception", e)
                    attempt += 1
                else:
                    break
            else:
                msg = "Connection could not be made after {} attempts. Due to exception {}"
                # TODO: verify if 'e' works here
                raise ExhaustedAttemptsException(msg.format(max_retries, e))

        return self.stat_response


class Submission(Statusable):
    """
    Represents a single submission from Astrometry.net.
    A submission is the result of any of the "upload or upload_url"
    A submission contains a list with jobs
    If the job_calibrations list is nonempty, the image is solved.
    """

    # TODO: when are there multiple jobs?
    url = BASE_URL + "/submissions/{submission.id}"

    def __init__(self, submission_id):
        self.id = submission_id
        self.url = self.url.format(submission=self)

    @ensure_status
    def __iter__(self):
        """
        Allowes to easily iterate over the jobs of a submission by doing:
         >>> for job in submission:
         ...    process_job()
        """
        return iter(self.jobs)

    def _make_status_request(self):
        r = Request(self.url)
        response = r.make()
        self.response = response

        # TODO verify which of these entries are valid in the response
        self.processing_started = response["processing_started"]
        self.processing_finished = response["processing_finished"]
        self.user_images = response["user_images"]
        self.images = response["images"]
        self.job_calibrations = response["job_calibrations"]

        self.jobs = [
            Job(job_id) for job_id in response["jobs"] if job_id is not None
        ]
        return response

    def _is_final_status(self):
        """
        We define 'final' here as processing has finished and the jobs have
        started, assuming there is always at least one job.
        """
        return hasattr(self, "jobs") and len(self.jobs) > 0

    def _status_success(self):
        if self._is_final_status():
            return all(job._status_success() for job in self.jobs)
        return False


class Job(Statusable):
    """
    Represents a single job from Astrometry.net.
    It can either still be running, or be finished.
    When finished, results can be queried using the appropriate methods.
    """

    url = BASE_URL + "/jobs/{job.id}"

    info_suffix = "/info"

    # does not include the .../api/ path ... :(
    wcs_file_url = "http://nova.astrometry.net/wcs_file/{job.id}"
    fits_file_url = "http://nova.astrometry.net/new_fits_file/{job.id}"
    rdls_file_url = "http://nova.astrometry.net/rdls_file/{job.id}"
    axy_file_url = "http://nova.astrometry.net/axy_file/{job.id}"
    corr_file_url = "http://nova.astrometry.net/corr_file/{job.id}"
    annotated_display_url = (
        "http://nova.astrometry.net/annotated_display/{job.id}"
    )
    red_green_image_display_url = (
        "http://nova.astrometry.net/red_green_image_display/{job.id}"
    )
    extraction_image_display_url = (
        "http://nova.astrometry.net/extraction_image_display/{job.id}"
    )

    def __init__(self, job_id):
        self.id = job_id
        self.url = self.url.format(job=self)

    def _make_status_request(self):
        r = Request(self.url)
        response = r.make()
        self.resp_status = response["status"]
        return response

    def _is_final_status(self):
        try:
            return self.resp_status in {"success", "failure"}
        except AttributeError:
            return False

    def _status_success(self):
        return self.resp_status == "success"

    @ensure_status
    @cache_response
    def info(self):
        r = Request(self.url + self.info_suffix)
        response = r.make()

        self.info_response = response
        self.objects_in_field = response["objects_in_field"]
        self.machine_tags = response["machine_tags"]
        self.tags = response["tags"]
        self.original_filename = response["original_filename"]
        # TODO make a calibration class ?
        # Only exists if status is success (?)
        # self.calibration = response['calibration']

        return response

    @ensure_status
    @cache_response
    def wcs_file(self):
        """
        Get the resulting wcs file as an astropy.io.fits.Header.
        """
        r = Request(self.wcs_file_url.format(job=self))
        binary_wcs = r.make()
        header = fits.Header.fromstring(binary_wcs)
        return header

    @ensure_status
    @cache_response
    def new_fits_file(self):
        return fits_file_request(self.fits_file_url.format(job=self))

    @ensure_status
    @cache_response
    def rdls_file(self):
        return fits_file_request(self.rdls_file_url.format(job=self))

    @ensure_status
    @cache_response
    def axy_file(self):
        return fits_file_request(self.axy_file_url.format(job=self))

    @ensure_status
    @cache_response
    def corr_file(self):
        return fits_file_request(self.corr_file_url.format(job=self))

    @ensure_status
    @cache_response
    def annotated_display(self):
        """
        JPEG image as a binary string
        """
        return file_request(self.annotated_display_url.format(job=self))

    @ensure_status
    @cache_response
    def red_green_image_display(self):
        """
        PNG image as a binary string
        """
        return file_request(self.red_green_image_display_url.format(job=self))

    @ensure_status
    @cache_response
    def extraction_image_display(self):
        """
        PNG image as a binary string
        """
        return file_request(self.extraction_image_display_url.format(job=self))
