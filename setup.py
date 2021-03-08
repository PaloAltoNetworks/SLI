import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sli",
    version="##_VERSION_##",
    author="Andrew Mallory",
    author_email="amallory@paloaltonetworks.com",
    description="Document generation library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://paloaltonetworks.com",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'skilletlib',
        'panforge',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'sli= sli.cli:cli',
        ]
    },
)
