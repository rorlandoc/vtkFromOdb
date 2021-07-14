import os, sys, pdb
from abaqus import *
from abaqusConstants import *
from odbTools import Timer, log, logList, logProgress, writeArray, getOriginalOdbName
import numpy as np

scalar  = ['SDV', 'FV', 'UVARM1', 'UVARM2', 'UVARM3', 'UVARM4','UVARM6']
vector  = ['U']
tensor  = ['S', 'LE']
contact = ['CSDMG']
tensorComponents = ['11', '22', '33', '12']
# tensorInvariants = ['MAX_INPLANE_PRINCIPAL', 'MIN_INPLANE_PRINCIPAL', 'OUTOFPLANE_PRINCIPAL', 
#                     'MAX_PRINCIPAL', 'MID_PRINCIPAL', 'MIN_PRINCIPAL']
# tensorInvariantConstants = [MAX_INPLANE_PRINCIPAL, MIN_INPLANE_PRINCIPAL, OUTOFPLANE_PRINCIPAL, 
#                             MAX_PRINCIPAL, MID_PRINCIPAL, MIN_PRINCIPAL]
tensorInvariants = ['MAX_INPLANE_PRINCIPAL']
tensorInvariantConstants = [MAX_INPLANE_PRINCIPAL]

#---
def computeMaxEnvelope(frame, field, instance, id=0):
    fieldName = "{0} {1} {2}".format(field.name, instance.name, id)
    log(1,"odbFieldExtractor", "Creating auxiliar field: {0}".format(fieldName))
    auxField = frame.FieldOutput(name=fieldName,
                                description = 'Generated envelope',
                                validInvariants = field.validInvariants,
                                type = field.type)

    log(1,"odbFieldExtractor", "Starting max envelope computation")
    bulkDataBlocks = field.getSubset(region=instance).bulkDataBlocks
    data = np.zeros((len(instance.elements),bulkDataBlocks[0].data.shape[1]))
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        data[labels,:] = np.maximum(data[labels,:], dataBlock.data)

    log(1,"odbFieldExtractor", "Adding integration point envelope data to field")    
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        auxField.addData(position = INTEGRATION_POINT,
                        instance = instance,
                        labels = labels + 1,
                        data = data[labels,:])
    return auxField
#---

#---
def computeMaxAbsEnvelope(frame, field, instance, id=0):
    fieldName = "{0} {1} {2}".format(field.name, instance.name, id)
    log(1,"odbFieldExtractor", "Creating auxiliar field: {0}".format(fieldName))
    auxField = frame.FieldOutput(name=fieldName,
                                description = 'Generated envelope',
                                validInvariants = field.validInvariants,
                                type = field.type)
    
    log(1,"odbFieldExtractor", "Starting max abs envelope computation")
    bulkDataBlocks = field.getSubset(region=instance).bulkDataBlocks
    data = np.zeros((len(instance.elements),bulkDataBlocks[0].data.shape[1]))
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        data[labels,:] = np.maximum(data[labels,:], np.absolute(dataBlock.data))

    log(1,"odbFieldExtractor", "Adding integration point envelope data to field")
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        auxField.addData(position = INTEGRATION_POINT,
                        instance = instance,
                        labels = labels + 1,
                        data = data[labels,:])
    return auxField
#---



#---
def averageBulkNodeData(bulkDataBlocks, size):
    log(1,"odbFieldExtractor", "Starting nodal averaging")
    log(1,"odbFieldExtractor", "Processing {0} bulkDataBlocks".format(len(bulkDataBlocks)))

    data = np.zeros(size)
    count = np.zeros(size)
    for block in bulkDataBlocks:
        unsortedData = block.data
        labels = block.nodeLabels
        for i,label in enumerate(labels):
            data[label - 1] += unsortedData[i]
            if len(size) > 1:
                count[label - 1] += np.array((1,)*size[1])
            else:
                count[label - 1] += 1

    if len(size) > 1:
        nzId = np.nonzero(count[:,0])
    else:
        nzId = np.nonzero(count)
    data[nzId] = data[nzId] / count[nzId]

    return data
