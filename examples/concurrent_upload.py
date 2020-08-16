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
    result_iter = c.upload_files_gen(fits_files)

    for job, filename in result_iter:

        if not job.success():
            log.info("File {} Failed".format(filename))
            continue

        wcs = job.wcs_file()
        with fits.open(filename) as hdul:
            # append resulting header (with astrometry) to existing header
            hdul[0].header.extend(wcs)

            # generate new filename to avoid overwriting
            path, name = os.path.split(filename)
            res_filename = name.split(".")[-1]
            res_filename.insert(-1, "astrom")
            write_filename = os.path.join(path, res_filename)

            log.info("Writing to {}...".format(write_filename))
            hdul.writeto(write_filename)


if __name__ == "__main__":
    main()
