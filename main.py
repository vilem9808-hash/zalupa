"""Native Python port of Wolf vs Rabbit v0.6. Python 3.10+, pygame-ce."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import random
import sys
import pygame as pg
from animation import ACTIONS, action_for, frame_for
from hud import HUD
from impact import draw_impacts

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
W, H, GROUND = 1152, 648, 523

def clamp(v, low, high):
    return max(low, min(high, v))

@dataclass(frozen=True)
class Attack:
    duration: float
    hit_at: float
    reach: int
    damage: int
    push: int
    stun: float
    cost: int = 0

ATTACKS = {
    'light': Attack(.28, .115, 220, 7, 22, .16),
    'heavy': Attack(.58, .29, 265, 16, 65, .27),
    'special': Attack(.74, .35, 320, 23, 110, .37, 40),
}

@dataclass
class Fighter:
    id: int
    x: float
    face: int
    y: float = GROUND
    vx: float = 0
    vy: float = 0
    hp: int = 100
    energy: int = 0
    wins: int = 0
    on_ground: bool = True
    attack: str | None = None
    attack_time: float = 0
    hit_done: bool = False
    stun: float = 0
    block: bool = False
    walk: float = 0
    ai_block: float = 0
    stun_total: float = 0
    guarded: bool = False
    knockback: float = 0
    recoil: float = 0
    block_time: float = 0

class Game:
    def __init__(self):
        pg.display.init()
        pg.font.init()
        self.window = pg.display.set_mode((1152, 760), pg.RESIZABLE)
        pg.display.set_caption('ВОЛК vs ЗАЯЦ — Galactic Duel')
        self.screen = pg.Surface((W, 760))
        self.arena = pg.Surface((W, H))
        self.fonts = {}
        self.sprites = {}
        for name in ('wolf', 'rabbit'):
            self.sprites[name] = {}
            for action in ACTIONS:
                frames = [pg.image.load(str(ROOT / f'assets/v3/{name}/{action}_{i}.png')).convert_alpha() for i in range(1,4)]
                self.sprites[name][action] = (frames, [pg.transform.flip(f, True, False) for f in frames])
        self.contact_points = {}
        for name in ('wolf','rabbit'):
            for action in ATTACKS:
                image = self.sprites[name][action][0][1]
                bounds = image.get_bounding_rect(min_alpha=128)
                # Search the upper body so an extended shoe cannot be
                # mistaken for the striking fist (especially rabbit special).
                y0,y1 = bounds.top+int(bounds.height*.12),bounds.top+int(bounds.height*.70)
                search = range(bounds.right-1,bounds.left-1,-1) if name=='wolf' else range(bounds.left,bounds.right)
                tip = next(x for x in search if sum(image.get_at((x,y)).a>180 for y in range(y0,y1))>=3)
                xs = range(max(bounds.left,tip-3),min(bounds.right,tip+4))
                ys = [y for x in xs for y in range(y0,y1) if image.get_at((x,y)).a>180]
                self.contact_points[(name,action)] = sum(ys)/len(ys)-image.get_height() if ys else -215
        self.hud = HUD(ROOT, self.sprites)
        self.background = pg.transform.smoothscale(pg.image.load(str(ROOT / 'assets/arena.png')).convert(), (W+28, H+18))
        self.mode_ai = True
        self.keys, self.pressed = set(), set()
        self.clock = 0
        self.ai_tick = 0
        self.round = 1
        self.reset()

    def reset(self, keep_wins=False):
        wins = (self.p1.wins, self.p2.wins) if keep_wins else (0, 0)
        self.p1, self.p2 = Fighter(1, 330, 1, wins=wins[0]), Fighter(2, 820, -1, wins=wins[1])
        self.phase, self.phase_time, self.remaining = 'intro', 1.65, 75.0
        self.paused = False
        self.shake = self.flash = 0
        self.particles = []
        self.impacts = []
        self.hit_stop = 0
        self.pose_states = {}
        if hasattr(self, 'hud'):
            self.hud.reset()
        self.winner = None
        self.ai_tick = 0
        self.pressed.clear()

    def new_match(self):
        self.round = 1
        self.reset()

    def round_end(self, winner):
        if self.phase != 'fight':
            return
        self.phase, self.phase_time, self.winner = 'end', 2.5, winner
        if winner:
            winner.wins += 1
        for f in (self.p1, self.p2):
            f.attack = None
            f.block = False
            f.vx = 0

    def start_attack(self, f, kind):
        attack = ATTACKS[kind]
        if f.attack or f.stun > 0 or self.phase != 'fight' or f.energy < attack.cost:
            return False
        f.attack, f.attack_time, f.hit_done, f.vx = kind, 0, False, 0
        f.energy -= attack.cost
        f.guarded = False
        return True

    def hit(self, attacker, defender, attack):
        gap = (defender.x-attacker.x)*attacker.face
        if not 0 <= gap <= attack.reach+20 or abs(defender.y-attacker.y) > 115:
            return
        guarded = defender.block and defender.on_ground and defender.face == -attacker.face
        damage = max(1, int(attack.damage*.16+.5)) if guarded else attack.damage
        defender.hp = clamp(defender.hp-damage, 0, 100)
        defender.energy = clamp(defender.energy+(4 if guarded else 10), 0, 100)
        attacker.energy = clamp(attacker.energy+(5 if guarded else 12), 0, 100)
        defender.stun = .09 if guarded else attack.stun
        defender.stun_total = defender.stun
        defender.guarded = guarded
        defender.knockback = attacker.face*(attack.push*3+60)*(.28 if guarded else 1)
        defender.recoil = 4 if guarded else 8 if attack.damage < 10 else 15
        defender.vx = 0
        self.hit_stop = .035 if guarded else .045 if attack.damage < 10 else .075 if attack.damage < 20 else .095
        cx = defender.x-attacker.face*32
        kind = attacker.attack or next((key for key,value in ATTACKS.items() if value==attack),'light')
        name = 'wolf' if attacker.id==1 else 'rabbit'
        fist_y = getattr(self,'contact_points',{}).get((name,kind),-215)
        cy = clamp(attacker.y+fist_y,defender.y-330,defender.y-70)
        self.impacts.append([cx,cy,.24,.24,guarded,attacker.face,attack.damage])
        defender.attack = None
        self.shake = 3 if guarded else 13 if attack.damage > 15 else 7
        self.flash = .05 if guarded else .11
        color = '#a8d9fa' if guarded else '#ffb06a' if attacker.id == 1 else '#a5eaff'
        for _ in range(8 if guarded else 18):
            self.particles.append([cx, cy, random.uniform(-270,270), random.uniform(-320,90), random.uniform(.18,.48), random.uniform(2,8), color])
        if defender.hp <= 0:
            self.round_end(attacker)

    def control(self, f, bindings, dt):
        left, right, jump, block, light, heavy, special = bindings
        alive = self.phase == 'fight' and f.stun <= 0
        f.block = alive and block in self.keys and f.on_ground and not f.attack
        f.block_time = f.block_time+dt if f.block else 0
        direction = (int(right in self.keys)-int(left in self.keys)) if alive and not f.block else 0
        if not f.attack and alive:
            f.vx = direction*(420 if pg.K_LSHIFT in self.keys or pg.K_RSHIFT in self.keys else 285)
            if direction:
                f.walk += dt*11
            if jump in self.pressed and f.on_ground and not f.block:
                f.vy, f.on_ground = -760, False
            for key, action in ((light,'light'), (heavy,'heavy'), (special,'special')):
                if key in self.pressed:
                    self.start_attack(f, action)
                    break
        else:
            f.vx *= .7

    def ai(self, dt):
        f, op = self.p2, self.p1
        self.ai_tick -= dt
        d = op.x-f.x
        dist = abs(d)
        f.block = False
        if f.stun > 0 or f.attack:
            f.vx *= .78
            return
        if self.ai_tick <= 0:
            self.ai_tick = random.uniform(.11,.24)
            f.ai_block = random.uniform(.1,.34) if op.attack and dist < 285 and random.random() < .65 else 0
            if dist < 285 and random.random() < .54:
                self.start_attack(f, 'heavy' if random.random() < .3 else 'light')
            elif dist < 340 and f.energy >= 40 and random.random() < .3:
                self.start_attack(f, 'special')
            elif dist < 350 and random.random() < .12 and f.on_ground:
                f.vy, f.on_ground = -740, False
        f.ai_block = max(0, f.ai_block-dt)
        f.block = f.ai_block > 0 and f.on_ground and not f.attack
        f.block_time = f.block_time+dt if f.block else 0
        sign = 1 if d >= 0 else -1
        if f.block or f.attack:
            f.vx = 0
        elif dist > 235:
            f.vx = sign*(325 if dist > 260 else 190)
        elif dist < 215:
            f.vx = -sign*115
        else:
            f.vx *= .7
        if abs(f.vx)>28 and f.on_ground:
            f.walk += dt*11

    def update_fighter(self, f, opponent, dt):
        if f.stun > 0:
            f.stun = max(0, f.stun-dt)
            f.vx *= .88
        if f.attack and self.phase == 'fight':
            f.attack_time += dt
            attack = ATTACKS[f.attack]
            if not f.hit_done and f.attack_time >= attack.hit_at:
                f.hit_done = True
                self.hit(f, opponent, attack)
            if f.attack_time >= attack.duration:
                f.attack, f.attack_time = None, 0
        f.knockback *= math.exp(-8*dt)
        f.recoil = max(0, f.recoil-50*dt)
        f.vy += 1950*dt
        f.y += f.vy*dt
        if f.y >= GROUND:
            f.y, f.vy, f.on_ground = GROUND, 0, True
        else:
            f.on_ground = False
        f.x = clamp(f.x+(f.vx+f.knockback)*dt, 110, W-110)
        if not f.attack and not f.stun:
            f.face = 1 if opponent.x >= f.x else -1

    def step(self, dt):
        if self.paused:
            self.pressed.clear()
            return
        if self.hit_stop > 0:
            frozen = min(dt,self.hit_stop)
            self.hit_stop -= frozen
            dt -= frozen
            if dt <= 0:
                return
        self.clock += dt
        if hasattr(self, 'hud'):
            self.hud.update((self.p1,self.p2),dt)
        for effect in self.impacts:
            effect[2] -= dt
        self.impacts = [effect for effect in self.impacts if effect[2] > 0]
        self.shake = max(0, self.shake-32*dt)
        self.flash = max(0, self.flash-dt)
        for p in self.particles:
            p[4] -= dt
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[3] += 550*dt
        self.particles = [p for p in self.particles if p[4] > 0]
        if self.phase == 'intro':
            self.phase_time -= dt
            if self.phase_time <= 0:
                self.phase = 'fight'
        elif self.phase == 'end':
            self.phase_time -= dt
            if self.phase_time <= 0:
                if max(self.p1.wins, self.p2.wins) >= 2:
                    self.phase = 'match'
                else:
                    self.round += 1
                    self.reset(True)
        if self.phase == 'fight':
            self.remaining = max(0, self.remaining-dt)
            if self.remaining <= 0:
                a, b = self.p1, self.p2
                self.round_end(None if a.hp == b.hp else a if a.hp > b.hp else b)
            else:
                self.control(self.p1, (pg.K_a,pg.K_d,pg.K_w,pg.K_s,pg.K_j,pg.K_k,pg.K_l), dt)
                if self.mode_ai:
                    self.ai(dt)
                else:
                    self.control(self.p2, (pg.K_LEFT,pg.K_RIGHT,pg.K_UP,pg.K_DOWN,pg.K_u,pg.K_i,pg.K_o), dt)
        self.update_fighter(self.p1,self.p2,dt)
        if self.hit_stop <= 0:
            self.update_fighter(self.p2,self.p1,dt)
        if self.p1.x > self.p2.x-220:
            mid = clamp((self.p1.x+self.p2.x)/2,220,W-220)
            self.p1.x, self.p2.x = mid-110, mid+110
        self.pressed.clear()

    def text(self, surface, text, pos, size=22, color='#f5e9d2', center=False):
        if size not in self.fonts:
            self.fonts[size] = pg.font.Font(str(ROOT/'assets/ui.ttf'),size)
        image = self.fonts[size].render(text,True,color)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        surface.blit(image,rect)

    def draw_fighter(self, f):
        name = 'wolf' if f.id == 1 else 'rabbit'
        action = action_for(f)
        frame = frame_for(action, f, self.clock, self.phase, self.phase_time, ATTACKS)
        progress = clamp(f.attack_time/ATTACKS[f.attack].duration,0,.999) if f.attack else 0
        flip = f.face != (1 if f.id==1 else -1)
        image = self.sprites[name][action][int(flip)][frame]
        shadow = pg.Surface((150,28),pg.SRCALPHA)
        pg.draw.ellipse(shadow,(9,3,27,150),(5,4,140,20))
        feet = image.subsurface((0,image.get_height()-40,image.get_width(),40)).get_bounding_rect(min_alpha=128)
        shadow_x = f.x-image.get_width()/2+feet.centerx if feet.width else f.x
        self.arena.blit(shadow,(shadow_x-75,f.y-8))
        bob = math.sin(self.clock*3.6+f.id)*1.8 if action == 'idle' else 0
        # Falling and lying are drawn poses; keep their feet/ground anchor fixed.
        draw_x = f.x - f.face*f.recoil
        if f.attack and frame == 1:
            opponent = self.p2 if f.id == 1 else self.p1
            reach = ATTACKS[f.attack].reach+20
            gap = (opponent.x-f.x)*f.face
            if 0 <= gap <= reach and abs(opponent.y-f.y) <= 115:
                # Stop the drawn fist at the target's front surface.
                draw_x += f.face*(max(40,gap-32)-reach)
        # Short dissolves soften pose transitions; the contact pose always snaps
        # into place so impact timing stays exact instead of showing ghost fists.
        key = (action, frame, flip)
        old = self.pose_states.get(f.id)
        if old is None or old['key'] != key:
            previous = old['image'] if old and old['key'][2] == flip else None
            old = {'key':key,'image':image,'previous':previous,'time':self.clock}
            self.pose_states[f.id] = old
        blend = min(1,(self.clock-old['time'])/.045)
        smooth = action in ('idle','walk','run','block') or (f.attack and frame==2)
        rect = image.get_rect(midbottom=(draw_x,f.y+bob))
        if smooth and old['previous'] is not None and blend < 1:
            previous = old['previous'].copy();previous.set_alpha(round(255*(1-blend)))
            current = image.copy();current.set_alpha(round(255*blend))
            self.arena.blit(previous,rect);self.arena.blit(current,rect)
        else:
            self.arena.blit(image,rect)
        color = '#e849ff' if f.id==1 else '#ffd364'
        if f.attack == 'special' and not f.hit_done:
            radius = int(28+12*math.sin(progress*math.pi))
            pg.draw.arc(self.arena,color,(f.x-radius,f.y-180-radius,radius*2,radius*2),0,math.pi*1.6,2)

    def render(self):
        a = self.arena
        a.blit(self.background,(-14+math.sin(self.clock*.14)*11,-9))
        for layer,count in enumerate((35,23,14)):
            for j in range(count):
                x = (j*179.71+layer*137+self.clock*(3.5,8,14)[layer])%(W+65)-28
                y = 16+(j*83.37+layer*43)%(380 if layer==2 else 275)
                v = int(150+75*math.sin(self.clock*(1.1+layer*.3)+j*2.3))
                pg.draw.circle(a,(v,v,min(255,v+30)),(x,y),max(1,int((layer+1)*.65+(.5+.5*math.sin(j*7.7))*.65)))
        for f in (self.p1,self.p2):
            self.draw_fighter(f)
        for p in self.particles:
            pg.draw.circle(a,p[6],(p[0],p[1]),max(1,int(p[5]*p[4]/.48)))
        draw_impacts(a,self.impacts)
        if self.flash:
            flash = pg.Surface((W,H),pg.SRCALPHA)
            flash.fill((255,255,255,int(self.flash/.11*35)))
            a.blit(flash,(0,0))
        self.screen.fill('#090e1a')
        self.text(self.screen,'ВОЛК vs ЗАЯЦ',(22,15),22,'#e8d1aa')
        for rect,label in self.buttons():
            pg.draw.rect(self.screen,'#292b3a',rect,border_radius=7)
            pg.draw.rect(self.screen,'#87746f',rect,1,border_radius=7)
            self.text(self.screen,label,rect.center,16,center=True)
        offset = (random.uniform(-self.shake,self.shake),56+random.uniform(-self.shake*.4,self.shake*.4)) if self.shake else (0,56)
        self.screen.blit(a,offset)
        self.hud.draw(self.screen,(self.p1,self.p2),self.remaining,self.round)
        if self.phase!='fight' or self.paused:
            panel = pg.Surface((W,165),pg.SRCALPHA)
            panel.fill((13,20,38,205))
            if self.paused:
                title, subtitle = 'ПАУЗА','P — продолжить'
            elif self.phase=='intro':
                title, subtitle = f'РАУНД {self.round}','ПРИГОТОВЬСЯ'
            elif self.phase=='match':
                title, subtitle = 'ПОБЕДА: '+('ВОЛК' if self.p1.wins>=2 else 'ЗАЯЦ'),'R — новый бой'
            else:
                title = ('ПОБЕДИЛ ВОЛК' if self.winner.id==1 else 'ПОБЕДИЛ ЗАЯЦ') if self.winner else 'НИЧЬЯ'
                subtitle = 'СЛЕДУЮЩИЙ РАУНД'
            self.text(panel,title,(W//2,65),45,center=True)
            self.text(panel,subtitle,(W//2,120),20,center=True)
            self.screen.blit(panel,(0,291))
        self.text(self.screen,'1: A/D — движение   W — прыжок   S — блок   J/K/L — быстрый / сильный / спецприём',(W//2,722),15,center=True)
        self.text(self.screen,'2: ←/→ ↑ ↓   U/I/O — атаки     P — пауза    R — заново    Shift — бег    F2 — режим    F11 — экран',(W//2,747),15,center=True)
        size = self.window.get_size()
        scale = min(size[0]/W,size[1]/760)
        dest = (max(1,int(W*scale)),max(1,int(760*scale)))
        self.viewport = pg.Rect((size[0]-dest[0])//2,(size[1]-dest[1])//2,*dest)
        self.window.fill('#050810')
        self.window.blit(pg.transform.smoothscale(self.screen,dest),self.viewport)
        pg.display.flip()

    def buttons(self):
        return [(pg.Rect(654,9,280,37),'Режим: '+('против ИИ' if self.mode_ai else '2 игрока')), (pg.Rect(950,9,180,37),'Новый бой')]

    def toggle_mode(self):
        self.mode_ai = not self.mode_ai
        self.keys.clear()
        self.new_match()

    def run(self, max_frames=0, screenshot=None):
        timer, running, frames = pg.time.Clock(), True, 0
        self.render()
        while running:
            dt = min(timer.tick(60)/1000,.032)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key not in self.keys:
                        self.pressed.add(event.key)
                        if event.key==pg.K_p:
                            self.paused = not self.paused
                        elif event.key==pg.K_r:
                            self.new_match()
                        elif event.key==pg.K_F2:
                            self.toggle_mode()
                        elif event.key==pg.K_F11:
                            pg.display.toggle_fullscreen()
                        elif event.key==pg.K_ESCAPE:
                            running = False
                    self.keys.add(event.key)
                elif event.type==pg.KEYUP:
                    self.keys.discard(event.key)
                elif event.type==pg.WINDOWFOCUSLOST:
                    self.keys.clear()
                    self.pressed.clear()
                    self.paused = True
                elif event.type==pg.MOUSEBUTTONDOWN and event.button==1:
                    x = (event.pos[0]-self.viewport.x)*W/self.viewport.width
                    y = (event.pos[1]-self.viewport.y)*760/self.viewport.height
                    for i,(rect,_) in enumerate(self.buttons()):
                        if rect.collidepoint(x,y):
                            self.toggle_mode() if i==0 else self.new_match()
            self.step(dt)
            self.render()
            frames += 1
            if max_frames and frames>=max_frames:
                running = False
        if screenshot:
            pg.image.save(self.screen,str(screenshot))
        pg.quit()


def main():
    parser = argparse.ArgumentParser(description='Волк против Зайца — Python / Pygame')
    parser.add_argument('--frames',type=int,default=0,help='Exit after N frames (smoke test)')
    parser.add_argument('--screenshot',type=Path)
    args = parser.parse_args()
    Game().run(args.frames,args.screenshot)

if __name__=='__main__':
    main()
