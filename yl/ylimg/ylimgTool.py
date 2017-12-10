# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from tool.toolStructObj import FunAddMagicMethod, typeNameOf, typestr
from tool.toolLog import colorFormat, tounicode
from tool.toolFuncation import mapmp, pipe

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import cv2
import skimage as sk
from skimage import io as sio
from skimage import data as da
from skimage.io import imread
from skimage.io import imsave
from skimage.transform import resize 

# randomm((m, n), max) => m*n matrix
# randomm(n, max) => n*n matrix
randomm = lambda shape,maxx:(np.random.random(
shape if (isinstance(shape,tuple) or isinstance(shape,list)
)else (shape,shape))*maxx).astype(int)
r = randomm(4,4)

def normalizing(arr):
    a = arr.astype(float)
    minn = a.min()
    return (a-minn)/(a.max() - minn)
normalizing = FunAddMagicMethod(normalizing)
norma = normalizing

def uint8(img):
    '''将0～1的float或bool值的图片转换为uint8格式'''
    return ((img)*255.999).astype(np.uint8)

greyToRgb = lambda grey:grey.repeat(3).reshape(grey.shape+(3,)) 

npa = FunAddMagicMethod(np.array)

def tprgb(ndarray):
    '''
    transpose to RGB, 将3*h*w的ndarray化为 h*w*3的RGB图
    即shape为 (...,3 , h, w)的ndarray转化为(..., h, w, 3)
    '''
    shape = ndarray.shape
    ndim = ndarray.ndim
    if ndim >= 3 and shape[-3] == 3:
        axes = list(range(ndim))[:-3]+[ndim-2,ndim-1,ndim-3]
        return ndarray.transpose(*axes)
    return ndarray
def mapp(f, matrix, need_i_j=False):
    '''
    for each item of a 2-D matrix
    return a new matrix consist of f:f(it) or f(it, i, j)
    性能差 尽量用y, x = np.mgrid[:10,:10]
    '''
    m, n = matrix.shape[:2]
    listt = [[None]*n for i in range(m)]
    for i in range(m):
        for j in range(n):
            it = matrix[i][j]
            listt[i][j] = f(it,i,j) if need_i_j else f(it)
    return np.array(listt)


from operator import add
def ndarrayToImgLists(arr):
    '''
    将所有ndarray转换为imgList
    '''
    arr = np.squeeze(arr)
    ndim = arr.ndim
    if arr.ndim==2 or (arr.ndim ==3 and arr.shape[-1] in [3,4]):
         return [arr]
    if arr.shape[-1] == 2: # 二分类情况下自动转换
        arr = arr.transpose(list(range(ndim))[:-3]+[ndim-1,ndim-3,ndim-2])
    imgdim = 3 if arr.shape[-1] in [3,4] else 2
    ls = list(arr)
    while ndim-1>imgdim:
        ls = reduce(add,map(list,ls),[])
        ndim -=1
    return ls

__torchToNumpy = lambda x:x.numpy()

__typesToNumpy = {
    'PIL.Image.Image':lambda x:np.array(x),
    'mxnet.ndarray.NDArray':lambda x:x.asnumpy(),
    
    'torch.FloatTensor':__torchToNumpy,
    'torch.DoubleTensor':__torchToNumpy,
    'torch.IntTensor':__torchToNumpy,
    'torch.LongTensor':__torchToNumpy,
    'torch.ShortTensor':__torchToNumpy,
    'torch.ByteTensor':__torchToNumpy,
    'torch.HalfTensor':__torchToNumpy,
    'torch.CharTensor':__torchToNumpy,
    }

def listToImgLists(l, res=None,doNumpy=ndarrayToImgLists):
    '''
    将 ndarray和list的混合结果树转换为 一维 img list
    '''
    if res is None:
        res = []
    for x in l:
        typeName = typestr(x)
        if typeName in __typesToNumpy:
            ndarray = __typesToNumpy[typeName](x)
            res.extend(doNumpy(ndarray))
        elif isinstance(x,(list,tuple)):
            listToImgLists(x,res=res,doNumpy=doNumpy)
        elif isinstance(x,dict):
            listToImgLists(x.values(),res=res,doNumpy=doNumpy)
        elif isinstance(x,np.ndarray):
            res.extend(doNumpy(x))
    return res