#---

#---
def processScalarField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(1,"odbFieldExtractor", "Processing scalar field: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        auxField = computeMaxAbsEnvelope(frame, field, instance)
        interpField = auxField.getSubset(position=ELEMENT_NODAL)
        data = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),))
    else:
        log(1,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(1, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def processVectorField(field, instance):
    t = Timer()
    t.reset()
    t.restart()
    log(1,"odbFieldExtractor", "Processing vector field: {0}".format(field.name))

    data = None
    bulkData = field.getSubset(region=instance).bulkDataBlocks
    if len(bulkData)>1:
        log(1,"odbFieldExtractor | ERROR", "BDB size is bigger than 1.", 2, 2)
    else:
        if bulkData[0].data.shape[1] != 3:
            log(1,"odbFieldExtractor | ERROR", "Vector fields should have 3 components.", 2, 2)
        else:
            data = bulkData[0].data

    t.stop()
    log(1, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def processTensorField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(1,"odbFieldExtractor", "Processing tensor field: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        auxField = computeMaxAbsEnvelope(frame, field, instance)
        interpField = auxField.getSubset(position=ELEMENT_NODAL)
        data = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),len(interpField.componentLabels)))
    else:
        log(1,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(1, "odbFieldExtractor", "Process completed in {0}".format(t))
        
    return data
#---

#---
def processTensorInvariants(field, instance, frame, maxAbs = False):
    t = Timer()
    t.reset()
    t.restart()
    log(1,"odbFieldExtractor", "Processing tensor invariants of: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        validInvariants = field.validInvariants
        invariants = [inv for inv in validInvariants if inv in tensorInvariantConstants]
        invariantStr = [tensorInvariants[x] for x, inv in enumerate(tensorInvariantConstants) if inv in invariants]
        
        data = np.zeros((len(instance.nodes),len(invariants)))
        for ind, inv in enumerate(invariants):
            log(1,"odbFieldExtractor", "Processing invariant: {0}".format(invariantStr[ind]))
            invField = field.getScalarField(invariant=inv)
        
            if maxAbs:
                auxField = computeMaxAbsEnvelope(frame, invField, instance, 1)
            else:
                auxField = computeMaxEnvelope(frame, invField, instance, 1)

            interpField = auxField.getSubset(position=ELEMENT_NODAL)
            data[:,ind] = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),))
    else:
        log(1,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(1, "odbFieldExtractor", "Process completed in {0}".format(t))
        
    return data, invariantStr
#---

#---
def processContactField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(1,"odbFieldExtractor", "Processing contact field: {0}".format(field.name))

    data = None
    bulkData = field.getSubset(region=instance).bulkDataBlocks
    if not len(bulkData)==0:
        
        auxFieldName = field.name[:10] + ' ' + instance.name
        auxFieldName = auxFieldName[::-1]
        if auxFieldName in frame.fieldOutputs.keys():
            log(1,"odbFieldExtractor", "Field already exists")
            auxField = frame.fieldOutputs[auxFieldName]
        else:
            log(1,"odbFieldExtractor", "Creating auxiliar field: {0}".format(auxFieldName))
            auxField = frame.FieldOutput(name = auxFieldName,
                                         description = 'Generated union field',
                                         type = SCALAR)
        
        data = np.zeros((len(instance.nodes),1))
        for block in bulkData:
            auxField.addData(position = NODAL,
                            instance = instance,
                            labels = block.nodeLabels,
                            data = block.data)
            data[block.nodeLabels-1] = block.data
        
    else:
        log(1,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(1, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def extractFieldData(odb, frameIdList):
    timer = Timer()
    timer.reset()
    timer.restart()
    log(0,"odbFieldExtractor", "Started process to extract field data from odb")
    log(0,"odbFieldExtractor", "Extracting {0} frames".format(len(frameIdList)))

    odbName = odb.name.split("/")[-1]
    instances = odb.rootAssembly.instances
    instanceNames = odb.rootAssembly.instances.keys()
    instanceNames = [x for x in instanceNames if not 'ASSEMBLY' in x]
    instanceNames = instanceNames[::-1]
    for i, frameId in enumerate(frameIdList):
        log(0,"odbFieldExtractor", "Processing frame {0}/{1}".format(i+1, len(frameIdList)))
        frame = odb.steps.values()[frameId[0]].frames[frameId[1]]
        fieldList = frame.fieldOutputs.keys()

        scalarFields  = [x for x in fieldList for y in scalar  if y in x]
        vectorFields  = [x for x in fieldList for y in vector  if y == x]
        tensorFields  = [x for x in fieldList for y in tensor  if y == x]
        contactFields = [x for x in fieldList for y in contact if y in x]

        logList("scalarFields", scalarFields) if len(scalarFields)>0 else None
        logList("vectorFields", vectorFields) if len(vectorFields)>0 else None
        logList("tensorFields", tensorFields) if len(tensorFields)>0 else None
        logList("contactFields", contactFields) if len(contactFields)>0 else None
        
        if odbName.endswith(".odb"):
            odbName = odbName[:-4]
        savePath = getOriginalOdbName(odbName) + '/fields/frame{0}'.format(i)
        os.makedirs(savePath)

        for instanceName in instanceNames:
            instance = instances[instanceName]
            log(0,"odbFieldExtractor", "Processing instance {0}".format(instance.name))
            scalarData = None
            vectorData = None
            tensorData = None 
            contactData = None
            
            for scalarField in scalarFields:
                if scalarField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[scalarField]
                    scalarData = processScalarField(field, instance, frame)
                if not scalarData is None:
                    log(0,"odbFieldExtractor", "Printing field {0}".format(scalarField))
                    writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, scalarField), scalarData)
                    scalarData = None
            
            for vectorField in vectorFields:
                if vectorField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[vectorField]
                    vectorData = processVectorField(field, instance)
                if not vectorData is None:
                    log(0,"odbFieldExtractor", "Printing field {0}".format(vectorField))
                    writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, vectorField), vectorData)
                    vectorData = None

            for tensorField in tensorFields:
                if tensorField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[tensorField]
                    tensorData = processTensorField(field, instance, frame)
                    invData, invLabels = processTensorInvariants(field, instance, frame)
                if not tensorData is None:
                    for ic, component in enumerate(tensorComponents):
                        log(0,"odbFieldExtractor", "Printing field {0}".format(tensorField + '_' + component))
                        writeArray("{0}/{1} {2}_{3}.csv".format(savePath, instance.name, tensorField, component), tensorData[:,ic])
                    tensorData = None
                if not invData is None and not len(invLabels) == 0:
                    for ii, inv in enumerate(invLabels):
                        log(0,"odbFieldExtractor", "Printing field {0}".format(tensorField + '_' + inv))
                        writeArray("{0}/{1} {2}_{3}.csv".format(savePath, instance.name, tensorField, inv), invData[:,ii])
                    invData = None
            
            for contactField in contactFields: 
                if contactField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[contactField]
                    if contactData is None:
                        auxData = None
                        auxData = processContactField(field, instance, frame)
                        if not auxData is None:
                            contactData = auxData
                    else:
                        auxData = None
                        auxData = processContactField(field, instance, frame)
                        if not auxData is None:
                            contactData += auxData
                    
            if not contactData is None:
                log(0,"odbFieldExtractor", "Printing field {0}".format(contactField.split()[0].strip()))
                writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, contactField.split()[0].strip()), contactData)
        
        del frame

    timer.stop()
    log(0, "odbFieldExtractor", "Process completed in {0}".format(timer))
