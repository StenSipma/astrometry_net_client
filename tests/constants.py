VALID_KEY = "valid key"
VALID_TOKEN = "the session token/key"

FILE = "./tests/data/target.200417.00000088.3x3.FR.fits"

STATUS_SUCCESS = {"status": "success"}
STATUS_FAILURE = {"status": "failure"}

WAITING_SUBMISSION_RESULT = {
    "user": 19291,
    "processing_started": "2021-01-02 13:04:40.768054",
    "processing_finished": "2021-01-02 13:04:41.266073",
    "user_images": [4267396],
    "images": [8984579],
    "jobs": [None],
    "job_calibrations": [],
}

# TODO: if the job is not finished, then the job_calibrations value should
#       be empy
SUCCESS_SUBMISSION_RESULT_2 = {
    "user": 19291,
    "processing_started": "2020-08-20 21:39:18.078664",
    "processing_finished": "2020-08-20 21:39:23.751193",
    "user_images": [3923714],
    "images": [9000296],
    "jobs": [2],
    "job_calibrations": [[4489363, 3030589]],
}


SUCCESS_SUBMISSION_RESULT = {
    "user": 19291,
    "processing_started": "2020-08-20 21:39:18.078664",
    "processing_finished": "2020-08-20 21:39:23.751193",
    "user_images": [3923714],
    "images": [9000296],
    "jobs": [4489363],
    "job_calibrations": [[4489363, 3030589]],
}

FAILED_SUBMISSION_RESULT = {
    "user": 19291,
    "processing_started": "2020-12-26 12:54:38.285579",
    "processing_finished": "2020-12-26 12:54:38.607799",
    "user_images": [4253916],
    "images": [8262117],
    "jobs": [4819815],
    "job_calibrations": [],
}

JOB_INFO = {
    "objects_in_field": ["NGC 3982"],
    "machine_tags": ["NGC 3982"],
    "tags": ["NGC 3982"],
    "status": "success",
    "original_filename": "100303_Li_00000014.fits",
    "calibration": {
        "ra": 179.11639240832304,
        "dec": 55.127941301867835,
        "radius": 0.2903240582718073,
        "pixscale": 0.566166136261909,
        "orientation": 179.35359923850913,
        "parity": 1.0,
    },
}
