import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="domain_stats", 
    version="1.0.0",
    author="MarkBaggett",
    author_email="lo127001@gmail.com",
    description="Malicious Domain Detection base on domain creation and first contact",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/markbaggett/domain_stats",
    license = "GNU General Public License v3 (GPLv3",
    packages=setuptools.find_packages(),
    install_requires = [
        'diskcache>=5.1.0',
        'Flask>=1.1.2',
        'gunicorn>=20.0.4',
        'publicsuffixlist>=0.7.6',
        'python-dateutil==2.8.1',
        'PyYAML==5.4',
        'rdap==1.1.0',
        'requests==2.25.1'
        ],
    include_package_data = True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points = {
        'console_scripts': ['domain-stats=domain_stats.launch:main',
                            'domain-stats-settings=domain_stats.settings:main',
                            'domain-stats-utils=domain_stats.utils:main'],
    },
    package_data={'domain_stats': ['data/*.*']}
)
