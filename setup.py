import setuptools

with open("README.rst", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="astrometry_net_client",
    version="0.2",
    author="Sten Sipma",
    author_email="sten.sipma@ziggo.nl",
    description="A Python interface for the Astrometry.net API.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/StenSipma/astrometry_net_client",
    packages=["astrometry_net_client"],
    install_requires=["astropy", "requests"],
)
