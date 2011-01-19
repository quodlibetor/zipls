#!/usr/bin/env python

# This program is licenses under the LGPL, you might have received a
# copy of it with this.
#
# Give this to whomever you want, include this notice, and if you make
# it better maybe let me know?
#
# bwm :: quodlibetor@gmail.com
#
# project home page: http://bitbucket.org/quodlibetor/zipls
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
    from mutagen.oggflac import OggFLAC
except ImportError:
    pass
else:
    MUTAGEN = True

VERSION = "0.1.1a"

#######################################################################
# Core Classes

class Song(object):
    _warned_about_no_mutagen = False
    def __init__(self, path,
                 title=None,
                 artist=None,
                 ext=None,
                 track_number=None,
                 album=None,
                 length=None):
        """Needs at the very least a path to a file.

        Pretty dumb about setting the artist, too.
        """
        if not os.path.exists(path):
            raise OSError("Does not Exist")
        self.path = path

        self.title = title
        if self.title is None:
            self._set_title()

        self.ext = ext
        if self.ext is None:
            self._set_ext_from_path(path)

        self.artist = artist
        if self.artist is None:
            self.set_artist_from_tag()

        self.track_number = track_number
        if self.track_number is not None:
            self.track_number = int(self.track_number)
        self.album = album
        self._length = length

    def __str__(self):
        name = ""
        if self.artist is not None:
            name += self.artist + " - "
        return name + self.title

    def __format__(self, fmt):
        """Return a string for the song.

        Accepts any of the known song attributes in curly braces, and
        puts the song in there.

        Known tags include path, title, artist, ext, track_number, album

        >>> song = Song(path="test/test-data/Sample.mp3",
        ...             artist="Someone Special",
        ...             track_number="1")
        >>> format(song, "{track_number} - {artist}.{ext}")
        '1 - Someone Special.mp3'

        Full string.format stuff should work, too:

        >>> format(song, "{track_number:04}")
        '0002'
        """
        def _read_tag(fmt):
            "return (tag, fmt)"
            orig = fmt
            string = ""
            while True and fmt:
                if fmt[0] == '}':
                    fmt = fmt[1:]
                    return string, fmt
                elif fmt[0] == ":":
                    while fmt[0] != '}':
                        fmt = fmt[1:]
                else:
                    string += fmt[0]
                    fmt = fmt[1:]
            raise RuntimeError("Unclosed tag in format, originally: %s" %
                               orig)

        ################################################################
        # format!
        original = fmt
        tags = list()
        while fmt:
            if fmt[0] == '{':
                tag, fmt = _read_tag(fmt[1:])
                tags.append(tag)
            else:
                fmt = fmt[1:]
        try:
            attrs = dict((tag, getattr(self, tag)) for tag in tags)
        except AttributeError as e:
            sys.exit("Can't format like you want because: %s" % e)

        return original.format(**attrs)

    def __eq__(self, other):
        return self.path == other.path and \
            self.title == other.title and \
            self.artist == other.artist and \
            self.ext == other.ext and \
            self.album == other.album
            # don't care about track numbers, though?

    @property
    def length(self):
        return (self._length if self._length
                else -1)

    def _set_ext_from_path(self, path):
        self.ext = path[path.rfind('.')+1:]
        if len(self.ext) == len(path):
            # since rfind returns -1 on error
            raise OSError("Couldn't set extension")

    def _set_title(self):
        # should really grab the title from audio info, but this is
        # also only necessary for non-extended m3u, probably, when
        # called by Songs which does all the heavy-duty parsing, so:
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

    ################################################################
    # Backend-specific artist setters
    def _set_artist_from_mp3(self):
        audio = EasyID3(self.path)
        self.artist = audio['artist'][0].strip()

    def _set_artist_from_flac(self):
        audio= FLAC(self.path)
        self.artist = audio['artist'][0].strip()

    def _set_artist_from_m4a(self):
        # mutagen.m4a is deprecated
        self._set_artist_from_mp4()

    def _set_artist_from_mp4(self):
        audio = MP4(self.path)
        self.artist = audio['\xa9ART'][0].strip()

    def _set_artist_from_ogg(self):
        # it's *probably* vorbis:
        try:
            self._set_artist_from_ogv()
        except:
            # maybe flac?
            try:
                self._set_artist_from_ogf()
            except:
                print "couldn't get artist info for %s" % self.title
                self.artist = None

    def _set_artist_from_ogv(self):
        audio = OggVorbis(self.path)
        self.artist = audio['artist'][0].strip()

    def _set_artist_from_ogf(self):
        audio = OggFLAC(self.path)
        self.artist = audio['artist'][0].strip()

