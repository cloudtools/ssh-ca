import glob
from setuptools import setup

setup(
    name='ssh-ca',
    version='0.3.1',
    description="SSH CA utilities",
    author="Bob Van Zant",
    author_email="bob@veznat.com",
    maintainer="Mark Peek",
    maintainer_email="mark@peek.org",
    url="https://github.com/cloudtools/ssh-ca",
    license="New BSD license",
    packages=['ssh_ca'],
    scripts=glob.glob('scripts/*'),
    use_2to3=True,
)
