# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Users\minorua\.qgis2\python\developing_plugins\TileLayerPlugin\addlayerdialog.ui'
#
# Created: Fri Jun 26 10:14:35 2015
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(600, 400)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.treeView = QtGui.QTreeView(Dialog)
        self.treeView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.verticalLayout.addWidget(self.treeView)
        self.checkBox_CreditVisibility = QtGui.QCheckBox(Dialog)
        self.checkBox_CreditVisibility.setEnabled(True)
        self.checkBox_CreditVisibility.setChecked(True)
        self.checkBox_CreditVisibility.setObjectName(_fromUtf8("checkBox_CreditVisibility"))
        self.verticalLayout.addWidget(self.checkBox_CreditVisibility)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pushButton_Settings = QtGui.QPushButton(Dialog)
        self.pushButton_Settings.setObjectName(_fromUtf8("pushButton_Settings"))
        self.horizontalLayout_2.addWidget(self.pushButton_Settings)
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
        Dialog.setWindowTitle(_translate("Dialog", "Add tile layer", None))
        self.checkBox_CreditVisibility.setText(_translate("Dialog", "Place the credit on the bottom right corner", None))
        self.pushButton_Settings.setText(_translate("Dialog", "Settings", None))
        self.pushButton_Add.setText(_translate("Dialog", "Add", None))
        self.pushButton_Close.setText(_translate("Dialog", "Close", None))