def showImgLists(imgs,**kv):
    n = len(imgs)
    if n == 4:
        showImgLists(imgs[:2],**kv)
        showImgLists(imgs[2:],**kv)
        return
    if n > 4:
        showImgLists(imgs[:3],**kv)
        showImgLists(imgs[3:],**kv)
        return 
    fig, axes = plt.subplots(ncols=n)
    count = 0
    axes = [axes] if n==1 else axes 
    for img in imgs:
        axes[count].imshow(img,**kv)
        count += 1
    plt.show()
def show(*imgsAndFuns,**kv):
    '''
    找出一个复杂结构中的所有numpy 转换为对应的图片并plt.show()出来
    
    Parameters
    ----------
    imgsAndFuns : list/tuple/dict 
    '''
    if 'cmap' not in kv:
        kv['cmap'] = 'gray'
    funs = [arg for arg in imgsAndFuns[1:] if callable(arg)]
    doNumpy = pipe(funs+[ndarrayToImgLists])
    imgls = listToImgLists(imgsAndFuns,doNumpy=doNumpy)
    assert len(imgls)!=0,"funcation `show`'s args `imgs`  has no any np.ndarray! "
    showImgLists(imgls,**kv)
show = FunAddMagicMethod(show)


def showb(*arr,**__kv):
    '''
    use shotwell to show picture
    Parameters
    ----------
    arr : np.ndarray or path
    '''
    
    if len(arr)!=1:
        map(lambda ia:showb(ia[1],tag=ia[0]),enumerate(arr))
        return 
    arr = arr[0]
    if isinstance(arr,np.ndarray):
        path = '/tmp/tmp-%s.png'%len(glob.glob('/tmp/tmp-*.png'))
        imsave(path,arr)
        arr = path
    cmd = 'shotwell "%s" &'%arr
    os.system(cmd)
showb = FunAddMagicMethod(showb)

def shows(*imgs):
    '''图片展示分析工具  使用浏览器同步显示同一图像的不同数据表示 如不同通道的image,gt,resoult 
    支持放大缩小与拖拽
    
    Parameters
    ----------
    imgs : list include path or np.ndarray 
        图片地址或图片np.ndarray 组成的list 要求所有图片宽高相同
    '''
    def listToPathList(l, res=None):
        if res is None:
            res = []
        for x in l:
            if isinstance(x,(list,tuple)):
                listToPathList(x,res)
            if isinstance(x,dict):
                listToPathList(x.values(),res)
            if isinstance(x,(str,unicode)):
                res.append(x)
            if isinstance(x,np.ndarray):
                path = '/tmp/shows-%s.png'%len(glob.glob('/tmp/shows-*.png'))
                imsave(path,x)
                res.append(path)
        return res
    paths = listToPathList(imgs)
    from showImgsInBrowser import showImgsInBrowser
    showImgsInBrowser(paths)
shows = FunAddMagicMethod(shows)

def loga(array):
    '''
    Analysis np.array with a graph. include shape, max, min, distribute
    '''
    typeName = typestr(array)
    if typeName in __typesToNumpy:
        array = __typesToNumpy[typeName](array)
    if isinstance(array,str) or isinstance(array,unicode):
        print 'info and histogram of',array
        l=[]
        eval('l.append('+array+')')
        array = l[0]
    if isinstance(array,list):
        array = np.array(array)
    print 'shape:%s ,type:%s ,max: %s, min: %s'%(str(array.shape),array.dtype.type, str(array.max()),str(array.min()))
    
    unique = np.unique(array)
    if len(unique)<10:
        dic=dict([(i*1,0) for i in unique])
        for i in array.ravel():
            dic[i] += 1
        listt = dic.items()
        listt.sort(key=lambda x:x[0])
        data,x=[v for k,v in listt],np.array([k for k,v in listt]).astype(float)
        if len(x) == 1:
            print 'All value is',x[0]
            return
        width = (x[0]-x[1])*0.7
        x -=  (x[0]-x[1])*0.35
    else:
        data, x = np.histogram(array.ravel(),8)
        x=x[1:]
        width = (x[0]-x[1])
    plt.plot(x, data, color = 'orange')
    plt.bar(x, data,width = width, alpha = 0.5, color = 'b')
    plt.show()
    return 

