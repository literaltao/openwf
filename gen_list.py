#generate trainlist and testlist for other files
import subprocess, sys
from loaders import *

def gen_list(d):
    #given parameters are either:
    #CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM
    #CLOSED_SITESTART, CLOSED_SITEEND, CLOSED_INSTNUM OPEN_INSTSTART, OPEN_INSTEND

    #FOLD_TOTAL is optional (default 10)

    #different modes
    #MODE 1: trainlist = testlist, all data in DATA_LOC (ignore parameters)
    #MODE 2: trainlist = testlist, according to parameters
    #MODE 3: trainlist != testlist: X-fold classification according to parameters, requires FOLD_NUM
    #MODE 4: trainlist != testlist: testlist is fold X, trainlist is fold X+1 (len(trainlist) = len(testlist))
    #MODE 5: trainlist != testlist: inverted MODE 3 (trainlist << testlist)
    #MODE 7: weaving MODE 5
    #DATA_LOC is where the files are
    #OUTPUT_LOC is the name to write
    #DATA_TYPE determines extension
    #non-weaving: training and testing instances are separated into blocks (e.g. 1-10 training, 11-20 testing)
    #weaving: training and testing instances are interweaved (e.g. *0 training, *2-*9 testing)

    if "CLOSED_SITESTART" in d.keys():
        cstart = d["CLOSED_SITESTART"]
        cend = d["CLOSED_SITEEND"]
    else:
        cstart = 0
        cend = d["CLOSED_SITENUM"]

    if "OPEN_INSTSTART" in d.keys():
        ostart = d["OPEN_INSTSTART"]
        oend = d["OPEN_INSTEND"]
    else:
        ostart = 0
        oend = d["OPEN_INSTNUM"]


    if ("FOLD_TOTAL" in d):
        foldtotal = d["FOLD_TOTAL"]
    else:
        foldtotal = 10

    d["DATA_TYPE"] = "cell"

##    fullsizename = "-"
##    if (cstart == 0):
##        fullsizename += str(cend)
##    else:
##        fullsizename += str(cstart) + "-" + str(cend)
##    fullsizename += "x{}+".format(d["CLOSED_INSTNUM"])
##    if (ostart == 0):
##        fullsizename += str(oend)
##    else:
##        fullsizename += str(ostart) + "-" + str(oend)
##
##    methodname = ""
##    smallsizename = ""
##    if d["FOLD_MODE"] == 2:
##        methodname = "-all"
##        smallsizename = ""
##    if d["FOLD_MODE"] == 3 or d["FOLD_MODE"] == 4:
##        methodname = "-fold"
##        smallsizename = "-{}-{}".format(d["FOLD_NUM"], foldtotal)
##    if d["FOLD_MODE"] == 5:
##        methodname = "-random"
##        smallsizename = "-{}x{}+{}".format(d["RANDCLOSED_SITENUM"],
##                                       d["RANDCLOSED_INSTNUM"],
##                                       d["RANDOPEN_INSTNUM"])
##
##    suggtrainname = "train{}{}{}".format(fullsizename, methodname, smallsizename)
##    suggtestname = "test{}{}{}".format(fullsizename, methodname, smallsizename)
##
##    if ("USE_SUGG_LIST_NAME" in d):
##        if d["USE_SUGG_LIST_NAME"] == 1:
##            d["TRAIN_LIST"] = suggtrainname
##            d["TEST_LIST"] = suggtestname
##    print "Wrote to", d["TRAIN_LIST"], d["TEST_LIST"]
##    print "Suggested name:", suggtrainname, suggtestname
        
    trainout = open(d["TRAIN_LIST"], "w")
    testout = open(d["TEST_LIST"], "w")
    if not("WEIGHT_LIST" in d):
        d["WEIGHT_LIST"] = "temp-weightlist"
    weightout = open(d["WEIGHT_LIST"], "w")

    ##print ostart, oend, cstart, cend, d["CLOS

    if (d["FOLD_MODE"] == 1):
        cmd = "ls " + d["DATA_LOC"]
        s = subprocess.check_output(cmd, shell=True)
        s = s.split("\n")
        for sname in s:
            if sname[-len(d["DATA_TYPE"]):] == d["DATA_TYPE"]:
                trainout.write(sname + "\n")
                testout.write(sname + "\n")

    if (d["FOLD_MODE"] == 2):
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                trainout.write(sname + "\n")
                testout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            trainout.write(sname + "\n")
            testout.write(sname + "\n")

    if (d["FOLD_MODE"] == 3):
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * d["FOLD_NUM"] and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (d["FOLD_NUM"]+1)):
                    testout.write(sname + "\n")
                else:
                    trainout.write(sname + "\n")
                    weightout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * d["FOLD_NUM"] + ostart and
                s < (oend-ostart)/foldtotal * (d["FOLD_NUM"]+1) + ostart):
                testout.write(sname + "\n")
            else:
                trainout.write(sname + "\n")
                weightout.write(sname + "\n")

    if (d["FOLD_MODE"] == 4):
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * d["FOLD_NUM"] and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (d["FOLD_NUM"]+1)):
                    testout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * d["FOLD_NUM"] + ostart and
                s < (oend-ostart)/foldtotal * (d["FOLD_NUM"]+1) + ostart):
                testout.write(sname + "\n")
        trainfoldnum = (d["FOLD_NUM"] + 1) % foldtotal
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * trainfoldnum and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (trainfoldnum+1)):
                    trainout.write(sname + "\n")
                    weightout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * trainfoldnum + ostart and
                s < (oend-ostart)/foldtotal * (trainfoldnum+1) + ostart):
                trainout.write(sname + "\n")
                weightout.write(sname + "\n")


    if (d["FOLD_MODE"] == 5):
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * d["FOLD_NUM"] and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (d["FOLD_NUM"]+1)):
                    trainout.write(sname + "\n")
                    weightout.write(sname + "\n")
                else:
                    testout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * d["FOLD_NUM"] + ostart and
                s < (oend-ostart)/foldtotal * (d["FOLD_NUM"]+1) + ostart):
                trainout.write(sname + "\n")
                weightout.write(sname + "\n")
            else:
                testout.write(sname + "\n")

    if (d["FOLD_MODE"] == 7):
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (((s - cstart) * d["CLOSED_INSTNUM"] + i) % foldtotal == d["FOLD_NUM"]):
                    trainout.write(sname + "\n")
                    weightout.write(sname + "\n")
                else:
                    testout.write(sname + "\n")
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if ((s - ostart) % foldtotal == d["FOLD_NUM"]):
                trainout.write(sname + "\n")
                weightout.write(sname + "\n")
            else:
                testout.write(sname + "\n")
        

    trainout.close()
    testout.close()
    weightout.close()

if __name__ == "__main__":
    d = load_options(sys.argv[1])
    gen_list(d)
