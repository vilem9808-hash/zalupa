import unittest
from types import SimpleNamespace
from animation import action_for, frame_for
from main import ATTACKS

class AnimationTests(unittest.TestCase):
    def fighter(self, **changes):
        data=dict(id=1,hp=100,stun=0,attack=None,block=False,on_ground=True,vx=0,vy=0,walk=0,attack_time=0)
        data.update(changes)
        return SimpleNamespace(**data)

    def test_run_and_action_priority(self):
        self.assertEqual(action_for(self.fighter(vx=420)),'run')
        self.assertEqual(action_for(self.fighter(vx=285)),'walk')
        self.assertEqual(action_for(self.fighter(vx=420,block=True)),'block')
        self.assertEqual(action_for(self.fighter(hp=0,attack='heavy')),'death')

    def test_impact_is_extended_pose(self):
        for name, attack in ATTACKS.items():
            f=self.fighter(attack=name,attack_time=attack.hit_at)
            self.assertEqual(frame_for(name,f,0,'fight',0,ATTACKS),1)
            f.attack_time=attack.duration-.001
            self.assertEqual(frame_for(name,f,0,'fight',0,ATTACKS),2)

    def test_death_stays_lying(self):
        f=self.fighter(hp=0)
        self.assertEqual(frame_for('death',f,0,'end',2.5,ATTACKS),0)
        self.assertEqual(frame_for('death',f,0,'end',2.1,ATTACKS),1)
        self.assertEqual(frame_for('death',f,0,'match',0,ATTACKS),2)

if __name__=='__main__':
    unittest.main()
