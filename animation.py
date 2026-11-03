"""Sprite animation timing, independent from combat simulation."""
import math

ACTIONS = ('idle', 'walk', 'run', 'jump', 'block', 'light', 'heavy', 'special', 'hit', 'death')


def action_for(fighter):
    if fighter.hp <= 0:
        return 'death'
    if fighter.stun > 0:
        return 'hit'
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
        return 1 if math.sin(clock*5) > 0 else 2
    if action == 'hit':
        return 0 if fighter.stun > .24 else 1 if fighter.stun > .10 else 2
    if action == 'death':
        elapsed = max(0, 2.5-phase_time)
        return 2 if phase == 'match' or elapsed >= .65 else 1 if elapsed >= .25 else 0
    return (0, 1, 2, 1)[int((clock + fighter.id*.17)*4) % 4]
