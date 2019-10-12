#!/usr/bin/env python

import pymel.core as pm
import pymel.core.datatypes as dt
import random
import os


import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from Qt.Core import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

windowName = "Kelebek Path Helper"

def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

class KelebekHelper(object):
    def __init__(self):
        super(KelebekHelper, self).__init__()
        self.infinityDict = {"Constant":0, "Linear":1, "Cycle":3, "Cycle with Offset":4, "Oscillate":5}
        self.seperation = 1
        self.randomRadiusX = 5
        self.randomRadiusY = 5
        self.randomRadiusZ = 5
        self.postInfinity = "Linear"
        self.preInfinity = "Linear"
        self.follow = True
        self.parametriclength = True
        self.count = 20
        self.referencePath = "M:\\Projects\\Kelebek_logoKelebekler_DEPO_191003\\scenes\\Rig\\test\\test_Rig_forReference.mb"
        self.controllerName = "cont_circle1"
        pass

    def attachToPath(self):

        try:curveTransform = pm.ls(sl=True)[0]
        except IndexError:
            pm.displayWarning("Nothing selected. Select the path curve")
            return
        curveShape = curveTransform.getShape()
        if (pm.nodeType(curveShape) != "nurbsCurve"):
            pm.displayWarning("Selection must be a nurbs curve.")

        if not pm.attributeQuery("drive", node=curveTransform, exists=True):
            pm.addAttr(curveTransform, shortName="drive", longName="drive", defaultValue=0, at="float", k=True)

        # get namespace
        refFileBasename = os.path.split(self.referencePath)[1]
        namespace = os.path.splitext(refFileBasename)[0]

        for i in range(self.count):
            n = (pm.createReference(self.referencePath, namespace=namespace))
            controller = pm.PyNode("{0}:{1}".format(n.fullNamespace, self.controllerName))
            # print controller

            # ---------------------------
            # Keyframe the loop animation
            # ---------------------------

            # get first and last frames of the timeslider range

            # key the loop animation

            # ----------------------------

            locator = pm.spaceLocator(name="loc_%s_%s" % (n.fullNamespace, i))
            r = pm.pathAnimation(locator,
                                 stu=i*self.seperation,
                                 etu=self.count + i*self.seperation,
                                 follow=self.follow,
                                 fractionMode=self.parametriclength, c=curveTransform,
                                 upAxis="Y",
                                 followAxis="Z",
                                 inverseFront=True,
                                 )


            rRel = pm.listConnections(r, t="animCurveTL")[0]
            pm.setAttr(rRel.postInfinity, self.infinityDict[self.postInfinity])
            pm.setAttr(rRel.preInfinity, self.infinityDict[self.preInfinity])
            pm.keyTangent(rRel, itt='linear', ott='linear')
            pm.connectAttr("%s.%s" % (curveTransform, "drive"), rRel.input)

            # ------------------
            # positioning
            # ------------------
            self.alignTo(controller.getParent(), locator, mode=2)
            pm.parentConstraint(locator, controller.getParent(), mo=False)
            pm.setAttr(controller.tx, (random.random()-0.5) * self.randomRadiusX)
            pm.setAttr(controller.ty, (random.random()-0.5) * self.randomRadiusY)
            pm.setAttr(controller.tz, (random.random()-0.5) * self.randomRadiusZ)
            # pm.parent(controller, locator)

    def alignTo(self, sourceObj=None, targetObj=None, mode=0, sl=False, o=(0, 0, 0)):
        offset = dt.Vector(o)
        if sl == True:
            selection = pm.ls(sl=True)
            if not len(selection) == 2:
                pm.error("select exactly 2 objects")
                return
            sourceObj = selection[0]
            targetObj = selection[1]
        if not sourceObj or not targetObj:
            pm.error("No source and/or target object defined")
            return
        if mode == 0:
            targetTranslation = pm.xform(targetObj, query=True, worldSpace=True, translation=True)
            pm.xform(sourceObj, worldSpace=True, translation=targetTranslation)
        if mode == 1:
            targetRotation = pm.xform(targetObj, query=True, worldSpace=True, rotation=True)
            pm.xform(sourceObj, worldSpace=True, rotation=targetRotation + offset)
        if mode == 2:
            targetMatrix = pm.xform(targetObj, query=True, worldSpace=True, matrix=True)
            pm.xform(sourceObj, worldSpace=True, matrix=targetMatrix)

    def moveKeys(self, value):
        selection = pm.ls(sl=True)
        for x in selection:
            if x.name().endswith(self.controllerName):
                mPath = self._getMotionPath(x.getParent()) # parent node of the controller is connected to motion path
                pm.keyframe(mPath, r=True, tc=value)

    def speedChange(self, value):
        selection = pm.ls(sl=True)
        for x in selection:
            if x.name().endswith(self.controllerName):
                mPath = self._getMotionPath(x.getParent()) # parent node of the controller is connected to motion path
                pm.keyframe(mPath, r=True, index=0, vc=value*-1)
                pm.keyframe(mPath, r=True, index=1, vc=value)

    def _getMotionPath(self, node):
        for x in pm.listHistory(node):
            if (pm.nodeType(x)) == "motionPath":
                return x
        return None

    def selectMotionPath(self):
        selection = pm.ls(sl=True)
        mList = [self._getMotionPath(x.getParent()) for x in selection]
        pm.select(mList)



