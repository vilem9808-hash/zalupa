"""Fixed zoom for the battle world; interface stays at its original size."""
class BattleCamera:
    def __init__(self,width=1152,height=648,ground=523,zoom=.76):
        if not 0<zoom<=1:raise ValueError('Zoom must be between 0 and 1')
        self.size=(width,height)
        self.world_size=(round(width/zoom),round(height/zoom))
        self.scale=(width/self.world_size[0],height/self.world_size[1])
        self.origin=((self.world_size[0]-width)/2,ground/self.scale[1]-ground)

    def project(self,x,y):
        return ((x+self.origin[0])*self.scale[0],(y+self.origin[1])*self.scale[1])
