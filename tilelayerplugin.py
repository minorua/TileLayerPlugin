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

    VERSION = "0.30"

    def __init__(self, iface):
        self.apiChanged23 = QGis.QGIS_VERSION_INT >= 20300

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(QFile.decodeName(__file__))
        # initialize locale
        settings = QSettings()
        locale = settings.value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'tilelayerplugin_{0}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.pluginName = self.tr("TileLayerPlugin")
        self.downloadTimeout = int(settings.value("/TileLayerPlugin/timeout", 10, type=int))
        self.navigationMessagesEnabled = int(settings.value("/TileLayerPlugin/naviMsg", Qt.Checked, type=int))

        self.layers = {}
        QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerRemoved(QString)"), self.layerRemoved)

    def initGui(self):
        # Create actions
        self.action = QAction(
            QIcon(":/plugins/tilelayerplugin/icon.png"),
            self.tr("Add Tile Layer..."), self.iface.mainWindow())
        self.actionSettings = QAction(
            self.tr("Settings..."), self.iface.mainWindow())

        # set object name
        self.action.setObjectName("TileLayerPlugin_AddLayer")
        self.actionSettings.setObjectName("TileLayerPlugin_Settings")

        # connect the actions to the methods
        self.action.triggered.connect(self.run)
        self.actionSettings.triggered.connect(self.settings)

        # Add toolbar button and menu item
        self.iface.layerToolBar().addAction(self.action)
        self.iface.insertAddLayerAction(self.action)
        self.iface.addPluginToMenu(self.pluginName, self.action)
        self.iface.addPluginToMenu(self.pluginName, self.actionSettings)
        #self.iface.addToolBarIcon(self.action)

        # Register plugin layer type
        self.tileLayerType = TileLayerType(self)
        QgsPluginLayerRegistry.instance().addPluginLayerType(self.tileLayerType)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.layerToolBar().removeAction(self.action)
        self.iface.removeAddLayerAction(self.action)
        self.iface.removePluginMenu(self.pluginName, self.action)
        self.iface.removePluginMenu(self.pluginName, self.actionSettings)
        #self.iface.removeToolBarIcon(self.action)

        # Unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(TileLayer.LAYER_TYPE)

        QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerRemoved(QString)"), self.layerRemoved)

    def layerRemoved(self, layerId):
      if layerId in self.layers:
        del self.layers[layerId]
        if debug_mode:
          qDebug("Layer %s removed" % layerId.encode("UTF-8"))

    def run(self):
      from addlayerdialog import AddLayerDialog
      dialog = AddLayerDialog(self.iface)
      dialog.show()
      accepted = dialog.exec_()
      if not accepted:
        return

      # change crs to EPSG:3857 (WGS 84 / Pseudo-Mercator)
      pseudo_mercator = QgsCoordinateReferenceSystem(3857)
      self.setCrs(pseudo_mercator)

      creditVisibility = dialog.ui.checkBox_CreditVisibility.isChecked()
      for serviceInfo in dialog.selectedServiceInfoList():
        layer = TileLayer(self, serviceInfo, creditVisibility, pseudo_mercator)
        if layer.isValid():
          QgsMapLayerRegistry.instance().addMapLayer(layer)
          self.layers[layer.id()] = layer

    def settings(self):
      from settingsdialog import SettingsDialog
      dialog = SettingsDialog(self.iface)
      dialog.show()
      accepted = dialog.exec_()
      if accepted:
        self.downloadTimeout = dialog.ui.spinBox_downloadTimeout.value()
        self.navigationMessagesEnabled = dialog.ui.checkBox_NavigationMessages.checkState()

    def setCrs(self, crs):
      if self.apiChanged23:
        mapCanvas = self.iface.mapCanvas()
        currentCrs = mapCanvas.mapSettings().destinationCrs()
        if currentCrs == crs:
          return
        # enable "on the fly"
        mapCanvas.setCrsTransformEnabled(True)

        # set crs
        mapCanvas.freeze()
        mapCanvas.setDestinationCrs(crs)
        if crs.mapUnits() != QGis.UnknownUnit:
          mapCanvas.setMapUnits(crs.mapUnits())
        mapCanvas.freeze(False)
      else:
        mapCanvas = self.iface.mapCanvas()
        currentCrs = mapCanvas.mapRenderer().destinationCrs()
        if currentCrs == crs:
          return
        # enable "on the fly"
        mapCanvas.mapRenderer().setProjectionsEnabled(True)

        # set crs
        mapCanvas.freeze()
        mapCanvas.mapRenderer().setDestinationCrs(crs)
        if crs.mapUnits() != QGis.UnknownUnit:
          mapCanvas.setMapUnits(crs.mapUnits())
        mapCanvas.freeze(False)

      msg = self.tr("Project CRS has been changed to EPSG:3857.")
      self.iface.messageBar().pushMessage(self.pluginName, msg, QgsMessageBar.INFO, 5)

    def tr(self, msg):
      return QCoreApplication.translate("TileLayerPlugin", msg)
