import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="inline-calendar",
    version="0.1",
    author="Egor birdi7",
    author_email="egor.birdi7@gmail.com",
    description="An inline calendar for telegram using aiogram",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Birdi7/Inline-calendar-for-telegram",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