loga = FunAddMagicMethod(loga)

__torchShape = lambda x:'%s %s'%(str(x.shape),x.type())
__logFuns = {
    'list':lambda x:colorFormat.b%('list  %d'%len(x)),
    'tuple':lambda x:colorFormat.b%('tuple %d'%len(x)),
    'dict':lambda x:colorFormat.b%('dict  %s'%len(x)),
    'dicto':lambda x:colorFormat.b%('dicto  %s'%len(x)),
    'tool.toolStructObj.dicto':lambda x:colorFormat.b%('dicto  %s'%len(x)),
    'tool.toolLog.SuperG':lambda x:colorFormat.b%('SuperG  %s'%len(x)),
    'numpy.ndarray':lambda x:colorFormat.r%('%s%s'%
                                    (unicode(x.shape).replace('L,','').replace('L',''),x.dtype)),


    'torch.FloatTensor':__torchShape,
    'torch.DoubleTensor':__torchShape,
    'torch.IntTensor':__torchShape,
    'torch.LongTensor':__torchShape,
    'torch.ShortTensor':__torchShape,
    'torch.ByteTensor':__torchShape,
    'torch.HalfTensor':__torchShape,
    'torch.CharTensor':__torchShape,
    
    'mxnet.ndarray.NDArray':lambda x:'mxnet.NDArray%s'%str(x.shape),
    }


def __discribOfInstance(instance,leafColor=None,MAX_LEN=45):
    typee = type(instance)
    typen = typeNameOf(typee)
#    print typen,typen in __logFuns
    if typen in __logFuns:
        return __logFuns[typen](instance)
    s = tounicode(instance)
    if len(s) > MAX_LEN:
        s = s[:MAX_LEN-3]+'...'
    return (leafColor or '%s')%s


def tree(seq,deep=None,leafColor=u'\x1b[31m%s\x1b[0m',__key=u'/',__leftStr=None, __islast=None,__deepNow=0, __sets=None):
    '''
    类似bash中的tree命令 简单查看list, tuple, dict, numpy组成的树的每一层结构
    可迭代部分用蓝色 叶子用红色打印 
    >>>tree(seq) 
    
    Parameters
    ----------
    seq : list or tuple or dict or numpy or any Object
        打印出 以树结构展开所有可迭代部分
    deep : int, default None
        能显示的最深深度, 默认不限制
    
    ps.可在__logFuns中 新增类别
    '''
    if deep and __deepNow > deep:
        return
    if __leftStr is None:
        __leftStr = [] 
        __islast = 1
        __sets = set()
#    s = __logFuns.get(type(seq),lambda x:colorFormat.r%tounicode(x)[:60])(seq)
    s = __discribOfInstance(seq,leafColor=leafColor)
    s = s.replace('\n',u'↳')
#    print ''.join(__leftStr)+u'├── '+tounicode(k)+': '+s
    print u'%s%s %s: %s'%(u''.join(__leftStr), u'└──' if __islast else u'├──',tounicode(__key),s)
    if isinstance(seq,(list,tuple,dict)) :
        if id(seq) in __sets:
            seq=[(colorFormat.r%u'【printed befor】','')]
        else:
            __sets.add(id(seq))
            if isinstance(seq,(list,tuple)):
                seq = list(enumerate(seq))
            elif isinstance(seq,(dict)):
                seq = list(seq.items())
    else:
        return 
    __leftStr.append(u'    'if __islast else u'│   ')
    for i,kv in enumerate(seq):
        __key,v = kv
        tree(v,deep=deep, leafColor=leafColor, __key=__key, __leftStr=__leftStr, 
             __islast=(i==len(seq)-1),__deepNow=__deepNow+1,__sets=__sets)
    __leftStr.pop()
tree = FunAddMagicMethod(tree)

def __typee__(x):
    return tounicode(type(x)).split("'")[1]

logModFuns = {
 type(os):lambda x:colorFormat.r%(__typee__(x)),
 }
