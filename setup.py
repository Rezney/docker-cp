from setuptools import setup

setup(name='docker-cp',
    version='0.1',
    description='Tool for copying from and to a container',
    license='MIT',
    packages=['dockercp'],
    install_requires=['docker'],
    entry_points={
        'console_scripts': ['docker-cp=dockercp.dockercp:main'],
    })
