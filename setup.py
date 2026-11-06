from setuptools import setup, find_packages

setup(
    name="facturae_optimus",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "lxml>=4.9.0",
        "python-dotenv>=0.19.0",
        "openpyxl>=3.0.0",
        "google-auth>=2.25.0",
        "google-auth-oauthlib>=1.2.0",
    ],
    python_requires=">=3.9",
)
