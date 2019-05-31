import csv
import sys
import math
from sys import stdout
import numpy as np
#import matplotlib.pylab as plt
import operator
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import cross_val_score
from sklearn import metrics
from sklearn import tree
import sklearn.metrics as skm
import scipy
import dill
import random
import os
from collections import defaultdict
import argparse
from itertools import chain
from loaders import *
import subprocess
#from tqdm import *

# re-seed the generator
#np.random.seed(1234)

#1. dictionary_() will extract features and write them to a target file (kFPdict) in the data folder
#2. calls RF_openworld(), which starts by dividing kFPdict into training and testing sets
#3. # -1 is IN, 1 is OUT
#file format: "direction time size"

"""Feeder functions"""

def neighborhood(iterable):
    iterator = iter(iterable)
    prev = (0)
    item = iterator.next()  # throws StopIteration if empty.
    for next in iterator:
        yield (prev,item,next)
        prev = item
        item = next
    yield (prev,item,None)

def chunkIt(seq, num):
  avg = len(seq) / float(num)
  out = []
  last = 0.0
  while last < len(seq):
    out.append(seq[int(last):int(last + avg)])
    last += avg
  return out

"""Non-feeder functions"""

def get_pkt_list(trace_data):
    first_line = trace_data[0]
    first_line = first_line.split("\t")

    first_time = float(first_line[0])
    dta = []
    for line in trace_data:
        a = line
        b = a.split("\t")

        if float(b[1]) > 0:
            #dta.append(((float(b[0])- first_time), abs(int(b[2])), 1))
            dta.append(((float(b[0])- first_time), 1))
        else:
            #dta.append(((float(b[1]) - first_time), abs(int(b[2])), -1))
            dta.append(((float(b[0]) - first_time), -1))
    return dta


def In_Out(list_data):
    In = []
    Out = []
    for p in list_data:
        if p[1] == -1:
            In.append(p)
        if p[1] == 1:
            Out.append(p)
    return In, Out

############### TIME FEATURES #####################

def inter_pkt_time(list_data):
    times = [x[0] for x in list_data]
    temp = []
    for elem,next_elem in zip(times, times[1:]+[times[0]]):
        temp.append(next_elem-elem)
    return temp[:-1]

def interarrival_times(list_data):
    In, Out = In_Out(list_data)
    IN = inter_pkt_time(In)
    OUT = inter_pkt_time(Out)
    TOTAL = inter_pkt_time(list_data)
    return IN, OUT, TOTAL

def interarrival_maxminmeansd_stats(list_data):
    interstats = []
    In, Out, Total = interarrival_times(list_data)
    if In and Out:
        avg_in = sum(In)/float(len(In))
        avg_out = sum(Out)/float(len(Out))
        avg_total = sum(Total)/float(len(Total))
        interstats.append((max(In), max(Out), max(Total), avg_in, avg_out, avg_total, np.std(In), np.std(Out), np.std(Total), np.percentile(In, 75), np.percentile(Out, 75), np.percentile(Total, 75)))
    elif Out and not In:
        avg_out = sum(Out)/float(len(Out))
        avg_total = sum(Total)/float(len(Total))
        interstats.append((0, max(Out), max(Total), 0, avg_out, avg_total, 0, np.std(Out), np.std(Total), 0, np.percentile(Out, 75), np.percentile(Total, 75)))
    elif In and not Out:
        avg_in = sum(In)/float(len(In))
        avg_total = sum(Total)/float(len(Total))
        interstats.append((max(In), 0, max(Total), avg_in, 0, avg_total, np.std(In), 0, np.std(Total), np.percentile(In, 75), 0, np.percentile(Total, 75)))
    else:
        interstats.extend(([0]*15))
    return interstats

def time_percentile_stats(trace_data):
    Total = get_pkt_list(trace_data)
    In, Out = In_Out(Total)
    In1 = [x[0] for x in In]
    Out1 = [x[0] for x in Out]
    Total1 = [x[0] for x in Total]
    STATS = []
    if In1:
        STATS.append(np.percentile(In1, 25)) # return 25th percentile
        STATS.append(np.percentile(In1, 50))
        STATS.append(np.percentile(In1, 75))
        STATS.append(np.percentile(In1, 100))
    if not In1:
        STATS.extend(([0]*4))
    if Out1:
        STATS.append(np.percentile(Out1, 25)) # return 25th percentile
        STATS.append(np.percentile(Out1, 50))
        STATS.append(np.percentile(Out1, 75))
        STATS.append(np.percentile(Out1, 100))
    if not Out1:
        STATS.extend(([0]*4))
    if Total1:
        STATS.append(np.percentile(Total1, 25)) # return 25th percentile
        STATS.append(np.percentile(Total1, 50))
        STATS.append(np.percentile(Total1, 75))
        STATS.append(np.percentile(Total1, 100))
    if not Total1:
        STATS.extend(([0]*4))
    return STATS

