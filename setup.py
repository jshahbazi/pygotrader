from setuptools import setup, find_packages

#with open('README.rst', encoding='UTF-8') as f:
#    readme = f.read()

setup(
    name="pygotrader",
    version="0.1.0",
    description="Algorithmic cryptocurrency trader",
    #long_description=readme,
    #install_requires=[''],
    packages=find_packages('src'),
    package_dir={'':'src'},
)
