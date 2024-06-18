from setuptools import setup, find_packages

setup(
    name='sn-libraries',  # Replace with your project's name
    version='0.1.0',  # Replace with your project's version
    packages=find_packages(where='src'),  # Find packages in the 'src' directory
    package_dir={'': 'src'},  # Specify the root package directory
    install_requires=[
        # List any external dependencies here
        'requests',
        'beautifulsoup4',
        # ... other dependencies
    ],
)
