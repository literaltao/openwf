#reads "match" data, which are in .results in log format


from loaders import *
import sys
import subprocess
import numpy
import time
import math
import os
from acc import *

def flog(msg, fname):
    f = open(fname, "a+")
    f.write(repr(time.time()) + "\t" + str(msg) + "\n")
    f.close()

def log(msg):
    LOG_FILE = d["OUTPUT_LOC"] + sys.argv[0].split("/")[-1] + ".log"
    flog(msg, LOG_FILE)

def rlog(msg):
    LOG_FILE = d["OUTPUT_LOC"] + sys.argv[0].split("/")[-1] + ".results"
    flog(msg, LOG_FILE)

try:
    d = load_options(sys.argv[1])
except Exception,e:
    print sys.argv[0], str(e)
    sys.exit(0)

match = []
classes = [] #true classes
if (d["CORE_TOTAL"] > 0):
    for i in range(0, d["CORE_TOTAL"]):
        fname = "{}{}-{}.score".format(d["INPUT_LOC"], d["ATTACK_NAME"], i)
        print "Loading", fname
        mat, names = load_score(fname)
        match += [r for r in mat]
        classes += [str_to_sinste(a)[0] for a in names]
else:
    fname = d["INPUT_LOC"] + d["ATTACK_NAME"] + ".score"
    match, names = load_score(fname)
    classes += [str_to_sinste(a)[0] for a in names]
for i in range(0, len(match)):
    if len(match[i]) != d["CLOSED_SITENUM"] + 1:
        print "len(match[{}]) = {}".format(i, len(match[i]))
        sys.exit(-1)
if (len(match) != d["CLOSED_SITENUM"] * d["CLOSED_INSTNUM"] + d["OPEN_INSTNUM"]):
    print "Match count unexpected ({} != {} entries)".format(len(match),
                                                             d["CLOSED_SITENUM"] * d["CLOSED_INSTNUM"] + d["OPEN_INSTNUM"])

#rescale each match so that it is between 0 and 1
scaled_match = []
for i in range(0, len(match)):
    minmatch = min(match[i])
    maxmatch = max(match[i])
    diff = maxmatch - minmatch
    if diff == 0:
        diff = 1
    scaled_match.append([])
    for j in range(0, len(match[i])):
        scaled_match[-1].append((match[i][j] - minmatch)/diff)
match = scaled_match


##for i in range(len(match)):
##    match[i][-1] = 0 #set open class to 0

##if ("MATCH_K" in d.keys() and "MATCH_L" in d.keys()):
##    MATCH_K = d["MATCH_K"]
##    MATCH_L = d["MATCH_L"]
##else:
##    MATCH_K = 2
##    MATCH_L = 0.9
##    print "MATCH_K and MATCH_L not found, using default (2, 0.9)"
##    #MATCH_K = 1, MATCH_L = 1 should disable this entirely

L_RANGE = []
base = 0
while base <= 1:
    L_RANGE.append(base)
    base += 0.01

L_RANGE = [0.08]
    
results = []
bestpr = 0
bestresults = []
for MATCH_K in range(3, 4):
    for MATCH_L in L_RANGE:
        gclasses = [] #guessed classes
        count = 0
        for i in range(0, len(match)):
            this_match = list(match[i])
            minmatch = min(this_match)
            maxmatch = max(this_match)
            maxclass = this_match.index(maxmatch)
            if (maxclass == d["CLOSED_SITENUM"]):
                maxclass = -1
            this_match[maxclass] = minmatch #cancel it
            kmatches = []
            for j in range(0, MATCH_K):
                kmatch = max(this_match)
                this_match[this_match.index(kmatch)] = minmatch        
                kmatches.append(kmatch)
        ##    print kmatches
        ##    print maxmatch, numpy.mean(kmatches)
            if numpy.mean(kmatches) > MATCH_L:
                gclasses.append(-1)
                count += 1
            else:
                gclasses.append(maxclass)
##        print gclasses[:1000]
        ##print count
        acc = get_acc(gclasses, classes)
        pr10 = acc_to_pr(acc, 20)
        pr1000 = acc_to_pr(acc, 1000)
        pr2 = acc_to_pr2(acc, 1000)

        string = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(MATCH_K, MATCH_L, acc[0], acc[1], acc[2], acc[3], acc[4])
        if acc[0]/float(acc[3]) >= 0.2:
            print pr10, pr1000
            print string
            res = [MATCH_K, MATCH_L, acc[0], acc[1], acc[2], acc[3], acc[4]]
            results.append(res)
            if pr2 > bestpr:
                bestpr = pr2
                bestresults = res

fout = open("match-conf.results", "w")
fout.write("\t".join([str(k) for k in results[-1]]) + "\n")
fout.write("\t".join([str(k) for k in bestresults]) + "\n")
fout.close()
