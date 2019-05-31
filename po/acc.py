import math
from loaders import str_to_sinste

def get_acc(gclasses, trueclasses):
    if len(gclasses) != len(trueclasses):
        print "error: len(gclasses) != len(trueclasses)"
        sys.exit(0)
    tp = 0
    fp = 0
    wp = 0
    p = 0
    n = 0
    for i in range(0, len(gclasses)):
        if (gclasses[i] != -1):
            #if we guess a postiive class...
            if (gclasses[i] == trueclasses[i]):
                #guess is right
                tp += 1
            elif (trueclasses[i] != -1):
                #guess is wrong, and true class is a positive
                wp += 1
            else:
                #guess is wrong, and true class is a negative
                fp += 1
            
    for i in range(0, len(trueclasses)):
        if (trueclasses[i] == -1):
            n += 1
        else:
            p += 1
    return [tp, wp, fp, p, n]

def confnames_to_acc(conf, names):
    if len(conf) != len(names):
        "conf and names need same length", len(conf), len(names)
        sys.exit(-1)
    #check if there actually is an open class by looking through names
    IS_OPEN = 0
    for name in names:
        if str_to_sinste(name)[0] == -1:
            IS_OPEN = 1
            break
    gclasses = []
    tclasses = []
    for i in range(0, len(conf)):
        tclasses.append(str_to_sinste(names[i])[0])
        gclass = conf[i].index(max(conf[i]))
        if IS_OPEN == 1 and gclass == len(conf[i]) - 1:
            gclass = -1
        gclasses.append(gclass)
    return get_acc(gclasses, tclasses)

def get_conf(x, n):
    return math.sqrt(x * (1-x)/float(n)) * 1.96

def acc_to_pr(acc, r):
    [tp, wp, fp, p, n] = acc
    tpr = tp/float(p)
    wpr = wp/float(p)
    fpr = fp/float(n)

    if (tpr + wpr + fpr == 0):
        return [0, 0]
    pr = tpr/(tpr+wpr+r*fpr)

    confs = [get_conf(tpr, p), get_conf(wpr, p), get_conf(fpr, n)]
    sumconf = math.sqrt(math.pow(confs[0], 2) +
                        math.pow(confs[1], 2) +
                        math.pow(r * confs[2], 2))
    myconf = (tpr + confs[0]) / (tpr + wpr + r * fpr - sumconf) - pr

    return [pr, myconf]

def wilson_max(p, n):
    z = 1.96
    val = p + z*z/(2*n) + z * math.sqrt(p * (1-p) / n + z*z/(4 * n * n))
    val /= (1 + z * z / n)
    return val

def acc_to_pr2(acc, r):
    [tp, wp, fp, p, n] = acc
    tpr = tp/float(p)
    wpr = wp/float(p)
    fpr = fp/float(n)

    if (tpr + wpr + fpr == 0):
        return 0
    pr = tpr/(tpr+wpr+r*fpr)

    confs = [get_conf(tpr, p), get_conf(wpr, p)]

    prmin = (tpr - confs[0]) / (tpr + confs[0] + wpr + confs[1] + r * wilson_max(fpr, n))
    return prmin
