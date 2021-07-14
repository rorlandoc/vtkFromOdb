import sys, time
import json

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
def logProgress(val, lastVal):
    if val == 0:
        lastVal = val
        print >> sys.__stdout__, " "*3 + "Progress [",
        sys.stdout.flush()
    elif val < 100.0:
        diff = val - lastVal
        if diff > 10.0:
            lastVal = val
            print >> sys.__stdout__, "="*5,
            sys.stdout.flush()
    else:
        print >> sys.__stdout__, "="*5 + " ] Done"  
    return lastVal
#---

#---
def writeList(filename, data):
    if not filename.endswith('.csv'):
        filename = filename + '.csv'
    with open(filename, "w+") as f:
        for dataEntry in data:
            str2write = str(dataEntry).replace("[","").replace("]","")
            f.write(str2write)
            f.write("\n")
#---

#---
def writeArray(filename, data):
    if not filename.endswith('.csv'):
        filename = filename + '.csv'
    data = data.tolist()
    with open(filename, "w+") as f:
        for dataEntry in data:
            str2write = str(dataEntry).replace("[","").replace("]","")
            f.write(str2write)
            f.write("\n")
#---

#---
def getOriginalOdbName(odbName):
    if odbName.endswith('.odb'):
        odbName = odbName[:-4]
    return odbName#[:-(odbName[::-1].index("_") + 1)]
#---

#---
# Mirec Miskuf
# https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json/13105359#13105359
def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )
#---

#---
# Mirec Miskuf
# https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json/13105359#13105359
def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )
#---

#---
# Mirec Miskuf
# https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json/13105359#13105359
def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data
#---