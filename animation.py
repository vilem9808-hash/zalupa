"""Sprite animation timing, independent from combat simulation."""
import math

ACTIONS = ('idle', 'walk', 'run', 'jump', 'block', 'light', 'heavy', 'special', 'hit', 'death')


def action_for(fighter):
    if fighter.hp <= 0:
        return 'death'
    if fighter.stun > 0:
        return 'block' if getattr(fighter,'guarded',False) else 'hit'
    if fighter.attack:
        return fighter.attack
    if fighter.block:
        return 'block'
    if not fighter.on_ground:
        return 'jump'
    if abs(fighter.vx) > 300:
        return 'run'
    return 'walk' if abs(fighter.vx) > 28 else 'idle'


def frame_for(action, fighter, clock, phase, phase_time, attacks):
    if action in attacks:
        attack = attacks[action]
        # The extended strike is shown before and through the actual hit frame.
        if fighter.attack_time < attack.hit_at * .65:
            return 0
        if fighter.attack_time < attack.hit_at + (attack.duration-attack.hit_at)*.35:
            return 1
        return 2
    if action in ('walk', 'run'):
        return int(fighter.walk * (1.35 if action == 'run' else 1)) % 3
    if action == 'jump':
        return 0 if fighter.vy < -300 else 1 if fighter.vy < 300 else 2
    if action == 'block':
        if getattr(fighter,'guarded',False) and fighter.stun > 0:
            return 0
        age = getattr(fighter,'block_time',.1)
        return 2 if age < .05 else 1 if age < .1 else 0
    if action == 'hit':
        progress = 1-fighter.stun/max(.001,getattr(fighter,'stun_total',.37))
        return min(2,int(max(0,progress)*3))
    if action == 'death':
        elapsed = max(0, 2.5-phase_time)
        return 2 if phase == 'match' or elapsed >= .65 else 1 if elapsed >= .25 else 0
    return (0, 1, 2, 1)[int((clock + fighter.id*.17)*4) % 4]


def phase_for(action, fighter, clock, phase, phase_time, attacks):
    """Continuous key-pose coordinate; baked motion supplies eight in-betweens."""
    if action in attacks:
        a=attacks[action];t=fighter.attack_time
        if t<=a.hit_at:
            u=max(0,min(1,t/a.hit_at))
            return u*u*(3-2*u)
        hold=min(.025,(a.duration-a.hit_at)*.15)
        u=max(0,min(1,(t-a.hit_at-hold)/max(.01,a.duration-a.hit_at-hold)))
        return 1+u*u*(3-2*u)
    if action in ('walk','run'):
        return (fighter.walk*(.4 if action=='walk' else .6))%3
    if action=='idle':return (clock*1.2+fighter.id*.13)%3
    if action=='jump':return max(0,min(2,(fighter.vy+760)/760))
    if action=='block':
        if fighter.stun>0 and getattr(fighter,'guarded',False):return 0
        return 2*(1-max(0,min(1,getattr(fighter,'block_time',.12)/.12)))
    if action=='hit':
        return 2*max(0,min(1,1-fighter.stun/max(.001,getattr(fighter,'stun_total',.37))))
    if action=='death':return 2 if phase=='match' else 2*max(0,min(1,(2.5-phase_time)/.7))
    return 0


def motion_index(phase, steps=8):
    return max(0,min(3*steps-1,int(phase*steps+.00001)))
