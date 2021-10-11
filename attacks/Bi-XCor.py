import subprocess
import math
import time
import numpy
import sys
import os
from loaders import *


def cc(p, q):
    if len(p) == 0 or len(q) == 0:
        return 0
    # calculates cross-correlation of p and q, two lists
    cclen = min(len(p), len(q))
    # we cut out the longer part and completely ignore it:
    ps = p[:cclen]
    qs = q[:cclen]

    cc = 0

    pm = numpy.mean(ps)
    qm = numpy.mean(qs)

    for i in range(0, cclen):
        cc += (ps[i] - pm) * (qs[i] - qm)

    denom = numpy.std(ps) * numpy.std(qs) * cclen
    cc /= denom

    return cc


def cc_match(testdata, class_m):
    # class_m is its mean inter and len
    testdata_inter = cell_to_cellinter(testdata)
    testdata_len = cell_to_celllen(testdata)
    cc_inter = cc(testdata_inter, class_m[0])
    cc_len = cc(testdata_len, class_m[1])
    return cc_inter * cc_len


def cell_to_cellinter(cell):
    # converts cell to interpacket timings

    # just in case...
    cell = sorted(cell, key=lambda c: c[0])

    cell_inter = []
    lasttime = cell[0][0]
    for i in range(0, len(cell)):
        cell_inter.append(cell[i][0] - lasttime)
        lasttime = cell[i][0]
    return cell_inter


def cell_to_celllen(cell):
    # converts cell to cell lengths

    cell_len = []
    for i in range(0, len(cell)):
        cell_len.append(cell[i][1])

    return cell_len


def dist(cell1, cell2):
    c1t = cell_to_cellinter(cell1)
    c2t = cell_to_cellinter(cell2)
    c1l = cell_to_celllen(cell1)
    c2l = cell_to_celllen(cell2)

    return 2 - cc(c1t, c2t) - cc(c1l, c2l)


try:
    d = load_options(sys.argv[1])
except Exception as e:
    print(sys.argv[0], str(e))
    sys.exit(0)

ofname = ofname = "{}{}-{}".format(d["OUTPUT_LOC"], "Bi-XCor", d["CORE_NAME"])
logfname = ofname + ".log"

flog(" " + sys.argv[0] + " " + sys.argv[1], logfname, logtime=1)
flog(repr(d), logfname)

[tpc, tnc, pc, nc] = [0, 0, 0, 0]
trainnames, testnames = get_list(d)

##fullnames = trainnames + testnames

##distloc = d["OUTPUT_LOC"] + sys.argv[0].split("/")[-1] + ".dist"
##fullflatnames = [names for sets in fullnames for names in sets]
##print len(fullflatnames)
##if len(fullflatnames) > 10000:
##    print "Too many instances ({}), did not write distance".format(len(fullflatnames))
##    sys.exit(-1)
##else:
##    write_dist(distloc, fullnames, dist)

##trainname = trainnames[28][25]
##traindata = load_cell(trainname, time=1)
##traindata_inter = cell_to_cellinter(traindata)
##traindata_len = cell_to_celllen(traindata)
##print traindata_inter
##sys.exit(0)

# Training:
# For each class, we learn mean interpacket times and mean packet lengths
# class_m[0] is a list, for example class_m[0][0] is the mean interpacket time
# between the first and second packets of all training pseqs belonging to the given site
# These are used for comparison with testing iptimes and plens using cross-correlation for classification
# a = time.time()

class_ms = []
for site in range(0, len(trainnames)):
    print("Training site %d of %d" % (site, len(trainnames)))
    iptime_means = (
        []
    )  # iptime_means[n] is the mean iptime between cell n-1 and n for pseqs of this site
    plen_means = []
    cell_counts = []
    for inst in range(0, len(trainnames[site])):
        cells = load_cell(trainnames[site][inst], time=1)
        last_ptime = cells[0][0]
        for cell_i in range(0, len(cells)):
            cell = cells[cell_i]
            try:
                iptime_means[cell_i] += cell[0] - last_ptime
                last_ptime = cell[0]
                plen_means[cell_i] += cell[1]
                cell_counts[cell_i] += 1
            except:
                iptime_means.append(cell[0] - last_ptime)
                last_ptime = cell[0]
                plen_means.append(cell[1])
                cell_counts.append(1)

    for i in range(0, len(iptime_means)):
        iptime_means[i] = iptime_means[i] / float(cell_counts[i])
        plen_means[i] = plen_means[i] / float(cell_counts[i])
    class_ms.append([iptime_means, plen_means])

# Testing:
print("Writing to {}.score".format(ofname))
sout = open(ofname + ".score", "w")
for site in range(0, len(testnames)):
    print("Testing site %d of %d" % (site, len(testnames)))
    for inst in range(0, len(testnames[site])):
        testname = testnames[site][inst]
        logmsg = testname
        testdata = load_cell(testname, time=1)
        class_probs = []  # class_probs[i] is the score of class i for this sinste
        for t in range(0, len(class_ms)):
            class_probs.append(cc_match(testdata, class_ms[t]))
            logmsg += "\t{}".format(class_probs[t])
        gs = class_probs.index(max(class_probs))

        if site == gs:
            if site == len(testnames) - 1 and d["OPEN_INSTNUM"] != 0:  # non-monitored
                tnc += 1
            else:
                tpc += 1
        if site == len(testnames) - 1 and d["OPEN_INSTNUM"] != 0:
            nc += 1
        else:
            pc += 1
        sout.write(logmsg + "\n")
sout.close()


##    c = time.time()
##    testtime += c - b

##log("Training time" + "\t" + str(traintime))
##log("Testing time" + "\t" + str(testtime))
print("TPR:" + str(tpc) + "/" + str(pc))
print("TNR:" + str(tnc) + "/" + str(nc))
