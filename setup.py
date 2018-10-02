from setuptools import setup

setup(
    name='routes-1846',
    version='0.1',
    packages=['routes1846'],
    package_data={"routes1846": ["data/base-board.json", "data/tiles.json"]},
    include_package_data=True
)
