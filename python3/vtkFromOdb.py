import os
import sys
from vtkTools import log, Timer
from vtkGridBuilder import buildUnstructuredGrid

timer = Timer()

#---
def createUnstructuredGrid(odbName):
    timer.reset()
    timer.restart()
    if odbName.endswith('.odb'):
        odbName = odbName[:-4]
    log(1, "vtkFromOdb", "Started process to create vtkUnstructuredGrid.")
    log(1, "vtkFromOdb", "  data from: {0}".format(odbName))

    buildUnstructuredGrid(odbName)

    timer.stop()
    log(1, "vtkFromOdb", "Process completed in {0}".format(timer))
#---

#---
if __name__=="__main__":
    odbName = sys.argv[1]

    if odbName.endswith('.odb'):
        odbName = odbName[:-4]
    if os.path.exists(odbName):
        if os.path.isfile("_errChecker"):
            log(0, "vtkFromOdb | ERROR", "Odb extraction process did not complete successfuly")
        else:
            createUnstructuredGrid(odbName)
    else:
        log(0, "vtkFromOdb | ERROR", "File not found: {0}".format(odbName), 2, 2)