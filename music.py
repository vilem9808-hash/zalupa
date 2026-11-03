"""Stream the bundled MP3 without loading the full track into RAM."""
import pygame as pg

class Music:
    def __init__(self,path,volume):
        self.available=False
        self.error=''
        try:
            if not pg.mixer.get_init():pg.mixer.init()
            pg.mixer.music.load(str(path))
            self.available=True
            self.set_volume(volume)
            pg.mixer.music.play(-1)
        except (pg.error,OSError) as exc:
            self.available=False
            self.error=str(exc)

    def set_volume(self,value):
        if self.available:
            try:pg.mixer.music.set_volume(max(0,min(100,value))/100)
            except pg.error as exc:self.available=False;self.error=str(exc)

    def stop(self):
        if self.available and pg.mixer.get_init():pg.mixer.music.stop()
