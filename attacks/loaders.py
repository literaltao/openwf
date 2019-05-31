import sys
import os
import time

def str_to_sinste(fname):
    #given a file name fold/X-Y.xxx or fold/Z.xxx, returns (site, inst)
    #site = -1 indicates open world

    while "/" in fname:
        fname = fname[fname.index("/")+1:]
    if "." in fname:
        fname = fname[:fname.index(".")]
    site = -1
    inst = -1
    if "-" in fname:
        fname = fname.split("-")
        site = int(fname[0])
        inst = int(fname[1])
    else:
        try:
            inst = int(fname)
        except:
            site = -1
            inst = -1

    return [site, inst]

def get_dillname(d):
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
    
    fullsizename = ""
    if (cstart == 0):
        fullsizename += str(cend)
    else:
        fullsizename += str(cstart) + "-" + str(cend)
    fullsizename += "x{}+".format(d["CLOSED_INSTNUM"])
    if (ostart == 0):
        fullsizename += str(oend)
    else:
        fullsizename += str(ostart) + "-" + str(oend)

    suggname = "{}-{}.dill".format(fullsizename, d["DATA_TYPE"])
    return suggname

def load_dill(fname, d):
    #loads dill and also separates the data into the right sets
    #very dependent on write_dill logic in the middle (to save time)
    f = open(fname, "r")
    dillset = dill.load(f)
    f.close()

    data = dillset["DATA"]
    names = dillset["NAMES"]

    cstart = dillset["CLOSED_SITESTART"]
    cend = dillset["CLOSED_SITEEND"]
    cinst = dillset["CLOSED_INSTNUM"]
    ostart = dillset["OPEN_INSTSTART"]
    oend = dillset["OPEN_INSTEND"]

    if fname != get_dillname(dillset):
        print "load_dill warning: expected input {}, got {}".format(get_dillname(d), fname)

    foldnum = d["FOLD_NUM"]
    foldtotal = 10

    if (d["FOLD_MODE"] == 2):
        traindata = data
        testdata = data
        trainnames = names
        testnames = names

    if (d["FOLD_MODE"] == 3):
        traindata = []
        testdata = []
        trainnames = []
        testnames = []
        for i in range(0, (cend - cstart) * cinst):
            if (i % cinst) * foldtotal / cinst == foldnum:
                testdata.append(data[i])
                testnames.append(names[i])
            else:
                traindata.append(data[i])
                trainnames.append(names[i])
        for i in range(0, oend - ostart): #i is index in open world data
            ti = i + (cend - cstart) * cinst #ti is index in overall data
            if (i * foldtotal / (oend - ostart)) == foldnum:
                testdata.append(data[ti])
                testnames.append(names[ti])
            else:
                traindata.append(data[ti])
                trainnames.append(names[ti])
        
    return traindata, testdata, trainnames, testnames
    
def write_dill(fname, data, names, d):
    dillset = {}

    #do some critical sanity checks

    if fname != get_dillname(d):
        print "write_dill warning: expected output {}, got {}".format(get_dillname(d), fname)

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
    cinst = d["CLOSED_INSTNUM"]
    
    dillset["CLOSED_SITESTART"] = cstart
    dillset["CLOSED_SITEEND"] = cend
    dillset["OPEN_INSTSTART"] = ostart
    dillset["OPEN_INSTEND"] = oend
    dillset["CLOSED_INSTNUM"] = cinst
    dillset["DATA_TYPE"] = d["DATA_TYPE"]

    [es, ei] = [cstart, 0]
    for i in range(0, len(names)):
        [rs, ri] = str_to_sinste(names[i])
        if ([rs, ri] != [es, ei]):
            print "write_dill error: name not in order, aborting"
            print "Got {}-{}, expected {}-{}".format(rs, ri, es, ei)
            sys.exit(-1)
        ei += 1
        if (ei == cinst and es != -1):
            es += 1
            ei = 0
        if (es == cend):
            es = -1

    dillset["DATA"] = data
    dillset["NAMES"] = names
    f = open(fname, "w")
    dill.dump(dillset, f)
    f.close()

