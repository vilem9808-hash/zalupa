import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import tempfile
from pathlib import Path
import unittest
import pygame as pg
from main import Game
from menu import HEROES
import settings


class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.path=Path(cls.temp.name)/'preferences.json'
        cls.game=Game(settings_path=cls.path)
        assert cls.game.scene=='main'

    @classmethod
    def tearDownClass(cls):
        pg.quit();cls.temp.cleanup()

    def setUp(self):
        self.g=self.game
        self.g.scene='main';self.g.running=True
        self.g.selected_heroes=['wolf','rabbit'];self.g.preferences=dict(settings.DEFAULTS)
        self.g.new_match();self.g.menu.focus=0;self.g.menu.hover=None

    def key(self,key):self.g.handle_event(pg.event.Event(pg.KEYDOWN,key=key,repeat=False))

    def test_pvp_swapped_heroes(self):
        m=self.g.menu;m.activate('pvp');m.activate('rabbit');m.activate('confirm')
        self.assertEqual((self.g.scene,m.stage),('select',1))
        m.activate('wolf');m.activate('confirm')
        self.assertEqual((self.g.p1.hero,self.g.p2.hero),('rabbit','wolf'))
        self.assertFalse(self.g.mode_ai);self.assertEqual(self.g.scene,'battle')
        self.g.render()

    def test_ai_and_mirror_match(self):
        m=self.g.menu;m.activate('ai');m.activate('wolf');m.activate('confirm');m.activate('wolf');m.activate('confirm')
        self.assertTrue(self.g.mode_ai)
        self.assertEqual((self.g.p1.hero,self.g.p2.hero),('wolf','wolf'))
        self.g.render()

    def test_selection_back_preserves_first_choice(self):
        m=self.g.menu;m.activate('pvp');m.activate('rabbit');m.activate('confirm');m.activate('back')
        self.assertEqual((m.stage,HEROES[m.cursor]),(0,'rabbit'))
        m.activate('back');self.assertEqual(self.g.scene,'main')

    def test_keyboard_navigation(self):
        self.key(pg.K_RETURN)
        self.assertEqual(self.g.scene,'select')
        self.key(pg.K_RIGHT);self.key(pg.K_RETURN);self.key(pg.K_RETURN)
        self.assertEqual((self.g.scene,self.g.p1.hero,self.g.p2.hero),('battle','rabbit','rabbit'))

    def test_pause_settings_and_resume_keep_match(self):
        g=self.g;g.scene='battle';g.p1.hp=42;g.remaining=31
        self.key(pg.K_ESCAPE)
        self.assertEqual(g.scene,'pause')
        g.menu.activate('settings');g.menu.activate('back')
        self.assertEqual(g.scene,'pause')
        self.key(pg.K_ESCAPE)
        self.assertEqual((g.scene,g.p1.hp,g.remaining),('battle',42,31))
        self.assertFalse(g.paused)

    def test_fullscreen_saves_and_restores_window(self):
        g=self.g;original=g.window.get_size()
        g.menu.activate('settings')
        try:
            self.assertTrue(g.set_fullscreen(True))
            self.assertTrue(settings.load(self.path)['fullscreen'])
            self.assertTrue(g.window.get_flags() & pg.FULLSCREEN)
            self.assertTrue(g.set_fullscreen(False))
            self.assertEqual(g.window.get_size(),original)
            self.assertFalse(settings.load(self.path)['fullscreen'])
        finally:g.set_fullscreen(False)

    def test_mouse_works_with_letterboxing(self):
        g=self.g;g.render()
        rect=g.menu.buttons('main')[1][1]
        x=g.viewport.x+rect.centerx*g.viewport.width/1152
        y=g.viewport.y+rect.centery*g.viewport.height/760
        g.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=(x,y)))
        self.assertEqual(g.scene,'select');self.assertTrue(g.mode_ai)

    def test_motion_banks_and_no_random_camera_jitter(self):
        g=self.g
        for hero in HEROES:
            for action,frames in g.motion[hero].items():self.assertEqual(len(frames),24)
        self.assertFalse(g.preferences['camera_shake'])
        g.scene='battle';g.phase='fight';g.shake=13
        g.render();first=pg.image.tobytes(g.screen,'RGB')
        g.render();second=pg.image.tobytes(g.screen,'RGB')
        self.assertEqual(first,second)

    def test_p_key_resumes_pause(self):
        self.g.scene='battle'
        self.key(pg.K_p);self.assertEqual(self.g.scene,'pause')
        self.key(pg.K_p);self.assertEqual(self.g.scene,'battle')
        self.assertFalse(self.g.paused)

    def test_root_alignment_between_running_keyframes(self):
        for hero in HEROES:
            roots=[]
            for index in (0,8,16):
                image,offset=self.g.motion[hero]['run'][index]
                box=image.get_bounding_rect(min_alpha=128)
                y=box.top+int(box.height*(.48 if hero=='wolf' else .65))
                xs=[x for x in range(box.left,box.right) if image.get_at((x,y)).a>128]
                roots.append(xs[len(xs)//2]+offset[0])
            self.assertLess(max(roots)-min(roots),20)

    def test_settings_toggle_keeps_keyboard_focus(self):
        g=self.g;g.menu.activate('settings');g.menu.focus=1
        self.key(pg.K_RETURN)
        self.assertTrue(g.preferences['camera_shake'])
        self.assertEqual(g.menu.focus,1)
        self.key(pg.K_RETURN)
        self.assertFalse(g.preferences['camera_shake'])
        self.assertFalse(g.preferences['fullscreen'])

    def test_music_slider_drag_applies_and_saves(self):
        g=self.g;g.menu.activate('settings');g.render()
        track=g.menu.volume_track()
        def pos(x,y):return (g.viewport.x+x*g.viewport.width/1152,g.viewport.y+y*g.viewport.height/760)
        g.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=pos(track.x+track.width*.75,track.centery)))
        self.assertEqual(g.preferences['music_volume'],75)
        self.assertTrue(g.menu.dragging)
        g.handle_event(pg.event.Event(pg.MOUSEMOTION,pos=pos(track.right+90,track.centery),rel=(90,0),buttons=(1,0,0)))
        self.assertEqual(g.preferences['music_volume'],100)
        g.handle_event(pg.event.Event(pg.MOUSEBUTTONUP,button=1,pos=pos(track.right+90,track.centery)))
        self.assertFalse(g.menu.dragging)
        self.assertEqual(settings.load(self.path)['music_volume'],100)
        self.assertAlmostEqual(pg.mixer.music.get_volume(),1,delta=.01)

    def test_music_volume_keyboard_mute_and_persistence(self):
        g=self.g;g.menu.activate('settings');g.menu.focus=2
        self.key(pg.K_HOME)
        self.assertEqual(g.preferences['music_volume'],0)
        self.assertEqual(pg.mixer.music.get_volume(),0)
        self.key(pg.K_END);self.key(pg.K_LEFT)
        self.assertEqual(g.preferences['music_volume'],95)
        self.assertEqual(settings.load(self.path)['music_volume'],95)
        self.assertEqual(g.menu.focus,2)

    def test_volume_migrates_old_settings_and_rejects_invalid_numbers(self):
        self.path.write_text('{"fullscreen":true,"camera_shake":false}')
        self.assertEqual(settings.load(self.path)['music_volume'],35)
        self.assertEqual(settings.normalize({'music_volume':400})['music_volume'],100)
        self.assertEqual(settings.normalize({'music_volume':-1})['music_volume'],0)
        for value in (True,'loud',float('nan'),float('inf')):
            self.assertEqual(settings.normalize({'music_volume':value})['music_volume'],35)

    def test_music_continues_across_menu_selection_and_battle(self):
        g=self.g
        self.assertTrue(g.music.available)
        self.assertTrue(pg.mixer.music.get_busy())
        g.menu.activate('ai');g.menu.activate('confirm');g.menu.activate('confirm')
        self.assertTrue(pg.mixer.music.get_busy())
        g.open_pause();g.menu.activate('settings')
        self.assertTrue(pg.mixer.music.get_busy())

    def test_corrupt_preferences_fall_back(self):
        self.path.write_text('[]')
        self.assertEqual(settings.load(self.path),settings.DEFAULTS)
        self.path.write_text('{broken')
        self.assertEqual(settings.load(self.path),settings.DEFAULTS)

if __name__=='__main__':unittest.main()
