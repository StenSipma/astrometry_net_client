import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
        name='astrometry_net_client',
        version='0.1',
        author="Sten Sipma",
        author_email='sten.sipma@ziggo.nl',
        description='A Python interface for the Astrometry.net API.',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/StenSipma/astrometry_net_client',
        packages=['astrometry_net_client']
        )
