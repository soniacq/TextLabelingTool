from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="text-labeling",
    version="0.1.2",
    author="Sonia Castelo",
    author_email="s.castelo@nyu.edu",
    description="Visual Text Labeling tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/soniacq/TextLabelingTool",
    packages=find_packages(exclude=['js', 'node_modules']),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "python-dateutil",
        "numpy",
        "scipy",
        "scikit-learn",
        "notebook",
        "pandas",
        "nltk",
        "spacy",
        "modAL"
    ]
)
