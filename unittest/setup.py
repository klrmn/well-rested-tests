from setuptools import setup

setup(
    name='well_rested_unittest',
    version='0.01',
    description='unittest2 extension for use with well-rested-tests-server',
    author='Leah Klearman',
    author_email='lklrmn@gmail.com',
    url='https://github.com/klrmn/well-rested-tests/unittest',
    install_requires=['unittest2==1.0.0', 'testtools==1.7.1',
                      'requests', 'six', 'testresources', 'fixtures',],
    py_modules=['well_rested_unittest'],
    entry_points={
        'console_scripts': [
            'wrtest = well_rested_unittest:main',
            'wrt = well_rested_unittest:wrt',
            'otest = well_rested_unittest:otest',
        ],
    },
    license='Mozilla Public License 2.0 (MPL 2.0)',
    keywords='unittest, well-rested-tests',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7'])