logMod = lambda mod:logModFuns.get(type(mod),lambda x:colorFormat.b%tounicode(__typee__(x))[:60])(mod)
def treem(mod,types=None,deep=None,__leftStrs=None,__name=u'/',__islast=None,__deepNow=0,__rootDir=None,__sets=None):
    '''
    类似bash中的tree命令 查看module及子module的每一层结构
    一目了然module的结构和api
    module用红色显示 其余部分用蓝色显示
    >>>treem(os)
    
    Parameters
    ----------
    mod : module
        显示出 以树结构展开module及其子module
        type(mod) should => module
    types : list of types, default None
        需要显示出来的类型(module 类型会自动添加)
        默认显示所有类型
    deep : int, default None
        能显示的最深深度
        默认不限制
    '''
    if deep and __deepNow > deep:
        return
    if __leftStrs is None:
        __leftStrs = [] 
        __islast = 1
        if '__file__' not in dir(mod): 
            print 'type(%s: %s) is not module!'%(logMod(mod),tounicode(mod))
            return 
        __rootDir = os.path.dirname(mod.__file__)
        __sets = set()
    typeStr = logMod(mod)
    modKinds = ['','','(not sub-module)','(printed befor)']
    modKind = 0
    if isinstance(mod,type(os)):
        if '__name__' in dir(mod) :
            __name = mod.__name__
        modKind = 1
        dirMod = dir(mod)
        if  mod in __sets:
            modKind = 3 
        elif '__file__' not in dir(mod) or __rootDir not in mod.__file__:
            modKind = 2
    names = (tounicode(__name)+('   ' if modKind<2 else u'  ·' )*20)[:40]+modKinds[modKind]
    
    print u'%s%s %s: %s'%(u''.join(__leftStrs), u'└──' if __islast else u'├──',typeStr,names)
    
    if modKind !=1:
        return
    __sets.add(mod)
    dirMod = [i for i in dirMod if i not in ['__name__','__file__','unicode_literals']]
    if types is not None:
        dirMod=[i for i in dirMod if type(mod.__getattribute__(i)) in  list(types)+[type(os)]] 
    __leftStrs.append(u'    'if __islast else u'│   ')
    for i,name in enumerate(dirMod):
        e = mod.__getattribute__(name)
        treem(e,types,deep,__leftStrs,name,__islast=(i==len(dirMod)-1),__deepNow=__deepNow+1,__rootDir=__rootDir,__sets=__sets)
    __leftStrs.pop()
treem = FunAddMagicMethod(treem)


def __dira(seq,instance=None, maxDocLen=50, deep=None, __leftStr=None,__key=u'/',__islast=None,__deepNow=0, __sets=None):
    '''
    类似bash中的tree命令 简单查看instance的 __attrs__ 组成的树的结构
    attr name用红色；str(instance.attr)用蓝色；
    如果attr 为instancemethod，builtin_function_or_method，method-wrapper之一
    instance.attr.__doc__用黑色 
    
    ps.可在__attrLogFuns中 新增常见类别
    '''
    if deep and __deepNow > deep:
        return
    s = __discribOfInstance(seq,colorFormat.b,MAX_LEN=maxDocLen)
    if maxDocLen < 100:
        s = s.replace('\n','↳')
    if __leftStr is None:
        __leftStr = [] 
        __islast = 1
        __sets = set()
        doc = '' if instance is None else getFunDoc(instance)
        if len(doc) > maxDocLen:
            doc = doc[:maxDocLen-3]+'...'
        s=colorFormat.b%('%d attrs%s'%(len(seq), doc.replace('\n','↳').replace(' :',',',1)))
#    print ''.join(__leftStr)+u'├── '+tounicode(k)+': '+s
    print u'%s%s %s: %s'%(u''.join(__leftStr), u'└──' if __islast else u'├──',colorFormat.r%tounicode(__key),s)
    if isinstance(seq,(list,tuple,dict)) :
        if id(seq) in __sets:
            seq=[(colorFormat.r%u'【printed befor】','')]
        else:
            __sets.add(id(seq))
            if isinstance(seq,(list,tuple)):
                seq = list(enumerate(seq))
            elif isinstance(seq,(dict)):
                seq = list(seq.items())
                seq.sort(key=lambda x:x[0])
    else:
        return 
    __leftStr.append(u'    'if __islast else u'│   ')
    for i,kv in enumerate(seq):
        __key,v = kv
        __dira(v,maxDocLen=maxDocLen,deep=deep,__leftStr=__leftStr,__key=__key,
               __islast=(i==len(seq)-1), __deepNow=__deepNow+1,__sets=__sets)#leafColor=colorFormat.black)
    __leftStr.pop()

