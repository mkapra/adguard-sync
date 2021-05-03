import setuptools

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="adguard-sync", # Replace with your own username
    version="1.0",
    author="Maximilian Kapra",
    author_email="maximilian@kapra.de",
    description="Sync dns rewrites on multiple adguards",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mkapra/adguard-sync",
    project_urls={
        "Bug Tracker": "https://github.com/mkapra/adguard-sync/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
)