class DoNotExport(Exception):
    "Exception raised by Songs.to_none"

class Songs(object):
    """The main playlist container.

    Holds a list of `Song`s, you can `add` playlists or `Song`s, and
    you can `copy_em` or `zip_em`.
    """
    def __init__(self, playlists,
                 export_type=None, song_class=Song):
        """Construct a list of songs from playlists

        Argument:
        `playlists`: a string (or list of strings) that are paths to playlist files.
        `song_class`: a Song-compatible class to use instead of the built-in.
        """
        self.Song = song_class
        self.songs = list()
        self.add(playlists)
        self.export_type = export_type
        if export_type is None:
            self.export_type = os.path.splitext(playlists[0])[1:]

    def add(self, addend):
        """Add a addend to the songlist

        These should all work:

        >>> songs.add("another/playlist").add("yet/another")
        >>> songs.add(Song("path/to/song.mp3"))
        >>> songs.add([song1, song2, song3])

        Argument:
        `addend`: some thing(s) to add to the songs.
                  Can be a (list of) Song(s) or paths to playlists.
                  Each element of a list should be the same kind of
                  thing, though.

        Returns:
        `self`: for chaining! Although I don't know why you would.
        """
        def _getext(path):
            return path[path.rfind('.')+1:]

        if hasattr(addend, "__iter__"):
            try:
                for playlist in addend:
                    setter = getattr(self, "_songs_from_%s"
                                     % _getext(playlist))
                    setter(os.path.expanduser(playlist))
            except AttributeError:
                if isinstance(addend[0], Song):
                    self.songs.extend(addend)
                else:
                    raise Exception("I don't know what to do with %s"
                                    % repr(addend))
        else:
            try:
                setter = getattr(self, "_songs_from_%s"
                                 % _getext(addend))
                setter(os.path.expanduser(addend))
            except AttributeError:
                if isinstance(addend, Song):
                    self.songs.extend(addend)
                else:
                    raise Exception("I don't know what to do with %s"
                                    % repr(addend))

        return self

    def zip_em(self, target, inner_dir=None,
               fmt="{track_number:02} - {artist} - {title}.{ext}"):
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
            export_func = getattr(self, "to_%s"%self.export_type)
            try:
                zf.writestr("{0}.{1}".format(inner_dir,
                                             self.export_type) ,
                            export_func(root=inner_dir,
                                        fmt=fmt),
                            )
            except DoNotExport:
                pass
            for i, song in enumerate(self.songs):
                print "zipping ", song
                zf.write(song.path,
                         os.path.join(inner_dir,
                                      format(song, fmt)))
        finally:
            zf.close()

    def copy_em(self, target,
                fmt="{track_number:02} - {artist} - {title}.{ext}"):
        target = os.path.expanduser(target)
        if not os.path.exists(target):
            os.makedirs(target)
        elif not os.path.isdir(target):
            sys.exit("Trying to copy files into non-directory. Quitting")

        try:
            with open(os.path.join(os.path.dirname(target),
                                   "{0}.{1}".format(os.path.basename(target),
                                                    self.export_type)), 'w') as fh:
                fh.write(getattr(self, "to_%s" % self.export_type)())
        except DoNotExport:
            pass
        for i, song in enumerate(self.songs):
            shutil.copy(song.path,
                        os.path.join(target,
                                     format(song,
                                            fmt)))

    ################################################################
    # Container Emulation
    def __iter__(self):
        return self.songs.__iter__()

    def __getitem__(self, key):
        return self.songs[key]

    def __len__(self):
        return len(self.songs)

    ################################################################
    # Playlist Parsers
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
                        self.songs.append(self.Song(path, title,
                                                    track_number=len(self)+1))
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
                self.songs.append(self.Song(path, title, artist,
                                            track_number=len(self)+1))
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
                            self.songs.append(self.Song(path=path, title=title,
                                                        artist=artist,
                                                        length=time,
                                                        track_number=len(self)+1))
                        except OSError as e:
                            print "could not add %s: %s" % (path, e)
                        artist = title = path = None
            else:
                fh.seek(0)
                for line in fh:
                    try:
                        self.songs.append(self.Song(line.strip()),
                                          track_number=len(self)+1)
                    except OSError as e:
                        print "could not add %s: %s" % (path, e)

    ################################################################
    # Playlist Writers
    def to_none(self, *a, **kw):
        raise DoNotExport()

    def to_pls(self,
               root="",
               fmt="{track_number:02} - {artist} - {title}.{ext}"):
        buf = "[playlist]\n"
        buf += "NumberOfEntries=%d\n\n" % len(self)

        for i, song in enumerate(self):
            try:
                buf += "File{track_number}:{path}\n"\
                       "Title{track_number}:{title}\n"\
                       "Length{track_number}:{length}\n\n".format(
                    track_number=i+1,
                    path=os.path.join(root,
                                      format(song, fmt)),
                    title=song.title,
                    length=song.length
                    )
            except KeyError as e:
                print e
                import pdb; pdb.set_trace()
        buf = buf[:-1]
        return buf

    def to_m3u(self,
               root="",
               fmt="{track_number:02} - {artist} - {title}.{ext}"):
        buf = "#EXTM3U\n\n"

        for song in self:
            buf += "#EXTINF:{song.length}:{song.artist} - {song.title}\n"\
                   "{path}\n\n".format(
                song=song,
                path=os.path.join(root,
                                  format(song, fmt)),
                )
        return buf[:-1]