def number_pkt_stats(trace_data):
    Total = get_pkt_list(trace_data)
    In, Out = In_Out(Total)
    return len(In), len(Out), len(Total)

def first_and_last_30_pkts_stats(trace_data):
    Total = get_pkt_list(trace_data)
    first30 = Total[:30]
    last30 = Total[-30:]
    first30in = []
    first30out = []
    for p in first30:
        if p[1] == -1:
            first30in.append(p)
        if p[1] == 1:
            first30out.append(p)
    last30in = []
    last30out = []
    for p in last30:
        if p[1] == -1:
            last30in.append(p)
        if p[1] == 1:
            last30out.append(p)
    stats= []
    stats.append(len(first30in))
    stats.append(len(first30out))
    stats.append(len(last30in))
    stats.append(len(last30out))
    return stats

#concentration of outgoing packets in chunks of 20 packets
def pkt_concentration_stats(trace_data):
    Total = get_pkt_list(trace_data)
    chunks= [Total[x:x+20] for x in xrange(0, len(Total), 20)]
    concentrations = []
    for item in chunks:
        c = 0
        for p in item:
            if p[1] == 1:
                c+=1
        concentrations.append(c)
    return np.std(concentrations), sum(concentrations)/float(len(concentrations)), np.percentile(concentrations, 50), min(concentrations), max(concentrations), concentrations

#Average number packets sent and received per second
def number_per_sec(trace_data):
    Total = get_pkt_list(trace_data)
    last_time = Total[-1][0]
    last_second = math.ceil(last_time)
    temp = []
    l = []
    for i in range(1, int(last_second)+1):
        c = 0
        for p in Total:
            if p[0] <= i:
                c+=1
        temp.append(c)
    for prev,item,next in neighborhood(temp):
        x = item - prev
        l.append(x)
    avg_number_per_sec = sum(l)/float(len(l))
    return avg_number_per_sec, np.std(l), np.percentile(l, 50), min(l), max(l), l

#Variant of packet ordering features from http://cacr.uwaterloo.ca/techreports/2014/cacr2014-05.pdf
def avg_pkt_ordering_stats(trace_data):
    Total = get_pkt_list(trace_data)
    c1 = 0
    c2 = 0
    temp1 = []
    temp2 = []
    for p in Total:
        if p[1] == 1:
            temp1.append(c1)
        c1+=1
        if p[1] == -1:
            temp2.append(c2)
        c2+=1
    avg_in = sum(temp1)/float(len(temp1))
    avg_out = sum(temp2)/float(len(temp2))

    return avg_in, avg_out, np.std(temp1), np.std(temp2)

def perc_inc_out(trace_data):
    Total = get_pkt_list(trace_data)
    In, Out = In_Out(Total)
    percentage_in = len(In)/float(len(Total))
    percentage_out = len(Out)/float(len(Total))
    return percentage_in, percentage_out

############### SIZE FEATURES #####################

#def total_size(list_data):
#    return sum([x[1] for x in list_data])

#def in_out_size(list_data):
#    In, Out = In_Out(list_data)
#    size_in = sum([x[1] for x in In])
#    size_out = sum([x[1] for x in Out])
#    return size_in, size_out

#def average_total_pkt_size(list_data):
#    return np.mean([x[1] for x in list_data])

#def average_in_out_pkt_size(list_data):
#    In, Out = In_Out(list_data)
#    average_size_in = np.mean([x[1] for x in In])
#    average_size_out = np.mean([x[1] for x in Out])
#    return average_size_in, average_size_out

#def variance_total_pkt_size(list_data):
#    return np.var([x[1] for x in list_data])

#def variance_in_out_pkt_size(list_data):
#    In, Out = In_Out(list_data)
#    var_size_in = np.var([x[1] for x in In])
#    var_size_out = np.var([x[1] for x in Out])
#    return var_size_in, var_size_out

#def std_total_pkt_size(list_data):
#    return np.std([x[1] for x in list_data])

