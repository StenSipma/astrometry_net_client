from astrometry_net_client.session import Session
from astrometry_net_client.settings import Settings
from astrometry_net_client.uploads import FileUpload


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
    """

    def __init__(self, session=None, settings=None, **kwargs):
        # TODO, make session optional?
        if session is None:
            self.session = Session(**kwargs)
        else:
            self.session = session

        if settings is None:
            setting_args = {k: v for k, v in kwargs if k in Settings._settings}
            self.settings = Settings(**setting_args)
        else:
            self.settings = Settings(settings)

        self.session.login()

        self.jobs = []
        self.submissions = []

    def upload_file(self, filename, settings=None):
        """
        Uploads a file, returning the wcs header if it succeeds

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
        upl_settings = self.settings
        if settings is not None:
            upl_settings.update(settings)

        upl = FileUpload(filename, session=self.session, settings=upl_settings)
        submission = upl.submit()

        submission.until_done()

        # pretty much guarenteed to have exactly one job
        job = submission.jobs[0]
        job.until_done()
        if job.success():
            return job.wcs_file()
        return None
