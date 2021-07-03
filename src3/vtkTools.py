import csv

#---
def formatElapsedTime(dt):
    if dt > 3600:
        return '{0:2g} h {1:2g} min {2:.2f} s'.format((dt//60)//60, dt//60, dt%60)
    elif dt>60:
        return '{0:2g} min {1:.2f} s'.format(dt//60, dt%60)
    elif dt>1:
        return '{0:.2f} s'.format(dt)
    elif dt<0.001:
        return '{0:.2f} us'.format(1000000.0*dt)
    else:
        return '{0:.2f} ms'.format(1000.0*dt)
#---

#---
def log(level, title, msg, padBefore=0, padAfter=0):
    levelStr = "> "*(level + 1)
    padBeforeStr = "\n"*padBefore
    padAfterStr = "\n"*padAfter
    stringVal = "{0}({1}){2}{3}{4}".format(padBeforeStr, title, levelStr, msg, padAfterStr)
    print(stringVal)
#---

#---
def logList(name, list):
    levelStr = " "*6
    print("")
    print(levelStr + ">> " + name + ':')
    for val in list:
        print(levelStr + val)
    print("")
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
