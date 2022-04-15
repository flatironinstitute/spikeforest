from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    scripts=[],
    install_requires=[
        'kachery-client>=1.2.0',
        'kachery-cloud>=0.1.4',
        'sortingview>=0.7.3',
        'spikeinterface>=0.93.0'
    ]
)