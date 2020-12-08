import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="domain_stats", 
    version="0.0.9",
    author="MarkBaggett",
    author_email="lo127001@gmail.com",
    description="Malicious Domain Detection base on domain creation and first contact",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/markbaggett/domain_stats",
    packages=setuptools.find_packages(),
    install_requires = ['requests','pyyaml', 'rdap', 'python-dateutil>2.7','publicsuffixlist','flask','gunicorn', 'diskcache'],
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
