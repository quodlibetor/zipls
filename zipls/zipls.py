#!/usr/bin/env python

# This program is licenses under the LGPL, you might have received a
# copy of it with this.
#
# Give this to whomever you want, include this notice, and if you make
# it better maybe let me know?
#
# bwm :: quodlibetor@gmail.com
#
# Oh and if it explodes it's not my fault.


"""Stick songs from playlists into a zip file.

Currently supports .pls, .m3u, and .xspf playlists.
"""

from __future__ import with_statement

import argparse
import os
import shutil
import sys
from zipfile import ZipFile
from xml.dom import minidom
from HTMLParser import HTMLParser

MUTAGEN = False
try:
    from mutagen.easyid3 import EasyID3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
except Exception:
    pass
else:
    MUTAGEN = True

VERSION = "0.1"

class Song(object):
    _warned_about_no_mutagen = False
    def __init__(self, path,
                 title=None,
                 artist=None,
                 ext=None):
        """Needs at the very least a path to a file.

        Pretty dumb about setting the artist, too.
        """
        if not os.path.exists(path):
            raise OSError("Does not Exist")
        self.path = path
        if title is not None:
            self.title = title
        else:
            self._set_title()
        if ext is None:
            self._set_ext_from_path(path)
        else:
            self.ext = ext
        self.artist = None
        if artist is None:
            self.set_artist_from_tag()
        else:
            self.artist = artist

    def _set_ext_from_path(self, path):
        self.ext = path[path.rfind('.')+1:]

    def __str__(self):
        name = ""
        if self.artist is not None:
            name += self.artist + " - "
        return name + self.title

    def _set_title(self):
        # should really grab the title from audio info, but this is
        # also only necessary for non-extended m3u, probably, so:
        name, ext  = os.path.splitext(self.path)
        self.title = os.path.basename(name)

    def set_artist_from_tag(self):
        if MUTAGEN:
            try:
                getattr(self, "_set_artist_from_%s" % self.ext.lower())()
            except AttributeError:
                print "Could not get artist name for '%s'" % self.title
        else:
            if not Song._warned_about_no_mutagen:
                print >>sys.stderr, "No ID3 tag library installed, so can't extract artist from mp3 tag.\n"\
                    "(install mutagen)"
                Song._warned_about_no_mutagen = True

    def _set_artist_from_mp3(self):
        audio = EasyID3(self.path)
        self.artist = audio['artist'][0].strip()

    def _set_artist_from_flac(self):
        audio= FLAC(self.path)
        self.artist = audio['artist'][0].strip()

    def _set_artist_from_m4a(self):
        self._set_artist_from_mp4()

    def _set_artist_from_mp4(self):
        audio = MP4(self.path)
        self.artist = audio['\xa9ART'][0].strip()

    def _set_artist_from_ogg(self):
        # it's *probably* vorbis:
        try:
            self._set_artist_from_ogv()
        except:
            print "couldn't get artist info for %s" % self.title
            self.artist = None

    def _set_artist_from_ogv(self):
        audio = OggVorbis(self.path)
        self.artist = audio['artist'][0]

