import os
import pdb
from abaqus import *
from abaqusConstants import *
from odbTools import Timer, log, deb, logList, writeArray, writeList, getOriginalOdbName
import numpy as np

supportedElements = ['SC8R', 'SC6R', 'CSS8', 'S4R']
tensorComponents = ['11', '22', '33', '12']
tensorInvariants = ['MAX_INPLANE_PRINCIPAL']
tensorInvariantConstants = [MAX_INPLANE_PRINCIPAL]

#---
def initFields(fieldVar):
    if fieldVar == 'disp':
        scalar  = []
        vector  = ['U']
        tensor  = []
        contact = []
    else:
        scalar  = ['SDV', 'FV', 'UVARM1', 'UVARM2', 'UVARM3', 'UVARM4','UVARM6']
        vector  = ['U']
        tensor  = ['S', 'LE']
        contact = ['CSDMG']
    return scalar, vector, tensor, contact
#---

#---
def createNewField(frame, _name, _description, _type, _validInvariants=None):
    fieldId = 0
    _name = "{0} {1}".format(_name, fieldId)
    while _name in frame.fieldOutputs.keys():
        fieldId += 1
        _name = "{0} {1}".format(_name, fieldId)
        if fieldId > 100:
            log(0, "odbFieldExtractor | ERROR", "Too many attempts to create field", 2, 2)
            exit(-1)
    if _validInvariants:
        return frame.FieldOutput(name = _name,
                                description = _description,
                                validInvariants = _validInvariants,
                                type = _type)
    else:
        return frame.FieldOutput(name = _name,
                                description = _description,
                                type = _type)
#---

#---
def filterSupportedEls(odb, instances, instanceNames):

    instanceElList = ()
    for instanceName in instanceNames:
        instance = instances[instanceName]

        supportedElsLabels = np.fromiter((el.label if el.type in supportedElements else -1 for el in instance.elements), np.int32)
        sortedIndices = supportedElsLabels.argsort()
        supportedElsLabels[:] = supportedElsLabels[sortedIndices]

        indexFirstPositive = supportedElsLabels.searchsorted(0)

        instanceElList += ((instanceName, supportedElsLabels[indexFirstPositive:]),)
        log(0, "odbFieldExtractor | DEBUG", "Instance {0} has {1} supported elements of {2} total".format(instanceName, len(supportedElsLabels[indexFirstPositive:]), len(instance.elements)))

    newSetName = "extractionElements"
    d = 0
    setName = newSetName + " {0}".format(d)
    while setName in odb.rootAssembly.elementSets:
        d += 1
        setName = newSetName + " {0}".format(d)
    supportedElmSet = odb.rootAssembly.ElementSetFromElementLabels(
            name = setName, 
            elementLabels = instanceElList 
    )

    return supportedElmSet

#---

#---
def computeMaxEnvelope(frame, field, instance):
    fieldName = "{0} {1}".format(field.name, instance.name)
    auxField = createNewField(frame, fieldName[::-1],'Generated envelope', field.type, field.validInvariants)

    bulkDataBlocks = field.getSubset(region=instance).bulkDataBlocks

    data = np.zeros((len(instance.elements), bulkDataBlocks[0].data.shape[1]))
    #log(0, "odbFieldExtractor | DEBUG", "data.shape: {0}".format(data.shape))
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        #log(0, "odbFieldExtractor | DEBUG", "block.shape: {0}".format(dataBlock.data.shape))
        data[labels,:] = np.maximum(data[labels,:], dataBlock.data)
    
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        auxField.addData(position = INTEGRATION_POINT,
                        instance = instance,
                        labels = labels + 1,
                        data = data[labels,:])
    return auxField


    # size = 1
    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) == 1:
    #         size = max(size, dataBlock.data.shape[1])
    #         log(0, "odbFieldExtractor | DEBUG", "size was {0} now is {1}".format(sizeold, size))

    
    # data = np.zeros((len(instance.elements), size))
    # log(0, "odbFieldExtractor | DEBUG", "data.shape: {0}".format(data.shape))
    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) > 1:
    #         log(0, "odbFieldExtractor | WARNING", "Ignoring data block due to incompatible elements")
    #     else:
    #         labels = dataBlock.elementLabels - 1
    #         log(0, "odbFieldExtractor | DEBUG", "block.shape: {0}".format(dataBlock.data.shape))
    #         data[labels,:] = np.maximum(data[labels,:], dataBlock.data)
    
    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) > 1:
    #         log(0, "odbFieldExtractor | WARNING", "Ignoring data block due to incompatible elements")
    #     else:
    #         labels = dataBlock.elementLabels - 1
    #         auxField.addData(position = INTEGRATION_POINT,
    #                         instance = instance,
    #                         labels = labels + 1,
    #                         data = data[labels,:])
    # return auxField
