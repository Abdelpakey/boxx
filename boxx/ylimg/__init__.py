# -*- coding: utf-8 -*-
from .ylimgTool import sk, sio, np, plt, plot, sda
from .ylimgTool import (show, showb, shows, loga, tree, treem, treea, dira, what, tprgb, 
                        torgb, mapp, normalizing, norma, imsave, imread, npa, 
                       getShapes, greyToRgb, resize, histEqualize)
from .ylimgTool import (uint8, randomm , r, labelToColor,getDefaultColorList,
                       standImg, getMeanStd, boolToIndex)

from .ylimgVideoAndGif import gifSave, videoToImgs, base64Img, generateBigImgForPaper

# Compatibility to old versions
logl = tree

import matplotlib.pyplot as plt

if __name__ == '__main__':

    pass
