"""Original comic styled menu: diagonal panels, halftones and bold lettering."""
import math
import pygame as pg
import pygame.gfxdraw as gfx

NAMES={'wolf':'ВОЛК','rabbit':'ЗАЯЦ'}
HEROES=('wolf','rabbit')
PURPLE='#9c39dc';YELLOW='#ffdf59';PINK='#ed437e';TEAL='#4fe1d6';INK='#171027'


class Menu:
    def __init__(self,game):
        self.game=game
        self.fonts={}
        self.focus=0
        self.cursor=0
        self.stage=0
        self.choice=['wolf','rabbit']
        self.hover=None
        self.dragging=False
        self.message=''
        self.background=self.make_background()
        self.heroes={}
        self.card_heroes={}
        self.roster_portraits={}
        for name in HEROES:
            image=game.sprites[name]['idle'][0][0]
            crop=image.subsurface(image.get_bounding_rect(min_alpha=128))
            factor=320/crop.get_height()
            self.heroes[name]=pg.transform.smoothscale(crop,(round(crop.get_width()*factor),320))
            self.card_heroes[name]=pg.transform.smoothscale(crop,(round(crop.get_width()*270/crop.get_height()),270))
            head=crop.subsurface((0,0,crop.get_width(),round(crop.get_height()*(.46 if name=='wolf' else .51))))
            head=head.subsurface(head.get_bounding_rect(min_alpha=128))
            factor=min(144/head.get_width(),150/head.get_height())
            self.roster_portraits[name]=pg.transform.smoothscale(head,(round(head.get_width()*factor),round(head.get_height()*factor)))

    def font(self,size,display=False):
        key=size,display
        if key not in self.fonts:
            self.fonts[key]=pg.font.Font(str(self.game.root/('assets/title.ttf' if display else 'assets/ui.ttf')),size)
        return self.fonts[key]

    def text(self,surface,text,pos,size=24,color='white',display=False,center=False):
        font=self.font(size,display)
        image=font.render(text,True,color)
        rect=image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        shadow=font.render(text,True,'#110a20')
        if color!=INK:surface.blit(shadow,rect.move(3,3))
        surface.blit(image,rect)

    def make_background(self):
        s=pg.Surface((1152,760));s.fill('#241235')
        pg.draw.polygon(s,'#642994',[(0,0),(790,0),(300,760),(0,760)])
        pg.draw.polygon(s,'#c03a86',[(0,595),(400,760),(0,760)])
        pg.draw.polygon(s,'#36205a',[(1152,0),(960,0),(510,760),(1152,760)])
        pg.draw.polygon(s,'#f7cf55',[(0,70),(1152,0),(1152,18),(0,91)])
        for x in range(12,1152,20):
            for y in range(12,760,20):
                pg.draw.circle(s,'#49255f' if x>600 else '#8444aa',(x,y),2)
        for j in range(19):
            angle=j*math.tau/19
            center=(350,420)
            p=(center[0]+math.cos(angle)*1200,center[1]+math.sin(angle)*1200)
            pg.draw.aaline(s,'#b667c9',center,p)
        shade=pg.Surface((1152,760),pg.SRCALPHA)
        pg.draw.polygon(shade,(13,8,24,215),[(592,190),(1152,140),(1152,760),(470,760)])
        s.blit(shade,(0,0))
        return s

    def buttons(self,scene):
        g=self.game
        if scene=='main':
            return [('pvp',pg.Rect(625,272,450,76),'ИГРОК ПРОТИВ ИГРОКА'),
                    ('ai',pg.Rect(605,371,450,76),'ИГРОК ПРОТИВ ИИ'),
                    ('settings',pg.Rect(585,470,450,76),'НАСТРОЙКИ'),
                    ('quit',pg.Rect(565,569,450,76),'ВЫХОД')]
        if scene=='select':
            return [('wolf',pg.Rect(656,302,168,218),'ВОЛК'),('rabbit',pg.Rect(856,302,168,218),'ЗАЯЦ'),
                    ('back',pg.Rect(65,655,230,61),'НАЗАД'),
                    ('confirm',pg.Rect(735,655,350,61),'НАЧАТЬ БОЙ' if self.stage else 'ПОДТВЕРДИТЬ')]
        if scene=='settings':
            return [('fullscreen',pg.Rect(190,235,772,72),'ПОЛНЫЙ ЭКРАН: '+('ВКЛ' if g.preferences['fullscreen'] else 'ВЫКЛ')),
                    ('shake',pg.Rect(190,332,772,72),'ТРЯСКА КАМЕРЫ: '+('ВКЛ' if g.preferences['camera_shake'] else 'ВЫКЛ')),
                    ('volume',pg.Rect(190,431,772,119),'ГРОМКОСТЬ МУЗЫКИ'),
                    ('back',pg.Rect(380,634,390,66),'НАЗАД')]
        if scene=='pause':
            return [('resume',pg.Rect(370,285,430,78),'ПРОДОЛЖИТЬ'),('settings',pg.Rect(350,390,430,78),'НАСТРОЙКИ'),('main',pg.Rect(330,495,430,78),'ГЛАВНОЕ МЕНЮ')]
        return []

    def panel(self,surface,rect,color=YELLOW,selected=False):
        x,y,w,h=rect
        pts=[(x+15,y),(x+w,y-5),(x+w-15,y+h),(x,y+h+5)]
        pg.draw.polygon(surface,'#0d0817',[(a+7,b+8) for a,b in pts])
        pg.draw.polygon(surface,color if selected else '#211630',pts)
        pg.draw.polygon(surface,color,pts,3)
        gfx.aapolygon(surface,pts,pg.Color(color))

    def render(self,surface,scene):
        surface.blit(self.background,(0,0))
        if scene=='main':
            self.text(surface,'ВОЛК',(60,112),65,YELLOW,True)
            self.text(surface,'vs ЗАЯЦ',(72,181),57,'white',True)
            self.text(surface,'ГАЛАКТИЧЕСКАЯ ДУЭЛЬ',(82,252),19,TEAL)
            wolf=self.heroes['wolf'];rabbit=self.heroes['rabbit']
            surface.blit(wolf,wolf.get_rect(midbottom=(220,679)))
            surface.blit(rabbit,rabbit.get_rect(midbottom=(430,680)))
            tag=self.font(56,True).render('ГО-ГО-ГО',True,PINK)
            surface.blit(pg.transform.rotate(tag,12),(38,299))
            self.text(surface,'BIZARRE / BATTLE',(653,184),32,YELLOW,True)
            self.text(surface,'01   ВЫБЕРИ СВОЙ ПУТЬ',(656,228),17,TEAL)
        elif scene=='select':
            self.text(surface,'ВЫБОР ГЕРОЯ',(576,69),49,YELLOW,True,True)
            role='ИГРОК 1' if self.stage==0 else ('СОПЕРНИК: ИИ' if self.game.mode_ai else 'ИГРОК 2')
            self.text(surface,role,(576,137),28,TEAL if self.stage==0 else PINK,True,True)
            self.text(surface,'ВЫБЕРИТЕ БОЙЦА И ПОДТВЕРДИТЕ',(576,184),18,'white',False,True)
            selected_name=HEROES[self.cursor]
            accent=TEAL if self.stage==0 else PINK
            self.panel(surface,pg.Rect(75,225,460,373),'#b18bca')
            self.text(surface,NAMES[selected_name],(305,250),30,YELLOW,True,True)
            char=self.heroes[selected_name]
            if selected_name=='rabbit':char=pg.transform.flip(char,True,False)
            surface.blit(char,char.get_rect(midbottom=(305,589)))
            self.panel(surface,pg.Rect(611,225,465,373),'#b18bca')
            self.text(surface,'ВЫБЕРИТЕ БОЙЦА',(844,252),23,YELLOW,True,True)
            for i,name in enumerate(HEROES):
                rect=self.buttons(scene)[i][1]
                selected=i==self.cursor
                self.panel(surface,rect,accent if selected else '#735780')
                portrait=self.roster_portraits[name]
                surface.blit(portrait,portrait.get_rect(center=(rect.centerx,rect.y+96)))
                self.text(surface,f'{i+1:02}',(rect.x+13,rect.y+8),14,accent if selected else '#bfa6cd')
                self.text(surface,NAMES[name],(rect.centerx,rect.bottom-27),23,YELLOW,True,True)
                if selected:
                    pg.draw.rect(surface,accent,(rect.x+18,rect.bottom-7,rect.width-30,4))
            self.text(surface,'ВЫБРАН: '+NAMES[selected_name],(844,556),19,accent,False,True)
            self.text(surface,'P1: '+NAMES[self.choice[0]],(100,615),20,TEAL)
            self.text(surface,('ИИ: ' if self.game.mode_ai else 'P2: ')+NAMES[self.choice[1]],(840,615),20,PINK)
            self.text(surface,'Можно выбрать одинаковых героев',(576,617),17,'#d5bfe4',False,True)
        elif scene=='settings':
            self.text(surface,'НАСТРОЙКИ',(576,133),53,YELLOW,True,True)
            self.text(surface,'Тряска камеры отключена по умолчанию',(576,200),18,TEAL,False,True)
            self.text(surface,'F11 — переключить экран в любой момент',(576,583),18,'white',False,True)
            if not self.game.music.available:self.text(surface,'Аудиоустройство недоступно — игра продолжится без музыки',(576,611),15,PINK,False,True)
            elif self.message:self.text(surface,self.message,(576,611),16,PINK,False,True)
        elif scene=='pause':
            self.text(surface,'ПАУЗА',(576,163),64,YELLOW,True,True)
        for i,(action,rect,label) in enumerate(self.buttons(scene)):
            if scene=='select' and action in HEROES:continue
            focused=self.hover==action or (self.hover is None and i==self.focus)
            self.panel(surface,rect,YELLOW,focused)
            if action=='volume':
                value=self.game.preferences['music_volume']
                color=INK if focused else 'white'
                self.text(surface,f'ГРОМКОСТЬ МУЗЫКИ: {value}%',(576,459),22,color,True,True)
                track=self.volume_track()
                pg.draw.rect(surface,'#594064',track,border_radius=4)
                width=round(track.width*value/100)
                if width:pg.draw.rect(surface,TEAL,(track.x,track.y,width,track.height),border_radius=4)
                pg.draw.circle(surface,INK,(track.x+width,track.centery),13)
                pg.draw.circle(surface,TEAL,(track.x+width,track.centery),10)
                self.text(surface,'0%',(track.x-39,track.y-8),16,color)
                self.text(surface,'100%',(track.right+13,track.y-8),16,color)
                self.text(surface,'Перетяните ползунок или используйте ← / →',(576,530),15,color,False,True)
            else:self.text(surface,label,rect.center,21 if len(label)>22 else 24,INK if focused else 'white',True,True)
        self.text(surface,'МЫШЬ / ← → ↑ ↓ / ENTER — выбор     ESC — назад',(576,741),15,'#ddd0e9',False,True)

    def volume_track(self):
        return pg.Rect(268,494,616,9)

    def drag_volume(self,point):
        track=self.volume_track()
        self.game.set_music_volume(100*(point[0]-track.x)/track.width,save=False)

    def finish_drag(self):
        if self.dragging:
            self.dragging=False
            self.game.save_preferences()

    def activate(self,action):
        self.finish_drag()
        g=self.game
        previous_scene=g.scene
        if action in ('ai','pvp'):
            g.mode_ai=action=='ai';g.scene='select'
            self.stage=0;self.cursor=HEROES.index(g.selected_heroes[0]);self.choice=list(g.selected_heroes)
        elif action in HEROES:
            self.cursor=HEROES.index(action);self.choice[self.stage]=action
        elif action=='confirm':
            self.choice[self.stage]=HEROES[self.cursor]
            if self.stage==0:
                self.stage=1;self.cursor=HEROES.index(self.choice[1])
            else:
                g.selected_heroes=list(self.choice);g.new_match();g.scene='battle';g.keys.clear();g.pressed.clear()
        elif action=='settings':
            g.settings_return=g.scene;g.scene='settings';self.message=''
        elif action=='fullscreen':g.set_fullscreen(not g.preferences['fullscreen'])
        elif action=='shake':
            g.preferences['camera_shake']=not g.preferences['camera_shake'];g.save_preferences()
        elif action=='back':
            if g.scene=='select' and self.stage:
                self.stage=0;self.cursor=HEROES.index(self.choice[0])
            else:g.scene=g.settings_return if g.scene=='settings' else 'main'
        elif action=='resume':g.scene='battle';g.paused=False;g.keys.clear();g.pressed.clear()
        elif action=='main':g.scene='main';g.paused=False;g.keys.clear();g.pressed.clear()
        elif action=='quit':g.running=False
        if g.scene!=previous_scene:self.focus=0
        elif action in ('fullscreen','shake','volume'):
            self.focus=next(i for i,(a,_,_) in enumerate(self.buttons(g.scene)) if a==action)
        self.hover=None

    def event(self,event,point=None):
        scene=self.game.scene
        buttons=self.buttons(scene)
        if event.type==pg.MOUSEBUTTONUP and getattr(event,'button',None)==1:
            self.finish_drag();return
        if scene=='settings':
            if event.type==pg.MOUSEMOTION and self.dragging and point is not None:
                self.drag_volume(point);return
            if event.type==pg.MOUSEBUTTONDOWN and event.button==1 and point is not None and self.volume_track().inflate(40,40).collidepoint(point):
                self.focus=2;self.hover='volume';self.dragging=True;self.drag_volume(point);return
            if event.type==pg.KEYDOWN and self.focus==2 and event.key in (pg.K_LEFT,pg.K_RIGHT,pg.K_HOME,pg.K_END):
                v=self.game.preferences['music_volume']
                v=0 if event.key==pg.K_HOME else 100 if event.key==pg.K_END else v+(-5 if event.key==pg.K_LEFT else 5)
                self.game.set_music_volume(v);return
        if event.type==pg.MOUSEMOTION and point is not None:
            self.hover=next((a for a,r,t in buttons if r.collidepoint(point)),None)
        if event.type==pg.MOUSEBUTTONDOWN and event.button==1 and point is not None:
            for action,rect,label in buttons:
                if rect.collidepoint(point):self.activate(action);return
        if event.type!=pg.KEYDOWN or getattr(event,'repeat',False):return
        if scene=='pause' and event.key==pg.K_p:
            self.activate('resume');return
        if event.key==pg.K_ESCAPE:
            self.activate('resume' if scene=='pause' else 'quit' if scene=='main' else 'back');return
        if scene=='select':
            if event.key in (pg.K_LEFT,pg.K_RIGHT,pg.K_a,pg.K_d):
                self.cursor=1-self.cursor;self.choice[self.stage]=HEROES[self.cursor]
            elif event.key in (pg.K_RETURN,pg.K_SPACE,pg.K_j,pg.K_u):self.activate('confirm')
        elif event.key in (pg.K_UP,pg.K_DOWN,pg.K_w,pg.K_s):
            self.focus=(self.focus+(-1 if event.key in (pg.K_UP,pg.K_w) else 1))%len(buttons);self.hover=None
        elif event.key in (pg.K_RETURN,pg.K_SPACE):self.activate(buttons[self.focus][0])