#---

#---
def computeMaxAbsEnvelope(frame, field, instance):
    fieldName = "{0} {1}".format(field.name, instance.name)
    auxField = createNewField(frame, fieldName[::-1],'Generated envelope', field.type, field.validInvariants)
    
    bulkDataBlocks = field.getSubset(region=instance).bulkDataBlocks

    data = np.zeros((len(instance.elements), bulkDataBlocks[0].data.shape[1]))
    #log(0, "odbFieldExtractor | DEBUG", "data.shape: {0}".format(data.shape))
    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        #log(0, "odbFieldExtractor | DEBUG", "block.shape: {0}".format(dataBlock.data.shape))
        data[labels,:] = np.maximum(data[labels,:], np.absolute(dataBlock.data))

    for block in range(len(bulkDataBlocks)):
        dataBlock = bulkDataBlocks[block]
        labels = dataBlock.elementLabels - 1
        auxField.addData(position = INTEGRATION_POINT,
                        instance = instance,
                        labels = labels + 1,
                        data = data[labels,:])
    return auxField

    # size = 1
    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) < 1:
    #         sizeold = size
    #         size = max(size, dataBlock.data.shape[1])
    #         log(0, "odbFieldExtractor | DEBUG", "size was {0} now is {1}".format(sizeold, size))

    # data = np.zeros((len(instance.elements),size))
    # log(0, "odbFieldExtractor | DEBUG", "data.shape: {0}".format(data.shape))
    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) > 1:
    #         log(0, "odbFieldExtractor | WARNING", "Ignoring data block due to incompatible elements")
    #     else:
    #         labels = dataBlock.elementLabels - 1
    #         log(0, "odbFieldExtractor | DEBUG", "block.shape: {0}".format(dataBlock.data.shape))
    #         data[labels,:] = np.maximum(data[labels,:], np.absolute(dataBlock.data))

    # for block in range(len(bulkDataBlocks)):
    #     dataBlock = bulkDataBlocks[block]
    #     if max(dataBlock.integrationPoints) > 1:
    #         log(0, "odbFieldExtractor | WARNING", "Ignoring data block due to incompatible elements")
    #     else:
    #         labels = dataBlock.elementLabels - 1
    #         auxField.addData(position = INTEGRATION_POINT,
    #                         instance = instance,
    #                         labels = labels + 1,
    #                         data = data[labels,:])
    # return auxField
#---

#---
def averageBulkNodeData(bulkDataBlocks, size):
    log(4,"odbFieldExtractor", "Processing {0} bulkDataBlocks".format(len(bulkDataBlocks)))

    data = np.zeros(size)
    count = np.zeros((size[0],))
    for block in bulkDataBlocks:
        unsortedData = block.data
        labels = block.nodeLabels
        if len(size)>1:
            for col in range(size[1]):
                data[:,col] += np.bincount(labels, weights=unsortedData[:,col], minlength=size[0]+1)[1:]
        else:
            data += np.bincount(labels, weights=unsortedData[:,0], minlength=size[0]+1)[1:]
        count += np.bincount(labels, minlength=size[0]+1)[1:]

    nzId = np.nonzero(count)
    if len(size) > 1:
        countnz = count[nzId]
        data[nzId] = data[nzId] / countnz[:, None]
    else:
        data[nzId] = data[nzId] / count[nzId]

    return data
