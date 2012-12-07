import os
from setuptools import setup

from route53_transfer import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='route53-transfer',
      version=__version__,
      description='Backup and restore Route53 zones, or transfer between AWS accounts.',
      long_description=read('README.rst'),
      url='http://github.com/RisingOak/route53-transfer',
      author='Cosmin Stejerean',
      author_email='cosmin@offbytwo.com',
      license='Apache License 2.0',
      packages=['route53_transfer'],
      scripts=['bin/route53-transfer'],
      tests_require=open('test-requirements.txt').readlines(),
      install_requires=open('requirements.txt').readlines(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Utilities'
        ]
     )
