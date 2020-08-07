from sys import argv

from astropy.io.fits import Header

from astrometry_net_client.session import Session
from astrometry_net_client.statusables import Submission
from astrometry_net_client.uploads import FileUpload

path = "/home/sten/Documents/Projects/PracticalAstronomyCrew"
key_location = path + "/key"
filename = path + "/test-data/target.200417.00000088.3x3.FR.fits"


def login():
    print("Creating session")
    s = Session(None, key_location=key_location)

    print("Loggin in")
    s.login()

    print(s)
    print(s.id)
    return s


def main():
    if len(argv) > 1 and argv[1] == "online":

        s = login()
        upl = FileUpload(filename, session=s)

        print(upl)
        print("Uploading")
        submission = upl.submit()

        print("Got submission:")
        print(submission)
        print("id", submission.id)
    else:
        submission = Submission(3723552)

    print("Before status:", submission)
    resp = submission.status()
    print("After status:", submission)

    print("Response:", resp)
    print("Start: ", submission.processing_started)
    print("User Img", submission.user_images)
    print("Calibrations", submission.job_calibrations)
    print("Jobs", submission.jobs)

    for job in submission:
        print("Before status:", job)
        resp = job.status()
        print("After Status:", job)

        resp = job.info()
        print("Info:", resp)
        wcs = job.wcs_file()
        print("WCS is Header:", isinstance(wcs, Header))


if __name__ == "__main__":
    main()
