# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Users\lenovo\.qgis2\python\developing_plugins\TileLayerPlugin\settingsdialog.ui'
#
# Created: Fri Nov 29 10:45:32 2013
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(512, 121)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lineEdit_externalDirectory = QtGui.QLineEdit(Dialog)
        self.lineEdit_externalDirectory.setObjectName(_fromUtf8("lineEdit_externalDirectory"))
        self.horizontalLayout.addWidget(self.lineEdit_externalDirectory)
        self.toolButton_externalDirectory = QtGui.QToolButton(Dialog)
        self.toolButton_externalDirectory.setObjectName(_fromUtf8("toolButton_externalDirectory"))
        self.horizontalLayout.addWidget(self.toolButton_externalDirectory)
        self.formLayout.setLayout(0, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.spinBox_downloadTimeout = QtGui.QSpinBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_downloadTimeout.sizePolicy().hasHeightForWidth())
        self.spinBox_downloadTimeout.setSizePolicy(sizePolicy)
        self.spinBox_downloadTimeout.setMinimumSize(QtCore.QSize(50, 0))
        self.spinBox_downloadTimeout.setMaximum(600)
        self.spinBox_downloadTimeout.setSingleStep(10)
        self.spinBox_downloadTimeout.setObjectName(_fromUtf8("spinBox_downloadTimeout"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.spinBox_downloadTimeout)
        self.verticalLayout.addLayout(self.formLayout)
        self.checkBox_NavigationMessages = QtGui.QCheckBox(Dialog)
        self.checkBox_NavigationMessages.setObjectName(_fromUtf8("checkBox_NavigationMessages"))
        self.verticalLayout.addWidget(self.checkBox_NavigationMessages)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "TileLayerPlugin Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "External layers directory", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_externalDirectory.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Download time-out (sec)", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_NavigationMessages.setText(QtGui.QApplication.translate("Dialog", "Display navigation messages", None, QtGui.QApplication.UnicodeUTF8))

