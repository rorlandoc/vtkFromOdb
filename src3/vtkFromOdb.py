import os,sys,shutil,subprocess, glob
from datetime import datetime
from time import perf_counter
from vtkTools import log, readArray, formatElapsedTime
from vtkGridBuilder import buildUnstructuredGrid

#---
def cleanUp(odbName):
    fileList = glob.glob(os.path.dirname(os.path.abspath(__file__)) + '/' + odbName + '_*.odb')
    for file in fileList:
        os.remove(file)
#---

#---
def getOdbData(odbName):
    tStart = perf_counter()
    if not odbName.endswith('.odb'):
        odbName = odbName + '.odb'
    log(1, "vtkFromOdb", "Started process to extract data from odb.")
    log(1, "vtkFromOdb", "  filename: {0}".format(odbName))

    errf = open("_errChecker","w+")
    errf.close()

    cmd = "abaqus cae noGui=odbExtractor.py -- {0}".format(odbName)
    log(1, "vtkFromOdb", "Running odbExtractor.py")
    log(1, "vtkFromOdb", "   {0}".format(cmd), 0, 1)
    process = subprocess.run(cmd.split(), shell=True)

    if os.path.isfile("_errChecker"):
        log(1, "vtkFromOdb | ERROR", "odbExtractor.py script failed")
        os.remove("_errChecker")
        cleanUp(odbName)
        exit(-1)

    tElapsed = perf_counter() - tStart
    log(1, "vtkFromOdb", "Process completed in {0}".format(formatElapsedTime(tElapsed)))
#---

#---
def createUnstructuredGrid(odbName):
    tStart = perf_counter()
    if odbName.endswith('.odb'):
        odbName = odbName[:-4]
    log(1, "vtkFromOdb", "Started process to create vtkUnstructuredGrid.")
    log(1, "vtkFromOdb", "  data from: {0}".format(odbName))

    buildUnstructuredGrid(odbName)

    tElapsed = perf_counter() - tStart
    log(1, "vtkFromOdb", "Process completed in {0}".format(formatElapsedTime(tElapsed)))
#---

#---
if __name__=="__main__":
    odbName = sys.argv[1]
    log(0, "vtkFromOdb", "Started script on: {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), 1)

    if not odbName.endswith('.odb'):
        odbName = odbName + '.odb'
    if os.path.exists(odbName):

        log(0, "vtkFromOdb", "Creating relevant directories")
        # try:
        #     os.makedirs(odbName[:-4] + "/fields")
        #     os.makedirs(odbName[:-4] + "/meshes")
        #     os.makedirs(odbName[:-4] + "/vtk")
        # except:
        #     dirId = 1
        #     while os.path.exists("{0}_{1}".format(odbName[:-4], dirId)):
        #         dirId = dirId + 1
        #         if dirId > 100:
        #             log(0, "vtkFromOdb | ERROR", "Too many attempts to move output directory", 2, 2)
        #             exit(-1)
        #     log(0, "vtkFromOdb", "Moving existing output directory to {0}_{1}".format(odbName[:-4], dirId))
        #     shutil.move(odbName[:-4], "{0}_{1}".format(odbName[:-4], dirId))
        #     os.makedirs(odbName[:-4] + "/fields")
        #     os.makedirs(odbName[:-4] + "/meshes")
        #     os.makedirs(odbName[:-4] + "/vtk")

        getOdbData(odbName)
        createUnstructuredGrid(odbName)
    else:
        log(0, "vtkFromOdb | ERROR", "File not found: {0}".format(odbName), 2, 2)

    log(0, "vtkFromOdb", "Ended script on: {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), 1, 1)