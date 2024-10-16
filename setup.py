from setuptools import setup, find_packages

setup(
    name="sn-libraries",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "instagrapi~=2.1.2",
        "hikerapi",
        "requests",
        "beautifulsoup4~=4.12.3",
        # Add any other dependencies here
    ],
    # Other metadata can remain the same
)
