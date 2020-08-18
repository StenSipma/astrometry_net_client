#!/usr/bin/env python3
import logging
import os
from sys import argv

from astropy.io import fits

from astrometry_net_client import Client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def is_fits(string):
    """
    Boolean function to test if the extension of the filename provided
    is either .fits or .fit (upper- or lowercase).
    """
    string = string.upper()
    return string.endswith(".FITS") or string.endswith(".FIT")


def change_filename(filename):
    """
    Generate new filename to avoid overwriting an existing file
    change: path/to/file.fits
    into  : path/to/file.astrom.fits
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
    result_iter = c.upload_files_gen(fits_files)

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
