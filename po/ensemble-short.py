import subprocess, math, time, sys, os
import numpy
import itertools
from loaders import *
from acc import *

accs = []
for i in range(0, 20):
    accs.append([0, 0, 0, 0, 0])

fold = "../attacks/output/full-"
attacks = ["Bi-XCor",
           "Pa-FeaturesSVM",
           "flearner",
           "Ha-kFP",
           "Pa-CUMUL"]

CLOSED_SITENUM = 100
CLOSED_INSTNUM = 200
OPEN_INSTNUM = 80000

a_gclasses = []
#a_gclasses[i] are the 100,000 guesses of attack number i
names = []
for i in range(CLOSED_SITENUM):
    for j in range(CLOSED_INSTNUM):
        names.append("{}-{}.cell".format(i, j))
for i in range(OPEN_INSTNUM):
    names.append("{}.cell".format(i))

#load all matches
for a in attacks:
    gclasses = [0] * 100000
    for i in range(10):
        fname = fold + a + "-" + str(i) + ".score"
        print "Reading", fname
        with open(fname) as fp:
            for line in fp:
                li = line.split("\t")
                [site, inst] = str_to_sinste(li[0])
                if site == -1:
                    site = CLOSED_SITENUM
                ind = site * 200 + inst
                scores = [float(x) for x in li[1:]]
                gclass = scores.index(max(scores))
                if gclass == 100:
                    gclass = -1
                gclasses[ind] = gclass
    a_gclasses.append(gclasses)
    
tclasses = [str_to_sinste(a)[0] for a in names]
attack_sets = [[0], [1], [2], [3], [4],
               [0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4],
               [0, 1, 2], [0, 1, 3], [0, 1, 4], [0, 2, 3], [0, 2, 4], [0, 3, 4],
               [1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4],
               [0, 1, 2, 3], [0, 1, 2, 4], [0, 1, 3, 4], [0, 2, 3, 4], [1, 2, 3, 4],
               [0, 1, 2, 3, 4]]

for attack_set in attack_sets:
    print attack_set
    lena = len(attack_set)
    
    gclasses = [0] * len(names)
    for j in range(0, len(names)): #for each instance
        votes = []
        for i in attack_set:
            votes.append(a_gclasses[i][j])
        gclass = max(set(votes), key=votes.count)
        if votes.count(gclass) != lena:
            gclass = -1
        if gclass == 100:
            gclass = -1
        gclasses[j] = gclass
##        cur_conf = [0] * len(matches[0][j])
##        for i in range(0, len(attacks)):
##            for k in range(0, len(matches[i][j])):
##                cur_conf[k] += matches[i][j][k] * weights[i]
##        gclass = cur_conf.index(max(cur_conf))
##        if cur_conf[gclass] < weight_limit:
##            gclass = -1
##        if gclass == 100:
##            gclass = -1
##        gclasses[j] = gclass

    acc = get_acc(gclasses, tclasses)
    fout = open("ensemble-subsets.results", "a")
    results = []
    results.append(str(attack_set))
    results += acc
    results += acc_to_pr(acc, 20)
    results += acc_to_pr(acc, 1000)
    results.append(acc_to_pr2(acc, 1000))
    fout.write("\t".join([str(r) for r in results]) + "\n")
    fout.close()

