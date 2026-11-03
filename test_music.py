import os
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import unittest
from unittest.mock import patch
import pygame as pg
from music import Music

class MusicTests(unittest.TestCase):
    def tearDown(self):
        if pg.mixer.get_init():pg.mixer.music.stop();pg.mixer.quit()

    def test_uploaded_mp3_decodes_and_loops(self):
        with patch('music.pg.mixer.music.play',wraps=pg.mixer.music.play) as play:
            m=Music(Path(__file__).parent/'assets/audio/bloody_stream.mp3',35)
            self.assertTrue(m.available,m.error)
            play.assert_called_once_with(-1)
            self.assertTrue(pg.mixer.music.get_busy())
            self.assertAlmostEqual(pg.mixer.music.get_volume(),.35,delta=.01)
            m.stop();self.assertFalse(pg.mixer.music.get_busy())

    def test_no_audio_device_does_not_crash_game(self):
        with patch('music.pg.mixer.get_init',return_value=None),patch('music.pg.mixer.init',side_effect=pg.error('audio unavailable')):
            m=Music('unused.mp3',35)
            self.assertFalse(m.available)
            m.set_volume(80);m.stop()

if __name__=='__main__':unittest.main()
