from __future__ import unicode_literals

from setuptools import find_packages, setup


setup(
    name='indico-plugin-vc-zoom',
    version='2.3-dev',
    description='Zoom video-conferencing plugin for Indico',
    url='https://github.com/indico/indico-plugins',
    license='MIT',
    author='Giovanni Mariano (ENEA) and Indico Team (CERN)',
    author_email='indico-team@cern.ch',
    packages=find_packages(),
    zip_safe=False,
    platforms='any',
    include_package_data=True,
    install_requires=[
        'indico>=2.3.2.dev0',
        'PyJWT<2'
    ],
    classifiers=[
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
    entry_points={'indico.plugins': {'vc_zoom = indico_vc_zoom.plugin:ZoomPlugin'}}
)