class Songs(object):
    """The main playlist container.

    Holds a list of `Song`s, you can `add` playlists or `Song`s, and
    you can `copy_em` or `zip_em`.
    """
    def __init__(self, playlists, song_class=Song):
        """Construct a list of songs from playlists

        Argument:
        `playlists`: a string (or list of strings) that are paths to playlist files.
        """
        self.Song = song_class
        self.songs = list()
        if hasattr(playlists, "__iter__"):
            for playlist in playlists:
                self.add(playlist)
        else:
            self.add(playlists)

    def add(self, playlist):
        """Add a playlist to the songlist

        Argument:
        `playlist`: a path to a playlist file.
        """
        def _getext(path):
            return path[path.rfind('.')+1:]

        setter = getattr(self, "_songs_from_%s" % _getext(playlist))
        setter(os.path.expanduser(playlist))

    def zip_em(self, target, inner_dir=None):
        """Create A ZipFile.

        Arguments:
        `target`: the name of the zipfile. If it does not end in
                  '.zip' that will be added.
        `inner_dir`: the name of a directory to put everything into
                     inside of the zip. Defaults to basename(target).
        """
        target = os.path.expanduser(target)
        if not target.endswith('.zip'):
            target += '.zip'
        if inner_dir is None:
            inner_dir = os.path.basename(os.path.splitext(target)[0])
        try:
            zf = ZipFile(target, 'w')
            for i, song in enumerate(self.songs):
                print "zipping ", song
                zf.write(song.path,
                         os.path.join(inner_dir,
                                      ('%02d - %s.%s' % (i+1,
                                                         song,
                                                         song.ext))))
        finally:
            zf.close()

    def copy_em(self, target):
        target = os.path.expanduser(target)
        if not os.path.exists(target):
            os.makedirs(target)
        elif not os.path.isdir(target):
            sys.exit("Trying to copy files into non-directory. Quitting")

        for i, song in enumerate(self.songs):
            shutil.copy(song.path,
                        os.path.join(target,
                                     "%02d - %s.%s" % (i+1,
                                                       song,
                                                       song.ext)))

    def __iter__(self):
        for song in self.songs:
            yield song

    def _songs_from_pls(self, playlist):
        root = os.path.dirname(playlist)
        with open(playlist, 'r') as fh:
            path = ""
            title = ""
            for line in fh:
                line = line.rstrip()
                if '=' in line and line.startswith("File"):
                    path = os.path.join(root, line.split('=')[1])
                elif '=' in line and line.startswith("Title"):
                    title = line.split('=')[1]
                    try:
                        self.songs.append(self.Song(path, title))
                    except OSError:
                        print "could not add %s" % path

    def _songs_from_xspf(self, playlist):
        def get_tag(element, tagname):
            h = HTMLParser()
            return h.unescape(element.getElementsByTagName(tagname)[0].firstChild.toxml())
        root = os.path.dirname(playlist)
        dom = minidom.parse(playlist)
        for e in dom.getElementsByTagName('track'):
            title = get_tag(e, 'title')
            path = os.path.join(root, get_tag(e, 'location'))
            try:
                artist = get_tag(e, 'creator')
            except:
                artist = None
            try:
                self.songs.append(self.Song(path, title, artist))
            except OSError:
                print "could not add %s" % path


    def _songs_from_m3u(self, playlist):
        root = os.path.dirname(playlist)
        artist = title = path = time = None
        with open(playlist, 'r') as fh:
            start = fh.readline().strip()
            if start == '#EXTM3U':
                for line in fh:
                    line = line.strip()
                    if line.startswith('#EXTINF:'):
                        time, title = line[8:].split(',', 1)
                        if ' - ' in title:
                            artist, title = title.split(' - ', 1)
                        else:
                            artist = None
                    elif not line.startswith('#') and len(line) > 0:
                        path = os.path.join(root, line)
                        try:
                            self.songs.append(self.Song(path, title,
                                                        artist=artist))
                        except OSError:
                            print "could not add %s" % path
                        artist = title = path = None
            else:
                fh.seek(0)
                for line in fh:
                    try:
                        self.songs.append(self.Song(line.strip()))
                    except OSError:
                        print "could not add %s" % path

def parse_args():
    parser = argparse.ArgumentParser(description="write playlists to a zip file",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="""Typically:
  All you need to do is: `zipls.py awesome.pls`.

  This will create a zip file "awesome.zip" with a folder inside
  of it named "awesome" with all of the songs inside of that. Like so:

      awesome.zip
          ->  awesome/
                ->  1 - Song1.mp3
                ->  2 - Song2.flac
                ->  etc...
p""")
    parser.add_argument('playlist', nargs='+',
                        help="\nthe playlist files to use to decide where to get the music from\n")
    parser.add_argument('-t', '--target', help="The file to write the music to.\n"
                        "(Defaults to the (first) playlist filename, with .zip instead of .pls)\n")
    parser.add_argument('-f', '--folder-name',
                        help="An internal folder name to put the music files inside of.\n"
                        "(Defaults to the name of the archive, minus 'zip'.)\n")
    parser.add_argument('-c', '--copy', action='store_true', default=False,
                        help="\nCopy files into a directory instead of zipping them.\n"
                        "(Target is a destination folder to copy them in this case.\n"
                        "Creates the folder if it doesn't exist)")

    return parser.parse_args()

def main(args):
    songs = Songs(args.playlist)
    if not args.target:
        target = os.path.splitext(os.path.basename(args.playlist[0]))[0]
        args.target = target
    if args.copy:
        songs.copy_em(args.target)
    else:
        songs.zip_em(args.target, args.folder_name)

if __name__ == "__main__":
    try:
        args = parse_args()
        main(args)
    except KeyboardInterrupt:
        print "\rCaught keyboard interrupt. Giving up without Cleaning up."
