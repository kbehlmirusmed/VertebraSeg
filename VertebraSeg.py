import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from SegmentEditorEffects import *
import vtkITK
import SimpleITK as sitk
import sitkUtils
import math
import vtkSegmentationCorePython as vtkSegmentationCore 
import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
import SampleData

#
# VertebraSeg
#

class VertebraSeg(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VertebraSeg" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["Kargil Behl and Ishan Sheth(MiRus LLC)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# VertebraSegWidget
#

class VertebraSegWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = VertebraSegLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)

#
# VertebraSegLogic
#

class VertebraSegLogic(ScriptedLoadableModuleLogic):
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

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False
    logging.info('Processing started')
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)
    if enableScreenshots:
      self.takeScreenshot('VertebraSegTest-Start','MyScreenshot',-1)
    logging.info('Processing completed')
    return True


class VertebraSeg(SegmentEditorThresholdEffect):

  # Load master volume
  sampleDataLogic = SampleData.SampleDataLogic()
  masterVolumeNode = sampleDataLogic.downloadCTACardio()

  ##gets the node coordinates to run the grow cut from later
  fidList = slicer.util.getNode('F')


  # Create segmentation
  segmentationNode = slicer.vtkMRMLSegmentationNode()
  slicer.mrmlScene.AddNode(segmentationNode)
  segmentationNode.CreateDefaultDisplayNodes() # only needed for display
  segmentationNode.name = 'Spine'
  segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)

  # Create seed segment inside lumbar and name
  fidList = slicer.util.getNode('F')
  fidRAS = [0,0,0]
  fidList.GetNthFiducialPosition(0, fidRAS)
  volumeID = fidList.GetNthFiducialAssociatedNodeID(0)
  volumeNode = slicer.mrmlScene.GetNodeByID(volumeID)
  rasToIJK = vtk.vtkMatrix4x4()
  volumeNode.GetRASToIJKMatrix(rasToIJK)
  fidRAS4 = [fidRAS[0], fidRAS[1], fidRAS[2], 1.0]
  fidIJK = rasToIJK.MultiplyFloatPoint(fidRAS4)


  lumbarSeed = vtk.vtkSphereSource()
  lumbarSeed.SetCenter(fidRAS[0], fidRAS[1], fidRAS[2])
  lumbarSeed.SetRadius(5)
  lumbarSeed.Update()
  segmentationNode.AddSegmentFromClosedSurfaceRepresentation(lumbarSeed.GetOutput(), "Lumbar", [1, 0, 0])

  segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
  segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
  segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
  slicer.mrmlScene.AddNode(segmentEditorNode)
  segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
  segmentEditorWidget.setSegmentationNode(segmentationNode)
  segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
  ######
  segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
  segmentEditorWidget.setActiveEffectByName("Local Threshold")
  effect = segmentEditorWidget.activeEffect()
  effect.setParameter("Minimum Threshold", 265)
  effect.setParameter("Maximum Threshold", 1009)

  effect.self().apply(fidIDK)

  ##this segment editor widget enables the user to access the list of segment extra effects editor questions
  

  
 ###################################################################################

def __init__(self, scriptedEffect):
  SegmentEditorThresholdEffect.__init__(self, scriptedEffect)
  scriptedEffect.name = 'Local Threshold'
  self.previewSteps = 4
  
def clone(self):
  import qSlicerSegmentationsEditorEffectsPythonQt as effects
  clonedEffect = effects.qSlicerSegmentEditorScriptedEffect(None)
  clonedEffect.setPythonSource(__file__.replace('\\','/'))
  return clonedEffect

