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
import os

from PyQt4.QtCore import Qt, QCoreApplication, QFile, QSettings, QTranslator, qVersion, qDebug
from PyQt4.QtGui import QAction, QIcon
from qgis.core import QGis, QgsCoordinateReferenceSystem, QgsMapLayerRegistry, QgsPluginLayerRegistry

from tilelayer import TileLayer, TileLayerType

debug_mode = 1


class TileLayerPlugin:

    VERSION = "0.60"

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(QFile.decodeName(__file__))
        # initialize locale
        settings = QSettings()
        locale = settings.value("locale/userLocale", "")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', '{0}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.pluginName = self.tr("TileLayerPlugin")
        self.downloadTimeout = int(settings.value("/TileLayerPlugin/timeout", 30, type=int))
        self.navigationMessagesEnabled = int(settings.value("/TileLayerPlugin/naviMsg", Qt.Checked, type=int))
        self.crs3857 = None
        self.layers = {}

        # register plugin layer type
        self.tileLayerType = TileLayerType(self)
        QgsPluginLayerRegistry.instance().addPluginLayerType(self.tileLayerType)

        # connect signal-slot
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.layerRemoved)

    def initGui(self):
        # create action
        icon = QIcon(os.path.join(self.plugin_dir, "icon.png"))
        self.action = QAction(icon, self.tr("Add Tile Layer..."), self.iface.mainWindow())
        self.action.setObjectName("TileLayerPlugin_AddLayer")

        # connect the action to the method
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        if QSettings().value("/TileLayerPlugin/moveToLayer", 0, type=int):
          self.iface.insertAddLayerAction(self.action)
          self.iface.layerToolBar().addAction(self.action)
        else:
          self.iface.addPluginToWebMenu(self.pluginName, self.action)

    def unload(self):
        # remove the plugin menu item and icon
        if QSettings().value("/TileLayerPlugin/moveToLayer", 0, type=int):
          self.iface.layerToolBar().removeAction(self.action)
          self.iface.removeAddLayerAction(self.action)
        else:
          self.iface.removePluginWebMenu(self.pluginName, self.action)

        # unregister plugin layer type
        QgsPluginLayerRegistry.instance().removePluginLayerType(TileLayer.LAYER_TYPE)

        # disconnect signal-slot
        QgsMapLayerRegistry.instance().layerRemoved.disconnect(self.layerRemoved)

    def layerRemoved(self, layerId):
      if layerId in self.layers:
        del self.layers[layerId]
        if debug_mode:
          qDebug("Layer %s removed" % layerId.encode("UTF-8"))

    def addTileLayer(self, layerdef, creditVisibility=True):
      """@api
         @param layerdef - an object of TileLayerDefinition class (in tiles.py)
         @param creditVisibility - visibility of credit label
         @returns newly created tile layer. if the layer is invalid, returns None
         @note added in 0.60
      """
      if self.crs3857 is None:
        self.crs3857 = QgsCoordinateReferenceSystem(3857)

      layer = TileLayer(self, layerdef, creditVisibility)
      if not layer.isValid():
        return None

      QgsMapLayerRegistry.instance().addMapLayer(layer)
      self.layers[layer.id()] = layer
      return layer

    def run(self):
      from addlayerdialog import AddLayerDialog
      dialog = AddLayerDialog(self)
      dialog.show()
      if dialog.exec_():
        creditVisibility = dialog.ui.checkBox_CreditVisibility.isChecked()
        for layerdef in dialog.selectedLayerDefinitions():
          self.addTileLayer(layerdef, creditVisibility)

    def settings(self):
      oldMoveToLayer = QSettings().value("/TileLayerPlugin/moveToLayer", 0, type=int)

      from settingsdialog import SettingsDialog
      dialog = SettingsDialog(self.iface)
      accepted = dialog.exec_()
      if not accepted:
        return False
      self.downloadTimeout = dialog.ui.spinBox_downloadTimeout.value()
      self.navigationMessagesEnabled = dialog.ui.checkBox_NavigationMessages.checkState()

      moveToLayer = dialog.ui.checkBox_MoveToLayer.checkState()
      if moveToLayer != oldMoveToLayer:
        if oldMoveToLayer:
          self.iface.layerToolBar().removeAction(self.action)
          self.iface.removeAddLayerAction(self.action)
        else:
          self.iface.removePluginWebMenu(self.pluginName, self.action)

        if moveToLayer:
          self.iface.insertAddLayerAction(self.action)
          self.iface.layerToolBar().addAction(self.action)
        else:
          self.iface.addPluginToWebMenu(self.pluginName, self.action)
      return True

    def tr(self, msg):
      return QCoreApplication.translate("TileLayerPlugin", msg)
