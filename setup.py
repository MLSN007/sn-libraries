from setuptools import setup, find_packages

setup(
    name='sn-libraries',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'facebook-sdk',
        'instagrapi',
        'hikerapi',
        'requests',
        'beautifulsoup4',
    ],
    description="A set of Python libraries for automating Facebook and Instagram functions.",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/MLSMIT/sn-libraries", 
    license="MIT", # or your chosen license
)
