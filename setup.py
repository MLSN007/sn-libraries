from setuptools import setup, find_namespace_packages

setup(
    name='sn-libraries',
    version='0.1.0',

    # Package discovery and structure
    packages=find_namespace_packages(where='src'),
    package_dir={'': 'src'},

    # Dependencies (with version specifiers for stability)
    install_requires=[
        'facebook-sdk~=3.1.0',  # Example version specifier
        'instagrapi~=2.1.2',
        'hikerapi',
        'requests',
        'beautifulsoup4~=4.12.3',
    ],

    # Metadata
    description="A set of Python libraries for automating Facebook and Instagram functions.",
    long_description=open('README.md').read(),  # Include README (if available)
    long_description_content_type='text/markdown',
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/MLSMIT/sn-libraries",

    # Additional details
    license="MIT",
    classifiers=[  # Classify your project for better discoverability on PyPI
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",  # Adjust as needed
    ],
    python_requires='>=3.7',  # Specify minimum Python version
    extras_require={
        'dev': ['pytest', 'coverage']
    },
    entry_points={
        'console_scripts': [
            'my_sn_tool = sn_libraries.tools:main',  # Define a command-line entry point
        ],
    },
)
