from setuptools import setup, find_packages

setup(
    name='herder',
    version="8.3",
    #description='',
    #author='',
    #author_email='',
    #url='',
    install_requires=['setuptools',
                      'pudge',
                      'buildutils',
                      'Pygments',
                      'Pylons>=0.9.6.1', 
                      'Babel',
                      'jsonlib',
                      'AuthKit>=dev',
                      'SQLAlchemy>=0.4.1',
                      'SQLAlchemyManager',
                      'pysqlite',
                      ],

    dependency_links=['http://authkit.org/svn/AuthKit/trunk/#egg=AuthKit-dev',
                      'svn://lesscode.org/pudge/trunk#egg=pudge-dev',
                      'svn://lesscode.org/buildutils/trunk#egg=buildutils-dev'
                      ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'herder': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors = {'herder': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', None),
    #        ('public/**', 'ignore', None)]},
    entry_points="""
    [paste.app_factory]
    main = herder.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
