import subprocess
import sys
import time
from loaders import *
        
try:
    optfname = sys.argv[1]
    d = load_options(optfname)
    ofname = "{}{}-{}".format(d["OUTPUT_LOC"], "Wa-kNN", d["CORE_NAME"])
except Exception,e:
    print sys.argv[0], str(e)
    sys.exit(0)

logfname = ofname + ".log"
flog(sys.argv[0] + " " + sys.argv[1], logfname, logtime=1)
flog(repr(d), logfname)

##if "CORE_NAME" in d:
##    froot = "{}{}-{}".format(d["OUTPUT_LOC"], sys.argv[0], d["CORE_NAME"])
##else:
##    froot = "{}{}".format(d["OUTPUT_LOC"], sys.argv[0])
##
d["TRAIN_LIST"] = ofname + "-trainlist"
d["TEST_LIST"] = ofname + "-testlist"
d["WEIGHT_LIST"] = ofname + "-weightlist"

trainnames, testnames = get_list(d)

#flatten trainnames, testnames
trainnamesf = [f for x in trainnames for f in x]
testnamesf = [f for x in testnames for f in x]

#write filelist for flearner
f = open(d["TRAIN_LIST"], "w")
for name in trainnamesf:
    f.write(name + "\n")
f.close()
f = open(d["WEIGHT_LIST"], "w")
for name in trainnamesf:
    f.write(name + "\n")
f.close()
f = open(d["TEST_LIST"], "w")
for name in testnamesf:
    f.write(name + "\n")
f.close()

#write new options file used for flearner
#we need to do this to write out the train/weight/test list
write_options(ofname + "flearner-options", d)

if d["DO_NOT_EXTRACT"] == 0:
    cmd = "python fextractor.py " + optfname
    subprocess.call(cmd, shell=True)

cmd = "./flearner " + ofname + "flearner-options"
subprocess.call(cmd, shell=True)

##f = open("flearner.log", "r")
##lines = f.readlines()
##f.close()
##for line in lines:
##    log(line[:-1])

##f = open(flname, "r")
##lines = f.readlines()
##f.close()
##for line in lines:
##    rlog(line)

##for i in range(0, len(lines)):
##    line = lines[i]
##    if "Training time" in line:
##        time = float(line.split("\t")[1])
##        lines[i] = "Training time\t" + str(time + extracttime) + "\n"
##    if "Testing time" in line:
##        time = float(line.split("\t")[1])
##        lines[i] = "Testing time\t" + str(time + extracttime) + "\n"
