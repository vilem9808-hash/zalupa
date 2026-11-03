"""Gold framed, live fighting-game HUD inspired by the supplied reference."""
import math
from pathlib import Path
import pygame as pg
import pygame.gfxdraw as gfx
from roster import HEROES, NAMES, HERO_DATA

DARK = '#10101e'
GOLD = '#d49a46'
LIGHT = '#ffe3a0'


def bevel(surface, points, fill=DARK, width=3):
    pg.draw.polygon(surface,'#352039',points)
    pg.draw.polygon(surface,fill,points)
    pg.draw.polygon(surface,'#503015',points,width+3)
    pg.draw.polygon(surface,GOLD,points,width)
    pg.draw.lines(surface,LIGHT,False,points[:max(2,len(points)//2+1)],1)
    gfx.aapolygon(surface,[(round(x),round(y)) for x,y in points],pg.Color(GOLD))


def medallion(surface, center, radius, points=12):
    x,y=center
    vertices=[(x+math.cos(-math.pi/2+i*math.pi/points)*radius*(1 if i%2==0 else .77),
               y+math.sin(-math.pi/2+i*math.pi/points)*radius*(1 if i%2==0 else .77)) for i in range(points*2)]
    bevel(surface,vertices,width=3)
    pg.draw.circle(surface,GOLD,center,int(radius*.72),2)
    pg.draw.circle(surface,'#72502c',center,int(radius*.67),1)
    for j in range(points):
        angle = j*math.tau/points
        p1=(x+math.cos(angle)*radius*.78,y+math.sin(angle)*radius*.78)
        p2=(x+math.cos(angle+.11)*radius*.91,y+math.sin(angle+.11)*radius*.91)
        pg.draw.aaline(surface,LIGHT,p1,p2)


class HUD:
    def __init__(self, root, sprites):
        self.fonts={}
        self.root=Path(root)
        self.portraits={}
        self.trail={1:100.,2:100.}
        for name in HEROES:
            image=sprites[name]['idle'][0][0]
            bbox=image.get_bounding_rect(min_alpha=128)
            # Head and shoulders, keeping the rabbit's ears in the portrait.
            head=pg.Rect(bbox.x,bbox.y,bbox.width,int(bbox.height*HERO_DATA[name]['head']))
            upper=image.subsurface(head)
            trim=upper.get_bounding_rect(min_alpha=128)
            head=pg.Rect(head.x+trim.x,head.y+trim.y,trim.width,trim.height)
            crop=image.subsurface(head)
            scale=min(108/head.width,96/head.height)
            self.portraits[name]=pg.transform.smoothscale(crop,(round(head.width*scale),round(head.height*scale)))

    def label(self,surface,text,center,size=22,color=LIGHT):
        if size not in self.fonts:
            self.fonts[size]=pg.font.Font(str(self.root/'assets/title.ttf'),size)
        image=self.fonts[size].render(text,True,color)
        shadow=self.fonts[size].render(text,True,'#21111d')
        rect=image.get_rect(center=center)
        surface.blit(shadow,rect.move(2,2));surface.blit(image,rect)

    def reset(self):
        self.trail={1:100.,2:100.}

    def update(self, fighters, dt):
        for f in fighters:
            self.trail[f.id] = max(float(f.hp), self.trail[f.id]-30*dt) if f.hp<self.trail[f.id] else float(f.hp)

    def draw(self,screen,fighters,remaining,round_no,mode_ai=False):
        top=pg.Surface((1152,132),pg.SRCALPHA)
        for f in fighters:
            left=f.id==1
            def pts(points):
                return points if left else [(1152-x,y) for x,y in points]
            portrait_frame=pts([(10,10),(109,1),(137,30),(116,111),(21,117),(1,67)])
            bevel(top,portrait_frame)
            portrait=self.portraits[f.hero]
            if (HERO_DATA[f.hero]['face']>0) != left:portrait=pg.transform.flip(portrait,True,False)
            top.blit(portrait,portrait.get_rect(midbottom=(66 if left else 1086,107)))
            pg.draw.polygon(top,GOLD,portrait_frame,3)
            self.label(top,'P1' if left else 'ИИ' if mode_ai else 'P2',(66 if left else 1086,124),12)
            bevel(top,pts([(133,8),(280,8),(304,32),(125,32)]))
            self.label(top,NAMES[f.hero],(210 if left else 942,20),18 if len(NAMES[f.hero])>7 else 24)
            outer=pts([(134,39),(519,39),(538,73),(123,73)])
            bevel(top,outer)
            # Draw into a small mask to preserve the slanted end caps.
            bar=pg.Surface((398,24),pg.SRCALPHA)
            pg.draw.polygon(bar,'#351326',[(9,0),(384,0),(398,24),(0,24)])
            amount=int(384*f.hp/100)
            trail=int(384*self.trail[f.id]/100)
            for y in range(24):
                pg.draw.line(bar,'#f6d28d',(8,y),(8+trail,y))
                t=y/23
                color=(255,int(75+100*(1-t)),int(20+30*(1-t)))
                if amount:pg.draw.line(bar,color,(8,y),(8+amount,y))
            mask=pg.Surface((398,24),pg.SRCALPHA)
            pg.draw.polygon(mask,'white',[(9,0),(384,0),(398,24),(0,24)])
            bar.blit(mask,(0,0),special_flags=pg.BLEND_RGBA_MULT)
            pg.draw.line(bar,'#ffefa5',(12,2),(min(389,8+amount),2),2)
            if not left:bar=pg.transform.flip(bar,True,False)
            top.blit(bar,(130 if left else 624,44))
            for j in range(2):
                x=490-j*24 if left else 662+j*24
                pg.draw.circle(top,'#46241a',(x,92),8)
                pg.draw.circle(top,LIGHT,(x,92),8,2)
                if f.wins>j:pg.draw.circle(top,'#ffc76a',(x,92),4)
        medallion(top,(576,59),60)
        self.label(top,f'{math.ceil(remaining):02}',(576,50),44)
        self.label(top,str(round_no),(576,99),13)
        screen.blit(top,(0,56))
        # Live super meters at the bottom of the arena, mirroring the reference.
        bottom=pg.Surface((1152,62),pg.SRCALPHA)
        for f in fighters:
            left=f.id==1
            x=68 if left else 790
            bevel(bottom,[(x,22),(x+294,22),(x+310,34),(x+292,48),(x,48),(x-17,35)],width=2)
            n=int(282*f.energy/100)
            start=x+4 if left else x+286-n
            for y in range(26,44):
                color=(170+(y-26)*3,40+(y-26)*2,255) if left else (50,150+(y-26)*4,255)
                if n:pg.draw.line(bottom,color,(start,y),(start+n,y))
            for j in range(1,5):
                k=x+4+j*56
                pg.draw.line(bottom,'#f8d58d',(k+5,25),(k-4,44),1)
            medallion(bottom,(42 if left else 1110,34),30,4)
            self.label(bottom,str(f.energy//40),(42 if left else 1110,33),26)
        screen.blit(bottom,(0,642))
