try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='tower',
    version="8.2-dev",
    #description='',
    #author='',
    #author_email='',
    #url='',
    install_requires=['setuptools', 
                      "Pylons>=0.9.6.1", 
                      'Babel',
                      'jsonlib',
                      ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'tower': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'tower': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    [paste.app_factory]
    main = tower.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
