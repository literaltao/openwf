import subprocess
import math
import sys
import time
from loaders import *
from gen_list import *

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
    #sinste: list of packet sizes

    #first 4 features

    insize = 0
    outsize = 0
    inpacket = 0
    outpacket = 0

    for i in range(0, len(sinste)):
        if sinste[i] > 0:
            outsize += sinste[i]
            outpacket += 1
        else:
            insize += abs(sinste[i])
            inpacket += 1
    features = [insize, outsize, inpacket, outpacket]

    #100 interpolants
    
    n = 100 #number of linear interpolants

    x = 0 #sum of absolute packet sizes
    y = 0 #sum of packet sizes
    graph = []
    
    for si in range(0, len(sinste)):
        x += abs(sinste[si])
        y += sinste[si]
        graph.append([x, y])


    #derive interpolants
    max_x = graph[-1][0] 
    gap = float(max_x)/(n+1)
    graph_ptr = 0

    for i in range(0, n):
        sample_x = gap * (i+1)
        while (graph[graph_ptr][0] < sample_x):
            graph_ptr += 1
            if (graph_ptr >= len(graph) - 1):
                graph_ptr = len(graph) - 1
                #wouldn't be necessary if floats were floats
                break
        next_y = graph[graph_ptr][1]
        next_x = graph[graph_ptr][0]
        last_y = graph[graph_ptr-1][1]
        last_x = graph[graph_ptr-1][0]

        if (next_x - last_x != 0):
            slope = (next_y - last_y)/float(next_x - last_x)
        else:
            slope = 1000
        sample_y = slope * (sample_x - last_x) + last_y

        features.append(sample_y)

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
    g = math.pow(10, -4)

    dist = 0
    for i in range(0, min(len(cell1), len(cell2))):
        dist += math.pow(cell1[i] - cell2[i], 2)
    dist = 1 - math.pow(math.e, -g * dist)
    return dist

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

of = d["OUTPUT_LOC"]
[tpc, tnc, nc, pc] = [0, 0, 0, 0]

ofname = of + sys.argv[0]
confname = "svm-conf.results"
if ("CORE_NAME" in d):
    ofname += "-" + str(d["CORE_NAME"])
    confname += "-" + str(d["CORE_NAME"])

if os.path.isfile(confname):
    os.remove(confname)

skipext = 0
if "DO_NOT_EXTRACT" in d:
    if d["DO_NOT_EXTRACT"] == 1:
        skipext = 1

trainext = ofname + ".train"
testext = ofname + ".test"

if (d["GEN_OWN_LIST"] == 1):
    gen_list(d)

traindata, trainnames = load_listn(d["TRAIN_LIST"])
testdata, testnames = load_listn(d["TEST_LIST"])
    
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
    d["SVM_C_LOG"] = 16
    d["SVM_G_LOG"] = -28
SVM_C = math.pow(2.0, d["SVM_C_LOG"])
SVM_G = math.pow(2.0, d["SVM_G_LOG"])

print "Start training..."
cmd = "./svm-train -c {1} -g {2} {3} {0}.model".format(
    ofname, SVM_C, SVM_G, trainext)
subprocess.call(cmd, shell=True)
print "Start testing..."
cmd = "./svm-predict -o {1} {2} {0}.model {0}.svmlog".format(
    ofname, confname, testext)
subprocess.call(cmd, shell=True)

f = open(confname, "r")
lines = f.readlines()
f.close()
site = 0
inst = 0
for line in lines:
    testname = testnames[site][inst]
    logmsg = "{}".format(testname)
    li = line.split(" ")[:-1]
##    print li
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
    inst += 1
    if (inst >= len(testnames[site])): #carry over
        site += 1
        inst = 0

log("TPR:" + str(tpc) + "/" + str(pc))
log("TNR:" + str(tnc) + "/" + str(nc))
