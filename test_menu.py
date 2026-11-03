import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import tempfile
from pathlib import Path
import unittest
import pygame as pg
from main import Game
from menu import HEROES
from roster import HERO_DATA
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
                y=box.top+int(box.height*HERO_DATA[hero]['hip'])
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

    def test_walking_has_eight_distinct_key_poses(self):
        for hero in HEROES:
            keys=self.g.sprites[hero]['walk'][0]
            frames=self.g.motion[hero]['walk']
            self.assertEqual(len(keys),8)
            self.assertEqual(len(frames),24)
            self.assertEqual(len({pg.image.tobytes(image,'RGBA') for image in keys}),8)
            roots=[]
            for i,image in enumerate(keys):
                self.assertIs(image,frames[i*3][0])
                box=image.get_bounding_rect(min_alpha=128)
                y=box.top+int(box.height*HERO_DATA[hero]['hip'])
                xs=[x for x in range(box.left,box.right) if image.get_at((x,y)).a>128]
                roots.append(xs[len(xs)//2]+frames[i*3][1][0])
            self.assertLess(max(roots)-min(roots),25)

    def test_portrait_grid_mouse_selects_real_heroes(self):
        g=self.g;g.menu.activate('pvp');g.render()
        self.assertEqual(set(g.menu.roster_portraits),set(HEROES))
        def click(index):
            rect=g.menu.buttons('select')[index][1]
            point=(g.viewport.x+rect.centerx*g.viewport.width/1152,g.viewport.y+rect.centery*g.viewport.height/760)
            g.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=point))
        click(1);self.assertEqual(HEROES[g.menu.cursor],'rabbit')
        click(len(HEROES)+1);self.assertEqual(g.menu.stage,1)
        click(0);click(len(HEROES)+1)
        self.assertEqual((g.scene,g.p1.hero,g.p2.hero),('battle','rabbit','wolf'))
        for image in g.menu.roster_portraits.values():
            self.assertLessEqual(image.get_width(),144)
            self.assertLessEqual(image.get_height(),150)

    def test_zoom_changes_rendering_but_not_fight_state(self):
        g=self.g;g.scene='battle';g.phase='fight'
        before=(g.p1.x,g.p1.y,g.p2.x,g.p2.y,g.p1.hp,g.p2.hp,g.remaining)
        g.render()
        self.assertEqual(before,(g.p1.x,g.p1.y,g.p2.x,g.p2.y,g.p1.hp,g.p2.hp,g.remaining))
        center,ground=g.camera.project(576,523)
        self.assertAlmostEqual(center,576)
        self.assertAlmostEqual(ground,523)
        self.assertLess(g.camera.scale[0],.8)
        self.assertLess(g.camera.scale[1],.8)
        _,head=g.camera.project(330,523-367)
        self.assertLess(ground-head,300)

    def test_new_heroes_selected_with_two_dimensional_keyboard_grid(self):
        g=self.g;g.menu.activate('ai')
        self.key(pg.K_DOWN);self.assertEqual(HEROES[g.menu.cursor],'matroskin')
        self.key(pg.K_RETURN);self.key(pg.K_DOWN)
        self.assertEqual(HEROES[g.menu.cursor],'pechkin')
        self.key(pg.K_RETURN)
        self.assertEqual((g.p1.hero,g.p2.hero),('matroskin','pechkin'))
        self.assertTrue(g.mode_ai)
        g.phase='fight';g.ai(.2)
        self.assertLess(g.p2.vx,0)
        g.render()

    def test_new_hero_mirror_matches_render_correct_native_direction(self):
        g=self.g
        for hero in ('matroskin','pechkin'):
            g.menu.activate('pvp');g.menu.activate(hero);g.menu.activate('confirm')
            g.menu.activate(hero);g.menu.activate('confirm')
            self.assertEqual((g.p1.hero,g.p2.hero),(hero,hero))
            g.render()
            self.assertTrue(any(key[0]==hero for key in g.motion_flips))

    def test_new_heroes_have_complete_animations_and_contacts(self):
        from animation import ACTIONS
        g=self.g
        for hero in ('matroskin','pechkin'):
            self.assertEqual(set(g.motion[hero]),set(ACTIONS))
            for action,frames in g.motion[hero].items():
                self.assertEqual(len(frames),24)
                self.assertEqual(len(g.sprites[hero][action][0]),8 if action=='walk' else 3)
                for image,_ in frames:self.assertGreater(image.get_bounding_rect(min_alpha=128).height,30)
            for action in ('light','heavy','special'):
                self.assertTrue(-400<g.contact_points[(hero,action)]<-70)
            g.selected_heroes=[hero,'wolf'];g.new_match();g.mode_ai=False;g.scene='battle';g.phase='fight'
            g.p1.x=500;g.p2.x=740
            g.start_attack(g.p1,'heavy')
            for _ in range(42):g.step(1/120)
            self.assertEqual(g.p2.hp,84)
            g.render()

    def test_four_distinct_portraits_and_names(self):
        from roster import NAMES
        g=self.g
        self.assertEqual(len(HEROES),4)
        self.assertEqual(set(g.hud.portraits),set(HEROES))
        self.assertEqual(NAMES['matroskin'],'МАТРОСКИН')
        self.assertEqual(NAMES['pechkin'],'ПЕЧКИН')
        self.assertEqual(len({pg.image.tobytes(image,'RGBA') for image in g.hud.portraits.values()}),4)

    def test_mouse_can_select_bottom_row_new_heroes(self):
        g=self.g;g.menu.activate('ai');g.render()
        def click(index):
            rect=g.menu.buttons('select')[index][1]
            point=(g.viewport.x+rect.centerx*g.viewport.width/1152,g.viewport.y+rect.centery*g.viewport.height/760)
            g.handle_event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=point))
        click(3);click(len(HEROES)+1);click(2);click(len(HEROES)+1)
        self.assertEqual((g.scene,g.p1.hero,g.p2.hero),('battle','pechkin','matroskin'))
        g.render()

    def test_corrupt_preferences_fall_back(self):
        self.path.write_text('[]')
        self.assertEqual(settings.load(self.path),settings.DEFAULTS)
        self.path.write_text('{broken')
        self.assertEqual(settings.load(self.path),settings.DEFAULTS)

if __name__=='__main__':unittest.main()