def icon(self):
  iconPath = os.path.join(os.path.dirname(__file__), 'SegmentEditorEffect.png')
  if os.path.exists(iconPath):
    return qt.QIcon(iconPath)
  return qt.QIcon()

  def helpText(self):
    return """<html>
  Fill segment in a selected region based on master volume intensity range<br>.
  <p>
  <b>Ctrl + left-click:</b> Add the selected island within the threshold to the segment.
  </p>
  <p>
  Options:
  <ul style="feature: 0">
    <li><b>Minimum diameter:</b> Prevent leaks through features that are smaller than the specified size.</li>
    <li><b>Feature size:</b> Spatial smoothness constraint used for WaterShed. Larger values result in smoother extracted surface.</li>
    <li><b>Segmentation algorithm:</b> Algorithm used to perform the selection on the specified region.</li>
    <li><b>ROI:</b> Region of interest that the threshold segmentation will be perfomed within. Selecting a smaller region will reduce leaks and improve speed.</li>
  </ul>
  </p>
  </html>"""

  def setCurrentSegmentTransparent(self):
    pass

  def restorePreviewedSegmentTransparency(self):
    pass

  def preview(self):
    opacity = 0.1 + (0.8 * self.previewState / self.previewSteps)
    min = self.scriptedEffect.doubleParameter("MinimumThreshold")
    max = self.scriptedEffect.doubleParameter("MaximumThreshold")
    # Get color of edited segment
    segmentationNode = self.scriptedEffect.parameterSetNode().GetSegmentationNode()
    if not segmentationNode:
      # scene was closed while preview was active
      return
    displayNode = segmentationNode.GetDisplayNode()
    if displayNode is None:
      logging.error("preview: Invalid segmentation display node!")
      color = [0.5,0.5,0.5]
    segmentID = self.scriptedEffect.parameterSetNode().GetSelectedSegmentID()
    # Make sure we keep the currenty selected segment hidden (the user may have changed selection)
    if segmentID != self.previewedSegmentID:
      self.setCurrentSegmentTransparent()
    # Change color hue slightly to make it easier to distinguish filled regions from preview
    r,g,b = segmentationNode.GetSegmentation().GetSegment(segmentID).GetColor()
    import colorsys
    colorHsv = colorsys.rgb_to_hsv(r, g, b)
    (r, g, b) = colorsys.hsv_to_rgb((colorHsv[0]+0.2) % 1.0, colorHsv[1], colorHsv[2])
    # Set values to pipelines
    for sliceWidget in self.previewPipelines:
      pipeline = self.previewPipelines[sliceWidget]
      pipeline.lookupTable.SetTableValue(1,  r, g, b,  opacity)
      layerLogic = self.getMasterVolumeLayerLogic(sliceWidget)
      pipeline.thresholdFilter.SetInputConnection(layerLogic.GetReslice().GetOutputPort())
      pipeline.thresholdFilter.ThresholdBetween(min, max)
      pipeline.actor.VisibilityOn()
      sliceWidget.sliceView().scheduleRender()
    self.previewState += self.previewStep
    if self.previewState >= self.previewSteps:
      self.previewStep = -1
    if self.previewState <= 0:
      self.previewStep = 1

  def getMasterVolumeLayerLogic(self, sliceWidget): # TODO: This function is not a member of SegmentEditorThresholdEffect in 4.10.2, so it is duplicated here for now.
    masterVolumeNode = self.scriptedEffect.parameterSetNode().GetMasterVolumeNode()
    sliceLogic = sliceWidget.sliceLogic()
    backgroundLogic = sliceLogic.GetBackgroundLayer()
    backgroundVolumeNode = backgroundLogic.GetVolumeNode()
    if masterVolumeNode == backgroundVolumeNode:
      return backgroundLogic
    foregroundLogic = sliceLogic.GetForegroundLayer()
    foregroundVolumeNode = foregroundLogic.GetVolumeNode()
    if masterVolumeNode == foregroundVolumeNode:
      return foregroundLogic
    logging.warning("Master volume is not set as either the foreground or background")
    foregroundOpacity = 0.0
    if foregroundVolumeNode:
      compositeNode = sliceLogic.GetSliceCompositeNode()
      foregroundOpacity = compositeNode.GetForegroundOpacity()
    if foregroundOpacity > 0.5:
        return foregroundLogic
    return backgroundLogic

  def setupOptionsFrame(self):
    SegmentEditorThresholdEffect.setupOptionsFrame(self)
    # Hide threshold options
    self.applyButton.setHidden(True)
    self.useForPaintButton.setHidden(True)
    # Add diameter selector
    self.minimumDiameterSpinBox = slicer.qMRMLSpinBox()
    self.minimumDiameterSpinBox.setMRMLScene(slicer.mrmlScene)
    self.minimumDiameterSpinBox.quantity = "length"
    self.minimumDiameterSpinBox.value = 9.0
    self.minimumDiameterSpinBox.singleStep = 0.5
    self.minimumDiameterSpinBox.setToolTip("Minimum diameter of the structure. Regions that are connected to the selected point by a bridge"
      " that this is thinner than this size will be excluded to prevent unwanted leaks through small holes.")
    self.kernelSizePixel = qt.QLabel()
    self.kernelSizePixel.setToolTip("Minimum diameter of the structure in pixels. Computed from the segment's spacing and the specified feature size.")
    minimumDiameterFrame = qt.QHBoxLayout()
    minimumDiameterFrame.addWidget(self.minimumDiameterSpinBox)
    minimumDiameterFrame.addWidget(self.kernelSizePixel)
    self.minimumDiameterMmLabel = self.scriptedEffect.addLabeledOptionsWidget("Minimum diameter:", minimumDiameterFrame)
    self.scriptedEffect.addOptionsWidget(minimumDiameterFrame)
    # Add algorithm options
    self.segmentationAlgorithmSelector = qt.QComboBox()
    self.segmentationAlgorithmSelector.addItem(SEGMENTATION_ALGORITHM_MASKING)
    self.segmentationAlgorithmSelector.addItem(SEGMENTATION_ALGORITHM_GROWCUT)
    self.segmentationAlgorithmSelector.addItem(SEGMENTATION_ALGORITHM_WATERSHED)
    self.scriptedEffect.addLabeledOptionsWidget("Segmentation algorithm: ", self.segmentationAlgorithmSelector)
    # Add feature size selector
    self.featureSizeSpinBox = slicer.qMRMLSpinBox()
    self.featureSizeSpinBox.setMRMLScene(slicer.mrmlScene)
    self.featureSizeSpinBox.quantity = "length"
    self.featureSizeSpinBox.value = 3.0
    self.featureSizeSpinBox.singleStep = 0.5
    self.featureSizeSpinBox.setToolTip("Spatial smoothness constraint used for WaterShed. Larger values result in smoother extracted surface.")
    self.scriptedEffect.addLabeledOptionsWidget("Feature size: ", self.featureSizeSpinBox)
    # Add ROI options
    self.roiSelector = slicer.qMRMLNodeComboBox()
    self.roiSelector.nodeTypes = ['vtkMRMLAnnotationROINode']
    self.roiSelector.noneEnabled = True
    self.roiSelector.setMRMLScene(slicer.mrmlScene)
    self.scriptedEffect.addLabeledOptionsWidget("ROI: ", self.roiSelector)
    # Connections
    self.minimumDiameterSpinBox.connect("valueChanged(double)", self.updateMRMLFromGUI)
    self.featureSizeSpinBox.connect("valueChanged(double)", self.updateMRMLFromGUI)
    self.segmentationAlgorithmSelector.connect("currentIndexChanged(int)", self.updateMRMLFromGUI)

  def setMRMLDefaults(self):
    self.scriptedEffect.setParameterDefault(MINIMUM_DIAMETER_MM_PARAMETER_NAME, 9)
    self.scriptedEffect.setParameterDefault(FEATURE_SIZE_MM_PARAMETER_NAME, 3)
    self.scriptedEffect.setParameterDefault(SEGMENTATION_ALGORITHM_PARAMETER_NAME, SEGMENTATION_ALGORITHM_GROWCUT)
    if slicer.app.majorVersion >= 4 and slicer.app.minorVersion >= 11:
      self.scriptedEffect.setParameterDefault(HISTOGRAM_BRUSH_TYPE_PARAMETER_NAME, HISTOGRAM_BRUSH_TYPE_DRAW)
    SegmentEditorThresholdEffect.setMRMLDefaults(self)

  def updateGUIFromMRML(self):
    SegmentEditorThresholdEffect.updateGUIFromMRML(self)
    minimumDiameterMm = self.scriptedEffect.doubleParameter(MINIMUM_DIAMETER_MM_PARAMETER_NAME)
    wasBlocked = self.minimumDiameterSpinBox.blockSignals(True)
    self.minimumDiameterSpinBox.value = abs(minimumDiameterMm)
    self.minimumDiameterSpinBox.blockSignals(wasBlocked)
    featureSizeMm = self.scriptedEffect.doubleParameter(FEATURE_SIZE_MM_PARAMETER_NAME)
    wasBlocked = self.featureSizeSpinBox.blockSignals(True)
    self.featureSizeSpinBox.value = abs(featureSizeMm)
    self.featureSizeSpinBox.blockSignals(wasBlocked)
    # Only enable feature size selection for watershed method
    segmentationAlgorithm = self.scriptedEffect.parameter(SEGMENTATION_ALGORITHM_PARAMETER_NAME)
    self.featureSizeSpinBox.enabled = (segmentationAlgorithm == SEGMENTATION_ALGORITHM_WATERSHED)
    segmentationAlgorithm = self.scriptedEffect.parameter(SEGMENTATION_ALGORITHM_PARAMETER_NAME)
    wasBlocked = self.segmentationAlgorithmSelector.blockSignals(True)
    self.segmentationAlgorithmSelector.setCurrentText(segmentationAlgorithm)
    self.segmentationAlgorithmSelector.blockSignals(wasBlocked)
    kernelSizePixel = self.getKernelSizePixel()
    if kernelSizePixel[0]<=0 and kernelSizePixel[1]<=0 and kernelSizePixel[2]<=0:
      self.kernelSizePixel.text = "feature too small"
      self.applyButton.setEnabled(False)
    else:
      self.kernelSizePixel.text = "{0}x{1}x{2} pixels".format(abs(kernelSizePixel[0]), abs(kernelSizePixel[1]), abs(kernelSizePixel[2]))
      self.applyButton.setEnabled(True)


  def updateMRMLFromGUI(self):
    SegmentEditorThresholdEffect.updateMRMLFromGUI(self)
    minimumDiameterMm = self.minimumDiameterSpinBox.value
    self.scriptedEffect.setParameter(MINIMUM_DIAMETER_MM_PARAMETER_NAME, minimumDiameterMm)
    featureSizeMm = self.featureSizeSpinBox.value
    self.scriptedEffect.setParameter(FEATURE_SIZE_MM_PARAMETER_NAME, featureSizeMm)
    segmentationAlgorithm = self.segmentationAlgorithmSelector.currentText
    self.scriptedEffect.setParameter(SEGMENTATION_ALGORITHM_PARAMETER_NAME, segmentationAlgorithm)

  def processInteractionEvents(self, callerInteractor, eventId, viewWidget):
    abortEvent = False
    if not callerInteractor.GetControlKey():
      return SegmentEditorThresholdEffect.processInteractionEvents(self, callerInteractor, eventId, viewWidget)
    if eventId == vtk.vtkCommand.LeftButtonPressEvent:
      abortEvent = True
      masterImageData = self.scriptedEffect.masterVolumeImageData()
      xy = callerInteractor.GetEventPosition()
      ijk = self.xyToIjk(xy, viewWidget, masterImageData)
      ijkPoints = vtk.vtkPoints()
      ijkPoints.InsertNextPoint(world[0], world[1], world[2])
      self.apply(ijkPoints)
    return abortEvent

  def runGrowCut(self, masterImageData, seedLabelmap, outputLabelmap):
    self.clippedMaskImageData = slicer.vtkOrientedImageData()
    intensityBasedMasking = self.scriptedEffect.parameterSetNode().GetMasterVolumeIntensityMask()
    segmentationNode = self.scriptedEffect.parameterSetNode().GetSegmentationNode()
    success = segmentationNode.GenerateEditMask(self.clippedMaskImageData,
      self.scriptedEffect.parameterSetNode().GetMaskMode(),
      masterImageData, # reference geometry
      "", # edited segment ID
      self.scriptedEffect.parameterSetNode().GetMaskSegmentID() if self.scriptedEffect.parameterSetNode().GetMaskSegmentID() else "",
      masterImageData if intensityBasedMasking else None,
      self.scriptedEffect.parameterSetNode().GetMasterVolumeIntensityMaskRange() if intensityBasedMasking else None)
    import vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic
    self.growCutFilter = vtkSlicerSegmentationsModuleLogic.vtkImageGrowCutSegment()
    self.growCutFilter.SetIntensityVolume(masterImageData)
    self.growCutFilter.SetSeedLabelVolume(seedLabelmap)
    self.growCutFilter.SetMaskVolume(self.clippedMaskImageData)
    self.growCutFilter.Update()
    outputLabelmap.ShallowCopy(self.growCutFilter.GetOutput())

  def apply(self, ijkPoints):
    kernelSizePixel = self.getKernelSizePixel()
    if kernelSizePixel[0]<=0 and kernelSizePixel[1]<=0 and kernelSizePixel[2]<=0:
      return
    qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
    # Get parameter set node
    parameterSetNode = self.scriptedEffect.parameterSetNode()
    # Get parameters
    minimumThreshold = self.scriptedEffect.doubleParameter("MinimumThreshold")
    maximumThreshold = self.scriptedEffect.doubleParameter("MaximumThreshold")
    # Get modifier labelmap
    modifierLabelmap = self.scriptedEffect.defaultModifierLabelmap()
    # Get master volume image data
    masterImageData = self.scriptedEffect.masterVolumeImageData()
    # Set intensity range
    oldMasterVolumeIntensityMask = parameterSetNode.GetMasterVolumeIntensityMask()
    parameterSetNode.MasterVolumeIntensityMaskOn()
    oldIntensityMaskRange = parameterSetNode.GetMasterVolumeIntensityMaskRange()
    intensityRange = [minimumThreshold, maximumThreshold]
    if oldMasterVolumeIntensityMask:
      intensityRange = [max(oldIntensityMaskRange[0], minimumThreshold), min(oldIntensityMaskRange[1], maximumThreshold)]
    parameterSetNode.SetMasterVolumeIntensityMaskRange(intensityRange)
    roiNode = self.roiSelector.currentNode()
    clippedMasterImageData = masterImageData
    if roiNode is not None:
      worldToImageMatrix = vtk.vtkMatrix4x4()
      masterImageData.GetWorldToImageMatrix(worldToImageMatrix)
      bounds = [0,0,0,0,0,0]
      roiNode.GetRASBounds(bounds)
      corner1RAS = [bounds[0], bounds[2], bounds[4], 1]
      corner1IJK = [0, 0, 0, 0]
      worldToImageMatrix.MultiplyPoint(corner1RAS, corner1IJK)
      corner2RAS = [bounds[1], bounds[3], bounds[5], 1]
      corner2IJK = [0, 0, 0, 0]
      worldToImageMatrix.MultiplyPoint(corner2RAS, corner2IJK)
      extent = [0, -1, 0, -1, 0, -1]
      for i in range(3):
          lowerPoint = min(corner1IJK[i], corner2IJK[i])
          upperPoint = max(corner1IJK[i], corner2IJK[i])
          extent[2*i] = int(math.floor(lowerPoint))
          extent[2*i+1] = int(math.ceil(upperPoint))
      imageToWorldMatrix = vtk.vtkMatrix4x4()
      masterImageData.GetImageToWorldMatrix(imageToWorldMatrix)
      clippedMasterImageData = slicer.vtkOrientedImageData()
      self.padder = vtk.vtkImageConstantPad()
      self.padder.SetInputData(masterImageData)
      self.padder.SetOutputWholeExtent(extent)
      self.padder.Update()
      clippedMasterImageData.ShallowCopy(self.padder.GetOutput())
      clippedMasterImageData.SetImageToWorldMatrix(imageToWorldMatrix)
    # Pipeline
    self.thresh = vtk.vtkImageThreshold()
    self.thresh.SetInValue(LABEL_VALUE)
    self.thresh.SetOutValue(BACKGROUND_VALUE)
    self.thresh.SetInputData(clippedMasterImageData)
    self.thresh.ThresholdBetween(minimumThreshold, maximumThreshold)
    self.thresh.SetOutputScalarTypeToUnsignedChar()
    self.thresh.Update()
    self.erode = vtk.vtkImageDilateErode3D()
    self.erode.SetInputConnection(self.thresh.GetOutputPort())
    self.erode.SetDilateValue(BACKGROUND_VALUE)
    self.erode.SetErodeValue(LABEL_VALUE)
    self.erode.SetKernelSize(
      kernelSizePixel[0],
      kernelSizePixel[1],
      kernelSizePixel[2])
    self.erodeCast = vtk.vtkImageCast()
    self.erodeCast.SetInputConnection(self.erode.GetOutputPort())
    self.erodeCast.SetOutputScalarTypeToUnsignedInt()
    self.erodeCast.Update()
    # Remove small islands
    self.islandMath = vtkITK.vtkITKIslandMath()
    self.islandMath.SetInputConnection(self.erodeCast.GetOutputPort())
    self.islandMath.SetFullyConnected(False)
    self.islandMath.SetMinimumSize(125)  # remove regions smaller than 5x5x5 voxels
    self.islandThreshold = vtk.vtkImageThreshold()
    self.islandThreshold.SetInputConnection(self.islandMath.GetOutputPort())
    self.islandThreshold.ThresholdByLower(BACKGROUND_VALUE)
    self.islandThreshold.SetInValue(BACKGROUND_VALUE)
    self.islandThreshold.SetOutValue(LABEL_VALUE)
    self.islandThreshold.SetOutputScalarTypeToUnsignedChar()
    self.islandThreshold.Update()
    # Points may be outside the region after it is eroded.
    # Snap the points to LABEL_VALUE voxels,
    snappedIJKPoints = self.snapIJKPointsToLabel(ijkPoints, self.islandThreshold.GetOutput())
    if snappedIJKPoints.GetNumberOfPoints() == 0:
      qt.QApplication.restoreOverrideCursor()
      return
    # Convert points to real data coordinates. Required for vtkImageThresholdConnectivity.
    seedPoints = vtk.vtkPoints()
    origin = masterImageData.GetOrigin()
    spacing = masterImageData.GetSpacing()
    for i in range(snappedIJKPoints.GetNumberOfPoints()):
      ijkPoint = snappedIJKPoints.GetPoint(i)
      seedPoints.InsertNextPoint(
        origin[0]+ijkPoint[0]*spacing[0],
        origin[1]+ijkPoint[1]*spacing[1],
        origin[2]+ijkPoint[2]*spacing[2])
    segmentationAlgorithm = self.scriptedEffect.parameter(SEGMENTATION_ALGORITHM_PARAMETER_NAME)
    if segmentationAlgorithm == SEGMENTATION_ALGORITHM_MASKING:
      self.runMasking(seedPoints, self.islandThreshold.GetOutput(), modifierLabelmap)
    else:
      self.floodFillingFilterIsland = vtk.vtkImageThresholdConnectivity()
      self.floodFillingFilterIsland.SetInputConnection(self.islandThreshold.GetOutputPort())
      self.floodFillingFilterIsland.SetInValue(SELECTED_ISLAND_VALUE)
      self.floodFillingFilterIsland.ReplaceInOn()
      self.floodFillingFilterIsland.ReplaceOutOff()
      self.floodFillingFilterIsland.ThresholdBetween(LABEL_VALUE, LABEL_VALUE)
      self.floodFillingFilterIsland.SetSeedPoints(seedPoints)
      self.floodFillingFilterIsland.Update()
      self.maskCast = vtk.vtkImageCast()
      self.maskCast.SetInputData(self.thresh.GetOutput())
      self.maskCast.SetOutputScalarTypeToUnsignedChar()
      self.maskCast.Update()
      self.imageMask = vtk.vtkImageMask()
      self.imageMask.SetInputConnection(self.floodFillingFilterIsland.GetOutputPort())
      self.imageMask.SetMaskedOutputValue(OUTSIDE_THRESHOLD_VALUE)
      self.imageMask.SetMaskInputData(self.maskCast.GetOutput())
      self.imageMask.Update()
      imageMaskOutput = slicer.vtkOrientedImageData()
      imageMaskOutput.ShallowCopy(self.imageMask.GetOutput())
      imageMaskOutput.CopyDirections(clippedMasterImageData)
      imageToWorldMatrix = vtk.vtkMatrix4x4()
      imageMaskOutput.GetImageToWorldMatrix(imageToWorldMatrix)
      segmentOutputLabelmap = slicer.vtkOrientedImageData()
      if segmentationAlgorithm == SEGMENTATION_ALGORITHM_GROWCUT:
        self.runGrowCut(clippedMasterImageData, imageMaskOutput, segmentOutputLabelmap)
      elif segmentationAlgorithm == SEGMENTATION_ALGORITHM_WATERSHED:
        self.runWatershed(clippedMasterImageData, imageMaskOutput, segmentOutputLabelmap)
      else:
        logging.error("Unknown segmentation algorithm: \"" + segmentationAlgorithm + "\"")
      segmentOutputLabelmap.SetImageToWorldMatrix(imageToWorldMatrix)
      self.selectedSegmentThreshold = vtk.vtkImageThreshold()
      self.selectedSegmentThreshold.SetInputData(segmentOutputLabelmap)
      self.selectedSegmentThreshold.ThresholdBetween(SELECTED_ISLAND_VALUE, SELECTED_ISLAND_VALUE)
      self.selectedSegmentThreshold.SetInValue(LABEL_VALUE)
      self.selectedSegmentThreshold.SetOutValue(BACKGROUND_VALUE)
      self.selectedSegmentThreshold.SetOutputScalarType(modifierLabelmap.GetScalarType())
      self.selectedSegmentThreshold.Update()
      modifierLabelmap.ShallowCopy(self.selectedSegmentThreshold.GetOutput())
    self.scriptedEffect.saveStateForUndo()
    self.scriptedEffect.modifySelectedSegmentByLabelmap(modifierLabelmap, slicer.qSlicerSegmentEditorAbstractEffect.ModificationModeAdd)
    parameterSetNode.SetMasterVolumeIntensityMask(oldMasterVolumeIntensityMask)
    parameterSetNode.SetMasterVolumeIntensityMaskRange(oldIntensityMaskRange)
    qt.QApplication.restoreOverrideCursor()

  def snapIJKPointsToLabel(self, ijkPoints, labelmap):
    import math
    snapIJKPoints = vtk.vtkPoints()
    kernelSize = self.getKernelSizePixel()
    kernelOffset = [0,0,0]
    labelmapExtent = labelmap.GetExtent()
    for i in range(len(kernelOffset)):
      kernelOffset[i] = int(math.ceil(kernelSize[i]-1)/2)
    for pointIndex in range(ijkPoints.GetNumberOfPoints()):
      point = ijkPoints.GetPoint(pointIndex)
      closestDistance = vtk.VTK_INT_MAX
      closestPoint = None
      # Try to find the closest point to the original within the kernel
      # If more IJK points are used in the future, this could be made faster
      for kOffset in range(-kernelOffset[2], kernelOffset[2]+1):
        k = int(point[2] + kOffset)
        for jOffset in range(-kernelOffset[1], kernelOffset[1]+1):
          j = int(point[1] + jOffset)
          for iOffset in range(-kernelOffset[0], kernelOffset[0]+1):
            i = int(point[0] + iOffset)

            if (labelmapExtent[0] > i or labelmapExtent[1] < i or
                labelmapExtent[2] > j or labelmapExtent[3] < j or
                labelmapExtent[4] > k or labelmapExtent[5] < k):
              continue # Voxel not in image
            value = labelmap.GetScalarComponentAsFloat(i, j, k, 0)
            if value <= 0:
              continue # Label is empty

            offsetPoint = [i, j, k]
            distance = vtk.vtkMath.Distance2BetweenPoints(point, offsetPoint)
            if distance >= closestDistance:
              continue
            closestPoint = offsetPoint
            closestDistance = distance
        if closestPoint is None:
          continue
        snapIJKPoints.InsertNextPoint(closestPoint[0], closestPoint[1], closestPoint[2])
      return snapIJKPoints


  def getKernelSizePixel(self):
    selectedSegmentLabelmapSpacing = [1.0, 1.0, 1.0]
    selectedSegmentLabelmap = self.scriptedEffect.selectedSegmentLabelmap()
    if selectedSegmentLabelmap:
      selectedSegmentLabelmapSpacing = selectedSegmentLabelmap.GetSpacing()

    # size rounded to nearest odd number. If kernel size is even then image gets shifted.
    minimumDiameterMm = abs(self.scriptedEffect.doubleParameter(MINIMUM_DIAMETER_MM_PARAMETER_NAME))
    kernelSizePixel = [int(round((minimumDiameterMm / selectedSegmentLabelmapSpacing[componentIndex]+1)/2)*2-1) for componentIndex in range(3)]
    return kernelSizePixel
   
    
class VertebraSegTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VertebraSeg1()

  def test_VertebraSeg1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
##    SampleData.downloadFromURL(
##      nodeNames='FA',
##      fileNames='FA.nrrd',
##      uris='http://slicer.kitware.com/midas3/download?items=5767')
##    self.delayDisplay('Finished with download and loading')
    effect.self().apply(ijkPoints)
    volumeNode = slicer.util.getNode("CTACardio_1")
    logic = VertebraSegLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

  
