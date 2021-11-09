from os import read
import sys
import os
import xml.etree.ElementTree as et
import xml.dom.minidom as md
from vtkTools import log, Timer, readArray
import pdb

#---
def getFileNames(path):
    items = os.listdir(path)
    return [x for x in items if os.path.isfile(os.path.join(path, x)) and ".vtk" in x]
#---


#---
def createTimeSeries(odbName, frameValues):
    timer = Timer()
    timer.reset()
    timer.restart()
    log(0, "vtkTimeSeriesBuilder", "Creating time series file")
    pathVtk = "{0}/vtk".format(odbName)
    files = getFileNames(pathVtk)
    numFrames = len(files)

    root = et.Element("VTKFile", {"version":"1.0",
                                    "type":"Collection", 
                                    "byte_order":"LittleEndian", 
                                    "header_type":"UInt32", 
                                    "compressor":"vtkZLibDataCompressor"})
    
    col = et.SubElement(root, "Collection")

    for i in range(numFrames):
        oldTree = et.parse("{0}/{1}_{2}.vtk".format(pathVtk, odbName, i))
        oldRoot = oldTree.getroot()

        for dataSet in oldRoot[0]:
            ds = et.SubElement(col, "DataSet", {"timestep": str(frameValues[i]),
                                                "group": "",
                                                "part": dataSet.attrib['index'],
                                                "file": dataSet.attrib['file']})

    xmlstr = md.parseString(et.tostring(root)).toprettyxml()
    with open("{0}/{1}.pvd".format(pathVtk, odbName), "w+") as f:
        f.write(xmlstr)

    timer.stop()
    log(0, "vtkTimerSeriesBuilder", "Process completed in {0}".format(timer))
#---

#---
if __name__ == "__main__":
    odbName = sys.argv[1]
    if odbName.endswith(".odb"):
        odbName = odbName[:-4]
    if os.path.isfile("{0}/vtk/frameValues.csv".format(odbName)):
        frameValues = readArray("{0}/vtk/frameValues.csv".format(odbName), float)
        createTimeSeries(odbName, frameValues)
    else:
        log(0, "vtkTimeSeriesBuilder | ERROR", "Frame values CSV file missing", 1, 1)
#---