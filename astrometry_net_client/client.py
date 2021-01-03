import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            args = {
                k: v
                for k, v in kwargs.items()
                if k in {"api_key", "key_location"}
            }
            self.session = Session(**args)
        else:
            self.session = session

        if settings is None:
            setting_args = {
                k: v for k, v in kwargs.items() if k in Settings._settings
            }
            self.settings = Settings(**setting_args)
        else:
            self.settings = Settings(settings)

        log.info("Logging in")
        self.session.login()

    def upload_files_gen(
        self,
        files_iter,
        filter_func=None,
        filter_args=None,
        workers=MAX_WORKERS,
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
        workers: int, optional
            A positive integer, controlling the amount of workers to use for
            the processing. Will not exceed the value of
            :py:const:`MAX_WORKERS`.
        filter_func: Callable
            Predicate filter function which takes in the `filename` and
            optionally some argument (`filter_args`).
        filter_args: List
            Arguments which are to be passed to the filter function.

        Yields
        ------
        (:py:class:`astrometry_net_client.statusables.Job`, ``str``):
            A tuple containing the finished
            :py:class:`astrometry_net_client.statusables.Job` and the
            corresponding filename. Yields when the Job is finished.
            NOTE: Order of yielded filenames can (and likely will) be different
            from the given ``files_iter``
        """
        workers = min(MAX_WORKERS, workers)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            log.info("Spawned executor {}".format(executor))

            # submit the files & save which future corresponds to which
            #  filename
            future_to_file = {
                executor.submit(
                    self.filtered_upload_wrapper,
                    filename,
                    filter_func=filter_func,
                    filter_args=filter_args,
                ): filename
                for filename in files_iter
            }

            # iterate over the results once they are completed.
            for future in as_completed(future_to_file):
                result_filename = future_to_file[future]
                try:
                    res_job = future.result()
                except Exception as e:
                    # This exception is thrown inside the computed function.
                    err_msg = "File {} stopped with exception {}"
                    log.error(err_msg.format(result_filename, e))
                else:
                    if res_job is not None:  # ignore if file was filtered out
                        yield res_job, result_filename

    def filtered_upload_wrapper(
        self, filename, filter_func=None, filter_args=None, *args, **kwargs
    ):
        """
        Wrapper around :py:func:`upload_file` which filters the given file
        based on a specified filter function.  Main use for this is a
        computationally heavy filter function, like counting number of sources
        locally, and only uploading if not enough are detected.

        Parameters
        ----------
        filename: str
            File to be uploaded. See :py:func:`upload_file`.
        filter_func: Callable
            Predicate filter function which takes in the `filename` and
            optionally some argument (`filter_args`).
        filter_args: List
            Arguments which are to be passed to the filter function.
        args: other arguments
            Directly passed to :py:func:`upload_file`
        kwargs: keyword arguments
            Directly passed to :py:func:`upload_file`

        Returns
        -------
        Job or None: :py:class:`astrometry_net_client.statusables.Job`, `None`
            Will be the job of the resulting upload (see
            :py:func:`upload_file`), or `None` when `filter_func` evaluated to
            `False`.
        """
        if filter_args is None:
            # allow arguments to be unpackable if it is not specified
            filter_args = []

        if filter_func is not None and not filter_func(filename, *filter_args):
            log.info("Filter function failed, skipping upload")
            return None

        return self.upload_file(filename, *args, **kwargs)

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
