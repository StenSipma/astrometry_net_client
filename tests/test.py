from sys import argv

from astrometry_net_client.client import Session
from astrometry_net_client.uploads import FileUpload
from astrometry_net_client.statusables import Submission


key_location = '/home/sten/Documents/Projects/PracticalAstronomyCrew/key'
filename = '/home/sten/Documents/Projects/PracticalAstronomyCrew/test-data/target.200417.00000088.3x3.FR.fits'


def login():
    print('Creating session')
    s = Session(None, key_location=key_location)

    print('Loggin in')
    s.login()

    print(s)
    print(s.id)
    return s


def main():
    if len(argv) > 1 and argv[1] == 'online':

        s = login()
        upl = FileUpload(filename, session=s)

        print(upl)
        print('Uploading')
        submission = upl.submit()

        print('Got submission:')
        print(submission)
        print('id', submission.id)
    else:
        submission = Submission(3723552)
    
    resp = submission.status()
    print('Response:', resp)
    print('Start: ', submission.processing_started)
    print('User Img', submission.user_images)
    print('Calibrations', submission.job_calibrations)
    print('Jobs', submission.jobs)

    for job in submission.jobs:
        print('Job ID:', job.id)
        resp = job.status()
        print('Job Response:', resp)
        print('Job Status:', job.result)


if __name__ == '__main__':
    main()
