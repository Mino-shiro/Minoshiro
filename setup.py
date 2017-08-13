from setuptools import setup, find_packages

with open('.version') as v:
    version = v.read()

with open('README.md') as r:
    readme = r.read()

with open('requirements.txt') as req:
    requirements = req.read().splitlines()

extras_require = {
    'postgres': ['asyncpg>=0.12.0']
}

package_data = {
    '': ['LICENSE', 'README.md', 'COPYING', 'requirements.txt', '.version']
}

setup(
    name='minoshiro',
    version=version,
    description=('An async Python3.6 library to search for anime, manga and'
                 'light novel using various web apis.'),
    long_description=readme,
    url='https://github.com/Mino-shiro/Minoshiro',
    author='MaT1g3R, dashwav',
    license='MIT',
    packages=find_packages(exclude=['tests', 'docs']),
    include_package_data=True,
    package_data=package_data,
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
