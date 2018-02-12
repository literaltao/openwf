from CaOSAD import *
from acc import *


d = {}
conf = []
names = []

acc = [0, 0, 0, 0, 0]

if os.path.exists("output/CaOSAD.py.results"):
    os.remove("output/CaOSAD.py.results")

for i in range(0, 10):
    
    d["OUTPUT_LOC"] = "output/"
    d["LEV_METHOD"] = 1
    d["FOLD_NUM"] = i
    d["CLOSED_SITENUM"] = 100
    d["CLOSED_INSTNUM"] = 10
    d["OPEN_INSTNUM"] = 1000

    [conf, names] = CaOSAD(d)
    this_acc = confnames_to_acc(conf, names)
    for i in range(0, len(this_acc)):
        acc[i] += this_acc[i]

    f = open("output/CaOSAD.py.results", "a")
    print len(conf), len(names)
    for k in range(0, len(conf)): #replaces the standard rlog function
        string = "0\t"
        string += names[k] + "\t"
        for j in range(0, len(conf[k])):
            string += str(conf[k][j]) + "\t"
        string = string[:-1] + "\n"
        f.write(string)
    f.close()
    

print acc_to_pr(acc, 10)
print acc_to_pr(acc, 1000)
