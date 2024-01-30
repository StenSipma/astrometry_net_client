import abc
import logging
import time
from functools import wraps

from astropy.io import fits

from astrometry_net_client.config import BASE_URL
from astrometry_net_client.exceptions import (
    StatusFailedException,
    StillProcessingException,
)
from astrometry_net_client.request import Request, file_request, fits_file_request

log = logging.getLogger(__name__)


def cache_response(func):
    """
    Wrapper around a function to cache its result in an attribute of the
    object. Name of the attribute is: _<funcname>_result

    Parameters
    ----------
    func
        function to be wrapped

    Returns
    -------
    wrapped function
    """
    func_name = func.__name__
    result_attr = "_{}_result".format(func_name)

    @wraps(func)
    def wrapper(self, *args, force=False, **kwargs):
        if not force and hasattr(self, result_attr):
            log_msg = "Result {} already cached. Reusing..."
            log.debug(log_msg.format(result_attr))
            return getattr(self, result_attr)
        result = func(self, *args, **kwargs)
        setattr(self, result_attr, result)
        return result

    return wrapper


def ensure_status_success(func):
    """
    Decorator for a method to enforce it only being called when the
    statusable is successful (and therefore also finished).

    Parameters
    ----------
    func
        function to be wrapped

    Returns
    -------
    wrapped function

    Raises
    ------
    StatusFailedException
        When the :py:meth:`success` evaluates to ``False`` but
        :py:meth:`done` to ``True``.
    StillProcessingException
        When :py:meth:`done` is ``False``
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.status()
        if not self.done():
            raise StillProcessingException()
        if not self.success():
            raise StatusFailedException()
        result = func(self, *args, **kwargs)
        return result

    return wrapper


def ensure_status(func):
    """
    Decorator for a method to enforce it only being called when the
    statusable is finished.

    Parameters
    ----------
    func
        function to be wrapped

    Returns
    -------
    wrapped function

    Raises
    ------
    StillProcessingException
        when :py:meth:`done` is ``False``
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.status()
        if not self.done():
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

    def status(self, force=False):
        """
        Method which queries the status if it is needed.

        ``status`` is a method which queries the status of the statusable
        if the current / last retrieved status is not :py:meth:`done` (or no
        status is known). If an earlier queried status signals that the
        statusable is finished, no further request is made.

        Parameters
        ----------
        force: bool
            Can be set to true to make a status request regardless of the
            result of :py:meth:`done`.

        Returns
        -------
            dict: Dictionary with the status response (content). Same as
                attribute :py:attr:`stat_response`.
        """
        if force or not self.done():
            log_msg = "Statusable {} not done, querying status..."
            log.debug(log_msg.format(self.__class__.__name__))
            self.stat_response = self._make_status_request()

        return self.stat_response

    def until_done(self, start=4, end=300, timeout=None):
        """
        Blocking method which waits for the Statusable to be finished.

        This method will keep querying the :py:func:`status` until the
        statusable is :py:func:`done`. Will sleep in increasing intervals
        between each status query, to avoid overloading the API server
        (and give room for possible threading). The sleeping behaviour is
        determined by ``start`` and ``end``.

        It is possible to specify a timeout, in seconds, after which a
        :py:exc:`TimeoutError` is raised.

        Parameters
        ----------
        start: int
            Determines the intitial sleep time, which is doubled after each
            query. Defaults to 4s.
        end: int or None
            If specified, gives a maximal value for the sleep time. Otherwise
            the sleep time will be doubled forever.
        timeout: int or None
            If specified will raise a :py:exc:`TimeoutError` when the
            method has been running for the given time.

        Returns
        -------
        dict:
            Dictionary with the status response (content). Same as attribute
            :py:attr:`stat_response`.

        Raises
        ------
        TimeoutError
            When parameter `timeout` is set and the waited time exceeds this
            value.

        Examples
        --------
        Will wait forever and doubles the sleep time until it reaches 300.

        >>> stat.until_done()

        Will wait forever, and doubles the sleep time until it is equal to 60s

        >>> stat.until_done(end=60)

        Will wait forever and doubles the sleep time indefinitely

        >>> stat.until_done(end=None)

        Waits until 120s have passed (default sleep behaviour)

        >>> stat.until_done(timeout=120s)
        TimeoutError
        """
        now = time.time  # alias the function for readablility
        start_time = now()

        sleep_time = start
        log_msg = "Starting the until done loop with: sleep_time = {}, timeout = {}"
        log.debug(log_msg.format(sleep_time, timeout))
        while timeout is None or now() - start_time < timeout:
            response = self.status()
            log.debug("Current status response: {}".format(response))

            if self.done():
                break

            log.debug("Not done, sleeping for {}s".format(sleep_time))
            time.sleep(sleep_time)
            sleep_time *= 2
            sleep_time = end if end and end < sleep_time else sleep_time
        else:
            raise TimeoutError()

        return self.stat_response

    def success(self):
        """
        Evaluates if the statusable was successful.

        Will always be ``False`` if :py:meth:`done` is ``False``.

        Returns
        -------
        bool
        """
        # TODO maybe return None when you cannot yet know ?
        return self._is_final_status() and self._status_success()

    def done(self):
        """
        Evaluates if the last :py:meth:`status` result is the final result.

        Returns
        -------
        bool:
            ``True``, when the last response from `status` is the final status
            (e.g. it does not change anymore). ``False`` otherwise
        """
        return self._is_final_status()


