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
from PyQt4.QtCore import QDir, QFile, QSettings
from PyQt4.QtGui import QDialog, QHeaderView, QStandardItem, QStandardItemModel
from qgis.core import QgsMessageLog
from ui_addlayerdialog import Ui_Dialog
import os
import codecs
from tiles import BoundingBox, TileLayerDefinition

debug_mode = 1

class AddLayerDialog(QDialog):
  def __init__(self, plugin):
    QDialog.__init__(self, plugin.iface.mainWindow())
    self.plugin = plugin

    # set up the user interface
    self.ui = Ui_Dialog()
    self.ui.setupUi(self)
    self.ui.pushButton_Add.clicked.connect(self.accept)
    self.ui.pushButton_Close.clicked.connect(self.reject)
    self.ui.pushButton_Settings.clicked.connect(self.settingsClicked)
    self.ui.treeView.doubleClicked.connect(self.treeItemDoubleClicked)
    self.setupTreeView()

  def setupTreeView(self):

    # tree view header labels
    headers = [self.tr("Title"), self.tr("Credit"), self.tr("Url"), self.tr("Zoom"), self.tr("Extent"), self.tr("yOrigin")] + ["index"]
    self.indexColumn = len(headers) - 1

    self.model = QStandardItemModel(0, len(headers))
    self.model.setHorizontalHeaderLabels(headers)

    self.serviceInfoList = []
    # import layer definitions from external layer definition directory, and append it into the tree
    extDir = QSettings().value("/TileLayerPlugin/extDir", "", type=unicode)
    if extDir:
      self.importFromDirectory(extDir)

    # import layer definitions from TileLayerPlugin/layers directory, and append it into the tree
    pluginDir = os.path.dirname(QFile.decodeName(__file__))
    self.importFromDirectory(os.path.join(pluginDir, "layers"))

    # model and style settings
    self.ui.treeView.setModel(self.model)
    self.ui.treeView.header().setResizeMode(QHeaderView.ResizeToContents)
    self.ui.treeView.expandAll()

  def importFromDirectory(self, path):
    d = QDir(path)
    d.setFilter(QDir.Files | QDir.Hidden)
    #d.setSorting(QDir.Size | QDir.Reversed)

    for fileInfo in d.entryInfoList():
      if debug_mode == 0 and fileInfo.fileName() == "debug.tsv":
        continue
      if fileInfo.suffix().lower() == "tsv":
        self.importFromTsv(fileInfo.filePath())

  # Line Format is:
  # title credit url [yOriginTop [zmin zmax [xmin ymin xmax ymax ]]]
  def importFromTsv(self, filename):
    # append file item
    rootItem = self.model.invisibleRootItem()
    basename = os.path.basename(filename)
    parent = QStandardItem(os.path.splitext(basename)[0])
    rootItem.appendRow([parent])

    # load service info from tsv file
    try:
      with codecs.open(filename, "r", "utf-8") as f:
        lines = f.readlines()
    except Exception as e:
      QgsMessageLog.logMessage(self.tr("Fail to read {0}: {1}").format(basename, unicode(e)), self.tr("TileLayerPlugin"))
      return False

    for i, line in enumerate(lines):
      if line.startswith("#"):
        continue
      vals = line.rstrip().split("\t")
      nvals = len(vals)
      try:
        if nvals < 3:
          raise
        title, credit, url = vals[0:3]
        if not url:
          raise
        if nvals < 4:
          serviceInfo = TileLayerDefinition(title, credit, url)
        else:
          yOriginTop = int(vals[3])
          if nvals < 6:
            serviceInfo = TileLayerDefinition(title, credit, url, yOriginTop)
          else:
            zmin, zmax = map(int, vals[4:6])
            if nvals < 10:
              serviceInfo = TileLayerDefinition(title, credit, url, yOriginTop, zmin, zmax)
            else:
              bbox = BoundingBox.fromString(",".join(vals[6:10]))
              serviceInfo = TileLayerDefinition(title, credit, url, yOriginTop, zmin, zmax, bbox)
      except:
        QgsMessageLog.logMessage(self.tr("Invalid line format: {} line {}").format(basename, i + 1), self.tr("TileLayerPlugin"))
        continue

      # append the service info into the tree
      vals = serviceInfo.toArrayForTreeView() + [len(self.serviceInfoList)]
      rowItems = map(QStandardItem, map(unicode, vals))
      parent.appendRow(rowItems)
      self.serviceInfoList.append(serviceInfo)
    return True

  def selectedLayerDefinitions(self):
    list = []
    for idx in self.ui.treeView.selectionModel().selection().indexes():
      if idx.column() == self.indexColumn and idx.data() is not None:
        list.append(self.serviceInfoList[int(idx.data())])
    return list

  def settingsClicked(self):
    if self.plugin.settings():
      self.setupTreeView()

  def treeItemDoubleClicked(self, index):
    if len(self.selectedLayerDefinitions()) > 0:
      self.accept()
