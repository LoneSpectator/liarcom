# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='liarcom',
    version='1.0.0',
    description=(
        '第三方Drcom登陆器'
    ),
    long_description=open('README.rst', 'rb').read().decode('utf8'),
    author='高铭',
    author_email='gaomingshsf@hotmail.com',
    maintainer='高铭',
    maintainer_email='gaomingshsf@hotmail.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/Everyb0dyLies/liarcom',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: Chinese (Simplified)',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=[
        'PyQt5'
    ]
)

