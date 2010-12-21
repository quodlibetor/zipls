from distutils.core import setup

from zipls import zipls

with open("README", 'r') as fh:
    long_desc = fh.read()

setup(name="zipls",
      version=zipls.VERSION,
      description="A script to zip your playlists",
      long_description=long_desc,
      author="Brandon W Maister",
      author_email="quodlibetor@gmail.com",
      url="http://bitbucket.org/quodlibetdor/zipls",
      packages=['zipls'],
      scripts=['scripts/zipls'],
      requires=['mutagen', 'argparse'],
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Operating System :: OS Independent",  # I think?
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: System :: Archiving",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Archiving :: Packaging",
        ]
      )
