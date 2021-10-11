CLOSED_SITENUM = 100
CLOSED_INSTNUM = 200
OPEN_INSTNUM = 800


def sinste_to_site_inst(sinste):
    if sinste >= CLOSED_SITENUM * CLOSED_INSTNUM:
        site = -1
        inst = sinste - CLOSED_SITENUM * CLOSED_INSTNUM
    else:
        site = sinste / CLOSED_INSTNUM
        inst = sinste % CLOSED_INSTNUM
    return site, inst


print("Generating dist/counts matrices...")
dists = []
counts = []
totalcount = 0
# length of all the above arrays = number of elements in data set

# dists[i][j] is the dist between element i and CLASS j
# counts[i][j] is how many distances of that class we found
# everything is double counted, but the counts will take care of that
for i in range(100000):
    dists.append([0] * 101)
    counts.append([0] * 101)

insite_counts = [0] * 101
insite_dists = [0] * 101

aname = "Ca-OSAD.py"

##print "Loading closed distance file..."
##with open("../attacks/output/dist-{}.predist".format(aname), "r") as f:
##    for line in f:
##        li = line.split(";")
##        sinste1 = int(li[0])
##        site1, inst1 = sinste_to_site_inst(sinste1)
##        sinste2 = int(li[1])
##        site2, inst2 = sinste_to_site_inst(sinste2)
##        dist = float(li[2])
##        dists[sinste1][site2] += dist
##        counts[sinste1][site2] += 1
##        dists[sinste2][site1] += dist
##        counts[sinste2][site1] += 1
##        totalcount += 1
##        if totalcount % 100000 == 0:
##            print "Read lines:", totalcount
##        if site1 == site2:
##            insite_dists[site1] += dist
##            insite_counts[site1] += 1

print("Loading closed distance file...")
with open("../attacks/output/dist-{}.predist".format(aname), "r") as f:
    for line in f:
        li = line.split(";")
        [site1, inst1, site2, inst2] = [int(l) for l in li[:4]]
        sinste1 = site1 * CLOSED_INSTNUM + inst1
        sinste2 = site2 * CLOSED_INSTNUM + inst2
        dist = float(li[5])
        dists[sinste1][site2] += dist
        counts[sinste1][site2] += 1
        dists[sinste2][site1] += dist
        counts[sinste2][site1] += 1
        totalcount += 1
        if totalcount % 100000 == 0:
            print("Read lines:", totalcount)
            print(insite_counts)
        if site1 == site2:
            insite_dists[site1] += dist
            insite_counts[site1] += 1

print("Loading open distance file...")
with open("../attacks/output/dist-{}-open.predist".format(aname), "r") as f:
    for line in f:
        li = line.split(";")
        sinste1 = int(li[0])
        site1, inst1 = sinste_to_site_inst(sinste1)
        sinste2 = int(li[1])
        site2, inst2 = sinste_to_site_inst(sinste2)
        dist = float(li[2])
        dists[sinste1][site2] += dist
        counts[sinste1][site2] += 1
        dists[sinste2][site1] += dist
        counts[sinste2][site1] += 1
        totalcount += 1
        if totalcount % 100000 == 0:
            print("Read lines:", totalcount)
        if site1 == site2:
            insite_dists[site1] += dist
            insite_counts[site1] += 1

print("Writing...")
fout = open("../attacks/output/dist-{}.dist".format(aname), "w")
fout.write("INSITE")
for i in range(101):
    fout.write("\t" + str(insite_dists[i] / float(insite_counts[i])))
fout.write("\n")
for i in range(100000):
    fout.write(str(i))
    for j in range(101):
        fout.write("\t" + str(dists[i][j] / counts[i][j]))
    fout.write("\n")
fout.close()
