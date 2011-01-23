#!/usr/bin/env python

import Tkinter as Tk, tkFileDialog, tkMessageBox
import os

import zipls

class Playlists(Tk.Frame):
    def __init__(self, master, playlists=None):
        Tk.Frame.__init__(self, master, padx=6)
        self.playlist_frames = Tk.Frame(self)
        self.playlist_frames.pack()

        self.add_button = Tk.Button(self, text="Add another playlist",
                                    command=self.add)
        self.add_button.pack(pady=3)
        if playlists is None:
            self.add()
        else:
            for pls in playlists:
                self.add(pls)
        self.pack()

    def set_or_add(self, pls):
        for ipls in PlaylistBox.playlists:
            if ipls.filepath is None:
                ipls.set(pls)
                ipls.pack()
                break
        else:
            self.add(pls)

    def add(self, pls=None):
        new_pls = PlaylistBox(self.playlist_frames)

        if pls is not None:
            new_pls.set(pls)
        new_pls.pack()
        self.playlist_frames.pack()


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

        self.empty_text = "No playlist selected"
        self.label_text = Tk.StringVar()
        self.label_text.set(self.empty_text)
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
        if filepath:
            self.set(filepath)
        elif self.filepath is not None:
            self.label_text.set(self.filepath)
        else:
            self.label_text.set(self.empty_text)

        self.label.pack()

    def set(self, filepath):
        self.label_text.set(filepath)
        self.filepath = filepath

        if PlaylistBox.playlists[0] is self and \
                TargetBox.single.target is None:
            target = os.path.splitext(filepath)[0]
            target += '.zip'
            TargetBox.single.change_to(target)

    def clear(self):
        self.label_text.set(self.empty_text)
        self.filepath = None

class TargetBox(Tk.Frame):
    # pseudo-singletonny object access
    single = None

    def __init__(self, master):
        if TargetBox.single is not None:
            raise RuntimeError("there can only be one target.")
        TargetBox.single = self

        Tk.Frame.__init__(self, master,
                          padx=3, bd=1, relief=Tk.SUNKEN)

        self.change_button = Tk.Button(self, text="Change",
                                       command=self.choose_other)

        self.target = None
        self.fmt = 'Target: {0}'
        self.empty_text = "(Nothing selected)"
        self.label_text = Tk.StringVar()
        self.label_text.set(self.fmt.format(self.empty_text))
        self.label = Tk.Label(self, textvariable=self.label_text)

        self.label.pack(side=Tk.LEFT)
        self.change_button.pack(side=Tk.RIGHT)
        self.pack(side=Tk.TOP, padx=2, pady=5)


    def choose_other(self):
        filepath = tkFileDialog.asksaveasfilename(filetypes=(("Zip file", "*.zip"),
                                                             ("Anything", "*")))
        dirname = os.path.dirname(filepath)
        if not os.path.isdir(dirname) and dirname != '':
            answer = tkMessageBox.askyesno("Directory does not exist",
                                           "The directory '{0}' doesn't exist.\n"
                                           "Do you want to create it?".format(dirname))
            if answer == 'yes':
                os.makedirs(dirname)
        if filepath:
            self.change_to(filepath)

    def change_to(self, filepath):
        TargetBox.target = self.target = filepath
        self.label_text.set(self.fmt.format(filepath))
        self.label.pack()

class Controls(Tk.Frame):
    def __init__(self, master, args, Control_Frames):
        Tk.Frame.__init__(self, master)

        self.zip_button = Tk.Button(self, text="Zip!",
                                    command=self.zip)

        self.args = args

        for Frame in Control_Frames:
            Frame(self)
        self.zip_button.pack()
        self.pack()

    def zip(self):
        plss = [pls.filepath
                for pls in PlaylistBox.playlists if pls.filepath]
        if not plss:
            tkMessageBox.showwarning("Eek!", "No playlists selected!")
            return

        target = TargetBox.single.target
        if not target.endswith('.zip'):
            target = os.path.splitext(target)[0] + '.zip'

        songs = zipls.Songs(plss)

        self.args.playlist = plss
        self.args.target = target
        zipls.main(self.args)

        tkMessageBox.showinfo("Done!",
                              "Zipped:\n" +
                              '\n'.join([format(song, '({track_number}) {artist} - {title}')
                                         for song in songs]) +
                              "\n\nto: " + target)


def main(args):
    root = Tk.Tk()
    root.title("Zip, Please!")

    w = Tk.Label(root, text="Welcome to zipls!",
                 pady=7)
    w.pack()

    playlists = Playlists(root)
    Controls(root, args, [TargetBox])

    if args.playlist is not None:
        for pls in args.playlist:
            playlists.set_or_add(pls)

    root.mainloop()

if __name__ == "__main__":
    main()