def load_cell(fname, time=0, ext=".cell"):
    #time = 0 means don't load packet times (saves time and memory)
    data = []
    starttime = -1
    try:
        f = open(fname, "r")
        lines = f.readlines()
        f.close()

        if ext == ".htor":
            #htor actually loads into a cell format
            for li in lines:
                psize = 0
                if "INCOMING" in li:
                    psize = -1
                if "OUTGOING" in li:
                    psize = 1
                if psize != 0:
                    if time == 0:
                        data.append(psize)
                    if time == 1:
                        time = float(li.split(" ")[0])
                        if (starttime == -1):
                            starttime = time
                        data.append([time - starttime, psize])

        if ext == ".cell":
            for li in lines:
                li = li.split("\t")
                p = int(li[1])
                if time == 0:
                    data.append(p)
                if time == 1:
                    t = float(li[0])
                    if (starttime == -1):
                        starttime = t
                    data.append([t-starttime, p])
        if ext == ".burst":
            #data is like: 1,1,1,-1,-1\n1,1,1,1,-1,-1,-1
            for li in lines:
                burst = [0, 0]
                li = li.split(",")
                data.append([li.count("1"), li.count("-1")])
                for l in li:
                    if l == "1":
                        burst[0] += 1
                    if l == "-1":
                        burst[1] += 1
                data.append(burst)

        if ext == ".pairs":
            #data is like: [[3, 12], [1, 24]]
            #not truly implemented
            data = list(lines[0])            
    except:
        print "Could not load", fname
        sys.exit(-1)
    return data

def load_cellt(fname, ext=".cell"):
    return load_cell(fname, time=1, ext=ext)

def load_set(d, site=-1, inst=-1, time=0, ext=".cell"):
    #loads all data OR all of a specific site OR a specific inst of a site
    CLOSED_SITENUM = d["CLOSED_SITENUM"]
    CLOSED_INSTNUM = d["CLOSED_INSTNUM"]
    OPEN_INSTNUM = d["OPEN_INSTNUM"]
    DATA_LOC = d["DATA_LOC"]

    data = []
    #there's probably a better way to simplify this

    if (site == -1 and inst == -1):
        #load closed world
        for i in range(0, CLOSED_SITENUM):
            data.append([])
            for j in range(0, CLOSED_INSTNUM):
                fname = str(i) + "-" + str(j) + ext
                data[-1].append(load_cell(DATA_LOC + fname, time, ext))

        #load open world
        data.append([])
        for i in range(0, OPEN_INSTNUM):
            fname = str(i) + ext
            data[-1].append(load_cell(DATA_LOC + fname, time, ext))

    if (site != -1 and inst == -1):
        #load all insts of one site
        if (site == CLOSED_SITENUM):
            for i in range(0, OPEN_INSTNUM):
                fname = str(i) + ext
                data.append(load_cell(DATA_LOC + fname, time, ext))
        else:
            for j in range(0, CLOSED_INSTNUM):
                fname = str(site) + "-" + str(j) + ext
                data.append(load_cell(DATA_LOC + fname, time, ext))

    if (site != -1 and inst != -1):
        #load one particular inst
        if (site == CLOSED_SITENUM):
            fname = str(inst) + ext
            data = load_cell(DATA_LOC + fname, time, ext)
        else:
            fname = str(site) + "-" + str(inst) + ext
            data = load_cell(DATA_LOC + fname, time, ext)
                
    return data

def load_all(CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM, INPUT_LOC, time=0):
    #deprecated; do not call
    print "deprecated: call load_set"
    sys.exit(0)

def load_log(fname):
    #reads the last two lines for tpc/tnc/pc/nc
    f = open(fname, "r")
    lines = f.readlines()
    f.close()
    [tpc, tnc, pc, nc] = [0, 0, 0, 0]
    tprline = lines[-2]
    tnrline = lines[-1]
    if "TPR" in tprline and "TNR" in tnrline:
        tprline = tprline.split("\t")[1].split(":")[1]
        tpc = int(tprline.split("/")[0])
        pc = int(tprline.split("/")[1])
        tnrline = tnrline.split("\t")[1].split(":")[1]
        tnc = int(tnrline.split("/")[0])
        nc = int(tnrline.split("/")[1])
        return [tpc, tnc, pc, nc]
    return -1

def load_score(fname):
    #reads the last lines for match value of each instance
    #note that data and names is flattened, unlike load_list
    f = open(fname, "r")
    lines = f.readlines()
    f.close()
