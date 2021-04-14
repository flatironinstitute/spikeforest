from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    scripts=[],
    install_requires=[
        'kachery-p2p>=0.8.21',
        'hither>=0.5.18',
        'labbox-ephys>=0.5.13'
    ]
)