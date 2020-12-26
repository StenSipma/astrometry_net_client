#!/usr/bin/env python3
import logging
import os
from sys import argv

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils import DAOStarFinder

from astrometry_net_client import Client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def find_sources(filename, detect_threshold=20, fwhm=3):
    with fits.open(filename) as f:
        data = f[0].data
    # find sources
    mean, median, std = sigma_clipped_stats(data, sigma=3.0, maxiters=5)
    daofind = DAOStarFinder(fwhm=fwhm, threshold=detect_threshold * std)
    sources = daofind(data - median)
    return sources


def enough_sources(filename, min_sources=5):
    sources = find_sources(filename)
    # terminate if not enough are found.
    # sources is None when no sources are found
    num_sources = len(sources) if sources is not None else 0
    if sources is None or num_sources <= min_sources:
        msg = "Not enough sources found: {} found, {} wanted."
        log.info(msg.format(num_sources, min_sources))
        return False
    log.info("Found {} sources".format(num_sources))
    return True


def is_fits(string):
    """
    Boolean function to test if the extension of the filename provided
    is either .fits or .fit (upper- or lowercase).

    Parameters
    ----------
    string: str
        (path to) filename to test

    Returns
    -------
    bool
    """
    string = string.upper()
    return string.endswith(".FITS") or string.endswith(".FIT")


def change_filename(filename):
    """
    Generate new filename to avoid overwriting an existing file
    change: ``path/to/file.fits``
    into  : ``path/to/file.astrom.fits``

    Parameters
    ----------
    filename: str
        The full path to the file which is to be changed

    Returns
    -------
    str
        The new path to the given filename
    """
    path, name = os.path.split(filename)
    res_filename = name.split(".")
    res_filename.insert(-1, "astrom")
    res_filename = ".".join(res_filename)
    return os.path.join(path, res_filename)


def main():
    if len(argv) < 3:
        print("Usage:")
        print(
            " $ python3 client.py [path/to/key/file] "
            "[file1 file2 file3 ... fileN]"
        )
        exit(-1)

    key_location, *files = argv[1:]

    log.info("Initializing client (loggin in)")
    c = Client(key_location=key_location)
    log.info("Log in done")

    # iterate over all the fits files in the specified diretory
    fits_files = filter(is_fits, files)

    # give the iterable of filenames to the function, which returns a
    # generator, generating pairs containing the finished job and filename.
    result_iter = c.upload_files_gen(
        fits_files, filter_func=enough_sources, filter_args=(10,)
    )

    for job, filename in result_iter:

        if not job.success():
            log.info("File {} Failed".format(filename))
            continue

        # retrieve the wcs file from the successful job
        wcs = job.wcs_file()
        with fits.open(filename) as hdul:
            # append resulting header (with astrometry) to existing header
            hdul[0].header.extend(wcs)

            write_filename = change_filename(filename)

            log.info("Writing to {}...".format(write_filename))
            try:
                hdul.writeto(write_filename)
            except Exception:
                log.error("File {} already exists.".format(write_filename))


if __name__ == "__main__":
    main()