#---

#---
def processScalarField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(2,"odbFieldExtractor", "Processing scalar field: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        auxField = computeMaxAbsEnvelope(frame, field, instance)
        interpField = auxField.getSubset(position=ELEMENT_NODAL)
        data = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),))
    else:
        log(3,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(3, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def processVectorField(field, instance):
    t = Timer()
    t.reset()
    t.restart()
    log(2,"odbFieldExtractor", "Processing vector field: {0}".format(field.name))

    data = None
    bulkData = field.getSubset(region=instance).bulkDataBlocks
    if len(bulkData)>1:
        log(3,"odbFieldExtractor | ERROR", "BDB size is bigger than 1.", 2, 2)
    else:
        if bulkData[0].data.shape[1] != 3:
            log(3,"odbFieldExtractor | ERROR", "Vector fields should have 3 components.", 2, 2)
        else:
            data = bulkData[0].data

    t.stop()
    log(3, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def processTensorField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(2,"odbFieldExtractor", "Processing tensor field: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        auxField = computeMaxAbsEnvelope(frame, field, instance)
        interpField = auxField.getSubset(position=ELEMENT_NODAL)
        data = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),len(interpField.componentLabels)))
    else:
        log(3,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(3, "odbFieldExtractor", "Process completed in {0}".format(t))
        
    return data
#---

#---
def processTensorInvariants(field, instance, frame, maxAbs = False):
    t = Timer()
    t.reset()
    t.restart()
    #log(1,"odbFieldExtractor", "Processing tensor invariants of: {0}".format(field.name))

    data = None
    if not len(field.getSubset(region=instance).bulkDataBlocks) == 0:
        validInvariants = field.validInvariants
        invariants = [inv for inv in validInvariants if inv in tensorInvariantConstants]
        invariantStr = [tensorInvariants[x] for x, inv in enumerate(tensorInvariantConstants) if inv in invariants]
        
        data = np.zeros((len(instance.nodes),len(invariants)))
        for ind, inv in enumerate(invariants):
            log(2,"odbFieldExtractor", "Processing invariant: {0}".format(invariantStr[ind]))
            invField = field.getScalarField(invariant=inv)
        
            if maxAbs:
                auxField = computeMaxAbsEnvelope(frame, invField, instance)
            else:
                auxField = computeMaxEnvelope(frame, invField, instance)

            interpField = auxField.getSubset(position=ELEMENT_NODAL)
            data[:,ind] = averageBulkNodeData(interpField.bulkDataBlocks, (len(instance.nodes),))
    else:
        log(3,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(3, "odbFieldExtractor", "Process completed in {0}".format(t))
        
    return data, invariantStr
#---

#---
def processContactField(field, instance, frame):
    t = Timer()
    t.reset()
    t.restart()
    log(2,"odbFieldExtractor", "Processing contact field: {0}".format(field.name))

    data = None
    bulkData = field.getSubset(region=instance).bulkDataBlocks
    if not len(bulkData)==0:
        
        auxFieldName = field.name[:10] + ' ' + instance.name
        auxFieldName = auxFieldName[::-1]
        if auxFieldName in frame.fieldOutputs.keys():
            auxField = frame.fieldOutputs[auxFieldName]
        else:
            auxField = createNewField(frame, auxFieldName, 'Generated union field', SCALAR)
        
        data = np.zeros((len(instance.nodes),1))
        for block in bulkData:
            auxField.addData(position = NODAL,
                            instance = instance,
                            labels = block.nodeLabels,
                            data = block.data)
            data[block.nodeLabels-1] = block.data
        
    else:
        log(3,"odbFieldExtractor", "BulkDataBlocks had no data")

    t.stop()
    log(3, "odbFieldExtractor", "Process completed in {0}".format(t))

    return data
#---

#---
def extractFieldData(odb, frameIdList, fieldVar, duplicate):
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
    relevantElements = filterSupportedEls(odb, instances, instanceNames)
    scalar, vector, tensor, contact = initFields(fieldVar)
    frameValues = []
    stepValues = {}
    stepValues[0] = 0
    for i, step in enumerate(odb.steps.values()):
        if i == 0:
            stepValues[i] = step.frames[-1].frameValue
        else:
            stepValues[i] = stepValues[i-1] + step.frames[-1].frameValue
    frametimer = Timer()
    for i, frameId in enumerate(frameIdList):
        frametimer.reset()
        frametimer.restart()
        log(0,"odbFieldExtractor", "Processing frame {0}/{1}".format(i+1, len(frameIdList)))
        frame = odb.steps.values()[frameId[0]].frames[frameId[1]]
        if frameId[0] == 0:
            frameValues.append([frame.frameValue])
        else:
            frameValues.append([stepValues[frameId[0]-1] + frame.frameValue])
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
        if duplicate:
            savePath = getOriginalOdbName(odbName) + '/fields/frame{0}'.format(i)
        else:
            savePath = odbName + '/fields/frame{0}'.format(i)
        os.makedirs(savePath)

        for instanceName in instanceNames:
            instance = instances[instanceName]
            log(1,"odbFieldExtractor", "Processing instance {0}".format(instance.name))
            scalarData = None
            vectorData = None
            tensorData = None 
            contactData = None
            
            for scalarField in scalarFields:
                if scalarField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[scalarField].getSubset(region=relevantElements)
                    scalarData = processScalarField(field, instance, frame)
                if not scalarData is None:
                    log(2,"odbFieldExtractor", "Printing field {0}".format(scalarField))
                    writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, scalarField), scalarData)
                    scalarData = None
            
            for vectorField in vectorFields:
                if vectorField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[vectorField]
                    vectorData = processVectorField(field, instance)
                if not vectorData is None:
                    log(2,"odbFieldExtractor", "Printing field {0}".format(vectorField))
                    writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, vectorField), vectorData)
                    vectorData = None

            for tensorField in tensorFields:
                if tensorField in frame.fieldOutputs.keys():
                    field = frame.fieldOutputs[tensorField].getSubset(region=relevantElements)
                    tensorData = processTensorField(field, instance, frame)
                    invData, invLabels = processTensorInvariants(field, instance, frame)
                if not tensorData is None:
                    for ic, component in enumerate(tensorComponents):
                        log(2,"odbFieldExtractor", "Printing field {0}".format(tensorField + '_' + component))
                        writeArray("{0}/{1} {2}_{3}.csv".format(savePath, instance.name, tensorField, component), tensorData[:,ic])
                    tensorData = None
                if not invData is None and not len(invLabels) == 0:
                    for ii, inv in enumerate(invLabels):
                        log(2,"odbFieldExtractor", "Printing field {0}".format(tensorField + '_' + inv))
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
                log(2,"odbFieldExtractor", "Printing field {0}".format(contactField.split()[0].strip()))
                writeArray("{0}/{1} {2}.csv".format(savePath, instance.name, contactField.split()[0].strip()), contactData)
        
        del frame
        frametimer.stop()
        log(0,"odbFieldExtractor", "Frame processed in {0}".format(frametimer))

    if odbName.endswith(".odb"):
        odbName = odbName[:-4]
    if duplicate:
        savePath = getOriginalOdbName(odbName) + '/vtk'
    else:
        savePath = odbName + '/vtk'
    writeList("{0}/frameValues.csv".format(savePath), frameValues)
    timer.stop()
    log(0, "odbFieldExtractor", "Process completed in {0}".format(timer))
