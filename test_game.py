"""Checks for the combat rules and round lifecycle; no display required."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame as pg
from main import Game, Fighter, ATTACKS

class CombatTests(unittest.TestCase):
    def setUp(self):
        self.g = Game.__new__(Game)
        self.g.pressed = set()
        self.g.keys = set()
        self.g.round = 1
        self.g.clock = 0
        self.g.mode_ai = False
        self.g.reset()
        self.g.phase = 'fight'
        self.g.p1.x, self.g.p2.x = 500, 600

    def test_attack_timing_and_one_hit(self):
        g = self.g
        g.start_attack(g.p1,'light')
        g.update_fighter(g.p1,g.p2,.10)
        self.assertEqual(g.p2.hp,100)
        g.update_fighter(g.p1,g.p2,.02)
        self.assertEqual(g.p2.hp,93)
        g.update_fighter(g.p1,g.p2,.02)
        self.assertEqual(g.p2.hp,93)

    def test_guard_reduces_damage_and_gains_energy(self):
        g = self.g
        g.p2.block = True
        g.hit(g.p1,g.p2,ATTACKS['heavy'])
        self.assertEqual(g.p2.hp,97)
        self.assertEqual((g.p1.energy,g.p2.energy),(5,4))

    def test_special_requires_and_spends_energy(self):
        g = self.g
        self.assertFalse(g.start_attack(g.p1,'special'))
        g.p1.energy = 40
        self.assertTrue(g.start_attack(g.p1,'special'))
        self.assertEqual(g.p1.energy,0)

    def test_range_and_height(self):
        g = self.g
        g.p2.x = 900
        g.hit(g.p1,g.p2,ATTACKS['special'])
        self.assertEqual(g.p2.hp,100)
        g.p2.x, g.p2.y = 600, 300
        g.hit(g.p1,g.p2,ATTACKS['special'])
        self.assertEqual(g.p2.hp,100)

    def test_knockout_is_awarded_once_and_match_ends(self):
        g = self.g
        g.p1.wins = 1
        g.p2.hp = 1
        g.start_attack(g.p1,'heavy')
        g.update_fighter(g.p1,g.p2,.3)
        self.assertEqual(g.phase,'end')
        self.assertEqual(g.p1.wins,2)
        g.round_end(g.p1)
        self.assertEqual(g.p1.wins,2)
        g.step(2.6)
        self.assertEqual(g.phase,'match')

    def test_timeout_next_round_and_draw(self):
        g = self.g
        g.remaining = .01
        g.p1.hp = 70
        g.p2.hp = 50
        g.step(.02)
        self.assertIs(g.winner,g.p1)
        g.step(2.6)
        self.assertEqual((g.round,g.p1.wins,g.p1.hp),(2,1,100))
        g.phase = 'fight'
        g.remaining = .01
        g.step(.02)
        self.assertIsNone(g.winner)
        self.assertEqual((g.p1.wins,g.p2.wins),(1,0))

    def test_pause_and_jump_lands(self):
        g = self.g
        g.paused = True
        g.step(.5)
        self.assertEqual(g.remaining,75)
        g.paused = False
        g.pressed.add(pg.K_w)
        g.step(.016)
        self.assertLess(g.p1.y,523)
        for _ in range(70):
            g.step(.016)
        self.assertTrue(g.p1.on_ground)
        self.assertEqual(g.p1.y,523)

if __name__ == '__main__':
    unittest.main()
