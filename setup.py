import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sli",
    version="0.0.0.0dev",
    author="Andrew Mallory",
    author_email="amallory@paloaltonetworks.com",
    description="A tool for working with Palo Alto Networks skillets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://paloaltonetworks.com",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'skilletlib',
        'panforge',
        'click',
        'jinja2==3.0.1',
        'pycryptodome',
        'paramiko',
        'requests',
        'xlsxwriter',
        'asyncssh',
    ],
    entry_points={
        'console_scripts': [
            'sli= sli.cli:cli',
        ]
    },
)
