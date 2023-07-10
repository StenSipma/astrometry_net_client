import logging
import time
from queue import Queue

from astrometry_net_client.session import Session
from astrometry_net_client.settings import Settings
from astrometry_net_client.uploads import FileUpload

log = logging.getLogger(__name__)

# TODO: document this value.
MAX_WORKERS = 10


class Client:
    """
    Higher level class which makes the interaction with the API easy.

    Parameters
    ----------
    session: :py:class:`astrometry_net_client.session.Session`
        Optional argument to provide the session for the API. If not provided,
        you must either specify the keyword ``api_key`` or ``location``, or
        have the key present in your environment. See
        :py:class:`astrometry_net_client.session.Session`
    settings: :py:class:`astrometry_net_client.settings.Settings`, dict
        An optional settings object, which will be applied to all uploads.
        If not specified, the settings object will be created from given
        keyword arguments which correspond to valid settings. For this see
        :py:class:`astrometry_net_client.settings.Settings`.
    kwargs: arguments
        Used to create a session or settings object, if either is not
        specified. Will extract the relevant arguments relevant to the object
        which is created before passing them to the object constructor.
        See :py:class:`astrometry_net_client.settings.Settings` and
        :py:class:`astrometry_net_client.session.Session`
    """

    def __init__(self, session=None, settings=None, **kwargs):
        # TODO, make session optional?
        if session is None:
            args = {k: v for k, v in kwargs.items() if k in {"api_key", "key_location"}}
            self.session = Session(**args)
        else:
            self.session = session

        if settings is None:
            setting_args = {k: v for k, v in kwargs.items() if k in Settings._settings}
            self.settings = Settings(**setting_args)
        else:
            self.settings = Settings(settings)

        log.info("Logging in")
        self.session.login()

    def upload_files_gen(
        self,
        files_iter,
        queue_size=MAX_WORKERS,
    ):
        """
        Generator which uploads a number of files concurrently, yielding the
        :py:class:`astrometry_net_client.statusables.Job` & filename when done.

        Note that the ``files_iter`` argument is fully consumed when submitting
        to the executor is done. This means that the results will only be
        yielded once the iterator is consumed.

        Parameters
        ----------
        files_iter: iterable
            Some iterable containing paths to the files which will be uploaded.
            Is fully consumed before any result is yielded.
        queue_size: int, optional
            A positive integer, controlling the size of the queue. This will
            determine the maximum number of simultaneous submissions. Must be
            greater than 0 and lower than :py:const:`MAX_WORKERS`. Default is
            :py:const:`MAX_WORKERS`.

        Yields
        ------
        (:py:class:`astrometry_net_client.statusables.Job`, ``str``):
            A tuple containing the finished
            :py:class:`astrometry_net_client.statusables.Job` and the
            corresponding filename. Yields when the Job is finished.
            NOTE: Order of yielded filenames can (and likely will) be different
            from the given ``files_iter``

        Raises
        ------
        ValueError
            When the queue_size is invalid.
        """
        SLEEP_TIME = 0.3  # seconds

        files_iter = iter(files_iter)
        if queue_size < 1 or queue_size > MAX_WORKERS:
            raise ValueError(
                "queue_size must be greater than 0 and less or equal to ",
                f"{MAX_WORKERS}, was: {queue_size}",
            )
        processing_queue = Queue(maxsize=queue_size)

        # Populate queue initially
        for _, filename in zip(range(queue_size), files_iter):
            self._insert_submission(filename, processing_queue)

        while not processing_queue.empty():
            filename, submission, job = processing_queue.get()
            log_msg = "Checking file {}, job exists: {}"
            log.debug(log_msg.format(filename, job is not None))
            # The item in the queue has 2 states; if it is still only a
            # submission job will be None and we have to create a job out of
            # it. When the job is made, we can check if the job is done. When
            # the job is finished return (yield) the value, otherwise put it
            # back in the queue.

            if job is None:
                submission.status()
                if submission.done():
                    job = submission.jobs[0]
                else:
                    processing_queue.put((filename, submission, job))
                    continue

            job.status()
            if job.done():
                try:
                    filename = next(files_iter)
                except StopIteration:
                    pass
                else:
                    self._insert_submission(filename, processing_queue)
                log_msg = "FINISHED submission {}, yielding..."
                log.info(log_msg.format(filename))
                yield (job, filename)
            else:
                processing_queue.put((filename, submission, job))

            time.sleep(SLEEP_TIME)

    def _insert_submission(self, filename, queue):
        """
        Helper function which creates an upload for the given filename, and
        inserts the submission in a queue. This is not intended to be used
        by a user.

        Parameters
        ----------
        filename: str
            The filename of the file to be submitted into the queue.
        queue: Queue
            The queue in which to insert the submission.
        """
        log_msg = "Submitting file {}"
        log.info(log_msg.format(filename))
        upl = FileUpload(filename, session=self.session, settings=self.settings)
        submission = upl.submit()
        queue.put((filename, submission, None))

    def upload_file(self, filename, settings=None):
        """
        Uploads file and returns completed job when finished solving.

        Parameters
        ----------
        filename: str
            Location + name of the file to upload.
        settings: :py:class:`astrometry_net_client.settings.Settings`
            An optional settings dict which only applies to this specific
            upload. Will override the default settings with which the
            :py:class:`Client` was constructed.

        Returns
        -------
        Job: :py:class:`astrometry_net_client.statusables.Job`
            The job of the resulting upload. NOTE: It is possible that the job
            did not succeed, therefore check with
            :py:meth:`astrometry_net_client.statusables.Statusable.success` if
            it did.
        """
        upl_settings = self.settings
        if settings is not None:
            upl_settings.update(settings)

        upl = FileUpload(filename, session=self.session, settings=upl_settings)
        start = time.time()
        submission = upl.submit()

        msg = "File {} submitted, waiting for it to finish"
        log.info(msg.format(filename))

        submission.until_done()  # blocks here

        # pretty much guarenteed to have exactly one job
        job = submission.jobs[0]

        job.until_done()  # blocks here
        end = time.time()

        msg = "Processing of file {} finished in {}s"
        log.info(msg.format(filename, end - start))

        return job

    def calibrate_file_wcs(self, filename, settings=None):
        """
        Uploads a file, returning the wcs header if it succeeds.

        Parameters
        ----------
        filename: str
            Location + name of the file to upload.
        settings: :py:class:`astrometry_net_client.settings.Settings`
            An optional settings dict which only applies to this specific
            upload. Will override the default settings with which the
            :py:class:`Client` was constructed.

        Returns
        -------
        :py:class:`astropy.io.fits.Header` or None
            Returns the Header if successful, None otherwise.
        """
        job = self.upload_file(filename, settings=settings)

        if job.success():
            return job.wcs_file()
        return None
