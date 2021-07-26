from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    scripts=[],
    install_requires=[
        'kachery-client>=1.0.12',
        'hither>=0.7.0',
        'sortingview>=0.2.33'
    ]
)