#def std_in_out_pkt_size(list_data):
#    In, Out = In_Out(list_data)
#    std_size_in = np.std([x[1] for x in In])
#    std_size_out = np.std([x[1] for x in Out])
#    return std_size_in, std_size_out

#def max_in_out_pkt_size(list_data):
#    In, Out = In_Out(list_data)
#    max_size_in = max([x[1] for x in In])
#    max_size_out = max([x[1] for x in Out])
#    return max_size_in, max_size_out

#def unique_pkt_lengths(list_data):
#    pass

############### FEATURE FUNCTION #####################


#If size information available add them in to function below
def TOTAL_FEATURES(trace_data, max_size=175):
    #this is called below in extract_dill to extract features
    list_data = get_pkt_list(trace_data)
    ALL_FEATURES = []

    # ------TIME--------
    intertimestats = [x for x in interarrival_maxminmeansd_stats(list_data)[0]]
    timestats = time_percentile_stats(trace_data)
    number_pkts = list(number_pkt_stats(trace_data))
    thirtypkts = first_and_last_30_pkts_stats(trace_data)
    stdconc, avgconc, medconc, minconc, maxconc, conc = pkt_concentration_stats(trace_data)
    avg_per_sec, std_per_sec, med_per_sec, min_per_sec, max_per_sec, per_sec = number_per_sec(trace_data)
    avg_order_in, avg_order_out, std_order_in, std_order_out = avg_pkt_ordering_stats(trace_data)
    perc_in, perc_out = perc_inc_out(trace_data)

    altconc = []
    alt_per_sec = []
    altconc = [sum(x) for x in chunkIt(conc, 70)]
    alt_per_sec = [sum(x) for x in chunkIt(per_sec, 20)]
    if len(altconc) == 70:
        altconc.append(0)
    if len(alt_per_sec) == 20:
        alt_per_sec.append(0)

    # ------SIZE--------

    #tot_size = total_size(list_data)
    #in_size, out_size = in_out_size(list_data)
    #avg_total_size = average_total_pkt_size(list_data)
    #avg_size_in, avg_size_out = average_in_out_pkt_size(list_data)
    #var_total_size = variance_total_pkt_size(list_data)
    #var_size_in, var_size_out = variance_in_out_pkt_size(list_data)
    #std_total_size = std_total_pkt_size(list_data)
    #std_size_in, std_size_out = std_in_out_pkt_size(list_data)
    #max_size_in, max_size_out = max_in_out_pkt_size(list_data)

    # TIME Features
    ALL_FEATURES.extend(intertimestats)
    ALL_FEATURES.extend(timestats)
    ALL_FEATURES.extend(number_pkts)
    ALL_FEATURES.extend(thirtypkts)
    ALL_FEATURES.append(stdconc)
    ALL_FEATURES.append(avgconc)
    ALL_FEATURES.append(avg_per_sec)
    ALL_FEATURES.append(std_per_sec)
    ALL_FEATURES.append(avg_order_in)
    ALL_FEATURES.append(avg_order_out)
    ALL_FEATURES.append(std_order_in)
    ALL_FEATURES.append(std_order_out)
    ALL_FEATURES.append(medconc)
    ALL_FEATURES.append(med_per_sec)
    ALL_FEATURES.append(min_per_sec)
    ALL_FEATURES.append(max_per_sec)
    ALL_FEATURES.append(maxconc)
    ALL_FEATURES.append(perc_in)
    ALL_FEATURES.append(perc_out)
    ALL_FEATURES.extend(altconc)
    ALL_FEATURES.extend(alt_per_sec)
    ALL_FEATURES.append(sum(altconc))
    ALL_FEATURES.append(sum(alt_per_sec))
    ALL_FEATURES.append(sum(intertimestats))
    ALL_FEATURES.append(sum(timestats))
    ALL_FEATURES.append(sum(number_pkts))

    #SIZE FEATURES
    #ALL_FEATURES.append(tot_size)
    #ALL_FEATURES.append(in_size)
    #ALL_FEATURES.append(out_size)
    #ALL_FEATURES.append(avg_total_size)
    #ALL_FEATURES.append(avg_size_in)
    #ALL_FEATURES.append(avg_size_out)
    #ALL_FEATURES.append(var_total_size)
    #ALL_FEATURES.append(var_size_in)
    #ALL_FEATURES.append(var_size_out)
    #ALL_FEATURES.append(std_total_size)
    #ALL_FEATURES.append(std_size_in)
    #ALL_FEATURES.append(std_size_out)
    #ALL_FEATURES.append(max_size_in)
    #ALL_FEATURES.append(max_size_out)

    # This is optional, since all other features are of equal size this gives the first n features
    # of this particular feature subset, some may be padded with 0's if too short.

    ALL_FEATURES.extend(conc)

    ALL_FEATURES.extend(per_sec)


    while len(ALL_FEATURES)<max_size:
        ALL_FEATURES.append(0)
    features = ALL_FEATURES[:max_size]

    return tuple(features)

