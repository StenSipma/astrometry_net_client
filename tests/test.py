import logging
from sys import argv

from astropy.io.fits import Header

from astrometry_net_client.session import Session
from astrometry_net_client.settings import Settings
from astrometry_net_client.statusables import Submission
from astrometry_net_client.uploads import FileUpload

path = "/home/sten/Documents/Projects/PracticalAstronomyCrew"
key_location = path + "/key"
filename = path + "/test-data/target.200417.00000088.3x3.FR.fits"


class DecreasedOutputFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        msg = result
        if len(msg) > 300:
            result = msg[:100] + " ... " + msg[-20:]

        return result


log = logging.getLogger("Testing")


def setup_logging(full=False):
    # Setup logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter if full else DecreasedOutputFormatter

    # create formatter
    formatter = formatter("%(name)s - %(levelname)s - %(message)s")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logging.basicConfig(handlers=[ch], level=logging.DEBUG)


def login():
    log.debug("Creating session")
    s = Session(None, key_location=key_location)

    log.debug("Loggin in")
    s.login()

    log.debug(s)
    log.debug(s.key)
    return s


def main():
    settings = Settings()
    settings.set_scale_range(10, 20)
    log.debug("Using settings: {}".format(settings))

    if "online" in argv[1:]:

        session = login()
        upl = FileUpload(filename, session=session, settings=settings)

        log.debug(upl)
        log.debug("Uploading")
        submission = upl.submit()

        log.debug("Got submission: {}".format(submission))
        log.debug("id {}".format(submission.id))
    else:
        submission = Submission(3723552)

    log.debug("Before status: {}".format(submission))
    resp = submission.until_done()
    log.debug("After status: {}".format(submission))

    log.debug("Response: {}".format(resp))
    log.debug("Start:  {}".format(submission.processing_started))
    log.debug("User Img {}".format(submission.user_images))
    log.debug("Calibrations {}".format(submission.job_calibrations))
    log.debug("Jobs {}".format(submission.jobs))

    for job in submission:
        log.debug("Before status: {}".format(job))
        resp = job.until_done()
        log.debug("After Status: {}".format(job))

        resp = job.info()
        log.debug("Info: {}".format(resp))
        # TODO: make sure to only do this when job is successfull
        # TODO:  decide how to handle... exception by wrapping around
        # TODO:  invalid request of this type will result in response 505
        # TODO: Check the response status at request level.
        wcs = job.wcs_file()
        log.debug("WCS is Header: {}".format(isinstance(wcs, Header)))


if __name__ == "__main__":
    full_logging = "full" in argv[1:]

    setup_logging(full_logging)
    main()