#######################################################################
## Script Logic

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
""")
    parser.add_argument('playlist', nargs='+',
                        help="\nthe playlist files to use to decide where to get the music from\n")
    parser.add_argument('-t', '--target', help="The file to write the music to.\n"
                        "(Defaults to the (first) playlist filename, with .zip instead of .pls)\n")
    parser.add_argument('-i', '--inner-folder-name',
                        help="An internal folder name to put the music files inside of.\n"
                        "(Defaults to the name of the archive, minus 'zip'.)\n")
    parser.add_argument('-c', '--copy', action='store_true', default=False,
                        help="\nCopy files into a directory instead of zipping them.\n"
                        "(Target is a destination folder to copy them in this case.\n"
                        "Creates the folder if it doesn't exist)")
    # TODO: Implement this
    # parser.add_argument('-r', '--rewrite-metadata',
    #                     action='store_true', default=False,
    #                     help="Change song metadata so that it will show up in media\n"
    #                     "players in the correct order and with the album changed to\n"
    #                     "the playlist name")
    parser.add_argument('-f', '--format',
                        action='store',
                        default="{track_number:02} - {artist} - {title}.{ext}",
                        help="An optional format string to customize the filename\n"
                        "output by zipls. Enclose tags in curly braces wherever you\n"
                        "want them to appear. See the README for more info and\n"
                        "examples. Known tags:\n"
                        "   {path}   {title}   {ext}   {track_number}   {album}")
    parser.add_argument('-w', '--write-playlist-type', action="store",
                        default=None,
                        help="The playlist type to write inside of the zip file.\n"
                        "Defaults to the type of the first playlist passed in.\n"
                        "Options:\n   none   pls   m3u   \n" # xspf
                        "If 'none' then no playlist will be written")

    return parser.parse_args()

def main(args):
    songs = Songs(args.playlist,
                  export_type=args.write_playlist_type)
    if not args.target:
        target = os.path.splitext(os.path.basename(args.playlist[0]))[0]
        args.target = target

    if not args.format.endswith(".{ext}"):
        args.format += ".{ext}"

    if args.copy:
        songs.copy_em(args.target, args.format)
    else:
        songs.zip_em(args.target, args.inner_folder_name, args.format)

if __name__ == "__main__":
    try:
        args = parse_args()
        main(args)
    except KeyboardInterrupt:
        print "\rCaught keyboard interrupt. Giving up without Cleaning up."
    except RuntimeError as e:
        print "Error! Error!: %s" % e
