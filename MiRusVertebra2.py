import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from random import random



class MiRusVertebra2(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MiRus Vertebra Segmentation TM"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Ishan & Kargil: MiRus LLC"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
Please mark fiducial points on the vertebrae you wish to segment. Then click 'Reload' and finally click 'Segment'.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This was created by MiRus LLC (Ishan & Kargil). Special thanks to Kyle Sunderland and the 3D Slicer Community for the extension.
"""

    # Additional initialization step after application startup is complete
    slicer.app.connect("startupCompleted()", registerSampleData)

#
# Register sample data sets in Sample Data module
#

def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname('CTA-cardio.nrrd'), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # scriptedmodule11
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='scriptedmodule1',
    sampleName='scriptedmodule11',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'scriptedmodule11.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='scriptedmodule11.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='scriptedmodule11'
  )

  # scriptedmodule12
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='scriptedmodule1',
    sampleName='scriptedmodule12',
    thumbnailFileName=os.path.join(iconsPath, 'scriptedmodule12.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='scriptedmodule12.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='scriptedmodule12'
  )

#
# scriptedmodule1Widget
#

class MiRusVertebra2Widget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    self.applyButton = qt.QPushButton('Segment')
    self.layout.addWidget(self.applyButton)


    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    #self.logic = scriptedmodule1Logic()

    # Connections

    # Buttons
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Make sure parameter node is initialized (needed for module reload)

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """

    saigttalCoronal = ("<layout type=\"horizontal\"><item><view class=\"vtkMRMLSliceNode\" singletontag=\"Yellow\"><property name=\"orientation\" action=\"default\">Sagittal</property><property name=\"viewlabel\" action=\"default\">Y</property><property name=\"viewcolor\" action=\"default\">#EDD54C</property></view></item><item><view class=\"vtkMRMLSliceNode\" singletontag=\"Green\"><property name=\"orientation\" action=\"default\">Coronal</property><property name=\"viewlabel\" action=\"default\">G</property><property name=\"viewcolor\" action=\"default\">#6EB04B</property></view></item></layout></item></layout>")


    layoutLogic = slicer.app.layoutManager().layoutLogic()

    layoutLogic.GetLayoutNode().AddLayoutDescription(587, saigttalCoronal)

    slicer.app.layoutManager().setLayout(587)

    

    #customLayoutID = 501
    #layoutManager = slicer.app.layoutManager()
    #layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(501, sideBySideView)             
    #layoutManager.setLayout(501)                            

    #layoutManager = slicer.app.layoutManager()
    #layoutManager.setLayout(29)

    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore

    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference("InputVolume"):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
    self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
    self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
      self.ui.applyButton.toolTip = "Compute output volume"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input and output volume nodes"
      self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
    self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
    self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
    self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)

  def onApplyButton(self):

    """
    Run processing when user clicks "Apply" button.
    """
    import SampleData
    masterVolumeNode = SampleData.SampleDataLogic().downloadCTACardio() #slicer.vtkMRMLSegmentEditorNode().GetMasterVolumeNode()

    layoutManager = slicer.app.layoutManager()
    

    from random import random
    
    lenVar = slicer.util.getNode('F')
    length = lenVar.GetNumberOfFiducials()

    
    for x in range(length):
      fidList = slicer.util.getNode('F')    
      segmentationNode = slicer.vtkMRMLSegmentationNode()
      segmentationNode.SetName('VertebraL' + str(x+1))
      slicer.mrmlScene.AddNode(segmentationNode)
      segmentationNode.CreateDefaultDisplayNodes() # only needed for display
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
      fidRAS = [0,0,0]
      fidList.GetNthFiducialPosition(x, fidRAS)
      volumeID = fidList.GetNthFiducialAssociatedNodeID(x)
      volumeNode = slicer.mrmlScene.GetNodeByID(volumeID)
      rasToIJK = vtk.vtkMatrix4x4()
      volumeNode.GetRASToIJKMatrix(rasToIJK)
      fidRAS4 = [fidRAS[0], fidRAS[1], fidRAS[2], 1.0]
      fidIJK = rasToIJK.MultiplyFloatPoint(fidRAS4)
      lumbarSeed = vtk.vtkSphereSource()
      lumbarSeed.SetCenter(fidRAS[0], fidRAS[1], fidRAS[2])
      lumbarSeed.SetRadius(5)
      lumbarSeed.Update()
      segmentationNode.AddSegmentFromClosedSurfaceRepresentation(lumbarSeed.GetOutput(), "Lumbar-" + str(x+1), [random(), random(), random()], str(x+1))
      slicer.util.selectModule('SegmentEditor')
      ##  segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
      segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
      slicer.mrmlScene.AddNode(segmentEditorNode)
      segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
      segmentEditorWidget.setSegmentationNode(segmentationNode)
      segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
      segmentEditorWidget.setActiveEffectByName("Local Threshold")
      effect = segmentEditorWidget.activeEffect() ##open segment editor tab
      print(effect)
      effect.setParameter("MinimumThreshold", "265")
      effect.setParameter("MaximumThreshold", "1009")
      effect.setParameter("MinimumDiameterMm", "9")
      effect.setParameter("SegmentationAlgorithm", "GrowCut")
      points = vtk.vtkPoints()
      points.InsertNextPoint(fidIJK[0:3])
      effect.self().apply(points)

      layoutManager.setLayout(1)

#
# scriptedmodule1Logic
#

class MiRusVertebra2Logic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputVolume, imageThreshold, fidList):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """
    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))