def getFunDoc(f):
    if '__doc__' in dir(f) and f.__doc__:
        return ' : %s'%(colorFormat.black%f.__doc__)
    return ''

__attrLogFun__ = {
'method-wrapper': lambda x:'method-wrapper%s'%getFunDoc(x),
'builtin_function_or_method':lambda x:'builtin-method%s'%getFunDoc(x),
'instancemethod':lambda x:'instancemethod%s'%getFunDoc(x),
'buffer':lambda x:'buffer : %s'%(colorFormat.b%(x)),
}

def dira(instance, pattern=None, maxDocLen=50, deep=None):
    '''
    以树的结构 分析instance的所有 attrs 
    attr name用红色；str(instance.attr)用蓝色；
    如果attr 为instancemethod，builtin_function_or_method，method-wrapper之一
    instance.attr.__doc__用黑色 
    
    Parameters
    ----------
    instance : Anything
        Anything, Instance better
    pattern : re.pattern
        用于匹配re.search参数 进行filter
    maxDocLen : int, default 50
        若有文档显示文档的字数长度
    deep : int, default None
        能显示的最深深度, 默认不限制
        
    ps.可在__attrLogFuns中 新增常见类别
    pps.不展开 ('__globals__', 'func_globals')
    '''
    dirs = dir(instance)
    if pattern is not None:
        import re
        dirs = filter(lambda name:re.search(pattern,name), dirs)
        print 'Filter by pattern: "%s"'%(colorFormat.r%pattern)
    def getAttr(attr):
        try:
#            if '__getattribute__' in dirs or 1:
            return instance.__getattribute__(attr)
        except (AttributeError, TypeError):
            pass
        except KeyError:
            pass
        try:
            if '__getattr__' in dirs:
                return instance.__getattr__(attr)
        except (AttributeError, TypeError):
            return colorFormat.red % 'Both "getattr" and "getattribute" are not work'
        return 'No "getattr" or "getattribute"'
    l = map(getAttr,dirs)
    def filterMethodName(attrName, attr):
        typee = type(attr)
        typn = typeNameOf(typee)
        if typn in __attrLogFun__:
            return __attrLogFun__[typn](attr)
        if attrName in ('__globals__', 'func_globals'):
            return colorFormat.b%('globals-dict %d'%len(attr))
        return attr
    l = map(filterMethodName,dirs,l)
    dic = dict(zip(dirs,l))    
    __dira(dic,instance=instance, maxDocLen=maxDocLen, deep=deep,__key=typeNameOf(type(instance)), )

dira = FunAddMagicMethod(dira)
treea = dira

def __readShape(n):
    return imread(n).shape
def getShapes(imgGlob, returnn=False):
    '''
    以多线程获得匹配imgGlob的所有图片的shapes
    并print出shapes的最大最小值
    
    Parameters
    ----------
    imgGlob : str
        图片的匹配路径
        如 "/img_data/*.png"
    returnn : bool ,default False
        默认不返回shapes
        为True，则返回shapes
    '''
    names = glob.glob(imgGlob)
    shapes = mapmp(__readShape,names)
    lens = list(map(len,shapes))
    dims = np.unique(lens)
    arr = shapes
    print 'Dims:'
    for dim in dims:
        print '\t %s dim: %d'%(dim,lens.count(dim))
    if len(dims)!=1:
        maxx = max(dims)
        arr=map(lambda s:s+(-1,)*(maxx-len(s)),shapes)
    arr=np.array(arr)
    maxx, minn = [],[]
    for dim in range(max(dims)):
        a = arr[:,dim]
        maxx.append(a[a!=-1].max())
        minn.append(a[a!=-1].min())
    
    print 'Shape:\n \t max shape: %s\n \t min shape: %s'%(maxx,minn)
    if returnn:
        return shapes

