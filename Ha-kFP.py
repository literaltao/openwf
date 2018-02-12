import csv
import sys
from sys import stdout
import RF_fextract
import numpy as np
#import matplotlib.pylab as plt
import operator
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import cross_val_score
from sklearn import metrics
from sklearn import tree
import sklearn.metrics as skm
import scipy
import dill
import random
import os
from collections import defaultdict
import argparse
from itertools import chain
from loaders import *
from gen_list import *
import subprocess
#from tqdm import *

# re-seed the generator
#np.random.seed(1234)

#1. dictionary_() will extract features and write them to a target file (kFPdict) in the data folder
#2. calls RF_openworld(), which starts by dividing kFPdict into training and testing sets
#3. 

d = {}


############ Feeder functions ############

def chunks(l, n):
    """ Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def checkequal(lst):
    return lst[1:] == lst[:-1]


############ Non-Feeder functions ########

def dictionary_():
    '''Extract Features -- A dictionary containing features for each traffic instance.'''

    data_dict = {'train_feature': [],
                 'train_label': [],
                 'test_feature': [],
                 'test_label': []}

    traindata, trainnames = load_listn(d["TRAIN_LIST"]) #loadlistn only loads names
    testdata, testnames = load_listn(d["TEST_LIST"])
    trainnames = [r for a in trainnames for r in a] #flatten names
    testnames = [r for a in testnames for r in a] #flatten names

    print "Creating training features...", len(trainnames)

    maxclass = len(trainnames) - 1
    #for kFP, we write the final class not as -1, but as maxclass
    count = 0
    intcount = 0
    for fname in trainnames:
        if ((count * 100)/len(trainnames) > (intcount + 1)):
            print "{}%... {}".format(intcount, fname)
            intcount += 1
        (i, j) = str_to_sinste(fname) #i is the true site, j is the true inst
        if i == -1:
            i = maxclass
        tcp_dump = open(fname).readlines()
        g = []
        g = RF_fextract.TOTAL_FEATURES(tcp_dump)
        data_dict['train_feature'].append(g)
        data_dict['train_label'].append((i,j))
        count += 1

    print "Creating testing features...", len(testnames)

    count = 0
    intcount = 0
    for fname in testnames:
        if ((count * 100)/len(testnames) > (intcount + 1)):
            print "{}%... {}".format(intcount, fname)
            intcount += 1
        (i, j) = str_to_sinste(fname) #i is the true site, j is the true inst
        if i == -1:
            i = maxclass
        tcp_dump = open(fname).readlines()
        g = []
        g = RF_fextract.TOTAL_FEATURES(tcp_dump)
        data_dict['test_feature'].append(g)
        data_dict['test_label'].append((i, j))
        count += 1

    fileObject = open(dilldatafname,'wb')
    dill.dump(data_dict,fileObject)
    fileObject.close()

def RF_openworld():
    '''Produces leaf vectors used for classification.'''

    fileObject1 = open(dilldatafname,'r')
    dic = dill.load(fileObject1)
    traindata = dic["train_feature"]
    trainsinste = dic["train_label"]
    testdata = dic["test_feature"]
    testsinste = dic["test_label"]

    trainlabel = [sinste[0] for sinste in trainsinste]
    testlabel = [sinste[0] for sinste in testsinste]
    
    print "Training ..."
    model = RandomForestClassifier(n_jobs=-1, n_estimators=1000, oob_score=True)
    model.fit(traindata, trainlabel)

    testlist = []
    f = open(d["TEST_LIST"], "r")
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line[0] != "#" and line != "":
            testlist.append(line)
    f.close()
    if len(testdata) != len(testlist):
        raise("Unexpected test size: {} != {}".format(len(testdata), len(testlist)))

    M = model.predict(testdata, get_predict=1)
    for i in range(0, len(M)):
        x = M[i]
        string = str(testlist[i])
        for xi in x:
            string += "\t" + str(xi)
        rlog(string)
    
    print "RF accuracy (open) = ", model.score(testdata, testlabel)

    train_leaf = zip(model.apply(traindata), trainlabel)
    test_leaf = zip(model.apply(testdata), testlabel)
    return train_leaf, test_leaf

def flog(msg, fname):
    f = open(fname, "a+")
    f.write(repr(time.time()) + "\t" + str(msg) + "\n")
    f.close()   

def log(msg):
    LOG_FILE = d["OUTPUT_LOC"] + sys.argv[0].split("/")[-1]
    if ("CORE_NAME" in d):
        LOG_FILE += "-" + str(d["CORE_NAME"])
    LOG_FILE += ".log"
    flog(msg, LOG_FILE)

def rlog(msg):
    LOG_FILE = d["OUTPUT_LOC"] + sys.argv[0].split("/")[-1]
    if ("CORE_NAME" in d):
        LOG_FILE += "-" + str(d["CORE_NAME"])
    LOG_FILE += ".results"
    flog(msg, LOG_FILE)

if __name__ == "__main__":

### Paths to data ###
        
    try:
        optfname = sys.argv[1]
        d = load_options(optfname)
    except Exception,e:
        print sys.argv[0], str(e)
        sys.exit(0)
        
    log(sys.argv[0] + " " + sys.argv[1])
    log(repr(d))
    rlog(sys.argv[0] + " " + sys.argv[1])
    rlog(repr(d))

    dilldatafname = d["OUTPUT_LOC"] + "kFPdict"
    if ("CORE_NAME" in d):
        dilldatafname += "-" + str(d["CORE_NAME"])
    
    if (d["GEN_OWN_LIST"] == 1):
        gen_list(d)

    #uncomment to re-build dictionary
    dictionary_()
    RF_openworld()
