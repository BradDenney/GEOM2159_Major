# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterEnum,
                       QgsProcessingFeatureSource)
import os
import math
from qgis.utils import iface
from qgis import processing


class BroilerNetworkBuffer(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    HYDRO = 'HYDRO'
    ROAD = 'ROAD'
    MASS = 'MASS'
    COMPOUND = 'COMPOUND'
    ITERATIONS = 'ITERATIONS'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BroilerNetworkBuffer()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'broilernetworkbuffer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Broiler Network Buffer')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("This tool calculates the area of land (minus roads and rivers) that can be covered with certain volumes of waste products from a broiler farm.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Select layer with central point for process'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.HYDRO,
                self.tr('Select data source for hydro network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROAD,
                self.tr('Select data source for road network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MASS,
                self.tr('Input mass of broiler waste (in tonnes)'),
            )
        )
        
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterEnum(
                self.COMPOUND,
                self.tr('Select compound to be calculated'),
                ['Nitrogen','Phosphorus','Potassium']
            )
        )
        
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATIONS,
                self.tr('Input desired number of iterations'),
            )
        )
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output buffer layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        pointFile = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        hydroFile = self.parameterAsSource(
            parameters,
            self.HYDRO,
            context
        )
        roadFile = self.parameterAsSource(
            parameters,
            self.ROAD,
            context
        )
        massBroilerWaste = self.parameterAsDouble(
            parameters,
            self.MASS,
            context
        )
        compound = self.parameterAsEnum(
            parameters,
            self.COMPOUND,
            context
        )
        iterations = self.parameterAsInt(
            parameters,
            self.ITERATIONS,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if pointFile is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            pointFile.fields(),
            3,
            pointFile.sourceCrs()
        )

        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(pointFile.sourceCrs().authid()))

        # Set mass & concentration of compound
        if parameters[self.COMPOUND] == 0:
            massCompound = parameters[self.MASS] * 30.714286
            concCompound = 0.005
        elif parameters[self.COMPOUND] == 1:
            massCompound = parameters[self.MASS] * 14.142857
            concCompound = 0.0027
        elif parameters[self.COMPOUND] == 2:
            massCompound = parameters[self.MASS] * 13.428571
            concCompound = 0.0025
        
        # Define parameters for Hydro buffer
        hydroBuffParameters = {
        'INPUT' : parameters[self.HYDRO],
        'DISTANCE' : 50,
        'DISSOLVE' : True,
        'OUTPUT' : 'memory:'
        }
        # Run Hydro buffer process
        hydroBuffer = processing.run('native:buffer', hydroBuffParameters)
        # Add buffer layer to data frame
        #hydroBuffer = iface.addVectorLayer(f'{filePath}Temp\\hydroBufferFile.shp', 'Hydro Buffer', 'ogr')

        # Define parameters for Road buffer
        roadBuffParameters = {
        'INPUT' : parameters[self.ROAD],
        'DISTANCE' : 40,
        'DISSOLVE' : True,
        'OUTPUT' : 'memory:'
        }
        # Run Road buffer process
        roadBuffer = processing.run('native:buffer', roadBuffParameters)
        # Add buffer layer to data frame
        #roadBuffer = iface.addVectorLayer(f'{filePath}Temp\\roadBufferFile.shp', 'Road Buffer', 'ogr')

        # Define parameters for Merge process
        mergeParameters = {
        'LAYERS' : [hydroBuffer["OUTPUT"], roadBuffer["OUTPUT"]],
        'OUTPUT' : 'memory:'
        }
        # Run Merge process
        mergeBuffer = processing.run('qgis:mergevectorlayers', mergeParameters)
        # Add merged layer to data frame
        #mergeBuffer = iface.addVectorLayer(f'{filePath}Temp\\mergeFile.shp', 'Merge Buffer', 'ogr')

        # Define parameters for Dissolve process
        dissolveParameters = {
        'INPUT' : mergeBuffer["OUTPUT"],
        'OUTPUT' : 'memory:'
        }
        # Run Dissolve process
        dissolveBuffer = processing.run('qgis:dissolve', dissolveParameters)
        # Add merged layer to data frame
        #dissolveBuffer = iface.addVectorLayer(f'{filePath}Temp\\dissolveFile.shp', 'Dissolve Buffer', 'ogr')

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
        'INPUT' : parameters[self.INPUT],
        'DISTANCE' : listDistBuff[0],
        'SEGMENTS' : 10,
        'OUTPUT' : 'memory:'
        }
        # Run Buffer0 process
        listBuff[0] = processing.run('native:buffer', parametersBuffer)
        # Add Buffer0 layer to data frame
        #listBuff[0] = iface.addVectorLayer(f'{filePath}Temp\\Buffer0File.shp', 'Buffer0', 'ogr')

        for count in range (1, iterations + 1):
            # Define parameters for Clip
            parametersClip = {
            'INPUT' : dissolveBuffer["OUTPUT"],
            'OVERLAY' : listBuff[count - 1]["OUTPUT"],
            'OUTPUT' : 'memory:'
            }
            # Run Clip process
            listClip.append(processing.run('qgis:clip', parametersClip))
            # Add Clip layer to data frame
            #listClip.append(iface.addVectorLayer(f'{filePath}Temp\\Clip{count}File.shp', f'Clip{count}', 'ogr'))

            # Create list of Clip features
            featuresClip = listClip[count]["OUTPUT"].getFeatures()
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
                'INPUT' : parameters[self.INPUT],
                'DISTANCE' : listDistBuff[count],
                'SEGMENTS' : 10,
                'OUTPUT' : 'memory:'
                }
                # Run Buffer process
                listBuff.append(processing.run('native:buffer', parametersBuffer))
                # Add Buffer layer to data frame
                #listBuff.append(iface.addVectorLayer(f'{filePath}{compound}Buffer.shp', f'Buffer{count}' ,'ogr'))
            else:
                # Define parameters for Buffer
                parametersBuffer = {
                'INPUT' : parameters[self.INPUT],
                'DISTANCE' : listDistBuff[count],
                'SEGMENTS' : 10,
                'OUTPUT' : 'memory:'
                }
                # Run Buffer process
                listBuff.append(processing.run('native:buffer', parametersBuffer))
                # Add Buffer layer to data frame
                #listBuff.append(iface.addVectorLayer(f'{filePath}Temp\\Buffer{count}File.shp', f'Buffer{count}', 'ogr'))

        # Read the dissolved layer and create output features
        for feature in listBuff[iterations]["OUTPUT"].getFeatures():
            new_feature =  QgsFeature()
            # Set geometry to dissolved geometry
            new_feature.setGeometry(feature.geometry())
            # Set attributes from sum_unique_values dictionary that we had computed
            new_feature.setAttributes(["Id", 0])
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Calculate area increase
        areaIncrease = listAreaBuff[iterations] - listAreaBuff[0]
        # Calculate percent increase
        pcIncrease = ((listAreaBuff[iterations] / listAreaBuff[0]) - 1) * 100
        
        # Print areaBuffer3
        feedback.pushInfo(f'{parameters[self.MASS]}t of broiler waste contains {int(round(massCompound / 1000))}t of fertiliser, which covers {int(round(listAreaBuff[iterations] / 10000))} Ha')
        # Print areaIncrease
        feedback.pushInfo(f'Process increases area covered by {int(round(areaIncrease / 10000))} Ha')
        # Print pcIncrease
        feedback.pushInfo(f'This is {round(pcIncrease)}% larger than original area')

        return {self.OUTPUT: dest_id}
