# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TileLayer Plugin
                                 A QGIS plugin
 Plugin layer for Tile Maps
                             -------------------
        begin                : 2012-12-16
        copyright            : (C) 2013 by Minoru Akagi
        email                : akaginch@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_addlayerdialog import Ui_Dialog
import os
import codecs
from tilelayer import TileServiceInfo, BoundingBox

class AddLayerDialog(QDialog):
  def __init__(self):
    QDialog.__init__(self)
    settings = QSettings()
    self.extDir = settings.value("/TileLayerPlugin/extDir", "", type=unicode)

    # set up the user interface
    self.ui = Ui_Dialog()
    self.ui.setupUi(self)
    extDirText = self.extDir if self.extDir != "" else self.tr("Not set")
    self.ui.label_externalDirectory.setText(extDirText)
    self.ui.pushButton_Add.clicked.connect(self.accept)
    self.ui.pushButton_Close.clicked.connect(self.reject)
    self.ui.toolButton_externalDirectory.clicked.connect(self.selectExternalDirectory)
    self.setupTreeView()

  def setupTreeView(self):
    # tree view header labels
    headers = [self.tr("Title"), self.tr("ProviderName"), self.tr("Url"), self.tr("Zoom"), self.tr("Extent"), self.tr("yOrigin")] + ["index"]
    self.indexColumn = len(headers) - 1

    self.model = QStandardItemModel(0, len(headers))
    self.model.setHorizontalHeaderLabels(headers)

    # import service info from files in the layers directory, and append it into the tree
    self.serviceInfoList = []
    pluginDir = os.path.dirname(QFile.decodeName(__file__))
    self.importFromDirectory(os.path.join(pluginDir, "layers"))

    # import service info also from external layers directory
    if self.extDir != "":
      self.importFromDirectory(self.extDir)

    # model and style settings
    self.ui.treeView.setModel(self.model)
    self.ui.treeView.header().setResizeMode(QHeaderView.ResizeToContents)
    self.ui.treeView.expandAll()

  def importFromDirectory(self, path):
    d = QDir(path)
    d.setFilter(QDir.Files | QDir.Hidden)
    #d.setSorting(QDir.Size | QDir.Reversed)

    for fileInfo in d.entryInfoList():
      self.importFromTsv(fileInfo.filePath())

  # Line Format is:
  # title providerName url [yOriginTop [zmin zmax [xmin ymin xmax ymax ]]]
  def importFromTsv(self, filename):
    # append file item
    rootItem = self.model.invisibleRootItem()
    parent = QStandardItem(os.path.splitext(os.path.basename(filename))[0])
    rootItem.appendRow([parent])

    # load service info from tsv file
    f = codecs.open(filename, "r", "utf-8")
    for line in f.readlines():
      vals = line.split("\t")
      nvals = len(vals)
      if nvals < 3:
        #TODO: log warning
        continue
      title, providerName, url = vals[0:3]
      if nvals < 4:
        serviceInfo = TileServiceInfo(title, providerName, url)
      else:
        yOriginTop = int(vals[3])
        if nvals < 6:
          serviceInfo = TileServiceInfo(title, providerName, url, yOriginTop)
        else:
          zmin, zmax = map(int, vals[4:6])
          if nvals < 10:
            serviceInfo = TileServiceInfo(title, providerName, url, yOriginTop, zmin, zmax)
          else:
            bbox = BoundingBox.fromString(",".join(vals[6:10]))
            serviceInfo = TileServiceInfo(title, providerName, url, yOriginTop, zmin, zmax, bbox)

      # append the service info into the tree
      vals = serviceInfo.toArrayForTreeView() + [len(self.serviceInfoList)]
      rowItems = map(QStandardItem, map(unicode, vals))
      parent.appendRow(rowItems)
      self.serviceInfoList.append(serviceInfo)
    f.close()

  def selectedServiceInfoList(self):
    list = []
    for idx in self.ui.treeView.selectionModel().selection().indexes():
      if idx.column() == self.indexColumn and idx.data() is not None:
        list.append(self.serviceInfoList[int(idx.data())])
    return list

  def selectExternalDirectory(self):
    # show select directory dialog
    d  = QFileDialog.getExistingDirectory(self, self.tr("Select external layers directory"), self.extDir)
    if d == "":
      return
    self.extDir = d
    settings = QSettings()
    settings.setValue("/TileLayerPlugin/extDir", self.extDir)
    self.ui.label_externalDirectory.setText(self.extDir)
    self.setupTreeView()