class Submission(Statusable):
    """
    Represents a single submission from Astrometry.net.  A submission is the
    result of any of the :py:class:`astrometry_net_client.UploadFile` or
    :py:class:`astrometry_net_client.UploadURL` uploaders.

    When :py:func:`status` is called and jobs are available, the status of the
    jobs will also be queried. To see the response of these jobs, see their
    ``response`` attribute.

    Note that some of the attributes listed below are only available when
    :py:func:`status` is queried.

    Attributes
    ----------
    id: int
        Identifier for the submission. Used in the request URL.
    user: int
        Identifier for the user which made the Submission.
    images: list(int)
        List of references to the uploaded images.
    job_calibrations: list(int)
        Identifier to the references used to solve the images.
    jobs: list(Jobs)
        The list of jobs which the Submission spawned. Will typically be one
        Job per uploaded image. When no job was spawned yet, the list will
        be: ``[None]``.
    processing_started: str
        If available, a string containing the date when the Submission process
        started.
    processing_finished: str
        If available, a string containing the date when the Submission process
        finished.

    See Also
    --------
    Statusable : For available function on getting the status & waiting
    """

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

        Returns
        -------
        Iterator over the :py:attr:`jobs`.
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
        self.user = response["user"]
        self.images = response["images"]
        self.job_calibrations = response["job_calibrations"]

        self.jobs = [Job(job_id) for job_id in response["jobs"] if job_id is not None]

        for job in self.jobs:
            job.status()

        return response

    def _is_final_status(self):
        """
        We define 'final' here as processing has finished and the jobs have
        started, assuming there is always at least one job.

        Returns
        -------
        bool
        """
        try:
            proc_finished = self.processing_finished is not None
        except AttributeError:
            return False

        jobs_created = hasattr(self, "jobs") and len(self.jobs) > 0
        return proc_finished and jobs_created

    def _status_success(self):
        if self.done():
            return all(job.success() for job in self)
        return False

    def __repr__(self):
        return "Submission({self.id})".format(self=self)

    def __str__(self):
        msg = "Submission(id={}, final={}, success={})"
        return msg.format(self.id, self.done(), self.success())

    def __hash__(self):
        return hash(self.id)


