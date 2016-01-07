from setuptools import setup

# These lines allow the version to be specified in Makefile.private.
import os
version = os.environ.get("MODULEVER", "0.0")

setup(
    install_requires=['numpy >= 1.7.0'],
    # We also require OpenCV but it's already in dls-python's `sys.path`.
    name='dls_barcode', version=version,
    description='Reading of Data Matrix-type barcodes',
    author='Kris Ward',
    author_email='kris.ward@diamond.ac.uk',
    packages=['dls_barcode'],
    zip_safe=False,
)
