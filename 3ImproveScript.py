def broilerBuffer(compound, massBroilerWaste, iterations):
    # Set mass & concentration of compound
    if compound == 'Nitrogen':
        massCompound = massBroilerWaste * 30.714286
        concCompound = 0.005
    elif compound == 'Phosphorus':
        massCompound = massBroilerWaste * 14.142857
        concCompound = 0.0027
    elif compound == 'Potassium':
        massCompound = massBroilerWaste * 13.428571
        concCompound = 0.0025
    
    # Set file path to data folder
    filePath = 'C:\\...\\3BaseScript\\'
    # Set file for Central Point
    pointFile = 'Data\\CentralPoint.shp'
    # Set file for Hydro data
    hydroFile = 'Data\\HY_WATERCOURSE.shp'
    # Set file for Roads data
    roadFile = 'Data\\TR_ROAD.shp'
    # Add Hydro layer to data frame
    hydroLayer = iface.addVectorLayer(f'{filePath}{hydroFile}', 'Hydro', 'ogr')
    # Add CentralPoint layer to data frame
    roadLayer = iface.addVectorLayer(f'{filePath}{roadFile}', 'Roads', 'ogr')
    # Add CentralPoint layer to data frame
    pointLayer = iface.addVectorLayer(f'{filePath}{pointFile}', 'Central Point', 'ogr')

    # Delete most Temp files
    for files in os.listdir(f'{filePath}\\Temp'):
        QgsVectorFileWriter.deleteShapeFile(f'{filePath}\\Temp\\{files}')

    # Define parameters for Hydro buffer
    hydroBuffParameters = {
    'INPUT' : hydroLayer,
    'DISTANCE' : 50,
    'DISSOLVE' : True,
    'OUTPUT' : f'{filePath}Temp\\hydroBufferFile.shp'
    }
    # Run Hydro buffer process
    processing.run('native:buffer', hydroBuffParameters)
    # Add buffer layer to data frame
    hydroBuffer = iface.addVectorLayer(f'{filePath}Temp\\hydroBufferFile.shp', 'Hydro Buffer', 'ogr')

    # Define parameters for Road buffer
    roadBuffParameters = {
    'INPUT' : roadLayer,
    'DISTANCE' : 40,
    'DISSOLVE' : True,
    'OUTPUT' : f'{filePath}Temp\\roadBufferFile.shp'
    }
    # Run Road buffer process
    processing.run('native:buffer', roadBuffParameters)
    # Add buffer layer to data frame
    roadBuffer = iface.addVectorLayer(f'{filePath}Temp\\roadBufferFile.shp', 'Road Buffer', 'ogr')

    # Define parameters for Merge process
    mergeParameters = {
    'LAYERS' : [hydroBuffer, roadBuffer],
    'OUTPUT' : f'{filePath}Temp\\mergeFile.shp'
    }
    # Run Merge process
    processing.run('qgis:mergevectorlayers', mergeParameters)
    # Add merged layer to data frame
    mergeBuffer = iface.addVectorLayer(f'{filePath}Temp\\mergeFile.shp', 'Merge Buffer', 'ogr')

    # Define parameters for Dissolve process
    dissolveParameters = {
    'INPUT' : mergeBuffer,
    'OUTPUT' : f'{filePath}Temp\\dissolveFile.shp'
    }
    # Run Dissolve process
    processing.run('qgis:dissolve', dissolveParameters)
    # Add merged layer to data frame
    dissolveBuffer = iface.addVectorLayer(f'{filePath}Temp\\dissolveFile.shp', 'Dissolve Buffer', 'ogr')

    # Establish reference lists
    listBuff = [0]
    listClip = [0]
    listAreaBuff = [0]
    listAreaClip = [0]
    listDistBuff = [0]

    # Calculate area of Buffer0
    listAreaBuff[0] = massCompound / concCompound
    # Calculate distance of Buffer0
    listDistBuff[0] = math.sqrt(listAreaBuff[0] / math.pi)

    # Define parameters for Buffer0
    parametersBuffer = {
    'INPUT' : pointLayer,
    'DISTANCE' : listDistBuff[0],
    'SEGMENTS' : 10,
    'OUTPUT' : f'{filePath}Temp\\Buffer0File.shp'
    }
    # Run Buffer0 process
    processing.run('native:buffer', parametersBuffer)
    # Add Buffer0 layer to data frame
    listBuff[0] = iface.addVectorLayer(f'{filePath}Temp\\Buffer0File.shp', 'Buffer0', 'ogr')

    for count in range (1, iterations + 1):
        # Define parameters for Clip
        parametersClip = {
        'INPUT' : dissolveBuffer,
        'OVERLAY' : listBuff[count - 1],
        'OUTPUT' : f'{filePath}Temp\\Clip{count}File.shp'
        }
        # Run Clip process
        processing.run('qgis:clip', parametersClip)
        # Add Clip layer to data frame
        listClip.append(iface.addVectorLayer(f'{filePath}Temp\\Clip{count}File.shp', f'Clip{count}', 'ogr'))

        # Create list of Clip features
        featuresClip = listClip[count].getFeatures()
        # Iterate through features
        for feature in featuresClip:
            # Determine feature area
            listAreaClip.append(feature.geometry().area())

        # Calculate Buffer area
        listAreaBuff.append(listAreaBuff[count - 1] + (listAreaClip[count] - listAreaClip[count - 1]))
        # Calculate Buffer distance
        listDistBuff.append(math.sqrt(listAreaBuff[count] / math.pi))

        # Cause final buffer to be saved permanently
        if count == iterations:
            # Define parameters for Buffer
            parametersBuffer = {
            'INPUT' : pointLayer,
            'DISTANCE' : listDistBuff[count],
            'SEGMENTS' : 10,
            'OUTPUT' : f'{filePath}{compound}Buffer.shp'
            }
            # Run Buffer process
            processing.run('native:buffer', parametersBuffer)
            # Add Buffer layer to data frame
            listBuff.append(iface.addVectorLayer(f'{filePath}{compound}Buffer.shp', f'Buffer{count}' ,'ogr'))
        else:
            # Define parameters for Buffer
            parametersBuffer = {
            'INPUT' : pointLayer,
            'DISTANCE' : listDistBuff[count],
            'SEGMENTS' : 10,
            'OUTPUT' : f'{filePath}Temp\\Buffer{count}File.shp'
            }
            # Run Buffer process
            processing.run('native:buffer', parametersBuffer)
            # Add Buffer layer to data frame
            listBuff.append(iface.addVectorLayer(f'{filePath}Temp\\Buffer{count}File.shp', f'Buffer{count}', 'ogr'))

    # Calculate area increase
    areaIncrease = listAreaBuff[iterations] - listAreaBuff[0]
    # Calculate percent increase
    pcIncrease = ((listAreaBuff[iterations] / listAreaBuff[0]) - 1) * 100
        
    # Remove Temporary map layers
    QgsProject.instance().removeMapLayer(hydroLayer)
    QgsProject.instance().removeMapLayer(roadLayer)
    QgsProject.instance().removeMapLayer(hydroBuffer)
    QgsProject.instance().removeMapLayer(roadBuffer)
    QgsProject.instance().removeMapLayer(mergeBuffer)
    QgsProject.instance().removeMapLayer(dissolveBuffer)
    for count in range(1, iterations+1):
        QgsProject.instance().removeMapLayer(listBuff[count - 1])
        QgsProject.instance().removeMapLayer(listClip[count])

    # Print areaBuffer3
    print(f'{massBroilerWaste}t of broiler waste contains {int(round(massCompound / 1000))}t of {compound}, which covers {int(round(listAreaBuff[iterations] / 10000))} Ha')
    # Print areaIncrease
    print(f'Process increases area covered by {int(round(areaIncrease / 10000))} Ha')
    # Print pcIncrease
    print(f'This is {round(pcIncrease)}% larger than original area')


# Run function
broilerBuffer('Phosphorus', 3000, 5)