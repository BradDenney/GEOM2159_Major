# -*- coding: utf-8 -*-

"""
This is a tool which, when run, will determine and visualise the area that can
be covered by an amount of concentrated waste, accounting for roads and creeks
(which need no fertilising).
This will demonstrate to clients the area that can be covered if they are smart
about their waste and use it as valuable soil enriching nutrients.
The constructed buffer can show clearly the area that can be covered, and
account for different land uses around the area.  This tool will not, however,
account for slope variation.  This may be an extension for this tool in the
future.
"""

# Import relevant Python and PyQGIS libraries
import math
import os
from qgis import processing
from qgis.core import (QgsFeature,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface


# Establish the processing algorithm
class BroilerNetworkBuffer(QgsProcessingAlgorithm):
    """
    This is a tool which, when run, will determine and visualise the area that
    can be covered by an amount of concentrated waste, accounting for roads and
    creeks (which need no fertilising).
    This will demonstrate to clients the area that can be covered if they are
    smart about their waste and use it as valuable soil enriching nutrients.
    The constructed buffer can show clearly the area that can be covered, and
    account for different land uses around the area.  This tool will not,
    however, account for slope variation.  This may be an extension for this
    tool in the future.
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
        Returns the algorithm name, used for identifying the algorithm.
        """
        return 'broilernetworkbuffer'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Broiler Network Buffer')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr("This tool calculates the area of land (minus roads and rivers) that can be covered with certain volumes of waste products from a broiler farm.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It must be a point layer.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Select layer with central point for process'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        # We add the hydrology data source. It must be a linear network.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.HYDRO,
                self.tr('Select data source for hydro network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        # We add the transport data source. It must be a linear network.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROAD,
                self.tr('Select data source for road network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        # We specify the mass of broiler waste available at the central waste.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MASS,
                self.tr('Input mass of broiler waste (in tonnes)'),
            )
        )
        
        # We specify the compound being calculated.
        self.addParameter(
            QgsProcessingParameterEnum(
                self.COMPOUND,
                self.tr('Select compound to be calculated'),
                ['Nitrogen','Phosphorus','Potassium']
            )
        )
        
        # We specify how many iterations we want to run of this process.
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATIONS,
                self.tr('Input desired number of iterations'),
            )
        )
        
        # We add a feature sink in which to store our processed feature.
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

        # Retrieve the feature sources and other parameter values.
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

        # If source was not found, throw an exception to indicate that the algorithm encountered a fatal error.
        if pointFile is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        # Specify information about the output layer.
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            pointFile.fields(),
            3,
            pointFile.sourceCrs()
        )

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

        # Define parameters for Road buffer
        roadBuffParameters = {
        'INPUT' : parameters[self.ROAD],
        'DISTANCE' : 40,
        'DISSOLVE' : True,
        'OUTPUT' : 'memory:'
        }
        # Run Road buffer process
        roadBuffer = processing.run('native:buffer', roadBuffParameters)

        # Define parameters for Merge process
        mergeParameters = {
        'LAYERS' : [hydroBuffer["OUTPUT"], roadBuffer["OUTPUT"]],
        'OUTPUT' : 'memory:'
        }
        # Run Merge process
        mergeBuffer = processing.run('qgis:mergevectorlayers', mergeParameters)

        # Define parameters for Dissolve process
        dissolveParameters = {
        'INPUT' : mergeBuffer["OUTPUT"],
        'OUTPUT' : 'memory:'
        }
        # Run Dissolve process
        dissolveBuffer = processing.run('qgis:dissolve', dissolveParameters)

        # Establish reference lists for loop
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

        # This step runs iterations of the buffer process and clip.
        # It calculates the area of the networks covered by the buffer and adds it to the waste buffer.
        # This is an iterative process.  More iterations get closer to the 'true' value.
        for count in range (1, iterations + 1):
            # Define parameters for Clip
            parametersClip = {
            'INPUT' : dissolveBuffer["OUTPUT"],
            'OVERLAY' : listBuff[count - 1]["OUTPUT"],
            'OUTPUT' : 'memory:'
            }
            # Run Clip process
            listClip.append(processing.run('qgis:clip', parametersClip))

            # Create list of Clip features
            featuresClip = listClip[count]["OUTPUT"].getFeatures()
            # Iterate through features
            for feature in featuresClip:
                # Determine feature area covered by clipped network buffer
                listAreaClip.append(feature.geometry().area())

            # Calculate Buffer area
            listAreaBuff.append(listAreaBuff[count - 1] + (listAreaClip[count] - listAreaClip[count - 1]))
            # Calculate Buffer distance
            listDistBuff.append(math.sqrt(listAreaBuff[count] / math.pi))

            # Define parameters for Buffer
            parametersBuffer = {
            'INPUT' : parameters[self.INPUT],
            'DISTANCE' : listDistBuff[count],
            'SEGMENTS' : 10,
            'OUTPUT' : 'memory:'
            }
            # Run Buffer process
            listBuff.append(processing.run('native:buffer', parametersBuffer))

        # Read the Buffer layer and create output features
        for feature in listBuff[iterations]["OUTPUT"].getFeatures():
            new_feature =  QgsFeature()
            # Set geometry to Buffer geometry
            new_feature.setGeometry(feature.geometry())
            # Set Id so feature can be indexed in Shapefile
            new_feature.setAttributes(["Id", 0])
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

        # Calculate area increase
        areaIncrease = listAreaBuff[iterations] - listAreaBuff[0]
        # Calculate percent increase
        pcIncrease = ((listAreaBuff[iterations] / listAreaBuff[0]) - 1) * 100
        
        # Print area of final Buffer
        feedback.pushInfo(f'{parameters[self.MASS]}t of broiler waste contains {int(round(massCompound / 1000))}t of fertiliser, which covers {int(round(listAreaBuff[iterations] / 10000))} Ha')
        # Print area that has been added through this process
        feedback.pushInfo(f'Process increases area covered by {int(round(areaIncrease / 10000))} Ha')
        # Print percent increase process has provided
        feedback.pushInfo(f'This is {round(pcIncrease)}% larger than original area')

        # Return final Buffer as ouput layer
        return {self.OUTPUT: dest_id}