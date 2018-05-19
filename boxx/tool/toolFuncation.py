# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
import time

from ..ylsys import cpun
from .toolStructObj import typestr

from functools import reduce

def getFunName(fun):
    '''
    获得函数的名称
    '''
    if '__name__' in dir(fun):
        return fun.__name__
    return '[unkonw]'

def dynamicWraps(func):
    '''
    decorator 动态规划 装饰器
    '''
    cache={}
    from functools import wraps
    @wraps(func)
    def wrap(*args,**kv):
        key = args+tuple(sorted(kv.items())) if len(kv) else args
        if key not in cache:
            cache[key]=func(*args, **kv)
        return cache[key]
    return wrap

def pipe(*funList):
    '''
    将一组函数组成一个管道函数
    
    Parameters
    ----------
    funList : Funcation or list of Funcation
        函数list
    '''
    if len(funList) == 1 and  '__iter__' in dir(funList[0]):
        funList = funList[0]
    return reduce(lambda f1,f2:(lambda x:f2(f1(x))), funList, lambda x:x)
    
def setTimeOut(fun, t=0):
    '''
    same to setTimeOut in JavaScript
    '''
    from threading import Timer
    thread = Timer(t,fun)
    thread.start()
    return thread

def setInterval(fun, inter, maxTimes=None):
    '''
    same to setInterval in JavaScript
    '''
    maxTimes = [maxTimes]
    def interFun(): 
        fun()
        if maxTimes[0] is not None:
            maxTimes[0] -= 1
            if maxTimes[0] <= 0:
                return 
        setTimeOut(interFun, inter)
    interFun()

from multiprocessing import Pool as PoolMp
from multiprocessing.dummy import Pool as PoolThread
def __multiprocessingFun__(args):
    '''
    多线程专用
    '''
    return args[0](*args[1:])

def __multiprocessLogFun__(args):
    '''
    '''
    
    fun, args, ind, lenn, logf = args
    if ind is None:
        return fun(*args)
    from .toolLog import timeit, percentStr, shortStr
    with timeit(None) as t:
        re = fun(*args)
    if logf:
        logf([fun, args, ind, lenn, logf])
    else:
        print('%s/%s(%s) spend %s args[0]: %s'%(ind,lenn,isinstance(lenn, int) and percentStr(ind*1./lenn),t.s,shortStr(args[0])), end='\n')
    return re

