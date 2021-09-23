from time import time
import math


class Vector:

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)



class Rectangular:

    def __init__(self, w, h):
        self.w = w
        self.h = h

    def setByCenter(self, x, y):
        self.tl = Vector(x - self.w // 2, y - self.w // 2)
        self.tr = Vector(self.tl.x + self.w - 1, self.tl.y)
        self.bl = Vector(self.tl.x, self.tl.y + self.h - 1)
        self.br = Vector(self.tl.x + self.w - 1, self.tl.y + self.h - 1)

    def setByTopLeft(self, x, y):
        self.tl = Vector(x, y)
        self.tr = Vector(x + self.w - 1, y)
        self.bl = Vector(x, y + self.h - 1)
        self.br = Vector(x + self.w - 1, y + self.h - 1)
    
    def isIntersectWith(self, other):
        for corner in [other.tl, other.tr, other.bl, other.br]:
            if (self.tl.x <= corner.x and corner.x <= self.tr.x and
                self.tl.y <= corner.y and corner.y <= self.bl.y):
                return True
        
        for corner in [self.tl, self.tr, self.bl, self.br]:
            if (other.tl.x <= corner.x and corner.x <= other.tr.x and
                other.tl.y <= corner.y and corner.y <= other.bl.y):
                return True
        
        return False


class RecoveryTool:

    def __init__(self, total_recovery_dur, act_duration, last_usage_time = 0):
        self.total_recovery_dur = total_recovery_dur
        self.act_duration = act_duration
        self.last_usage_time = last_usage_time
        self.used = False
    

    def getRecoveryTimeLeft(self):
        dif =  time() - self.last_usage_time
        return 0 if dif >= self.total_recovery_dur else self.total_recovery_dur - dif
    

    def getActiveTimeLeft(self):
        dif = time() - self.last_usage_time
        return 0 if dif >= self.act_duration else self.act_duration - dif
    

    def use(self):
        self.last_usage_time = time()
        self.used = True


    def canUse(self):
        return self.getRecoveryTimeLeft() == 0
