==========
Zip Please
==========

A script to help you zip playlists.

Homepage: http://bitbucket.org/quodlibetor/zipls

.. contents::


Installation
============

To make this work best you want to have pip
(http://pypi.python.org/pypi/pip) installed, although technically it
is possible to install it without it.

From a terminal, (Terminal.app if you're on a Mac, or whatever turns
you on) after installing pip, do::

    sudo pip install argparse mutagen zipls

That should do it. If it doesn't, please contact_ me.

Usage
=====

Users
-----

Graphical Use
~~~~~~~~~~~~~

After installation there should be a program ``zipls`` that you can
run. Run it.

That is to say that, in general, if you run zipls without any
arguments it will give you a gui.

If you run it from a command line with playlist files as arguments,
you can give it the ``-g`` switch to make it still run in graphical
mode. All arguments given to the command line should still apply even
if run in graphics mode.

Command Line
~~~~~~~~~~~~

Typically::

    zipls PLAYLIST.pls

that'll generate a zip file PLAYLIST.zip with a folder PLAYLIST inside
of it with all the songs pointed to by PLAYLIST.pls.

And of course::

    zipls --help

works. (Did you think I was a jerk?)

Programmers
-----------

Basically all you care about is the ``Songs`` class from zipls. It
takes a path, or list of paths, to a playlist and knows how to zip
them::

    from zipls import Songs

    songs = Songs("path/to/playlist.m3u")

    # __init__ just goes through add():
    songs.add("path/to/another/playlist.xspf")
    # lists of paths also work:
    songs.add(['another.pls', 'something/else.m3u'])

    songs.zip_em('path/to/zipcollection')

Extending
~~~~~~~~~

First of all, just email me with an example of the playlist that you
want zipls to parse and I'll do it. But if you want to *not*
monkey-patch it:

If you want to add a new playlist format with extension EXT: subclass
``Songs`` and implement a function ``_songs_from_EXT(self,
'path/to/pls')`` that expects to receive a path to the playlist.

Similarly, if you want to add audio format reading capabilities
subclass ``Song`` (singular) and create a ``_set_artist_from_EXT``, where
EXT is the extension of the music format you want to add. You'll also
need to initialize ``Songs`` with your new song class.

So if I wanted to add ``.spf`` playlists and ``.mus`` audio::

    class MusSong(zipls.Song):
        def _set_artist_from_mus(self):
            # and then probably:
            from mutagen.mus import Mus
            self.artist = Mus(self.path)['artist'][0]
    class SpfSongs(zipls.Songs):
        def _songs_from_spf(self, playlist):
            # add songs

    songs = SpfSongs('path/to/playlist', MusSong)


Works With
----------

playlist formats:

    - .pls
    - .xspf
    - .m3u

A variety of common audio formats. (Ogg Vorbis, MP3/4, FLAC...)
Basically everything supported by mutagen_ should work

.. _contact:

Contact and Copying
===================

My name's Brandon, email me at quodlibetor@gmail.com, and the project
home page is http://bitbucket.org/quodlibetor/zipls .

Basically do whatever you want, and if you make something way better
based on this, lemme know.

Copyright (C) 2010 Brandon W Maister quodlibetor@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. _mutagen: https://code.google.com/p/mutagen/
