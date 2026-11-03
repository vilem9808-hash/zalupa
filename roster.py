"""Shared hero identities for battle, portraits and the selection grid."""
HERO_DATA={
    'wolf':dict(name='ВОЛК',face=1,height=367,head=.46,hip=.48,color='#ffb06a'),
    'rabbit':dict(name='ЗАЯЦ',face=-1,height=346,head=.51,hip=.65,color='#a5eaff'),
    'matroskin':dict(name='МАТРОСКИН',face=1,height=367,head=.46,hip=.48,color='#ff6c69'),
    'pechkin':dict(name='ПЕЧКИН',face=1,height=380,head=.40,hip=.55,color='#ffe080'),
}
HEROES=tuple(HERO_DATA)
NAMES={key:value['name'] for key,value in HERO_DATA.items()}