def mapmp(fun, *iterables, **kv):
    '''
    Map with Multi Processing:多进程版本的map函数
    mapmp(fun, sequence[, sequence, ...], pool=None, thread=False)->list
    !Important, multi processing must do in `__name__ == '__main__'`'s block 
    see more at https://docs.python.org/3/library/multiprocessing.html
    
    >>> mapmp(np.add, range(3), range(3), pool=3)
    [0, 2, 4]
    
    Notice
    ----------
    * 多进程中 异常无法精确定位
    * numpy操作 由于指令集优化 及numpy版本原因 可能多进程可能会更慢
    * 多进程中 list, dict等元素会被直接复制，无法改变内部元素
    
    Parameters
    ----------
    fun : function
        *多进程*只支持`def`定义的函数 不能是lambda 和 内部函数 
        否则 PicklingError: Can't pickle 
    *iterables : list 
        用于fun的参数list, fun需要N个参数则有N个列表
    pool : int, default None
        进程数目，默认为CPU进程数
    logfreq : int, default None
        打印进度的频次 默认不打印
    logf : funcation, default None
        Hook Funcation For log , every logfreq
        do logf([fun, args, ind, lenn, logf])
    thread : bool, default False
        是否以*多线程*形式替换多进程
    '''    
    Pool = PoolMp
    if 'thread' in kv and kv['thread']:
        Pool = PoolThread
    pool = Pool(kv['pool']) if 'pool' in kv and kv['pool'] else Pool()
    
    pooln = kv['pool'] if 'pool' in kv else cpun
    logf = kv['logf'] if 'logf' in kv else None
    
    if 'logfreq' in kv and kv['logfreq']:
        logfreq = kv['logfreq']
        l = iterables[-1] = list(iterables[-1])
        lenn = len(l)
        
        def yieldWithIndFun(fun, iterables, lenn, logf, logfreq):
            for i,args in enumerate(zip(*iterables)):
                yield (fun, args, None if i%logfreq else i, lenn, logf)
        chunksize = kv['chunksize'] if 'chunksize' in kv else min(max(1, logfreq*2//3), lenn//pooln)
        re = pool.map(__multiprocessLogFun__, yieldWithIndFun(fun, iterables, lenn, logf, logfreq), chunksize=chunksize)
    else:
        def yieldWithFun(fun, iterables):
            for args in zip(*iterables):
                yield (fun,)+args
        re = pool.map(__multiprocessingFun__,  yieldWithFun(fun, iterables))
    pool.close()
    pool.join()
    return re

def mapmt(fun, *mapArgList, **kv):
    '''
    Map with Multi Threading:多线程版本的map函数， 适用于IO密集型任务
    mapmt(fun, sequence[, sequence, ...], pool=None)->list
    
    >>> mapmt(np.add, range(3), range(3), pool=3)
    [0, 2, 4]
    
    
    Parameters
    ----------
    fun : function
        与 map 使用相同的函数 
    *mapArgList : list 
        用于fun的参数list, fun需要N个参数则有N个列表
    pool : int, default None
        线程数目，默认为CPU进程数
    '''
    return mapmp(fun, *mapArgList,thread=True, **kv)

class multiThread():
    '''
    将多线程封装成为类的形式
    
    Example
    ----------
    >>> mt = multiThread(pool=8)
    >>> for arg in args:
            mt(f,*arg)
    >>> mt.join()
    
    Init Parameters
    ----------
    pool : int, default 8
        线程池的最大线程数目
        
    Method
    ----------
    __call__(fun,*l,**kv):
        fun : 需要多线程的函数 
        *l,**kv : 传给函数的参数们
        新建一个线程 并运行fun(*l,**kv)
    join(): 
        等待至所有线程中止。阻塞主线程直至没有子线程运行。 
    '''
    TIME_GAP = .001
    def __init__(self,pool=8):
        self.pool = pool
        self.left = pool
        self.l=[]
    def __call__(self,fun,*l,**kv):
        while not self.left:
            time.sleep(self.TIME_GAP)
        self.left -=1
        def f():
            try:
                r = fun(*l,**kv)
            finally:
                self.left += 1
        self.l.append(setTimeOut(f))
        if len(self.l)>100:
            self.l = self.l[-90:]
    f = lambda fun,*l,**kv:fun(*l,**kv) #用于测试单线程的性能
    def join(self):
        while self.left!=self.pool:
            time.sleep(self.TIME_GAP)
#        print('pool',self.pool)

def retry(fun, times=None, exception=Exception, timeGap=0, log=True):
    '''
    重试一个容易raise Exception的无参数函数fun times次数，被捕获的exception 保存在 retry.e 中
    最后返回 fun() 
    
    Parameters
    ----------
    fun : funcation
        没有参数的过程函数
    times : int, default None
        try 的次数 默认为无限次
    exception : Exception Class, default builtins.Exception
        需要被捕获的异常， 默认捕获所有异常 
    timeGap : float, default 0
        retry 需要等待多少秒时间
    log : bool, default True
        是否打印错误信息    
    Returns
    -------
    fun() : anything
    '''
    count = 0
    while (True if times is None else times - 1):
        try:
            r = fun()
            return r
        except exception as e:
            retry.e = e
            if log:
                fname = fun.__name__ if 'func_name' in dir(fun) else str(fun)
                print((('\x1b[31m%s\x1b[0m'%"%dth's Exception: %s of %s")%(count, typestr(e), fname)))
                print(e)
                print('')
        if timeGap:
            time.sleep(timeGap)
        if times is not None:
            times -= 1    
        count += 1
    return fun()

if __name__ == "__main__":
    
    def fun():
        for i in range(10):
            print(i)
            time.sleep(1)
    from threading import Timer
    thread = Timer(0,fun)
    thread.start()
    pass