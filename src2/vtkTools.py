import sys, time, csv

#---
def formatElapsedTime(dt):
    s = dt
    days    = s // (24*3600); s %= (24*3600)
    hours   = s // 3600;      s %= 3600
    minutes = s // 60;        s %= 60
    if dt > 3600*24:
        return '{0:2g} days {0:2g} h {1:2g} min {2:.2f} s'.format(days, hours, minutes, s)
    if dt > 3600:
        return '{0:2g} h {1:2g} min {2:.2f} s'.format(hours, minutes, s)
    elif dt>60:
        return '{0:2g} min {1:.2f} s'.format(minutes, s)
    elif dt>1:
        return '{0:.2f} s'.format(s)
    elif dt<0.001:
        return '{0:.2f} us'.format(1000000.0*s)
    else:
        return '{0:.2f} ms'.format(1000.0*s)
#---

#---
class Timer(object):
    def __init__(self):
        self.t0 = self.t1   = time.time()
        self.totalIntervals = 0.0
    def __repr__(self):
        return formatElapsedTime(self.totalIntervals)
    def restart(self):
        self.t1 = time.time()
    def reset(self):
        self.t0 = self.t1 = time.time()
        self.totalIntervals = 0.0
    def stop(self):
        dt = time.time()-self.t1
        self.totalIntervals += dt
        return dt
    @property
    def elapsed(self):
        return formatElapsedTime(self.stop())
    @property
    def total(self):
        return formatElapsedTime(time.time()-self.t0)
#---

#---
def log(level, title, msg, padBefore=0, padAfter=0):
    levelStr = "> "*(level + 1)
    padBeforeStr = "\n"*padBefore
    padAfterStr = "\n"*padAfter
    stringVal = "{0}({1}){2}{3}{4}".format(padBeforeStr, title, levelStr, msg, padAfterStr)
    print >> sys.__stdout__, stringVal
#---

#---
def logList(name, list):
    levelStr = " "*6
    print >> sys.__stdout__, ""
    print >> sys.__stdout__, levelStr + ">> " + name + ':'
    for val in list:
        print >> sys.__stdout__, levelStr + val
    print >> sys.__stdout__, ""
#---

#---
def readArray(filename, type):
    if not filename.endswith('.csv'):
        filename = filename + '.csv'
    data = []
    with open(filename) as csvf:
        contents = csv.reader(csvf, delimiter=',', dialect='excel')
        for row in contents:
            for ind, item in enumerate(row):
                if item.strip() == '.':
                    row[ind] = '0.0'
            row = list(map(type, row))
            if len(row) > 1:
                data.append(row)
            else:
                data.append(row[0])
    return data
