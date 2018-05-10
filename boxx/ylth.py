#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
sysc.py: system config
'''
from __future__ import unicode_literals

from . import *
from .ylsys import cpun, cloud, cuda, usecuda
from .ylimg import npa
from .tool import FunAddMagicMethod

from collections import OrderedDict
from functools import wraps

#if 'torch' in sys.modules:
#    del sys.modules[('torch')]
#    sys.modules.pop('torch')
import torch
#from imp import reload  
#reload(torch)
#reload(torch.nn)
#reload(torch.nn.modules.module)
#import importlib
#torch = importlib.reload(torch)
from torch.autograd import Variable
import torch.utils.data
th = torch
nn = th.nn


# default whether choose cuda
#th.long = torch.cuda.LongTensor 
#th.double = torch.cuda.DoubleTensor 
#th.int = torch.cuda.IntTensor 
#th.short = torch.cuda.ShortTensor 
#th.byte = torch.cuda.ByteTensor 
#th.half = torch.cuda.HalfTensor 
#th.char = torch.cuda.CharTensor 
#th.float = torch.cuda.FloatTensor 

# add summary to torch.nn.Module
from torchsummary import summary
nn.Module.summary = lambda self, inputShape=(3,244,244):summary(self, inputShape)


def dedp(model):
    '''get raw model instead of torch.nn.DataParallel '''
    return model.module if isinstance(model, torch.nn.DataParallel) else model

usecpu = (not cuda and usecuda=='auto') or not usecuda
if usecpu:
    cudaAttri =  lambda self,*l,**kv:self
    nn.Module.cuda = cudaAttri
    Variable.cuda = cudaAttri
    torch.Tensor.cuda = cudaAttri
    
    
#    class FakeDataParallel(torch.nn.DataParallel):
#        def __init__(self, x):
#            super(FakeDataParallel, self).__init__()
    torch.nn.DataParallel = cudaAttri
    
    class withh():
        def __init__(self, *l):
            pass
        def __call__(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, typee, value, traceback):
            pass
    torch.cuda.device = withh

    th.cuda.LongTensor = th.LongTensor
    th.cuda.DoubleTensor = th.DoubleTensor
    th.cuda.IntTensor = th.IntTensor
    th.cuda.ShortTensor = th.ShortTensor
    th.cuda.ByteTensor = th.ByteTensor
    th.cuda.HalfTensor = th.HalfTensor
    th.cuda.CharTensor = th.CharTensor
    th.cuda.FloatTensor = th.FloatTensor
    
    rawDataLoader = th.utils.data.DataLoader
    from functools import wraps    
#    def warp(f):
#        @wraps(f)
#        def DataLoader(*l, **kv):
#            if 'pin_memory' in kv:
#                kv.pop('pin_memory')
#            r = f(*l, **kv)
#            return r
#        return DataLoader
    
    class DataLoaderForCPU(rawDataLoader):
        def __init__(self, *l, **kv):
            rawDataLoader.__init__(self, *l, **kv)
            self.pin_memory = False
        
    th.utils.data.DataLoader = DataLoaderForCPU
    
    rawThLoad = torch.load
    def torchLoad(*l, **kv):
        return rawThLoad(*l,**(kv.update({'map_location':'cpu'}) or kv))
    torch.load = torchLoad
    if 'Module' in str(torch.nn.Module.load_state_dict):
        torch.rawModule = rawModule = torch.nn.Module.load_state_dict
    else :
        rawModule = torch.rawModule 
    def tryLoad(self, state_dict, strict=True):
        try:
            rawModule(self, state_dict, strict)
        except (KeyError,RuntimeError) as e:
            print('\x1b[31m%s\x1b[0m' % '\n"try strict=False! in Module.load_state_dict() " messge from boxx.ylth \n')
            para = state_dict
            para = OrderedDict(
                        [(k.replace('module.', ''),v) for k,v in para.items()]
                )
            rawModule(self, para, strict)
            
    nn.Module.load_state_dict = tryLoad
    torch.nn.modules.module.Module.load_state_dict = tryLoad

_TensorBase = torch._TensorBase if '_TensorBase' in dir(torch) else torch._C._TensorBase

def tht(t):
    '''
    anything t to torch.Tensor
    '''
    if not isinstance(t, _TensorBase):
        t = th.from_numpy(npa-t).cuda()
    return t.cuda()
tht = FunAddMagicMethod(tht)

t = tht(r)

@wraps(torch.autograd.Variable)
def var(t, *l,  **kv):
    t = tht(t)
    t = Variable(t, *l, **kv)
    return t.cuda()
var = FunAddMagicMethod(var)


def kaimingInit(model):
    stateDict = model.state_dict()
    for key in stateDict:
        tag = 0
        t = stateDict[key]
        
        if (t.ndimension()==4 and t.shape[-1]>2) or 'conv' in key:
            nn.init.kaiming_normal(stateDict[key], mode='fan_out')
            tag = 1
        elif 'bn' in key and 'weight' in key:
            stateDict[key][...] = 1
            tag = 1
        elif 'bias' in key :
            stateDict[key][...] = 0
            tag = 1
        elif 'fc' in key and t.ndimension()==2:
            nn.init.kaiming_normal(t)


if __name__ == '__main__':
    l = ['LongTensor',
     'DoubleTensor',
     'IntTensor',
     'ShortTensor',
     'ByteTensor',
     'HalfTensor',
     'CharTensor',
     'FloatTensor']
    formatt = 'th.cuda.%s = th.%s'
    print('\n'.join([formatt%(i,i) for i in l]))

        
    