class Job(Statusable):
    """
    Represents a single job from Astrometry.net.
    It can either still be running, or be finished.
    When finished, results can be queried using the appropriate methods.

    Attributes
    ----------
    id: int
        Identifier for the Astrometry.net Job.
    resp_status: str
        The status of the Job (as it was last queried). Can be: ``"success"``,
        ``"failure"`` or ``"solving"``.
    objects_in_field : list(str)
        Detected objects in the field. Result of the :py:meth:`info` query.
    machine_tags : list(str)
        Tags made by the API (machine). Result of the :py:meth:`info` query.
    tags : list(str)
        All tags of the Job. Can be made by users or by the API. Result of
        the :py:meth:`info` query.
    original_filename : str
        Filename of the uploaded file. Will not include the path. Result of
        the :py:meth:`info` query.
    calibration : dict
        Dictionary containing information about the solved image, example:

        >>> job.calibration
        {"parity": 1.0, "orientation": 105.74942079091929,
                "pixscale": 1.0906710701159739, "radius": 0.8106715896625917,
                "ra": 169.96633791366915, "dec": 13.221011585315143}

    See Also
    --------
    Statusable : For available functions on getting the status & waiting
    """

    url = BASE_URL + "/jobs/{job.id}"

    info_suffix = "/info"

    # does not include the .../api/ path ... :(
    wcs_file_url = "http://nova.astrometry.net/wcs_file/{job.id}"
    fits_file_url = "http://nova.astrometry.net/new_fits_file/{job.id}"
    rdls_file_url = "http://nova.astrometry.net/rdls_file/{job.id}"
    axy_file_url = "http://nova.astrometry.net/axy_file/{job.id}"
    corr_file_url = "http://nova.astrometry.net/corr_file/{job.id}"
    annotated_display_url = "http://nova.astrometry.net/annotated_display/{job.id}"
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

        self.objects_in_field = response["objects_in_field"]
        self.machine_tags = response["machine_tags"]
        self.tags = response["tags"]
        self.original_filename = response["original_filename"]
        # TODO make a calibration class ?
        if self.success():
            self.calibration = response["calibration"]

        return response

    @ensure_status_success
    @cache_response
    def wcs_file(self):
        """
        Get the resulting wcs file as an astropy.io.fits.Header.

        Returns
        -------
        astropy.io.fits.Header
        """
        r = Request(self.wcs_file_url.format(job=self))
        binary_wcs = r.make()
        header = fits.Header.fromstring(binary_wcs)
        return header

    @ensure_status_success
    @cache_response
    def new_fits_file(self):
        """
        Get the new fits file (original file + new header).

        Returns
        -------
        astropy.io.fits.HDUList
        """
        return fits_file_request(self.fits_file_url.format(job=self))

    @ensure_status_success
    @cache_response
    def rdls_file(self):
        return fits_file_request(self.rdls_file_url.format(job=self))

    @ensure_status_success
    @cache_response
    def axy_file(self):
        return fits_file_request(self.axy_file_url.format(job=self))

    @ensure_status_success
    @cache_response
    def corr_file(self):
        return fits_file_request(self.corr_file_url.format(job=self))

    @ensure_status_success
    @cache_response
    def annotated_display(self):
        """
        JPEG image as a binary string.

        Since the result of this call is raw JPEG bytes, you still have to write it to
        a file in order to view it. See the example below on how to do this.

        Example
        -------
        >>> # Given that you uploaded some file and have the Job in the variable 'job'
        >>> raw_file_bytes = job.annotated_display()
        >>>
        >>> # Use any name, as long as it has the JPEG extension
        >>> filename_to_write = "annotated_display.jpeg"
        >>> with open(filename_to_write, "wb") as f:
        >>>     f.write(raw_file_bytes)
        >>> # Now you can open the file with your preferred image viewer

        Returns
        -------
        bytes
        """
        return file_request(self.annotated_display_url.format(job=self))

    @ensure_status_success
    @cache_response
    def red_green_image_display(self):
        """
        PNG image as a binary string

        Returns
        -------
        bytes
        """
        return file_request(self.red_green_image_display_url.format(job=self))

    @ensure_status_success
    @cache_response
    def extraction_image_display(self):
        """
        PNG image as a binary string

        Returns
        -------
        bytes
        """
        return file_request(self.extraction_image_display_url.format(job=self))

    def __repr__(self):
        return "Job({self.id})".format(self=self)

    def __str__(self):
        msg = "Job(id={}, final={}, success={})"
        return msg.format(self.id, self.done(), self.success())

    def __hash__(self):
        return hash(self.id)
