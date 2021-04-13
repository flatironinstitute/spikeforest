from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    scripts=[],
    install_requires=[
        'kachery-p2p>=0.8.20',
        'hither>=0.5.18'
    ]
)