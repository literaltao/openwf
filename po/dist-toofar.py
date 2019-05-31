
from loaders import *
import sys
import subprocess
import numpy
import time
import math
import random
import os
from acc import *

CLOSED_SITENUM = 100
CLOSED_INSTNUM = 200
OPEN_INSTNUM = 800

#requires dist-process to be run first to obtain dist from predist
#predist is obtained from attacks/dist.py and dist-open.py
#scores are obtained from attacks/

def sinste_to_site_inst(sinste):
    if sinste >= CLOSED_SITENUM * CLOSED_INSTNUM:
        site = -1
        inst = sinste - CLOSED_SITENUM * CLOSED_INSTNUM
    else:
        site = sinste / CLOSED_INSTNUM
        inst = sinste % CLOSED_INSTNUM
    return site, inst

anames = ["Bi-XCor", "Ha-kFP", "flearner", "Pa-CUMUL", "Pa-FeaturesSVM", "Ca-OSAD"]
dnames = ["Wa-kNN.py", "Pa-FeaturesSVM.py", "Pa-CUMUL.py", "cc.py", "Ca-OSAD.py"]
#this should work even if aname has less data than dname,
#as is the case for aname Ca-OSAD (but not dname Ca-OSAD.py)
for aname in anames:
    match = []
    classes = [] #true classes

    if aname == "Ca-OSAD":
        fname = "../attacks/output/full-Ca-OSAD.py.score"
        print "Loading", fname
        mat, names = load_score(fname)
        match += [r for r in mat]
        classes += [str_to_sinste(a)[0] for a in names]
    else:    
        for i in range(10):
            fname = "{}{}-{}.score".format("../attacks/output/full-", aname, i)
            print "Loading", fname
            mat, names = load_score(fname)
            match += [r for r in mat]
            classes += [str_to_sinste(a)[0] for a in names]

    cmatch = [] #match, divided by class
    #cmatch[i] are all the instances of class i
    for i in range(101):
        cmatch.append([])
    for i in range(len(match)):
        cmatch[classes[i]].append(match[i])

    #obtain each guess
    coclasses = [] #original guesses, divided by class
    for i in range(101):
        coclasses.append([])
    for i in range(len(cmatch)):
        for j in range(len(cmatch[i])):
            this_match = list(cmatch[i][j])
            maxmatch = max(this_match)
            maxclass = this_match.index(maxmatch)
            if (maxclass == 100):
                maxclass = -1
            coclasses[i].append(maxclass)
                
    for dname in dnames:

        print "Generating dist/counts matrices..."
        cdists = []
        #length of all the above arrays = number of elements in data set

        #cdists[i][j][k] is the distance between the jth element of class i, and class k
        #edists[i] is the expected self-distance of class i

        for i in range(101):
            cdists.append([])

        print "Loading distance file..."
        with open("../attacks/output/dist-" + dname + ".dist", "r") as f:
            count = 0
            li = f.readline().split("\t")
            edists = [float(k) for k in li[1:]]
            for line in f:
                li = line.split("\t")
                site, inst = sinste_to_site_inst(int(li[0]))
                cdists[site].append([float(k) for k in li[1:]])

        #M (M_toofar) from 0.01 to 2, 200 different values
                
        fout = open("../attacks/output/disttf-{}-{}.results".format(aname, dname), "w")
        for i in range(len(coclasses)):
            for j in range(len(coclasses[i])):
                adist = cdists[i][j][coclasses[i][j]] #distance with assumed class
                edist = edists[coclasses[i][j]]
                writestr = ""
                for K in range(1, 201):
                    M = K/100.0
                    if adist > M * edist: #should be rejected
                        writestr += "-1\t"
                    else:
                        writestr += str(coclasses[i][j]) + "\t"
                writestr = writestr[:-1] + "\n"
                fout.write(writestr)

        fout.close()