##    start = 0
##    for line_i in range(0, len(lines)):
##        if lines[line_i].split("\t")[1][0] == "{": #this line is options
##            start = line_i
##    start += 1
##    lines = lines[start:]
    data = []
    names = []
    for line in lines:
        li = line.split("\t")
        if (len(li) > 2):
            name = li[0]
            if name in names:
                data[names.index(name)] = [float(c) for c in li[1:]]
            else:
                names.append(name)
                data.append([float(c) for c in li[1:]])
    return data, names

def load_dist(fname):
    #reads the entire file for distances
    #fills in the blanks too
    #note that data and names is flattened, unlike load_list
    f = open(fname, "r")
    lines = f.readlines()
    f.close()
    names = []
    dist = []
    if len(lines) > 30000:
        a = raw_input("Number of lines = {}. Abort (y)?\n".format(len(lines)))
        if (a == "y"):
            sys.exit(-1)
    for line_i in range(0, len(lines)):
        line = lines[line_i][:-1]
        li = line.split("\t")
        names.append(li[0])
        this_dist = []
        for i in range(0, line_i):
            this_dist.append(dist[i][line_i])
        this_dist.append(0)
        this_dist += [float(c) for c in li[1:]]
        dist.append(this_dist)
    return dist, names


def kfold(data, fi, foldtotal):
    #input: full data set, current fi, total number of folds
    #output: traindata, testdata
    traindata = []
    testdata = []
    for cdata in data: #each class
        traindata.append([])
        testdata.append([])
        
        test_indices = []

        test_num_start = (len(cdata) * fi) / foldtotal
        test_num_end = test_num_start + max(len(cdata)/foldtotal, 1)
        for ti in range(0, len(cdata)):
            if ti < test_num_end and ti >= test_num_start:
                test_indices.append(ti)
        
        for inst in range(0, len(cdata)):
            if inst in test_indices:
                testdata[-1].append(cdata[inst])
            else:
                traindata[-1].append(cdata[inst])

    return traindata, testdata

##def load_list(flist, time=0):
##    #loads the list of files in flist
##    #deprecated.
##    data = []
##    opendata = []
##    datanames = []
##    opendatanames = []
##    f = open(flist, "r")
##    fnames = f.readlines()
##    f.close()
##    for fname in fnames:
##        fname = fname[:-1]
##        relfname = fname.split("/")[-1]
##        relfname = relfname.split(".")[0]
##        if "-" in relfname:
##            s = int(relfname.split("-")[0])
##            i = int(relfname.split("-")[1])
##            while s >= len(data):
##                data.append([])
##                datanames.append([])
##            data[s].append(load_cell(fname, time))
##            datanames[s].append(fname)
##        else:
##            i = int(relfname)
##            opendata.append(load_cell(fname, time))
##            opendatanames.append(fname)
##    data.append(opendata)
##    if (opendatanames != []):
##        datanames.append(opendatanames)
##    return data, datanames
##
##def load_listn(flist):
##    #loads the list of files in flist
##    #only loads names. returns data as empty set.
##    #deprecated.
##    datanames = []
##    opendatanames = []
##    f = open(flist, "r")
##    fnames = f.readlines()
##    f.close()
##    for fname in fnames:
##        fname = fname[:-1]
##        relfname = fname.split("/")[-1]
##        relfname = relfname.split(".")[0]
##        if "-" in relfname:
##            s = int(relfname.split("-")[0])
##            i = int(relfname.split("-")[1])
##            while s >= len(datanames):
##                datanames.append([])
##            datanames[s].append(fname)
##        else:
##            i = int(relfname)
##            opendatanames.append(fname)
##    datanames.append(opendatanames)
##    return [], datanames
    


def read_value(string):
    if string[0] == "'" and string[-1] == "'":
        return string[1:-1]
    val = string
    try:
        val = int(string)
    except:
        try:
            val = float(string)
        except:
            pass
    return val

def load_options(fname):
    d_options = {}
    f = open(fname, "r")
    lines = f.readlines()
    f.close()
    for line in lines:
        ignore = 0
        if (len(line) > 0):
            if line[0] == "#":
                ignore = 1
        if (ignore == 0 and "\t" in line):
            line = line[:-1]
            li = line.split("\t")
            d_options[li[0]] = read_value(li[1])
    return d_options

