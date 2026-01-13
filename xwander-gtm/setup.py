"""Setup for xwander-gtm plugin"""

from setuptools import setup, find_packages

setup(
    name='xwander-gtm',
    version='1.0.0',
    description='Google Tag Manager operations plugin for xwander platform',
    author='Xwander Growth Team',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'google-api-python-client>=2.0.0',
        'google-auth>=2.0.0',
        'google-auth-oauthlib>=0.5.0',
        'google-auth-httplib2>=0.1.0',
        'PyYAML>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'xw-gtm=xwander_gtm.cli:cli',
        ],
    },
    python_requires='>=3.8',
)
