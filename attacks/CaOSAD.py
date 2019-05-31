import subprocess, sys, time, os
from loaders import *
#run-Ca-OSAD.py calls this

##cmd = "rm WaOSAD-small-0.lev"
##subprocess.call(cmd, shell=True)

##cmd = "./clLev 2 0 " + str(optfname) + " WaOSAD-small-0.lev 0 1"
##subprocess.call(cmd, shell=True)

def CaOSAD(d):

    required_d = ["OUTPUT_LOC", "LEV_METHOD", "FOLD_NUM",
                  "CLOSED_SITENUM", "CLOSED_INSTNUM", "OPEN_INSTNUM"]
    for o in required_d:
        if not(o in d.keys()):
            raise Exception("Required option", o, "not in d")

    myname = sys.argv[0]
    of = d["OUTPUT_LOC"]
    [tpc, tnc, nc, pc] = [0, 0, 0, 0]
    #Some sanity checks, because Ca-OSAD is heavy

    fname = "{}clLev-{}".format(of, d["LEV_METHOD"])
    
    check_fail = 0

    print "Checking lev distance files, generated with clLev...",
    if (os.path.isfile(fname + ".lev")):
        print " YES"
    else:
        print " NO"
        check_fail = 1
        
    print "Checking matrix files, generated with clgen_stratify...",
    if (os.path.isfile(fname + "-" + str(d["FOLD_NUM"]) + ".matrix")):
        print " YES"
    else:
        print " NO"
        check_fail = 1

    if (check_fail == 1):
        raise Exception("Some checks failed, aborting")

    #combine matrices:

    if os.path.isfile("{}.train".format(fname)):
        os.remove("{}.train".format(fname))
    for i in range(0, 10):
        if i == d["FOLD_NUM"]:
            cmd = "cat {}-{}.matrix > {}.test".format(fname, i, fname)
        else:
            cmd = "cat {}-{}.matrix >> {}.train".format(fname, i, fname)
        subprocess.call(cmd, shell=True)

    SVM_C = 1024
    print "Start training..."
    cmd = "./svm-train -h 0 -t 4 -c {} {} {}".format(
        SVM_C, fname + ".train", fname + ".model")
    subprocess.call(cmd, shell=True)

    if os.path.isfile("svm-conf.results"):
        os.remove("svm-conf.results")
    print "Start testing..."
    cmd = "./svm-predict -o svm-conf.results {0}{1} {0}{2} {0}{3}".format(
        fname, ".test", ".model", ".svmlog")
    subprocess.call(cmd, shell=True)

    f = open("svm-conf.results", "r")
    lines = f.readlines()
    f.close()
    site = 0
    inst = 0
    conf = []
    for line in lines:
        li = line.split(" ")[:-1]
        
        class_probs = [] #class_probs[i] is the score of class i for this sinste
        for t in range(0, len(li)):
            class_probs.append(float(li[t]))
        conf.append(class_probs)
    names = []
    #names is flimsy, if we ever change how folds work in clgen_stratify then we need to change it here
    for site in range(0, d["CLOSED_SITENUM"]):
        for inst in range(0, d["CLOSED_INSTNUM"]):
            if (inst * 10) / d["CLOSED_INSTNUM"] == d["FOLD_NUM"]:
                names.append("{}-{}.cell".format(str(site), str(inst)))
    for inst in range(0, d["OPEN_INSTNUM"]):
        if (inst * 10) / d["OPEN_INSTNUM"] == d["FOLD_NUM"]:
            names.append("{}.cell".format(str(inst)))

    return conf, names
