import subprocess
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

##if "CORE_NAME" in d:
##    froot = "{}{}-{}".format(d["OUTPUT_LOC"], sys.argv[0], d["CORE_NAME"])
##else:
##    froot = "{}{}".format(d["OUTPUT_LOC"], sys.argv[0])
##
##d["TRAIN_LIST"] = froot + "trainlist"
##d["TEST_LIST"] = froot + "testlist"
##d["WEIGHT_LIST"] = froot + "weightlist"

if (d["GEN_OWN_LIST"] == 1):
    gen_list(d)
traindata, trainnames = load_listn(d["TRAIN_LIST"])
testdata, testnames = load_listn(d["TEST_LIST"])
##a = time.time()
skip = 0
if "DO_NOT_EXTRACT" in d:
    if d["DO_NOT_EXTRACT"] == 1:
        skip = 1
if (skip == 0):
    print "Extracting..."
    cmd = "python fextractor.py " + optfname
    subprocess.call(cmd, shell=True)
if "CORE_NAME" in d:
    flname = d["OUTPUT_LOC"] + "flearner-" + str(d["CORE_NAME"]) + ".results"
else:
    flname = d["OUTPUT_LOC"] + "flearner.results"
if os.path.isfile(flname):
    os.remove(flname)
##b = time.time()
##extracttime = b - a
cmd = "./flearner " + optfname
subprocess.call(cmd, shell=True)

##f = open("flearner.log", "r")
##lines = f.readlines()
##f.close()
##for line in lines:
##    log(line[:-1])

f = open(flname, "r")
lines = f.readlines()
f.close()
for line in lines:
    rlog(line)

##for i in range(0, len(lines)):
##    line = lines[i]
##    if "Training time" in line:
##        time = float(line.split("\t")[1])
##        lines[i] = "Training time\t" + str(time + extracttime) + "\n"
##    if "Testing time" in line:
##        time = float(line.split("\t")[1])
##        lines[i] = "Testing time\t" + str(time + extracttime) + "\n"
