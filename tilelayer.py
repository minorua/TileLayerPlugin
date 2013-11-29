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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsMessageBar
import os
import math
from tiles import *
from downloader import Downloader

debug_mode = 1

class LayerDefaultSettings:

  TRANSPARENCY = 0
  BLENDING_MODE = "SourceOver"

class TileLayer(QgsPluginLayer):

  LAYER_TYPE = "TileLayer"
  MAX_TILE_COUNT = 64
  RENDER_HINT = QPainter.SmoothPixmapTransform    #QPainter.Antialiasing

  def __init__(self, plugin, layerDef, providerNameLabelVisibility=1):
    QgsPluginLayer.__init__(self, TileLayer.LAYER_TYPE, layerDef.title)
    self.plugin = plugin
    self.iface = plugin.iface
    self.layerDef = layerDef
    self.providerNameLabelVisibility = 1 if providerNameLabelVisibility else 0

    # set custom properties
    self.setCustomProperty("title", layerDef.title)
    self.setCustomProperty("providerName", layerDef.providerName)
    self.setCustomProperty("serviceUrl", layerDef.serviceUrl)
    self.setCustomProperty("yOriginTop", layerDef.yOriginTop)
    self.setCustomProperty("zmin", layerDef.zmin)
    self.setCustomProperty("zmax", layerDef.zmax)
    if layerDef.bbox:
      self.setCustomProperty("bbox", layerDef.bbox.toString())
    self.setCustomProperty("providerNameLabelVisibility", self.providerNameLabelVisibility)

    crs = QgsCoordinateReferenceSystem("EPSG:3857")
    self.setCrs(crs)
    if layerDef.bbox:
      self.setExtent(BoundingBox.degreesToMercatorMeters(layerDef.bbox).toQgsRectangle())
    else:
      self.setExtent(QgsRectangle(-layerDef.TSIZE1, -layerDef.TSIZE1, layerDef.TSIZE1, layerDef.TSIZE1))
    self.setValid(True)
    self.tiles = None
    self.setTransparency(LayerDefaultSettings.TRANSPARENCY)
    self.setBlendingMode(LayerDefaultSettings.BLENDING_MODE)

    self.downloader = Downloader(self)
    QObject.connect(self.downloader, SIGNAL("replyFinished(QString, int, int)"), self.networkReplyFinished)

  def setBlendingMode(self, modeName):
    self.blendingModeName = modeName
    self.blendingMode = getattr(QPainter, "CompositionMode_" + modeName, 0)
    self.setCustomProperty("blendMode", modeName)

  def setTransparency(self, transparency):
    self.transparency = transparency
    self.setCustomProperty("transparency", transparency)

  def setProviderNameLabelVisibility(self, visible):
    self.providerNameLabelVisibility = visible
    self.setCustomProperty("providerNameLabelVisibility", 1 if visible else 0)

  def draw(self, rendererContext):
    if rendererContext.extent().isEmpty():
      qDebug("Drawing is skipped because map extent is empty.")
      return True

    painter = rendererContext.painter()
    if not self.isCurrentCrsSupported(rendererContext):
      if self.plugin.navigationMessagesEnabled:
        msg = self.tr("TileLayer is available in EPSG:3857 or EPSG:900913")
        self.iface.messageBar().pushMessage(self.plugin.pluginName, msg, QgsMessageBar.INFO, 2)
      return True

    # calculate zoom level
    mpp1 = self.layerDef.TSIZE1 / self.layerDef.TILE_SIZE
    zoom = int(math.ceil(math.log(mpp1 / rendererContext.mapToPixel().mapUnitsPerPixel(), 2) + 1))
    zoom = max(0, min(zoom, self.layerDef.zmax))
    #zoom = max(self.layerDef.zmin, min(zoom, self.layerDef.zmax))

    # calculate tile range (yOrigin is top)
    size = self.layerDef.TSIZE1 / 2 ** (zoom - 1)
    matrixSize = 2 ** zoom
    ulx = max(0, int((rendererContext.extent().xMinimum() + self.layerDef.TSIZE1) / size))
    uly = max(0, int((self.layerDef.TSIZE1 - rendererContext.extent().yMaximum()) / size))
    lrx = min(int((rendererContext.extent().xMaximum() + self.layerDef.TSIZE1) / size), matrixSize - 1)
    lry = min(int((self.layerDef.TSIZE1 - rendererContext.extent().yMinimum()) / size), matrixSize - 1)

    # bounding box limit
    if self.layerDef.bbox:
      trange = BoundingBox.degreesToTileRange(zoom, self.layerDef.bbox)
      ulx = max(ulx, trange.xmin)
      uly = max(uly, trange.ymin)
      lrx = min(lrx, trange.xmax)
      lry = min(lry, trange.ymax)
      if lrx < ulx or lry < uly:
        # the tile range is out of bounding box
        return True

    # zoom limit
    if zoom < self.layerDef.zmin:
      if self.plugin.navigationMessagesEnabled:
        msg = self.tr("Current zoom level ({0}) is smaller than zmin ({1}): {2}").format(zoom, self.layerDef.zmin, self.layerDef.title)
        self.iface.messageBar().pushMessage(self.plugin.pluginName, msg, QgsMessageBar.INFO, 2)
      return True

    if self.layerDef.serviceUrl[0] == ":":
      # save painter state
      painter.save()
      self.drawDebugInfo(rendererContext, zoom, ulx, uly, lrx, lry)
    else:
      # create Tiles class object and throw url into it
      self.tiles = Tiles(zoom, ulx, uly, lrx, lry, self.layerDef)
      urls = []
      for ty in range(uly, lry + 1):
        for tx in range(ulx, lrx + 1):
          url = self.layerDef.tileUrl(zoom, tx, ty)
          self.tiles.addTile(url, Tile(zoom, tx, ty))
          urls.append(url)

      if len(urls) > self.MAX_TILE_COUNT:
        msg = self.tr("Tile count is over limit ({0}, max={1})").format(len(urls), self.MAX_TILE_COUNT)
        self.iface.messageBar().pushMessage(self.plugin.pluginName, msg, QgsMessageBar.WARNING, 4)
        return True

      # download tile data
      files = self.downloader.fetchFilesAsync(urls, self.plugin.downloadTimeout)
      for url in files.keys():
        self.tiles.setImageData(url, files[url])
      if self.iface:
        cacheHits = self.downloader.cacheHits
        downloadedCount = self.downloader.fetchSuccesses - cacheHits
        msg = self.tr("{0} files downloaded. {1} caches hit.").format(downloadedCount, cacheHits)
        barmsg = None
        if self.downloader.errorStatus != Downloader.NO_ERROR:
          if self.downloader.errorStatus == Downloader.TIMEOUT_ERROR:
            barmsg = self.tr("Download Timeout - {}").format(self.name())
          else:
            msg += self.tr(" {} files failed.").format(self.downloader.fetchErrors)
            if self.downloader.fetchSuccesses == 0:
              barmsg = self.tr("Failed to download all {0} files. - {1}").format(self.downloader.fetchErrors, self.name())
        self.iface.mainWindow().statusBar().showMessage(msg, 5000)
        if barmsg:
          self.iface.messageBar().pushMessage(self.plugin.pluginName, barmsg, QgsMessageBar.WARNING, 4)

      # save painter state and apply layer style
      painter.save()
      self.prepareStyle(painter)

      # draw tiles
      self.drawTiles(rendererContext, self.tiles)
      #self.drawTilesDirectly(rendererContext, self.tiles)

      # draw provider name on the bottom right
      if self.providerNameLabelVisibility and self.layerDef.providerName != "":
        margin, paddingH, paddingV = (5, 4, 3)
        canvasSize = painter.viewport().size()
        rect = QRect(0, 0, canvasSize.width() - margin, canvasSize.height() - margin)
        textRect = painter.boundingRect(rect, Qt.AlignBottom | Qt.AlignRight, self.layerDef.providerName)
        bgRect = QRect(textRect.left() - paddingH, textRect.top() - paddingV, textRect.width() + 2 * paddingH, textRect.height() + 2 * paddingV)
        painter.fillRect(bgRect, QColor(240, 240, 240, 150))  #197, 234, 243, 150))
        painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, self.layerDef.providerName)

    if debug_mode:
      # draw plugin icon
      image = QImage(os.path.join(os.path.dirname(QFile.decodeName(__file__)), "icon_old.png"))
      painter.drawImage(5, 5, image)
    # restore painter state
    painter.restore()
    return True

  def drawTiles(self, rendererContext, tiles):
    # create an image that has the same resolution as the tiles
    image = tiles.image()

    # tile extent to pixel
    map2pixel = rendererContext.mapToPixel()
    extent = tiles.extent()
    topLeft = map2pixel.transform(extent.topLeft().x(), extent.topLeft().y())
    bottomRight = map2pixel.transform(extent.bottomRight().x(), extent.bottomRight().y())
    rect = QRect(QPoint(round(topLeft.x()), round(topLeft.y())), QPoint(round(bottomRight.x()), round(bottomRight.y())))

    # draw the image on the map canvas
    rendererContext.painter().drawImage(rect, image)

    self.log("Tiles extent: " + str(extent))
    self.log("Draw into canvas rect: " + str(rect))

  def drawTilesDirectly(self, rendererContext, tiles):
    p = rendererContext.painter()
    for url, tile in tiles.tiles.items():
      self.log("Draw tile: zoom: %d, x:%d, y:%d, data:%s" % (tile.zoom, tile.x, tile.y, str(tile.data)))
      rect = self.getPixelRect(rendererContext, tile.zoom, tile.x, tile.y)
      if tile.data is not None:
        image = QImage()
        image.loadFromData(tile.data)
        p.drawImage(rect, image)

  def prepareStyle(self, painter):
    oldRenderHints = 0
    if self.RENDER_HINT is not None:
      oldRenderHints = painter.renderHints()
      painter.setRenderHint(self.RENDER_HINT, True)
    oldCompositionMode = painter.compositionMode()
    painter.setCompositionMode(self.blendingMode)
    oldOpacity = painter.opacity()
    painter.setOpacity(0.01 * (100 - self.transparency))
    return [oldRenderHints, oldCompositionMode, oldOpacity]

  def restoreStyle(self, painter, oldStyles):
    if self.RENDER_HINT is not None:
      painter.setRenderHints(oldStyles[0])
    painter.setCompositionMode(oldStyles[1])
    painter.setOpacity(oldStyles[2])

  def drawDebugInfo(self, rendererContext, zoom, ulx, uly, lrx, lry):
    if "frame" in self.layerDef.serviceUrl:
      self.drawFrames(rendererContext, zoom, ulx, uly, lrx, lry)
    if "number" in self.layerDef.serviceUrl:
      self.drawNumbers(rendererContext, zoom, ulx, uly, lrx, lry)
    if "info" in self.layerDef.serviceUrl:
      self.drawInfo(rendererContext, zoom, ulx, uly, lrx, lry)

  def drawFrame(self, rendererContext, zoom, x, y):
    rect = self.getPixelRect(rendererContext, zoom, x, y)
    p = rendererContext.painter()
    p.drawRect(rect)

  def drawFrames(self, rendererContext, zoom, xmin, ymin, xmax, ymax):
    for y in range(ymin, ymax + 1):
      for x in range(xmin, xmax + 1):
        self.drawFrame(rendererContext, zoom, x, y)

  def drawNumber(self, rendererContext, zoom, x, y):
    rect = self.getPixelRect(rendererContext, zoom, x, y)
    p = rendererContext.painter()
    if not self.layerDef.yOriginTop:
      y = (2 ** zoom - 1) - y
    p.drawText(rect, Qt.AlignCenter, "(%d, %d)\nzoom: %d" % (x, y, zoom));

  def drawNumbers(self, rendererContext, zoom, xmin, ymin, xmax, ymax):
    for y in range(ymin, ymax + 1):
      for x in range(xmin, xmax + 1):
        self.drawNumber(rendererContext, zoom, x, y)

  def drawInfo(self, rendererContext, zoom, xmin, ymin, xmax, ymax):
    lines = []
    lines.append("TileLayer")
    lines.append(" zoom: %d, tile matrix extent: (%d, %d) - (%d, %d), tile count: %d * %d" % (zoom, xmin, ymin, xmax, ymax, xmax - xmin, ymax - ymin) )
    lines.append(" map extent: %s" % rendererContext.extent().toString() )
    lines.append(" map center: %lf, %lf" % (rendererContext.extent().center().x(), rendererContext.extent().center().y() ) )
    lines.append(" map size: %f, %f" % (rendererContext.extent().width(), rendererContext.extent().height() ) )
    lines.append(" canvas size (pixel): %d, %d" % (rendererContext.painter().viewport().size().width(), rendererContext.painter().viewport().size().height() ) )
    lines.append(" logicalDpiX: %f" % rendererContext.painter().device().logicalDpiX() )
    lines.append(" outputDpi: %f" % self.iface.mapCanvas().mapRenderer().outputDpi() )
    lines.append(" mapUnitsPerPixel: %f" % rendererContext.mapToPixel().mapUnitsPerPixel() )
    p = rendererContext.painter()
    for i, line in enumerate(lines):
      p.drawText(10, i * 20 + 20, line)
      self.log(line)

  def getPixelRect(self, rendererContext, zoom, x, y):
    r = self.layerDef.getMapRect(zoom, x, y)
    map2pix = rendererContext.mapToPixel()
    topLeft = map2pix.transform(r.xMinimum(), r.yMaximum())
    bottomRight = map2pix.transform(r.xMaximum(), r.yMinimum())
    return QRect(QPoint(round(topLeft.x()), round(topLeft.y())), QPoint(round(bottomRight.x()), round(bottomRight.y())))
    #return QRectF(QPointF(round(topLeft.x()), round(topLeft.y())), QPointF(round(bottomRight.x()), round(bottomRight.y())))
    #return QgsRectangle(topLeft, bottomRight)

  def isCurrentCrsSupported(self, rendererContext):
    crs = rendererContext.coordinateTransform()
    if crs:
      epsg = crs.destCRS().srsid()
      if epsg == 3857 or epsg == 900913:
          return True
    return False

  def networkReplyFinished(self, url, error, isFromCache):
    if self.iface is None or isFromCache:
      return
    downloadedCount = self.downloader.fetchSuccesses - self.downloader.cacheHits
    totalCount = self.downloader.finishedCount() + self.downloader.unfinishedCount()
    msg = self.tr("{0} of {1} files downloaded.").format(downloadedCount, totalCount)
    if self.downloader.fetchErrors:
      msg += self.tr(" {} files failed.").format(self.downloader.fetchErrors)
    self.iface.mainWindow().statusBar().showMessage(msg)

  def readXml(self, node):
    self.readCustomProperties(node)
    self.layerDef.title = self.customProperty("title", "")
    self.layerDef.providerName = self.customProperty("providerName", "")
    self.layerDef.serviceUrl = self.customProperty("serviceUrl", "")
    self.layerDef.yOriginTop = int(self.customProperty("yOriginTop", 1))
    self.layerDef.zmin = int(self.customProperty("zmin", TileDefaultSettings.ZMIN))
    self.layerDef.zmax = int(self.customProperty("zmax", TileDefaultSettings.ZMAX))
    bbox = self.customProperty("bbox", None)
    if bbox:
      self.layerDef.bbox = BoundingBox.fromString(bbox)
      self.setExtent(BoundingBox.degreesToMercatorMeters(self.layerDef.bbox).toQgsRectangle())
    # layer style
    self.transparency = int(self.customProperty("transparency", LayerDefaultSettings.TRANSPARENCY))
    self.blendingModeName = self.customProperty("blendMode", LayerDefaultSettings.BLENDING_MODE)
    self.providerNameLabelVisibility = int(self.customProperty("providerNameLabelVisibility", 1))
    return True

  def writeXml(self, node, doc):
    element = node.toElement();
    element.setAttribute("type", "plugin")
    element.setAttribute("name", TileLayer.LAYER_TYPE);
    return True

  def metadata(self):
    lines = []
    fmt = u"%s:\t%s"
    lines.append(fmt % (self.tr("Title"), self.layerDef.title))
    lines.append(fmt % (self.tr("Provider name"), self.layerDef.providerName))
    lines.append(fmt % (self.tr("URL"), self.layerDef.serviceUrl))
    lines.append(fmt % (self.tr("yOrigin"), u"%s (yOriginTop=%d)" % (("Bottom", "Top")[self.layerDef.yOriginTop], self.layerDef.yOriginTop)))
    if self.layerDef.bbox:
      extent = self.layerDef.bbox.toString()
    else:
      extent = self.tr("Not set")
    lines.append(fmt % (self.tr("Zoom range"), "%d - %d" % (self.layerDef.zmin, self.layerDef.zmax)))
    lines.append(fmt % (self.tr("Layer Extent"), extent))
    return "\n".join(lines)

  def log(self, msg):
    if debug_mode:
      qDebug(msg)

  def dump(self, detail=False, bbox=None):
    pass

class TileLayerType(QgsPluginLayerType):
  def __init__(self, plugin):
    QgsPluginLayerType.__init__(self, TileLayer.LAYER_TYPE)
    self.plugin = plugin

  def createLayer(self):
    return TileLayer(self.plugin, TileServiceInfo.createEmptyInfo())

  def showLayerProperties(self, layer):
    from propertiesdialog import PropertiesDialog
    dialog = PropertiesDialog(layer)
    dialog.show()
    accepted = dialog.exec_()
    if accepted:
      layer.setTransparency(dialog.ui.spinBox_Transparency.value())
      layer.setBlendingMode(dialog.ui.comboBox_BlendingMode.currentText())
      layer.setProviderNameLabelVisibility(dialog.ui.checkBox_ProviderNameLabelVisibility.isChecked())
      layer.emit(SIGNAL("repaintRequested()"))
    return True
