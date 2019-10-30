def broilerBuffer(compound,massBroilerWaste):
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
    filePath = 'C:\\RMIT\\Geospatial Programming\\MajorProject\\3BaseScript\\'
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

    # Define parameters for Hydro buffer
    hydroBuffParameters = {
    'INPUT':hydroLayer,
    'DISTANCE':50,
    'DISSOLVE':True,
    'OUTPUT':f'{filePath}Temp\\hydroBufferFile.shp'
    }
    # Run Hydro buffer process
    processing.run('native:buffer',hydroBuffParameters)
    # Add buffer layer to data frame
    hydroBuffer = iface.addVectorLayer(f'{filePath}Temp\\hydroBufferFile.shp','Hydro Buffer','ogr')

    # Define parameters for Road buffer
    roadBuffParameters = {
    'INPUT':roadLayer,
    'DISTANCE':40,
    'DISSOLVE':True,
    'OUTPUT':f'{filePath}Temp\\roadBufferFile.shp'
    }
    # Run Road buffer process
    processing.run('native:buffer',roadBuffParameters)
    # Add buffer layer to data frame
    roadBuffer = iface.addVectorLayer(f'{filePath}Temp\\roadBufferFile.shp','Road Buffer','ogr')

    # Define parameters for Merge process
    mergeParameters = {
    'LAYERS':[hydroBuffer,roadBuffer],
    'OUTPUT':f'{filePath}Temp\\mergeFile.shp'
    }
    # Run Merge process
    processing.run('qgis:mergevectorlayers',mergeParameters)
    # Add merged layer to data frame
    mergeBuffer = iface.addVectorLayer(f'{filePath}Temp\\mergeFile.shp','Merge Buffer','ogr')

    # Define parameters for Dissolve process
    dissolveParameters = {
    'INPUT':mergeBuffer,
    'OUTPUT':f'{filePath}Temp\\dissolveFile.shp'
    }
    # Run Dissolve process
    processing.run('qgis:dissolve',dissolveParameters)
    # Add merged layer to data frame
    dissolveBuffer = iface.addVectorLayer(f'{filePath}Temp\\dissolveFile.shp','Dissolve Buffer','ogr')

    # Calculate area of Buffer0
    areaBuffer0 = massCompound / concCompound
    # Calculate distance of Buffer0
    distanceBuffer0 = math.sqrt(areaBuffer0/math.pi)

    # Define parameters for Buffer0
    parametersBuffer0 = {
    'INPUT':pointLayer,
    'DISTANCE':distanceBuffer0,
    'OUTPUT':f'{filePath}Temp\\Buffer0File.shp'
    }
    # Run Buffer0 process
    processing.run('native:buffer',parametersBuffer0)
    # Add Buffer0 layer to data frame
    Buffer0 = iface.addVectorLayer(f'{filePath}Temp\\Buffer0File.shp','Buffer0','ogr')

    # Define parameters for Clip1
    parametersClip1 = {
    'INPUT':dissolveBuffer,
    'OVERLAY':Buffer0,
    'OUTPUT':f'{filePath}Temp\\Clip1File.shp'
    }
    # Run Clip1 process
    processing.run('qgis:clip',parametersClip1)
    # Add Clip1 layer to data frame
    Clip1 = iface.addVectorLayer(f'{filePath}Temp\\Clip1File.shp','Clip1','ogr')

    # Create list of Clip1 features
    featuresClip1 = Clip1.getFeatures()
    # Iterate through features
    for feature in featuresClip1:
        # Determine feature area
        areaClip1 = feature.geometry().area()

    # Calculate Buffer 1 area
    areaBuffer1 = areaBuffer0 + areaClip1
    # Calculate Buffer 1 distance
    distanceBuffer1 = math.sqrt(areaBuffer1/math.pi)

    # Define parameters for Buffer1
    parametersBuffer1 = {
    'INPUT':pointLayer,
    'DISTANCE':distanceBuffer1,
    'OUTPUT':f'{filePath}Temp\\Buffer1File.shp'
    }
    # Run Buffer1 process
    processing.run('native:buffer',parametersBuffer1)
    # Add Buffer1 layer to data frame
    Buffer1 = iface.addVectorLayer(f'{filePath}Temp\\Buffer1File.shp','Buffer1','ogr')

    # Define parameters for Clip2
    parametersClip2 = {
    'INPUT':dissolveBuffer,
    'OVERLAY':Buffer1,
    'OUTPUT':f'{filePath}Temp\\Clip2File.shp'
    }
    # Run Clip2 process
    processing.run('qgis:clip',parametersClip2)
    # Add Clip2 layer to data frame
    Clip2 = iface.addVectorLayer(f'{filePath}Temp\\Clip2File.shp','Clip2','ogr')

    # Create list of Clip2 features
    featuresClip2 = Clip2.getFeatures()
    # Iterate through features
    for feature in featuresClip2:
        # Determine feature area
        areaClip2 = feature.geometry().area()

    # Calculate Buffer 2 area
    areaBuffer2 = areaBuffer1 + (areaClip2 - areaClip1)
    # Calculate Buffer 2 distance
    distanceBuffer2 = math.sqrt(areaBuffer2/math.pi)

    # Define parameters for Buffer2
    parametersBuffer2 = {
    'INPUT':pointLayer,
    'DISTANCE':distanceBuffer2,
    'OUTPUT':f'{filePath}Temp\\Buffer2File.shp'
    }
    # Run Buffer2 process
    processing.run('native:buffer',parametersBuffer2)
    # Add Buffer2 layer to data frame
    Buffer2 = iface.addVectorLayer(f'{filePath}Temp\\Buffer2File.shp','Buffer2','ogr')

    # Define parameters for Clip3
    parametersClip3 = {
    'INPUT':dissolveBuffer,
    'OVERLAY':Buffer2,
    'OUTPUT':f'{filePath}Temp\\Clip3File.shp'
    }
    # Run Clip3 process
    processing.run('qgis:clip',parametersClip3)
    # Add Clip3 layer to data frame
    Clip3 = iface.addVectorLayer(f'{filePath}Temp\\Clip3File.shp','Clip3','ogr')

    # Create list of Clip3 features
    featuresClip3 = Clip3.getFeatures()
    # Iterate through features
    for feature in featuresClip3:
        # Determine feature area
        areaClip3 = feature.geometry().area()

    # Calculate Buffer 3 area
    areaBuffer3 = areaBuffer2 + (areaClip3 - areaClip2)
    # Calculate Buffer 2 distance
    distanceBuffer3 = math.sqrt(areaBuffer3/math.pi)

    # Define parameters for Buffer3
    parametersBuffer3 = {
    'INPUT':pointLayer,
    'DISTANCE':distanceBuffer3,
    'OUTPUT':f'{filePath}Buffer3.shp'
    }
    # Run Buffer3 process
    processing.run('native:buffer',parametersBuffer3)
    # Add Buffer3 layer to data frame
    Buffer3 = iface.addVectorLayer(f'{filePath}Buffer3.shp','Buffer3','ogr')

    # Calculate area increase
    areaIncrease = areaBuffer3 - areaBuffer0
    # Calculate percent increase
    pcIncrease = ((areaBuffer3/areaBuffer0)-1)*100

    # Remove Temporary map layers
    QgsProject.instance().removeMapLayer(hydroLayer)
    QgsProject.instance().removeMapLayer(roadLayer)
    QgsProject.instance().removeMapLayer(hydroBuffer)
    QgsProject.instance().removeMapLayer(roadBuffer)
    QgsProject.instance().removeMapLayer(mergeBuffer)
    QgsProject.instance().removeMapLayer(dissolveBuffer)
    QgsProject.instance().removeMapLayer(Buffer0)
    QgsProject.instance().removeMapLayer(Clip1)
    QgsProject.instance().removeMapLayer(Buffer1)
    QgsProject.instance().removeMapLayer(Clip2)
    QgsProject.instance().removeMapLayer(Buffer2)
    QgsProject.instance().removeMapLayer(Clip3)

    # Delete most Temp files
    for files in os.listdir(f'{filePath}\\Temp'):
        QgsVectorFileWriter.deleteShapeFile(f'{filePath}\\Temp\\{files}')

    # Print areaBuffer3
    print(f'{massBroilerWaste}t of broiler waste contains {int(round(massCompound/1000))}t of {compound}, which covers {int(round(areaBuffer3/10000,0))} Ha')
    # Print areaIncrease
    print(f'Process increases area covered by {int(round(areaIncrease/10000))} Ha')
    # Print pcIncrease
    print(f'This is {round(pcIncrease,0)}% larger than original area')


# Run function
broilerBuffer('Nitrogen',7000)