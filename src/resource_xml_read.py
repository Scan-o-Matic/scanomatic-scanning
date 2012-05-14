#!/usr/bin/env python
"""
This module reads xml-files as produced by scannomatic and returns numpy-arrays.
"""
__author__ = "Martin Zackrisson"
__copyright__ = "Swedish copyright laws apply"
__credits__ = ["Martin Zackrisson"]
__license__ = "GPL v3.0"
__version__ = "0.992"
__maintainer__ = "Martin Zackrisson"
__email__ = "martin.zackrisson@gu.se"
__status__ = "Development"


#
# DEPENDENCIES
#

import os, sys
import types
import logging
import numpy as np
import re
import matplotlib.pyplot as plt

#
# SCANNOMATIC LIBRARIES
#


#
# FUNCTIONS
#

#
# CLASSES
#

class XML_Reader():

    def __init__(self, file_path):

        self._file_path = file_path
        self._logger = logging.getLogger('XML_Reader.{0}'.format(file_path.split(os.sep)[-1]))
        self._loaded = False
        self._data = None
        self._meta_data = None

        if not self.read():
            self._logger.error("XML Reader not fully initialized!")

    def read(self, file_path=None):
        """Reads the file_path file using short-format xml"""
        try:
            fs  = open(self._file_path, 'r')
        except:
            self._logger.error("XML-file '{0}' not found".format(self._file_path))
            return False

        f = fs.readline()
        fs.close()
        self._data = {}
        self._meta_data = {}

        XML_TAG_CONT = "{0}>(.*)</{0}"
        XML_TAG_INDEX_VALUE_CONT  =  "<{0} {1}..(\d).>([^<]*)</{0}>"
        XML_TAG_INDEX_VALUE = "<{0} {1}..(\d*).>"
        XML_TAG_2_INDEX_VALUE = "<{0} {1}..(\d*). {2}..(\d*).>"
        XML_TAG_2_INDEX_VALUE_CONT = "<{0} {1}..{3}. {2}..{4}.>[^\d]*([0-9.]*)<"

        #METADATA
        tags = ['start-t','desc','n-plates']
        for t in tags:
            self._meta_data[t] = re.findall(XML_TAG_CONT.format(t), f)

        #DATA

        nscans = len(re.findall(XML_TAG_INDEX_VALUE.format('s','i'), f))
        pms = re.findall(XML_TAG_INDEX_VALUE_CONT.format('p-m', 'i'), f)
        pms = map(lambda x: map(eval, x), pms)
        colonies = sum([p[1][0]*p[1][1] for p in pms])
        measures = colonies * nscans
        max_pm = np.max(np.array([p[1] for p in pms]),0)

        for pm in pms:
            self._data[pm[0]] = np.zeros((pm[1] + (nscans,)),dtype=np.float64)
        
        colonies_done = 0
        for x in xrange(max_pm[0]):
            for y in xrange(max_pm[1]):
                try:
                    v = map(lambda x: x == 'nan' and np.nan or np.float64(x), 
                        re.findall(XML_TAG_2_INDEX_VALUE_CONT.format('gc','x','y',x,y), f))
                except ValueError:
                    print XML_TAG_2_INDEX_VALUE_CONT.format('gc','x','y',x,y)
                    print re.findall(XML_TAG_2_INDEX_VALUE_CONT.format('gc','x','y',x,y), f)
                    #self._logger.error( re.findall(XML_TAG_2_INDEX_VALUE_CONT.format('gc','x','y',x,y), f))

                slicers = [False] * len(pms)
                for i,pm in enumerate(pms):
                    if x < pm[1][0] and y < pm[1][1]:                        
                        slicers[i] = True

                slice_start = 0
                for i,pm in enumerate(slicers):
                    if pm:
                        self._data[i][x,y,:] = (np.array(v)[range(slice_start, len(v), sum(slicers))])[-1::-1]
                        slice_start += 1
                        colonies_done += 1

            print "Completed {0}%\r".format(100*colonies_done/float(colonies))
           
                    
        return True

    def set_file_path(self, file_path):
        """Sets file-path"""
        self._file_path = file_path

    def get_meta_data(self):
        """Returns meta-data dictionary"""
        return self._meta_data

    def get_file_path(self):
        """Returns the currently set file-path"""
        return self._file_path

    def get_colony(self, plate, x, y):
        """Returns the data array for a specific colony"""
        try:
            return self._data[plate][x,y,:]
        except:
            return None

    def get_plate(self, plate):
        """Returns the data for the plate specified"""
        try:
            return self._data[plate]
        except:
            return None

    def get_shapes(self):
        """Gives the shape for each plate in data"""
        try:
            return [(p, self._data[p].shape) for p in self._data.keys()]
        except:
            return None

def random_plot_on_separate_panels(xml_parser):
    fig = plt.figure()
    for i in xrange(4):
        ax = fig.add_subplot(2,2,i+1, title='Plate {0}'.format(i))
        d = xml_parser.get_plate(i)
        if d is not None:
            x,y,z = d.shape
            for j in xrange(10):
                tx = np.random.randint(0,x)
                ty = np.random.randint(0,y)
                ax.semilogy(d[tx, ty,:], basey=2, label="{0}:{1}".format(tx,ty) )
        ax.legend(loc = 4, ncol=2)

    return fig

def random_plot_on_same_panel(xml_parser, different_line_styles=False):
    fig = plt.figure()
    col_maps = [np.array([0.15,0.15,0.10]), np.array([0.25,0,0]), np.array([0,0.25,0]), np.array([0,0,0.25])]
    if different_line_styles:
        line_styles = [':', '-.', '--', '-']
    else:
        line_styles = ['-']*4

    ax = fig.add_subplot(1,1,1, title='All on same graph')
    for i in xrange(4):
        d = xml_parser.get_plate(i)
        if d is not None:
            x,y,z = d.shape
            for j in xrange(4):
                tx = np.random.randint(0,x)
                ty = np.random.randint(0,y)
                ax.semilogy(d[tx, ty,:], line_styles[i], basey=2, label="{0} {1}:{2}".format(i, tx,ty), 
                    color=list(col_maps[i]*(1 + 0.75*(j+1))) + [1] )
    ax.legend(loc = 4, ncol=4, title='Plate Colony_ X:Colony_Y')
    
    return fig