def flog(msg, fname):
    f = open(fname, "a+")
    f.write(repr(time.time()) + "\t" + str(msg) + "\n")
    f.close()

def write_options(fname, d_options):
    other = d_options.keys()
    order = ["CLOSED_SITENUM", "CLOSED_INSTNUM", "OPEN_INSTNUM", "OPEN",
             "INPUT_LOC", "OUTPUT_LOC", "DATA_LOC", "ATTACK_LOC", "DATA_TYPE",
             "LEV_METHOD", "LEV_LOC",
             "FOLD_MODE", "FOLD_NUM", "FOLD_TOTAL"]
    f = open(fname, "w")
    for opt in order:
        if opt in d_options.keys():
            f.write(str(opt) + "\t" + str(d_options[opt]) + "\n")
            other.remove(opt)
    for opt in other:
        f.write(str(opt) + "\t" + str(d_options[opt]) + "\n")
    f.close()

def write_dist(fname, cellnames, dist, t=1):
    #fname is the target output name
    #cellnames is the list of names of input files coressponding to dist
    #dist is a function callback, calculating the distance between any two cells
    startsite = 0
    startinst = 0
##    print cellnames
    if os.path.isfile(fname):
        done = 0
        while (done == 0):
            a = raw_input("dist file already exists. Re-create? y=yes, r=resume, n=skip")
            if a == "y":
                os.remove(fname)
                done = 1
            elif a == "r":
                f = open(fname, "r")
                line = f.readlines()[-1]
                li = line.split("\t")[0]
                f.close()
                for site in range(0, len(cellnames)):
                    for inst in range(0, len(cellnames[site])):
                        if cellnames[site][inst] == li:
                            startsite = site
                            startinst = inst + 1
                            if (startinst == len(cellnames[site])): #carry the one
                                startsite += 1
                                startinst = 0
                done = 1
            elif a == "n":
                startsite = len(cellnames)
                startinst = 0
                done = 1

    start_time = time.time()
    total_count = len([k for k in cellnames for j in k])
    count = 0
    for site1 in range(startsite, len(cellnames)):
        for inst1 in range(startinst, len(cellnames[site1])):
            if (count != 0):
                rate = (time.time() - start_time)/float(count)
                exp_time = (total_count - count) * rate
            else:
                rate = 0
                exp_time = 0
            print "write_dist {}/{}-{} time left {}".format(site1, len(cellnames), inst1, int(exp_time))
            count += 1
            dstr = cellnames[site1][inst1] + "\t"
            cell1 = load_cell(cellnames[site1][inst1], time=t)
            for site2 in range(0, len(cellnames)):
                for inst2 in range(0, len(cellnames[site2])):
                    if site2 > site1 or (site2 == site1 and inst2 > inst1):
                        cell2 = load_cell(cellnames[site2][inst2], time=t)
                        dstr += str(dist(cell1, cell2)) + "\t"
            dstr = dstr[:-1]
            fout = open(fname, "a")
            fout.write(dstr + "\n")
            fout.close()
        startinst = 0

def write_data(fname, data, comment=""):
    #general function for writing to a file
    #supports list, list of list, list of list of list, dict
    #not ducky
    f = open(fname, "w")
    f.write("#" + str(sys.argv) + "\n")
    if comment != "":
        f.write("#" + comment + "\n")

    if type(data) is list:
        f.write("!LIST\n")
        for i in range(0, len(data)):
            string = ""
            if type(data[i]) is list:
                for j in range(0, len(data[i])):
                    if type(data[i][j]) is list:
                        for k in range(0, len(data[i][j])):
                            string += repr(data[i][j][k]) + ","
                        string = string[:-1]
                    else:
                        string += repr(data[i][j])
                    string += "\t"
                string = string[:-1]
            else:
                string += repr(data[i])
            f.write(string + "\n")
    
    if type(data) is dict:
        f.write("!DICT\n")
        for k in data.keys():
            f.write(k + "\t" + data[k] + "\n")
    f.close()

