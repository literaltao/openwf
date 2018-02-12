import subprocess
import math
import sys
import time
from loaders import *
from gen_list import *

##for c_i in range(0, 10):
##    for g_i in range(0, 10):
##        cpow = (c_i - 5) * 2
##        gpow = (g_i - 5) * 2
##        c = math.pow(10, cpow)
##        g = math.pow(10, gpow)
##        cmd = "./svm-train "
##        cmd += "-c " + str(c) + " "
##        cmd += "-g " + str(g) + " "
##        cmd += "svm.train svm.model"
##        subprocess.call(cmd, shell=True)
##
##        cmd = "./svm-predict svm.test svm.model svm.results >> temp-acc"
##        subprocess.call(cmd, shell=True)
##
##        cmd = "grep Accuracy temp-acc"
##        s = subprocess.check_output(cmd, shell=True)
##        print c_i, g_i, c, g, s
##
##        cmd = "rm svm.results"
##        cmd = "rm temp-acc"
##        subprocess.call(cmd, shell=True)

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

    
def extract(sinste):
    #input "sinste" is a list of cells
    features = []
    
    #SIZE MARKERS
    #does not do anything for cells; see number markers
    mcount = 0 #number of markers, pad to 300 later
    sizemarker = 0 #size accumulator
    for si in range(0, len(sinste)):
        if (si > 0):
            if (sinste[si] * sinste[si-1] < 0): #direction change
                features.append(sizemarker/600)
                mcount += 1
        sizemarker += sinste[si] #can be negative
        if mcount >= 300:
            break

    for i in range(mcount, 300):
        features.append(0)

    #HTML SIZE
    #this almost certainly doesn't actually give html document size
    count_started = 0
    htmlsize = 0
    appended = 0
    for si in range(0, len(sinste)):
        if sinste[si] < 0: #incoming
            count_started = 1
            htmlsize += sinste[si]
        if sinste[si] > 0 and count_started == 1:
            features.append(htmlsize)
            appended = 1
            break
    if (appended == 0):
        features.append(0)

    #TOTAL TRANSMITTED BYTES
    totals = [0, 0]
    for si in range(0, len(sinste)):
        if (sinste[si] < 0):
            totals[0] += abs(sinste[si])
        if (sinste[si] > 0):
            totals[1] += abs(sinste[si])
    features.append(totals[0])
    features.append(totals[1])

    #NUMBER MARKERS
    mcount = 0 #also 300
    nummarker = 0
    for si in range(0, len(sinste)):
        if (si > 0):
            if (sinste[si] * sinste[si-1] < 0): #direction change
                features.append(nummarker)
                mcount += 1
        nummarker += 1
        if mcount >= 300:
            break

    for i in range(mcount, 300):
        features.append(0)

    #NUM OF UNIQUE PACKET SIZES
    uniqsizes = []
    for si in range(0, len(sinste)):
        if not(sinste[si] in uniqsizes):
            uniqsizes.append(sinste[si])
    features.append(len(uniqsizes)/2) #just 1 for cells

    #PERCENTAGE INCOMING PACKETS
    if sum(totals) != 0:
        t = totals[0]/float(sum(totals))
        t = int(t/0.05) * 0.05 #discretize by 0.05
        features.append(t)
    else:
        features.append(0)

    #NUMBER OF PACKETS
    t = totals[0] + totals[1]
    t = int(t/15) * 15 #discertize by 15
    features.append(t)

    for si in range(0, len(sinste)):
        features.append(sinste[si])

    return features

def read_feats(fname):
    feats = []
    with open(fname, "r") as f:
        lines = f.readlines()
        for line in lines:
            this_feat = []
            li = line.split(" ")[1:]
            for l in li:
                l = l.split(":")[1]
                this_feat.append(float(l))
            feats.append(this_feat)
    return feats

def dist(cell1, cell2):
    #does not implement high dimensionality kernel trick?
    feat1 = extract(cell1)
    feat2 = extract(cell2)

    dist = 0
    for i in range(0, min(len(feat1), len(feat2))):
        dist += math.pow(feat1[i] - feat2[i], 2)
    dist = 1 - math.pow(math.e, -SVM_G * 10000 * dist)
    return dist

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

of = d["OUTPUT_LOC"] #alias
[tpc, tnc, nc, pc] = [0, 0, 0, 0]

ofname = of + sys.argv[0]
confname = "svm-conf.results"
if ("CORE_NAME" in d):
    ofname += "-" + str(d["CORE_NAME"])
    confname += "-" + str(d["CORE_NAME"])
    
if os.path.isfile(confname):
    os.remove(confname)
    
if (d["GEN_OWN_LIST"] == 1):
    gen_list(d)
traindata, trainnames = load_listn(d["TRAIN_LIST"])
testdata, testnames = load_listn(d["TEST_LIST"])

skipext = 0
if "DO_NOT_EXTRACT" in d:
    if d["DO_NOT_EXTRACT"] == 1:
        skipext = 1
        trainext = d["EXTRACT_TRAIN_LOC"]
        testext = d["EXTRACT_TEST_LOC"]
        modelext = d["EXTRACT_MODEL_LOC"]
else:
    trainext = ofname + ".train"
    testext = ofname + ".test"
    modelext = ofname + ".model"
if (skipext == 0):

    print "Extracting features..."
    #extract features
    fullnames = [trainnames, testnames]
    fullexts = [trainext, testext]
    for type_i in range(0, 2):
        fout = open(fullexts[type_i], "w")
        for ci in range(0, len(fullnames[type_i])):
            print "Site {} of {}".format(ci, len(fullnames[type_i]))
            for ti in range(0, len(fullnames[type_i][ci])):
                cells = load_cell(fullnames[type_i][ci][ti])
                feats = extract(cells)
                fout.write(str(ci))
                for fi in range(0, len(feats)):
                    fout.write(" " + str(fi+1) + ":" + str(feats[fi]))
                fout.write("\n")
        fout.close()
    if not("SVM_C_LOG" in d and "SVM_G_LOG" in d):
        d["SVM_C_LOG"] = 10
        d["SVM_G_LOG"] = -25
    SVM_C = math.pow(2.0, d["SVM_C_LOG"])
    SVM_G = math.pow(2.0, d["SVM_G_LOG"])

    print "Start training..."
    cmd = "./svm-train -c {} -g {} {} {}".format(
        SVM_C, SVM_G, trainext, modelext)
    subprocess.call(cmd, shell=True)
    
print "Start testing..."
cmd = "./svm-predict -o {} {} {} {}.svmlog".format(
    confname, testext, modelext, ofname)
subprocess.call(cmd, shell=True)

f = open(confname, "r")
lines = f.readlines()
f.close()
site = 0
inst = 0
for line in lines:
    testname = testnames[site][inst]
    logmsg = "{}".format(testname)
    inst += 1
    if inst >= len(testnames[site]):
        site += 1
        inst = 0
    li = line.split(" ")[:-1]
    
    class_probs = [] #class_probs[i] is the score of class i for this sinste
    for t in range(0, len(li)):
        class_probs.append(float(li[t]))
        logmsg += "\t{}".format(class_probs[t])
    gs = class_probs.index(max(class_probs))

    if site == gs:
        if site == len(testnames) - 1 and d["OPEN_INSTNUM"] != 0: #non-monitored
            tnc += 1
        else:
            tpc += 1
    if site == len(testnames) - 1 and d["OPEN_INSTNUM"] != 0:
        nc += 1
    else:
        pc += 1
    rlog(logmsg)

log("TPR:" + str(tpc) + "/" + str(pc))
log("TNR:" + str(tnc) + "/" + str(nc))
