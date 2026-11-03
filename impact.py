"""Contact burst rendering; effects only exist for successful hits and guards."""
import math
import pygame as pg


def draw_impacts(surface, impacts):
    for effect in impacts:
        x,y,life,total,guarded,direction,power=effect
        age=1-life/total
        radius=(14+power*.7)*(1+age*1.5)
        color='#90ddff' if guarded else '#ffc34d'
        overlay=pg.Surface((300,300),pg.SRCALPHA)
        alpha=int(220*(1-age))
        c=pg.Color(color);c.a=alpha
        pg.draw.circle(overlay,c,(150,150),max(1,int(radius)),2)
        for j in range(12 if not guarded else 8):
            angle=j*math.tau/(12 if not guarded else 8)+.19
            inner=radius*(.22+age*.6)
            outer=radius*(1.25+(j%3)*.25)
            p1=(150+math.cos(angle)*inner,150+math.sin(angle)*inner)
            p2=(150+math.cos(angle+.035)*outer,150+math.sin(angle+.035)*outer)
            p3=(150+math.cos(angle-.10)*inner,150+math.sin(angle-.10)*inner)
            pg.draw.polygon(overlay,c,[p1,p2,p3])
        pg.draw.circle(overlay,(255,251,215,alpha),(150,150),max(1,int(8*(1-age))))
        surface.blit(overlay,(x-150,y-150))
