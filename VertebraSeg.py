class VertebraSeg(SegmentEditorThresholdEffect):

  #Load master volume
sampleDataLogic = SampleData.SampleDataLogic()
masterVolumeNode = sampleDataLogic.downloadCTACardio() ##slicer.mrmlScene

  delayDisplay("Please mark a point on each of the five lumbar")

  for x in range(2):
#x=0
  print('Next Point in Loop')
  print(x)
  fidList = slicer.util.getNode('F')    
  segmentationNode = slicer.vtkMRMLSegmentationNode()
  segmentationNode.SetName('VertebraL' + str(x+1))
  slicer.mrmlScene.AddNode(segmentationNode)
  segmentationNode.CreateDefaultDisplayNodes() # only needed for display
  segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
  fidRAS = [0,0,0]
  fidList.GetNthFiducialPosition(x, fidRAS)
  print('The new RAS point is: ')
  print(fidRAS)
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
  segmentationNode.AddSegmentFromClosedSurfaceRepresentation(lumbarSeed.GetOutput(), "Lumbar-" + str(x+1), [random(), random(), random()], str(x+1))
  segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
  segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
  segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
  slicer.mrmlScene.AddNode(segmentEditorNode)
  segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
  segmentEditorWidget.setSegmentationNode(segmentationNode)
  segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
  segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
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

  ##this segment editor widget enables the user to access the list of segment extra effects editor questions
