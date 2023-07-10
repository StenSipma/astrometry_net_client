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
            " $ python3 client.py [path/to/key/file] " "[file1 file2 file3 ... fileN]"
        )
        exit(-1)

    key_location, *files = argv[1:]

    log.info("Initializing client (loggin in)")
    # create client object with the session
    c = Client(key_location=key_location)

    log.info("Log in done")

    # set view field width in this range (15-30 arcmin)
    # WARNING: this can be very different for your application. Comment
    #          or remove if you are not sure!
    c.settings.set_scale_range(15, 30)

    # iterate over all the fits files in the specified diretory
    for filename in filter(is_fits, files):
        log.info("Uploading {}...".format(filename))

        try:
            # upload and wait for the result
            wcs = c.calibrate_file_wcs(filename)
        except OSError:
            log.info("File not found:", filename, "ignoring...")
            continue

        # when the result was successful
        if wcs is not None:
            with fits.open(filename) as hdul:
                # append resulting header (with astrometry) to existing header
                hdul[0].header.extend(wcs)

                # generate new filename to avoid overwriting
                write_filename = change_filename(filename)

                log.info("Writing to {}...".format(write_filename))
                hdul.writeto(write_filename)
        else:
            log.info("Failed")


if __name__ == "__main__":
    main()
