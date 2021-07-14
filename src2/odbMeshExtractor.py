import os, sys
from abaqus import *
from abaqusConstants import *
from odbTools import Timer, log, writeList, getOriginalOdbName

timer = Timer()
timerInstance = Timer()

vtkElemType = {'S4R' :  9,   # quad
               'SC8R': 12,   # hex
               'SC6R': 13 }  # wedge

#---
def extractNodalCoordinates(instance):
    timerInstance.reset()
    timerInstance.restart()
    log(1, "odbMeshExtractor", "Started process to extract node data")
    log(1, "odbMeshExtractor", "   instance name: {0}".format(instance.name))
    
    numNodes = len(instance.nodes)
    nodes = [[coord for coord in instance.nodes[n].coordinates] for n in range(numNodes)]

    timerInstance.stop()
    log(1, "odbMeshExtractor", "Process completed in {0}".format(timerInstance))

    return nodes
#---

#---
def extractElementConectivities(instance):
    timerInstance.reset()
    timerInstance.restart()
    log(1, "odbMeshExtractor", "Started process to extract element data")
    log(1, "odbMeshExtractor", "   instance name: {0}".format(instance.name))

    numElements = len(instance.elements)
    elements = [[node-1 for node in instance.elements[e].connectivity] for e in range(numElements)]
    elementsType = [[vtkElemType[instance.elements[e].type]] for e in range(numElements)]

    timerInstance.stop()
    log(1, "odbMeshExtractor", "Process completed in {0}".format(timerInstance))

    return elements, elementsType
#---

#---
def extractMeshData(odb):
    timer.reset()
    timer.restart()
    log(0, "odbMeshExtractor", "Started process to extract mesh data from odb")
    instances = odb.rootAssembly.instances
    instanceNames = odb.rootAssembly.instances.keys()
    instanceNames = [x for x in instanceNames if not 'ASSEMBLY' in x]
    for instanceName in instanceNames:
        instance = instances[instanceName]
        nodes = extractNodalCoordinates(instance)
        els, elsType = extractElementConectivities(instance)

        log(0, "odbMeshExtractor", "Printing nodal coordinates")
        writeList("{0}/meshes/{1} nodes".format(getOriginalOdbName(odb.name), instance.name), nodes)
        log(0, "odbMeshExtractor", "Printing element connectivities")
        writeList("{0}/meshes/{1} elements".format(getOriginalOdbName(odb.name), instance.name), els)
        log(0, "odbMeshExtractor", "Printing element types")
        writeList("{0}/meshes/{1} elementsType".format(getOriginalOdbName(odb.name), instance.name), elsType)

    timer.stop()
    log(0, "odbMeshExtractor", "Process completed in {0}".format(timer))