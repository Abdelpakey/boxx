#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
useage:
    >>> import boxx.p
    
help(p) for more help
'''
from . import p, py2
if py2:
    p(1)
else:
    p(6)
#from . import *
#print(prettyFrameStack())
#fs = getFatherFrames(endByMain=1)
#list(map(pipe(prettyFrameLocation,log),fs))
if __name__ == '__main__':
    pass