class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == windowName:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        #initialize logic class
        self.kelebekHelper = KelebekHelper()

        #variables
        self.lastPosition = 0
        self.lastSpeed = 0

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.resize(230, 400)
        self.buildUI()

    def buildUI(self):
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.verticalLayout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText("Position")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label)

        self.position_dial = QtWidgets.QDial(self)
        self.position_dial.setMaximum(99)
        self.position_dial.setPageStep(1)
        self.position_dial.setTracking(True)
        self.position_dial.setInvertedAppearance(False)
        self.position_dial.setInvertedControls(False)
        self.position_dial.setWrapping(True)
        self.position_dial.setNotchesVisible(False)
        self.verticalLayout.addWidget(self.position_dial)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setFont(font)
        self.label_2.setText("Speed")
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout_2.addWidget(self.label_2)

        self.speed_dial = QtWidgets.QDial(self)
        self.speed_dial.setMaximum(99)
        self.speed_dial.setPageStep(1)
        self.speed_dial.setTracking(True)
        self.speed_dial.setInvertedAppearance(False)
        self.speed_dial.setInvertedControls(False)
        self.speed_dial.setWrapping(True)
        self.speed_dial.setNotchesVisible(False)
        self.verticalLayout_2.addWidget(self.speed_dial)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.multiplier_dSpn = QtWidgets.QDoubleSpinBox(self)
        self.multiplier_dSpn.setValue(1.0)
        self.verticalLayout_3.addWidget(self.multiplier_dSpn)

        self.selectMotionPath_pb = QtWidgets.QPushButton(self)
        self.selectMotionPath_pb.setText("Select Motion Path")
        self.verticalLayout_3.addWidget(self.selectMotionPath_pb)

        self.line = QtWidgets.QFrame(self)
        self.line.setLineWidth(5)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_3.addWidget(self.line)

        self.groupBox = QtWidgets.QGroupBox(self)

        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox)
        self.formLayout = QtWidgets.QFormLayout()

        self.count_lb = QtWidgets.QLabel(self.groupBox, text="Count:")
        self.count_spn = QtWidgets.QSpinBox(self.groupBox)
        self.count_spn.setMaximumSize(QtCore.QSize(50, 16777215))
        self.count_spn.setProperty("value", 20)
        self.formLayout.addRow(self.count_lb, self.count_spn)

        self.seperation_lb = QtWidgets.QLabel(self.groupBox, text="Seperation:")
        self.seperation_dSpn = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.seperation_dSpn.setMaximumSize(QtCore.QSize(50, 16777215))
        self.seperation_dSpn.setValue(1.0)
        self.formLayout.addRow(self.seperation_lb, self.seperation_dSpn)

        self.randX_lb = QtWidgets.QLabel(self.groupBox, text="Random Position X:")
        self.randX_dSpn = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.randX_dSpn.setMaximumSize(QtCore.QSize(50, 16777215))
        self.randX_dSpn.setValue(5.0)
        self.formLayout.addRow(self.randX_lb, self.randX_dSpn)

        self.randY_lb = QtWidgets.QLabel(self.groupBox, text="Random Position Y:")
        self.randY_dSpn = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.randY_dSpn.setMaximumSize(QtCore.QSize(50, 16777215))
        self.randY_dSpn.setValue(5.0)
        self.formLayout.addRow(self.randY_lb, self.randY_dSpn)

        self.randZ_lb = QtWidgets.QLabel(self.groupBox, text="Random Position Z:")
        self.randZ_dSpn = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.randZ_dSpn.setMaximumSize(QtCore.QSize(50, 16777215))
        self.randZ_dSpn.setValue(5.0)
        self.formLayout.addRow(self.randZ_lb, self.randZ_dSpn)

        self.verticalLayout_4.addLayout(self.formLayout)

        self.attachToPath_pb = QtWidgets.QPushButton(self.groupBox, text="Attach to path")
        self.verticalLayout_4.addWidget(self.attachToPath_pb)
        self.verticalLayout_3.addWidget(self.groupBox)


        # self.attach_pb = QtWidgets.QPushButton(self)
        # self.attach_pb.setText("")

        self.position_dial.valueChanged.connect(self.onSlidePosition)
        self.speed_dial.valueChanged.connect(self.onSlideSpeed)
        self.attachToPath_pb.clicked.connect(self.onAttachToPath)
        self.selectMotionPath_pb.clicked.connect(self.kelebekHelper.selectMotionPath)

        # layout = QtWidgets.QVBoxLayout(self)

    def onSlidePosition(self):
        currentPosition = self.position_dial.value()
        mult = self.multiplier_dSpn.value()
        val=0
        if self.lastPosition > currentPosition and currentPosition != 0:
            val = mult

        if self.lastPosition < currentPosition and currentPosition != 99:
            val = -mult

        self.kelebekHelper.moveKeys(val*0.01)
        self.lastPosition = self.position_dial.value()

    def onSlideSpeed(self):
        currentPosition = self.speed_dial.value()
        mult = self.multiplier_dSpn.value()
        val = 0
        if self.lastSpeed > currentPosition and currentPosition != 0:
            val = -mult

        if self.lastSpeed < currentPosition and currentPosition != 99:
            val = mult

        self.kelebekHelper.speedChange(val * 0.01)
        self.lastSpeed = self.speed_dial.value()

    def onAttachToPath(self):
        self.kelebekHelper.count = self.count_spn.value()
        self.kelebekHelper.seperation = self.seperation_dSpn.value()
        self.kelebekHelper.randomRadiusX = self.randX_dSpn.value()
        self.kelebekHelper.randomRadiusY = self.randY_dSpn.value()
        self.kelebekHelper.randomRadiusZ = self.randZ_dSpn.value()

        self.kelebekHelper.attachToPath()

# testUI().show()





