import os
import sys
import vtk
from vtkTools import log, logList, readArray, Timer

timer = Timer()
timerInstance = Timer()

#---
def getInstanceList(odbName):
    log(1, "vtkGridBuilder", "Gathering instances")

    meshPath = "{0}/meshes/".format(odbName)
    files = os.listdir(meshPath)
    instances = [file.replace(".csv","").replace("elementsType","").replace("elements","").replace("nodes","").strip() for file in files]
    instances = list(set(instances)) # get unique
    
    return instances
#---

#---
def getFrameList(odbName):
    log(1, "vtkGridBuilder", "Gathering frame information")

    fieldsPath = "{0}/fields/".format(odbName)
    frames = os.listdir(fieldsPath)

    return frames
#---

#---
def getMeshData(odbName, instances):
    timerInstance.reset()
    timerInstance.restart()
    log(1, "vtkGridBuilder", "Gathering mesh data")

    meshPath = "{0}/meshes/".format(odbName)
    nodes =        {x:readArray(meshPath + x + ' nodes'       , float) for x in instances}
    elements =     {x:readArray(meshPath + x + ' elements'    , int  ) for x in instances}
    elementsType = {x:readArray(meshPath + x + ' elementsType', int  ) for x in instances}

    timerInstance.stop()
    log(1, "vtkGridBuilder", "Process completed in {0}".format(timerInstance))

    return nodes, elements, elementsType
#---

#---
def getFieldData(odbName, instances, frame):
    timerInstance.reset()
    timerInstance.restart()
    log(1, "vtkGridBuilder", "Gathering fields")

    fieldsPath = "{0}/fields/{1}/".format(odbName,frame)
    files = os.listdir(fieldsPath)
    fields = {i:[f.replace(i,"").replace(".csv","").strip() for f in files if i + ' ' in f] for i in instances}


    data = {}
    for instance in fields:
        log(1, "vtkGridBuilder", "Reading {0} fields".format(instance))
        data[instance] = {x:readArray(fieldsPath + instance + ' ' + x, float) for x in fields[instance]}

    timerInstance.stop()
    log(1, "vtkGridBuilder", "Process completed in {0}".format(timerInstance))

    return fields, data
#---

#---
def buildUnstructuredGrid(odbName):
    timer.reset()
    timer.restart()
    log(1, "vtkGridBuilder", "Started process of building vtkUnstructuredGrid")

    instances = getInstanceList(odbName)
    frames = getFrameList(odbName)
    nodes, elements, elementsType = getMeshData(odbName, instances)

    for i, frame in enumerate(frames):
        log(1, "vtkGridBuilder", "Processing frame {0}/{1}".format(i+1, len(frames)))
        fields, data = getFieldData(odbName, instances, frame)
        
        grid = []
        for ip, instance in enumerate(instances):
            log(1, "vtkGridBuilder", "Processing instance {0}".format(instance))

            log(1, "vtkGridBuilder", "Creating vtkPoint array")
            points = vtk.vtkPoints()
            for node in nodes[instance]:
                points.InsertNextPoint(node[0], node[1], node[2])

            log(1, "vtkGridBuilder", "Creating vtkCell array")
            cells = vtk.vtkCellArray()
            for i, element in enumerate(elements[instance]):
                if elementsType[instance][i] == 9: # quad
                    currentCell = vtk.vtkQuad()
                elif elementsType[instance][i] == 12: # hex
                    currentCell = vtk.vtkHexahedron()
                elif elementsType[instance][i] == 13: # wedge
                    currentCell = vtk.vtkWedge()

                for ipoint in range(currentCell.GetNumberOfPoints()):
                    currentCell.GetPointIds().SetId(ipoint, element[ipoint])
                cells.InsertNextCell(currentCell)

            log(1, "vtkGridBuilder", "Creating vtkUnstructuredGrid")
            grid.append(vtk.vtkUnstructuredGrid())
            grid[ip].SetPoints(points)
            grid[ip].SetCells(elementsType[instance], cells)

            for field in fields[instance]:
                log(1, "vtkGridBuilder", "Processing field {0}".format(field))
                fieldData = data[instance][field]
                try:
                    numComponents = len(fieldData[0])
                except:
                    numComponents = 1
                if numComponents == 1:
                    log(1, "vtkGridBuilder", "Creating array")
                    array = vtk.vtkFloatArray()
                    array.SetNumberOfComponents(1)
                    array.SetName(field)
                    for ival, val in enumerate(fieldData):
                        array.InsertTuple1(ival, val)
                    grid[ip].GetPointData().AddArray(array)
                elif numComponents == 3:
                    log(1, "vtkGridBuilder", "Creating vector")
                    array = vtk.vtkFloatArray()
                    array.SetNumberOfComponents(3)
                    array.SetName(field)
                    for ival, val in enumerate(fieldData):
                        array.InsertTuple3(ival, val[0], val[1], val[2])
                    grid[ip].GetPointData().SetVectors(array)
                else:
                    log(1, "vtkGridBuilder | ERROR", "Field {0} {1} has unsupported number of components ({2})".format(field, instance, numComponents))
            
            # log(1, "vtkGridBuilder", "Writing {0}.vtu file".format(instance))
            # writer = vtk.vtkXMLUnstructuredGridWriter()
            # vtkPath = "{0}/vtk/{1}/".format(odbName, frame)
            # writer.SetFileName(vtkPath + instance + '.vtu')
            # writer.SetInputData(grid[ip])
            # writer.Write()
        
        mb = vtk.vtkMultiBlockDataSet()
        for ig, g in enumerate(grid):
            mb.SetBlock(ig, g)
        writer = vtk.vtkXMLMultiBlockDataWriter()
        writer.SetFileName("{0}/vtk/{1}_{2}.vtk".format(odbName, odbName, frame.replace("frame","")))
        writer.SetInputData(mb)
        writer.Write()

    timer.stop()
    log(1, "vtkGridBuilder", "Process completed in {0}".format(timer))
#---

#---
if __name__ == "__main__":
    odbName = sys.argv[-1]
    if odbName.endswith(".odb"):
        odbName = odbName[:-4]
    buildUnstructuredGrid(odbName)
