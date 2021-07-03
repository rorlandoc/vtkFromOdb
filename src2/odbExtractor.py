import os,sys,json,shutil
from numpy import true_divide
from abaqus import *
from odbAccess import openOdb
from odbMeshExtractor import extractMeshData
from odbFieldExtractor import extractFieldData
from odbTools import log, logList, json_load_byteified, writeList, getOriginalOdbName

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
def getAllFields(odb, frameList):
    log(0, "odbExtractor", "Collecting fields")
    fieldList = []
    for frame in frameList:
        fields = frame.fieldOutputs.values()
        for field in fields:
            if not field.name in fieldList:
                fieldList.append(field.name)
    return fieldList
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
def extractData(odb, frameList, fieldList):
    log(0, "odbExtractor", "Started process to extract data from odb")
    extractMeshData(odb)
    extractFieldData(odb, frameList, fieldList)
#---    

#---
if __name__ == "__main__":
    odbName = sys.argv[-1]

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
    if not os.path.isfile("outputRequest.json"):
        log(0, "odbExtractor | ERROR", "JSON output request not found")
    else:
        log(0, "odbExtractor", "Reading output request from outputRequest.json")
        with open("outputRequest.json", "r") as f:
            data = json_load_byteified(f)
        frameIdList = data['frameIdList']
        extracting = True

    
    if extracting:
        newOdbName = copyOriginalOdb(odbName)
        odb = init(newOdbName)
        frameList = getFramesFromIds(odb, frameIdList)
        fieldList = getAllFields(odb, frameList)
        extractData(odb, frameList, fieldList)
        odb.close()
        #os.remove(newOdbName)
        if os.path.isfile("_errChecker"):
            os.remove("_errChecker")
    
    