def load_data(fname):
    #inverse of write_data
    #skips comments

    f = open(fname, "r")
    lines = f.readlines()
    f.close()
    #this is dumb?
    lines2 = []
    for line in lines:
        if not(line[0] == "#"):
            lines2.append(line[:-1])
    lines = lines2

    if lines[0] == "!LIST":
        data = []
        for line in lines[1:]:
            if ("\t") in line:
                this_data = []
                for lin in line.split("\t"):
                    if (",") in lin:
                        this_this_data = []
                        for li in lin.split(","):
                            this_this_data.append(read_value(li))
                        this_data.append(this_this_data)
                    else:
                        this_data.append(read_value(lin))
                data.append(this_data)
            else:
                data.append(read_value(line))
    if lines[0] == "!DICT":
        data = {}
        for line in lines[1:]:
            lin = line.split("\t")
            data[lin[0]] = lin[1]

    return data

def read_mpairs(fname):
    f = open(fname, "r")
    lines = f.readlines()
    f.close()

    mpairs = []

    for line in lines:
        mpair = [0, 0]
        li = line.split(",")
        for l in li:
            if l == "-1":
                mpair[1] += 1
            elif l == "1":
                mpair[0] += 1
        mpairs.append(mpair)
    return mpairs
    
import pprint

def options_to_string(d_options):
    return pprint.saferepr(d_options)

def names_to_instnums(tnameslist):
    #from a list of file names, get CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM
    CLOSED_SITENUM = 0
    CLOSED_INSTNUM = 0
    OPEN_INSTNUM = 0
    for n in tnameslist:
        sinste = str_to_sinste(n)
        if sinste[0] == -1:
            OPEN_INSTNUM = max(OPEN_INSTNUM, sinste[1])
        else:
            CLOSED_SITENUM = max(CLOSED_SITENUM, sinste[0])
            CLOSED_INSTNUM = max(CLOSED_INSTNUM, sinste[1])

    return [CLOSED_SITENUM + 1, CLOSED_INSTNUM + 1, OPEN_INSTNUM + 1]

def load_data_from_list(mylist, time=0):
    #mylist is a two-layer nested structure of names
    #returns the same nested structure but with cells instead
    #set time parameter to decide to load time or not
    data = []
    opendata = []
    for alist in mylist:
        data.append([])
        for name in alist:
            data[-1].append(load_cell(name, time))
    return data
    

def get_list(d):
    #replaces gen_list.py, load_listn, load_list. Use load_data_from_list on this output to get data.
    #returns train_list, test_list, where train_list[i] are the filenames of class i.
    #train_list[cend] are the filenames of the open class, if any. (OPEN_INSTNUM = 0 explicitly defines no open class)
    #get cstart, cend, ostart, oend. two ways to do so: with or without an explicit start.

    if "TRAIN_CINSTNUM" in d.keys():
        return get_list_with_sizes(d) #divert to other function
    
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

    reqs = ["CLOSED_INSTNUM", "DATA_LOC", "FOLD_MODE", "FOLD_NUM", "DATA_TYPE"]
    for req in reqs:
        if not req in d.keys():
            raise Exception("{} not found in options.".format(req))

    iend = d["CLOSED_INSTNUM"]

    #default 10-fold. (Not much reason to change this.)

    if ("FOLD_TOTAL" in d):
        foldtotal = d["FOLD_TOTAL"]
    else:
        foldtotal = 10

    train_list = []
    test_list = []
    for i in range(cend):
        train_list.append([])
        test_list.append([])
    if oend != 0:
        train_list.append([])
        test_list.append([])

    #different modes
    #MODE 2: trainlist = testlist, according to parameters
    #MODE 3: standard X-fold. trainlist != testlist: testlist is fold ~X, trainlist is fold X (len(testlist) << len(trainlist))
    #MODE 4: trainlist != testlist: testlist is fold X, trainlist is fold X+1 (len(trainlist) == len(testlist))
        #for final set, testlist is fold X+1, trainlist is fold X

    if (d["FOLD_MODE"] == 2):
        for s in range(cstart, cend):
            for i in range(0, iend):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                train_list[s].append(sname)
                test_list[s].append(sname)
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            train_list[-1].append(sname)
            test_list[-1].append(sname)

    if (d["FOLD_MODE"] == 3):
        for s in range(cstart, cend):
            for i in range(0, iend):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * d["FOLD_NUM"] and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (d["FOLD_NUM"]+1)):
                    test_list[s].append(sname)
                else:
                    train_list[s].append(sname)
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * d["FOLD_NUM"] + ostart and
                s < (oend-ostart)/foldtotal * (d["FOLD_NUM"]+1) + ostart):
                test_list[-1].append(sname)
            else:
                train_list[-1].append(sname)

    if (d["FOLD_MODE"] == 4):
        for s in range(cstart, cend):
            for i in range(0, iend):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * d["FOLD_NUM"] and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (d["FOLD_NUM"]+1)):
                    test_list[s].append(sname)
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * d["FOLD_NUM"] + ostart and
                s < (oend-ostart)/foldtotal * (d["FOLD_NUM"]+1) + ostart):
                test_list[-1].append(sname)
        trainfoldnum = d["FOLD_NUM"] + 1
        if trainfoldnum >= foldtotal:
            trainfoldnum = d["FOLD_NUM"] - 1
        for s in range(cstart, cend):
            for i in range(0, d["CLOSED_INSTNUM"]):
                sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
                if (i >= d["CLOSED_INSTNUM"]/foldtotal * trainfoldnum and
                    i < d["CLOSED_INSTNUM"]/foldtotal * (trainfoldnum+1)):
                    train_list[s].append(sname)
        for s in range(ostart, oend):
            sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
            if (s >= (oend-ostart)/foldtotal * trainfoldnum + ostart and
                s < (oend-ostart)/foldtotal * (trainfoldnum+1) + ostart):
                train_list[-1].append(sname)

    return train_list, test_list