__color10 = [
 (1.0, 1.0, 1.0),
 (0.8666666666666667, 1.0, 1.0),
 (0.8, 1.0, 1.0),
 (0.6666666666666667, 1.0, 1.0),
 (0.5333333333333333, 1.0, 1.0),
 (0.4666666666666667, 1.0, 1.0),
 (0.33333333333333337, 1.0, 1.0),
 (0.19999999999999996, 1.0, 1.0),
 (0.1333333333333333, 1.0, 1.0),
 (0.06666666666666665, 1.0, 1.0)]

def getHsvColors(hn,sn,vn):
    '''
    在hsv空间产生尽可能不同的颜色集
    hn,sn,vn 分别表示 h，s，v对应每个通道的可选值的数目
    return `hn*sn*vn`个 以float三元组为HSV颜色形式的list
    '''
    def toNcolor(n,incloud0=False):
        if incloud0:
            n -= 1
        l = [1.-i*1./n for i in range(n)]
        if incloud0:
            return l+[0.]
        return l
    
    hs,ss,vs = map(toNcolor,[hn,sn,vn])
    cs = []
    for s in ss:
        for v in vs:
            for h in hs:
                c = (h,s,v)
                cs += [c]
    return cs

def getDefaultColorList(colorNum=None, includeBackGround=None,uint8=False):
    '''
    产生尽可能不同的颜色集，用于多label上色
    
    Parameters
    ----------
    colorNum : int, default None
        颜色数目,default 21
    includeBackGround : bool or int, default None
        None: 没有背景色 即不包含黑色
        1 : 第一类为背景即黑色 
        -1: 最后一类为背景即黑色
    uint8 : bool, default False
        是否返还 np.uint8 格式的颜色
        
    Return
    ----------
    以float三元组为RGB颜色形式的list
    '''
    if colorNum is None:
        colorNum=21
        includeBackGround=1
    if includeBackGround is not None:
        colorNum -= 1
    
    if colorNum <= 12:
        colors = getHsvColors(6, 1, 2)
        
    elif colorNum <= 20:
        colors = __color10+[(c[0],1.0,.5) for c in __color10]
    elif colorNum <= 30:
        colors = __color10+[(c[0],1.0,.66666) for c in __color10]+[(c[0],1.0,.333333) for c in __color10]
        
    elif colorNum <= 60:
        colors = getHsvColors(colorNum//3+1 if colorNum%3 else colorNum//3,1,3)
    else :
        colors = getHsvColors(colorNum//6+1,2,3)
    
    if includeBackGround == -1:
        colors = colors[:colorNum] + [(0.,0.,0.)]
    elif includeBackGround is not None:
        colors = [(0.,0.,0.)] + colors[:colorNum]
    else:
        colors = colors[:colorNum] 
    if uint8 :
        return list((np.array(colors)*255).astype(np.uint8))
    
    from colorsys import hsv_to_rgb
    toRgb = lambda hsv:hsv_to_rgb(*hsv)
    return list(map(toRgb,colors))

def labelToColor(label, colors=None, includeBackGround=None):
    '''
    将颜色集colors映射到label上 返回彩色的label图

    Parameters
    ----------
    label : W*H of int
        W*H的labelMap
    colors : list of RGB color, default None
        对应k类的RGB颜色集，若为None 则会自动生成尽可能不同的颜色集
    includeBackGround : bool or int, default None
        若colors为None 情况下才生效:
            None: 生成的颜色集没有背景色 即不包含黑色
            1   : 第一类为背景即黑色 
            -1  : 最后一类为背景即黑色
    '''
    if colors is None:
        colors = getDefaultColorList(label.max()+1, includeBackGround=includeBackGround)
    colors = np.array(colors)
    if 1.1>(colors).max()>0:
        colors = uint8(colors)
    rgb = np.zeros(label.shape+(3,), np.uint8)
    for c in np.unique(label):
        rgb[label==c] = colors[int(c)]
    return rgb

def standImg(img):
    '''
    任何输入img都转换为 shape is (m, n, 3) dtype == Float
    '''
    from ylnp import isNumpyType
    if img.ndim == 2:
        img = greyToRgb(img)
    if img.dtype == np.uint8:
        img = img/255.
    if isNumpyType(img, bool):
        img = img*1.0
    if isNumpyType(img, float):
        return img
    
if __name__ == '__main__':

    pass
