import setuptools

with open("README.rst", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="astrometry_net_client",
    version="0.3.1",
    author="Sten Sipma",
    author_email="sten.sipma@ziggo.nl",
    description="A Python interface for the Astrometry.net API.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/StenSipma/astrometry_net_client",
    packages=["astrometry_net_client"],
    install_requires=["astropy", "requests"],
    keywords="astronomy astrometry client coordinates wcs api",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
)
