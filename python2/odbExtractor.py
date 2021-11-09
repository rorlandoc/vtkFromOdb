import os
import sys
import shutil
from abaqus import *
from odbAccess import openOdb
from odbMeshExtractor import extractMeshData
from odbFieldExtractor import extractFieldData
from odbTools import log, json_load_byteified, ArgumentParser, redirectStdOut, Timer
from datetime import datetime
import pdb

#---
def init(odbName):
    log(0, "odbExtractor", "Opening odb: {0}".format(odbName))
    return openOdb(odbName)
#---

#---
def getFramesFromIds(odb, frameIdList):
    log(0, "odbExtractor", "Collecting frames")
    # change from step number to 0-based index
    ids = [[x[0]-1, x[1]] for x in frameIdList]
    steps = odb.steps.values()
    frames = [steps[x[0]].frames[x[1]] for x in ids]
    return frames
#---

#---
def copyOriginalOdb(odbName):
    copyIndex = 0
    newOdbName = "{0}_{1}.odb".format(odbName[:-4],copyIndex)
    while os.path.exists(newOdbName):
        copyIndex += 1
        newOdbName = "{0}_{1}.odb".format(odbName[:-4],copyIndex)
        if copyIndex > 5:
            log(1, "odbExtractor | ERROR", "Too many attempts to copy original odb", 2, 2)
            exit(-1)
    log(1, "odbExtractor", "Copying file to: {0}".format(newOdbName))
    shutil.copy(odbName, newOdbName)
    return newOdbName
#---

#---
def extractData(odb, frameList, fieldVar, duplicate):
    log(0, "odbExtractor", "Started process to extract data from odb")
    extractFieldData(odb, frameList, fieldVar, duplicate)
    extractMeshData(odb, duplicate)
#---    

#---
def parseInput():
    ap = ArgumentParser(usage="abaqus cae noGui=odbExtractor.py -- [-h] -o odbName.odb -r request.json [-f {all, disp}] [-d {true, false}]",
                        description="Script to extract field information from an Abaqus odb file and convert into VTK datasets")

    ap.add_argument("-o", "--odb", required=True, type=str, default=None,
        help="Filename of the ODB from which to extract info.")
    ap.add_argument("-r", "--request", required=True, type=str, default=None,
        help="Filename of the JSON file containing the frames to be extracted.")
    ap.add_argument("-f", "--fields",  required=False, type=str, default=None, choices=['all', 'disp'],
        help="ALL for all suported fields; DISP for displacement only. (default = all)")
    ap.add_argument("-d", "--duplicate", required=False, type=str, default=True, choices=['true', 'false'],
        help="Select whether to copy the odb before extraction, leaving the original intact. (default = True)")

    with redirectStdOut(sys.__stdout__):
        args = ap.parse_known_args()[0]
    if args.duplicate:
        if args.duplicate == "true":
            duplicate = True
        else:
            duplicate = False
    if args.fields:
        return args.odb, args.request, args.fields, duplicate
    else:
        return args.odb, args.request, 'all', duplicate
#---

#---
if __name__ == "__main__":
    overallTimer = Timer()
    overallTimer.reset()
    overallTimer.restart()
    log(0, "odbExtractor", "Started script on: {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), 1, 1)

    odbName, outputRequestName, fieldsVar, duplicate = parseInput()

    log(0, "odbExtractor | OPTIONS", "ODB file:            {0}".format(odbName))
    log(0, "odbExtractor | OPTIONS", "Output request file: {0}".format(outputRequestName))
    log(0, "odbExtractor | OPTIONS", "Fields selection:    {0}".format(fieldsVar))
    log(0, "odbExtractor | OPTIONS", "Duplicate ODB:       {0}".format(duplicate))

    errf = open("_errChecker","w+")
    errf.close()

    if not odbName.endswith('.odb'):
        odbName = odbName + '.odb'

    try:
        os.makedirs(odbName[:-4] + "/fields")
        os.makedirs(odbName[:-4] + "/meshes")
        os.makedirs(odbName[:-4] + "/vtk")
    except:
        dirId = 1
        while os.path.exists("{0}_{1}".format(odbName[:-4], dirId)):
            dirId = dirId + 1
            if dirId > 100:
                log(0, "odbExtractor | ERROR", "Too many attempts to move output directory", 2, 2)
                exit(-1)
        log(0, "odbExtractor", "Moving existing output directory to {0}_{1}".format(odbName[:-4], dirId))
        shutil.move(odbName[:-4], "{0}_{1}".format(odbName[:-4], dirId))
        os.makedirs(odbName[:-4] + "/fields")
        os.makedirs(odbName[:-4] + "/meshes")
        os.makedirs(odbName[:-4] + "/vtk")
    
    extracting = False
    if not os.path.isfile(outputRequestName):
        log(0, "odbExtractor | ERROR", "JSON output request not found")
    else:
        with open(outputRequestName, "r") as f:
            data = json_load_byteified(f)
        frameIdList = data['frameIdList']
        extracting = True

    if extracting:
        if duplicate:
            odbName = copyOriginalOdb(odbName)
        odb = init(odbName)
        frameIdList = [[x[0]-1, x[1]] for x in frameIdList]
        extractData(odb, frameIdList, fieldsVar, duplicate)
        odb.close()
        if duplicate:
            os.remove(odbName)
        if os.path.isfile("_errChecker"):
            os.remove("_errChecker")
        os.system("pvpython vtkFromOdb.py {0}".format(odbName))
        os.system("pvpython vtkTimeSeriesBuilder.py {0}".format(odbName))

    overallTimer.stop()
    log(0, "odbExtractor", "Ended script on: {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), 1, 1)
    log(0, "odbExtractor", "Total execution time: {0}".format(overallTimer), 0, 1)
    
    