from setuptools import setup, find_packages

setup(
    name="social_media_api_project",  # Your package name
    version="0.1.0",  # Your package version
    packages=find_packages(),
    install_requires=[
        "facebook-sdk",
        # Add other dependencies here
    ],
    # ... other metadata (description, author, etc.)
)
