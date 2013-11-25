# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Users\lenovo\.qgis2\python\developing_plugins\TileLayerPlugin\addlayerdialog.ui'
#
# Created: Tue Nov 26 08:54:17 2013
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
        Dialog.resize(600, 400)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.treeView = QtGui.QTreeView(Dialog)
        self.treeView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.verticalLayout.addWidget(self.treeView)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setEnabled(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.label_externalDirectory = QtGui.QLabel(Dialog)
        self.label_externalDirectory.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_externalDirectory.sizePolicy().hasHeightForWidth())
        self.label_externalDirectory.setSizePolicy(sizePolicy)
        self.label_externalDirectory.setText(_fromUtf8(""))
        self.label_externalDirectory.setObjectName(_fromUtf8("label_externalDirectory"))
        self.horizontalLayout.addWidget(self.label_externalDirectory)
        self.toolButton_externalDirectory = QtGui.QToolButton(Dialog)
        self.toolButton_externalDirectory.setEnabled(True)
        self.toolButton_externalDirectory.setObjectName(_fromUtf8("toolButton_externalDirectory"))
        self.horizontalLayout.addWidget(self.toolButton_externalDirectory)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.checkBox_ProviderNameLabelVisibility = QtGui.QCheckBox(Dialog)
        self.checkBox_ProviderNameLabelVisibility.setEnabled(True)
        self.checkBox_ProviderNameLabelVisibility.setChecked(True)
        self.checkBox_ProviderNameLabelVisibility.setObjectName(_fromUtf8("checkBox_ProviderNameLabelVisibility"))
        self.verticalLayout.addWidget(self.checkBox_ProviderNameLabelVisibility)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton_Add = QtGui.QPushButton(Dialog)
        self.pushButton_Add.setDefault(True)
        self.pushButton_Add.setObjectName(_fromUtf8("pushButton_Add"))
        self.horizontalLayout_2.addWidget(self.pushButton_Add)
        self.pushButton_Close = QtGui.QPushButton(Dialog)
        self.pushButton_Close.setObjectName(_fromUtf8("pushButton_Close"))
        self.horizontalLayout_2.addWidget(self.pushButton_Close)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Add tile layer", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "External layers directory:", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton_externalDirectory.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox_ProviderNameLabelVisibility.setText(QtGui.QApplication.translate("Dialog", "Provider name label on the bottom right", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_Add.setText(QtGui.QApplication.translate("Dialog", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_Close.setText(QtGui.QApplication.translate("Dialog", "Close", None, QtGui.QApplication.UnicodeUTF8))

