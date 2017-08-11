from setuptools import setup

with open('.version') as v:
    version = v.read()

with open('README.md') as r:
    readme = r.read()

with open('requirements.txt') as req:
    requirements = req.read().splitlines()

extras_require = {
    'postgres': ['asyncpg>=0.12.0']
}

setup(
    name='minoshiro',
    version=version,
    description=('An async Python3.6 library to search for anime, manga and'
                 'light novel using various web apis.'),
    long_description=readme,
    url='https://github.com/MaT1g3R/Roboragi',
    author='MaT1g3R, dashwav, Nihilate',
    license='MIT',
    packages=['minoshiro'],
    include_package_data=True,
    install_requires=requirements,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: AsyncIO',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English'
    ]
)