def flog(msg, fname, logtime=0):
    f = open(fname, "a")
    if logtime == 0:
        f.write(str(msg) + "\n")
    if logtime == 1:
        f.write(repr(time.time()) + "\t" + str(msg) + "\n")
    f.close()

    
def get_list_with_sizes(d):
    #instead of using fold mode, this uses specific sizes to return train_list and test_list:
    #TRAIN_CINST_NUM (TRCN), TRAIN_OINST_NUM (TRON), TEST_CINST_NUM (TECN), TEST_OINST_NUM (TEON),
    #START_CINST_NUM (STCN), START_OINST_NUM (STON)
    #the test_inst always follow the train_inst if RE = 1 or otherwise if RE = -1
    #(So this currently cannot be used to implement 10-fold testing.)

    #e.g. if the above are 20, 2000, 30, 3000, 50, 0, then instances 50-70 are training and 70-100 are testing

    TRCN = d["TRAIN_CINSTNUM"]
    TRON = d["TRAIN_OINSTNUM"]
    TECN = d["TEST_CINSTNUM"]
    TEON = d["TEST_OINSTNUM"]
    STCN = d["START_CINSTNUM"]
    STON = d["START_OINSTNUM"]
    SN = d["CLOSED_SITENUM"]
    CN = d["CLOSED_INSTNUM"]
    ON = d["OPEN_INSTNUM"]
    RE = d["TRAIN_FIRST"]

    if RE == -1:
        #we are going to pretend the train list is the test list
        #for this to work, we need to reverse train/test numbers now
        TECN = d["TRAIN_CINSTNUM"]
        TEON = d["TRAIN_OINSTNUM"]
        TRCN = d["TEST_CINSTNUM"]
        TRON = d["TEST_OINSTNUM"]

    assert(TRCN + TECN + STCN <= CN)
    assert(TRON + TEON + STON <= ON)

    train_list = []
    test_list = []
    for i in range(SN):
        train_list.append([])
        test_list.append([])
    if ON != 0:
        train_list.append([])
        test_list.append([])

    for s in range(SN):
        for i in range(CN):
            sname = d["DATA_LOC"] + str(s) + "-" + str(i) + "." + d["DATA_TYPE"]
            if i >= STCN and i < STCN + TRCN:
                train_list[s].append(sname)
            elif i >= STCN + TRCN and i < STCN + TRCN + TECN:
                test_list[s].append(sname)
    for s in range(ON):
        sname = d["DATA_LOC"] + str(s) + "." + d["DATA_TYPE"]
        if s >= STON and s < STON + TRON:
            train_list[-1].append(sname)
        elif s >= STON + TRON and s < STON + TRON + TEON:
            test_list[-1].append(sname)

    if RE == 1:
        return train_list, test_list
    else:
        return test_list, train_list
