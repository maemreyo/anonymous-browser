from setuptools import setup, find_packages

setup(
    name="anonymous-browser",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "browserforge==1.2.1",
        "camoufox==0.4.9",
        "playwright==1.42.0",
    ],
) 