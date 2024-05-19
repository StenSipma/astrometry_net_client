#!/usr/bin/env python3
import argparse
import logging
import textwrap
from pathlib import Path

from astropy.io import fits

from astrometry_net_client import Client, Settings

# These lines set up logging
FMT = "[%(asctime)s] %(levelname)-8s |" " %(funcName)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=FMT)
log = logging.getLogger(__name__)


def is_fits(filename: Path):
    """
    Boolean function to test if the extension of the filename provided
    is either .fits or .fit (upper- or lowercase).

    Parameters
    ----------
    filename: Path

    Returns
    -------
    bool
    """
    end = filename.suffix.upper()
    return end.endswith(".FITS") or end.endswith(".FIT")


def main():
    # Commandline argument parsing
    args = parse_arguments()

    s = Settings()
    if args.plate_scale:
        s.set_scale_estimate(
            args.plate_scale, args.plate_scale_err, unit="arcsecperpix"
        )
    if args.plate_scale_range:
        s.set_scale_range(
            args.plate_scale_range[0], args.plate_scale_range[1], unit="arcsecperpix"
        )
    if args.fov_width:
        s.set_scale_estimate(args.fov_width, args.fov_width_err, unit="arcminwidth")
    if args.fov_width_range:
        s.set_scale_estimate(args.fov_width, args.fov_width_err, unit="arcminwidth")

    log.info("Initializing client (logging in)")
    c = Client(api_key=args.key, key_location=args.key_location, settings=s)
    log.info("Log in done")

    # Prepare the output directory
    output_dir = Path(args.output).absolute()
    if output_dir.exists():
        log.warning(f"Output directory: '{output_dir}' already exists")
    else:
        log.info(f"Output directory '{output_dir}' does not exist, creating...")
        output_dir.mkdir(parents=True)

    DO_OVERWRITE = args.overwrite_solve
    if DO_OVERWRITE:
        log.warning(
            "The overwrite-solve is ON, files that exists in the output directory may be overwritten."
        )

    files = [Path(f) for f in args.fits_file]
    # iterate over all the fits files in the specified diretory, ignore all files
    # which are not fits files.
    fits_files = filter(is_fits, files)

    # give the iterable of filenames to the function, which returns a
    # generator, generating pairs containing the finished job and filename.
    result_iter = c.upload_files_gen(fits_files)

    # Iterate over the jobs when they are finished
    for job, filename in result_iter:

        if not job.success():
            log.info("File {} Failed".format(filename))
            continue

        # If the job was successful, we want to get the new wcs file from astrometry.net
        wcs = job.wcs_file()
        # Then we want to add the resulting WCS to the existing file, and write in a
        # new location
        with fits.open(filename) as hdul:
            hdul[0].header.extend(wcs)

            write_filename = output_dir / filename.name

            log.info("Writing to {}...".format(write_filename))
            try:
                hdul.writeto(write_filename, overwrite=DO_OVERWRITE)
            except OSError:
                log.error("File {} already exists.".format(write_filename))


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="anc_upload.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
                Description
                -----------
                Upload a list of FITS files to find a WCS using nova.astrometry.net, and put the solved files (original file + extended with WCS) in the 'output' directory.
                REQUIRES an account on https://nova.astrometry.net to get an api key. See: https://nova.astrometry.net/api_help

                Setting some basic settings is supported via command line arguments, but for more specific Settings edit the script!

                Examples
                --------
                A very basic example is:
                    $ anc_upload.py --key-location ./key file1.fits file2.fits ./dir_with_files/*

                This assumes you have the api key in the current directory in a file named 'key'.
                It will upload 'file1.fits', 'file2.fits' and all fits files in the 'dir_with_files' directory.

                Another example, setting the plate scale to be between 0.56 and 1.75 arcsec/pixel:
                    $ anc_upload.py --key-location ./key --plate-scale-range 0.56 1.75 file1.fits file2.fits file3.fits
                """
        ),
        epilog="Script and library made by Sten Sipma. For comments and suggestions, please make an issue on Github at https://github.com/StenSipma/astrometry_net_client",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="DIRECTORY",
        default="./anc_output",
        help="Directory in which to put the solved files. Default='./anc_output'",
    )
    parser.add_argument(
        "fits_file", type=str, nargs="+", help="One or more FITS files to upload"
    )
    parser.add_argument(
        "--overwrite-solve",
        action="store_true",
        help="If a file with a similar name already exists in the 'output' directory, overwrite it. Default: False",
    )

    # One of the methods to specify the key:
    key_group = parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument(
        "--key-location",
        metavar="FILE",
        type=str,
        help="Plaintext file in which the nova.astrometry API key is stored",
    )
    key_group.add_argument(
        "--key",
        type=str,
        help="Specify the nova.astrometry API key. NOTE: that the safer option is '--key-location'",
    )

    # Settings
    scale_group = parser.add_argument_group(
        title="Settings",
        description="Some options for basic settings / hints to give to Astrometry.net",
    )
    scale_group.add_argument(
        "--plate-scale",
        metavar="FLOAT",
        type=float,
        help="Unit: arcsec / pixel. Give an estimate for the plate scale of your instrument. Astrometry.net will look around: plate-scale within plate-scale-err of that value",
    )
    scale_group.add_argument(
        "--plate-scale-err",
        metavar="FLOAT",
        type=float,
        default=10,
        help="Specify the range (percent) around the 'plate-scale' value for Astrometry.net to search for. Default=10 percent",
    )
    scale_group.add_argument(
        "--plate-scale-range",
        metavar="FLOAT",
        nargs=2,
        type=float,
        help="Unit: arcsec / pixel. Same as 'plate-scale' but instead gives the range explicitiy (LOWER, UPPER)",
    )

    scale_group.add_argument(
        "--fov-width",
        metavar="FLOAT",
        type=float,
        help="Unit: arcmin. Give an estimate for the FoV width of the instrument. Astrometry.net will look around: fov-width within fov-width-err of that value.",
    )
    scale_group.add_argument(
        "--fov-width-err",
        metavar="FLOAT",
        type=float,
        default=10,
        help="Specify the range (percent) around the 'fov-width' value for Astrometry.net to search for. Default=10 percent",
    )
    scale_group.add_argument(
        "--fov-width-range",
        metavar="FLOAT",
        nargs=2,
        type=float,
        help="Unit: arcmin. Same as 'fov-width' but instead gives the range explicitiy (LOWER, UPPER)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
