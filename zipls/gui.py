#!/usr/bin/env python

import Tkinter as Tk, tkFileDialog, tkMessageBox
import os

import zipls

class Playlists(Tk.Frame):
    def __init__(self, master, playlists=None):
        Tk.Frame.__init__(self, master, padx=6)
        self.add_button = Tk.Button(self, text="Add another playlist",
                                    command=self.add)
        self.add_button.pack()
        if playlists is None:
            self.add()
        else:
            for pls in playlists:
                self.add(pls)
        self.pack()

    def add(self, pls=None):
        new_pls = PlaylistBox(self)
        if pls is not None:
            new_pls.filepath = pls
            new_pls.label_text.set(pls)
        new_pls.pack()
        self.pack()


class PlaylistBox(Tk.Frame):
    filetypes = (("Any Playlist", "*.pls *.m3u *.xspf"),
                 ("PLS", "*.pls"),
                 ("M3U", "*.m3u"),
                 ("M3U8", "*.m3u8"),
                 ("XML Sharable Playlist", "*.xspf"),
                 ("Anything", "*"))
    playlists = list()

    def __init__(self, master):
        Tk.Frame.__init__(self, master, padx=5,
                          bd=1, relief=Tk.SUNKEN)
        self.filepath = None

        self.label_text = Tk.StringVar()
        self.label_text.set("No playlist selected")
        self.label = Tk.Label(self, textvariable=self.label_text)
        self.label.pack()

        self.button = Tk.Button(self, text="Choose a playlist file",
                                command=self.get_file)
        self.button.pack(side=Tk.LEFT)

        self.clear_button = Tk.Button(self, text="Clear!",
                                      command=self.clear)
        self.clear_button.pack(side=Tk.RIGHT)

        self.pack(fill=Tk.X)

        PlaylistBox.playlists.append(self)

    def get_file(self):
        filepath = tkFileDialog.askopenfilename(filetypes=PlaylistBox.filetypes)
        if filepath is not None:
            self.label_text.set(filepath)
            self.filepath = filepath

    def clear(self):
        self.label_text.set("No playlist selected")
        self.filepath = None

class Controls(Tk.Frame):
    def __init__(self, master):
        Tk.Frame.__init__(self, master)

        self.zip_button = Tk.Button(self, text="Zip!",
                                    command=self.zip)
        self.zip_button.pack()
        self.pack()

    def zip(self):
        plss = [pls.filepath
                for pls in PlaylistBox.playlists if pls.filepath]
        if not plss:
            tkMessageBox("No playlists selected!")
            return

        target = os.path.splitext(plss[0])[0]
        target += '.zip'
        songs = zipls.Songs(plss)
        songs.zip_em(target)

        tkMessageBox.showinfo("Done!",
                              "Zipped:\n" +
                              '\n'.join([format(song, '({track_number}) {artist} - {title}')
                                         for song in songs]) +
                              "\n\nto: " + target)


def main(args):
    root = Tk.Tk()
    root.title("Zip, Please!")

    w = Tk.Label(root, text="Welcome to zipls!")
    w.pack()

    if args.playlist:
        Playlists(root, args.playlist)
    else:
        Playlists(root)
    Controls(root)

    root.mainloop()

if __name__ == "__main__":
    main()