def chunks(l, n):
    """ Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def checkequal(lst):
    return lst[1:] == lst[:-1]


############ Non-Feeder functions ########

def extract_dill(trainnames, testnames, ofname):
    '''Extract Features -- A dictionary containing features for each traffic instance.'''

    data_dict = {'train_feature': [],
                 'train_label': [],
                 'test_feature': [],
                 'test_label': []}

    print "Creating training features...", len(trainnames)

    maxclass = len(trainnames) - 1
    #for kFP, we write the final class not as -1, but as maxclass
    count = 0
    intcount = 0
    for fname in trainnames:
        if ((count * 100)/len(trainnames) > (intcount + 1)):
            print "{}%... {}".format(intcount, fname)
            intcount += 1
        (i, j) = str_to_sinste(fname) #i is the true site, j is the true inst
        if i == -1:
            i = maxclass
        tcp_dump = open(fname).readlines()
        g = []
        g = TOTAL_FEATURES(tcp_dump)
        data_dict['train_feature'].append(g)
        data_dict['train_label'].append((i,j))
        count += 1

    print "Creating testing features...", len(testnames)

    count = 0
    intcount = 0
    for fname in testnames:
        if ((count * 100)/len(testnames) > (intcount + 1)):
            print "{}%... {}".format(intcount, fname)
            intcount += 1
        (i, j) = str_to_sinste(fname) #i is the true site, j is the true inst
        if i == -1:
            i = maxclass
        tcp_dump = open(fname).readlines()
        g = []
        g = TOTAL_FEATURES(tcp_dump)
        data_dict['test_feature'].append(g)
        data_dict['test_label'].append((i, j))
        count += 1

    fileObject = open(ofname + ".dill",'wb')
    dill.dump(data_dict,fileObject)
    fileObject.close()

def RF_openworld(testnames, ofname):
    '''Produces leaf vectors used for classification.'''

    fileObject = open(ofname + ".dill",'r')
    dic = dill.load(fileObject)
    fileObject.close()
    traindata = dic["train_feature"]
    trainsinste = dic["train_label"]
    testdata = dic["test_feature"]
    testsinste = dic["test_label"]

    trainlabel = [sinste[0] for sinste in trainsinste]
    testlabel = [sinste[0] for sinste in testsinste]
    
    print "Training ..."
    model = RandomForestClassifier(n_jobs=-1, n_estimators=1000, oob_score=True)
    model.fit(traindata, trainlabel)

    #read names from relevant test list
    if len(testdata) != len(testnames):
        raise("Unexpected test size: {} != {}".format(len(testdata), len(testnames)))

    #log the match scores
    sout = open(ofname + ".score", "w")
    M = model.predict(testdata, get_predict=1)
    for i in range(0, len(M)):
        x = M[i]
        string = str(testnames[i])
        for xi in x:
            string += "\t" + str(xi)
        sout.write(string + "\n")
    sout.close()
    
    print "RF accuracy (open) = ", model.score(testdata, testlabel)

##    train_leaf = zip(model.apply(traindata), trainlabel)
##    test_leaf = zip(model.apply(testdata), testlabel)
##    return train_leaf, test_leaf
        
try:
    optfname = sys.argv[1]
    d = load_options(optfname)
except Exception,e:
    print sys.argv[0], str(e)
    sys.exit(0)

ofname = "{}{}-{}".format(d["OUTPUT_LOC"], "Ha-kFP", d["CORE_NAME"])
logfname = ofname + ".log"
flog(sys.argv[0] + " " + sys.argv[1], logfname, logtime=1)
flog(repr(d), logfname)

atrainnames, atestnames = get_list(d)
#unpack trainnames, testnames
trainnames = [name for tname in atrainnames for name in tname]
testnames = [name for tname in atestnames for name in tname]

if d["DO_NOT_EXTRACT"] == 0:
    extract_dill(trainnames, testnames, ofname)
RF_openworld(testnames, ofname) #testnames is only used to output score here
