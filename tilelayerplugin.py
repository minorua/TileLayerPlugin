# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TileLayerPlugin
                                 A QGIS plugin
 Plugin layer for Tile Maps
                              -------------------
        begin                : 2012-12-16
        copyright            : (C) 2013 by Minoru Akagi
        email                : akaginch@gmail.com

 Partly based on openlayers_plugin.py
        copyright            : (C) 2009 by Pirmin Kalberer, Sourcepole
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
import os.path
from tilelayer import *

debug_mode = 1

class TileLayerPlugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(QFile.decodeName(__file__))
        # initialize locale
        settings = QSettings()
        locale = settings.value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'tilelayerplugin_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.pluginName = QCoreApplication.translate("TileLayerPlugin", "TileLayerPlugin")
        self.downloadTimeout = int(settings.value("/TileLayerPlugin/timeout", 10, type=int))
        self.navigationMessagesEnabled = int(settings.value("/TileLayerPlugin/naviMsg", Qt.Checked, type=int))

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/tilelayerplugin/icon.png"),
            QCoreApplication.translate("TileLayerPlugin", "Add Tile Layer..."), self.iface.mainWindow())
        self.actionSettings = QAction(
            QCoreApplication.translate("TileLayerPlugin", "Settings"), self.iface.mainWindow())

        # connect the action to the run method
        self.action.triggered.connect(self.run)
        self.actionSettings.triggered.connect(self.settings)

        # Add toolbar button and menu item
        self.iface.insertAddLayerAction(self.action)
        self.iface.layerToolBar().addAction(self.action)
        if debug_mode:
          self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.pluginName, self.actionSettings)
        #self.iface.newLayerMenu().addAction(self.action)
        #self.iface.addPluginToMenu(u"&TileLayer Plugin", self.action)

        # Register plugin layer type
        self.tileLayerType = TileLayerType(self)
        QgsPluginLayerRegistry.instance().addPluginLayerType(self.tileLayerType)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removeAddLayerAction(self.action)
        self.iface.layerToolBar().removeAction(self.action)
        if debug_mode:
          self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu(self.pluginName, self.actionSettings)

        # Unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(TileLayer.LAYER_TYPE)

    def run(self):
      from addlayerdialog import AddLayerDialog
      dialog = AddLayerDialog()
      dialog.show()
      accepted = dialog.exec_()
      if not accepted:
        return
      self.setCRS()
      providerNameLabelVisibility = dialog.ui.checkBox_ProviderNameLabelVisibility.isChecked()
      for serviceInfo in dialog.selectedServiceInfoList():
        layer = TileLayer(self, serviceInfo, providerNameLabelVisibility)
        if layer.isValid():
          QgsMapLayerRegistry.instance().addMapLayer(layer)

    def settings(self):
      from settingsdialog import SettingsDialog
      dialog = SettingsDialog()
      dialog.show()
      accepted = dialog.exec_()
      if accepted:
        self.downloadTimeout = dialog.ui.spinBox_downloadTimeout.value()
        self.navigationMessagesEnabled = dialog.ui.checkBox_NavigationMessages.checkState()

    def setCRS(self):
      crs = QgsCoordinateReferenceSystem("EPSG:3857")
      mapCanvas = self.iface.mapCanvas()
      currentCrs = mapCanvas.mapRenderer().destinationCrs()
      if currentCrs == crs:
        return
      mapCanvas.mapRenderer().setProjectionsEnabled(True) 
      trans = QgsCoordinateTransform(currentCrs, crs)
      extent = trans.transform(mapCanvas.extent(), QgsCoordinateTransform.ForwardTransform)
      mapCanvas.mapRenderer().setDestinationCrs(crs)
      mapCanvas.freeze(False)   #
      mapCanvas.setMapUnits(crs.mapUnits())   #
      mapCanvas.setExtent(extent)
