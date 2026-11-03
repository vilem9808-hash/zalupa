import unittest
from main import Game, ATTACKS
from animation import action_for,frame_for

class ContactTests(unittest.TestCase):
    def setUp(self):
        self.g=Game.__new__(Game)
        self.g.pressed=set();self.g.keys=set();self.g.round=1;self.g.clock=0;self.g.mode_ai=False
        self.g.reset();self.g.phase='fight'
        self.g.p1.x,self.g.p2.x=500,600

    def test_contact_freezes_simulation_and_not_health_twice(self):
        g=self.g
        g.start_attack(g.p1,'heavy')
        g.update_fighter(g.p1,g.p2,.30)
        health,time,x=g.p2.hp,g.remaining,g.p2.x
        self.assertGreater(g.hit_stop,0)
        self.assertEqual(len(g.impacts),1)
        g.step(.02)
        self.assertEqual((g.p2.hp,g.remaining,g.p2.x),(health,time,x))
        self.assertEqual(frame_for('heavy',g.p1,g.clock,g.phase,g.phase_time,ATTACKS),1)
        self.assertEqual(action_for(g.p2),'hit')

    def test_miss_has_no_contact_effect(self):
        g=self.g;g.p2.x=900
        g.hit(g.p1,g.p2,ATTACKS['heavy'])
        self.assertEqual(g.hit_stop,0)
        self.assertFalse(g.impacts)
        self.assertEqual(g.p2.knockback,0)

    def test_guard_holds_guard_pose_and_reduces_push(self):
        g=self.g;g.p2.block=True
        g.hit(g.p1,g.p2,ATTACKS['heavy'])
        self.assertEqual(action_for(g.p2),'block')
        self.assertTrue(g.impacts[0][4])
        guarded_push=g.p2.knockback
        g.reset();g.phase='fight';g.p1.x,g.p2.x=500,600
        g.hit(g.p1,g.p2,ATTACKS['heavy'])
        self.assertGreater(g.p2.knockback,guarded_push)

    def test_target_moves_away_after_hitstop(self):
        g=self.g
        g.hit(g.p1,g.p2,ATTACKS['heavy'])
        old_x=g.p2.x
        for _ in range(15):g.step(.016)
        self.assertGreater(g.p2.x,old_x)
        self.assertLess(g.p2.hp,100)

    def test_impact_is_on_target_side_not_attacker(self):
        g=self.g
        g.hit(g.p1,g.p2,ATTACKS['light'])
        x,y,*_=g.impacts[0]
        self.assertEqual(x,g.p2.x-32)
        self.assertEqual(y,g.p2.y-215)
        self.assertEqual(frame_for('hit',g.p2,0,g.phase,0,ATTACKS),0)

if __name__=='__main__':unittest.main()
