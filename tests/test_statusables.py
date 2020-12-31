import pytest
from constants import FAILED_SUBMISSION_RESULT, SUCCESS_SUBMISSION_RESULT

from astrometry_net_client import Job, Submission


@pytest.mark.parametrize(
    "statusable, success",
    [
        (Submission(4113880), False),
        (Submission(3781056), True),
        (Job(4450465), False),
        (Job(4446851), True),
    ],
)
@pytest.mark.online
def test_statusables(statusable, success):
    # No status queried yet
    assert not statusable.done()
    assert not statusable.success()

    resp = statusable.status()

    assert resp is not None
    assert statusable.done()
    assert statusable.success() == success


@pytest.mark.parametrize(
    "sid, result",
    [
        (4113880, FAILED_SUBMISSION_RESULT),
        (3781056, SUCCESS_SUBMISSION_RESULT),
    ],
)
@pytest.mark.online
def test_submission_response(sid, result):
    submission = Submission(sid)
    response = submission.status()
    ud_response = submission.until_done()

    assert response == result
    assert response == ud_response

    for key in result.keys():
        print(f"{key=}")
        assert hasattr(submission, key)
        if key != "jobs":
            assert getattr(submission, key) == result[key]

    # test iteration is done properly
    for j1, j2 in zip(submission, submission.jobs):
        print(f"{j1=}, {j2=}")
        assert j1 == j2

    # test if job ids correspond correctly
    for job in submission:
        assert job.id in result["jobs"]


def test_submission_success(mock_status_success):
    s = Submission(0)
    assert not s.success()
    assert not s.done()
    s.status()
    assert s.success()
    assert s.done()


def test_submission_failure(mock_status_failure):
    s = Submission(0)
    assert not s.success()
    assert not s.done()
    s.status()
    assert not s.success()
    assert s.done()
