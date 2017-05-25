from setuptools import setup, find_packages


setup(
    name="ish",
    version='0.1',
    url='https://github.com/calston/ish',
    license='MIT',
    description="Interpipe Shell",
    author='Colin Alston',
    author_email='colin.alston@gmail.com',
    packages=find_packages(),
    scripts=['bin/ish'],
    include_package_data=True,
    install_requires=[
        'requests',
        'BeautifulSoup4',
        'colored'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
)
