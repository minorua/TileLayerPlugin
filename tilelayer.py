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
from downloader import Downloader

debug_mode = 0

R = 6378137

class DefaultSettings:

  ZMIN = 10
  ZMAX = 15
  TRANSPARENCY = 0
  BLENDING_MODE = "SourceOver"

def degreesToMercatorMeters(lon, lat):
  # formula: http://en.wikipedia.org/wiki/Mercator_projection#Mathematics_of_the_Mercator_projection
  x = R * lon * math.pi / 180
  y = R * math.log(math.tan(math.pi / 4 + (lat * math.pi / 180) / 2))
  return x, y

def degreesToTile(zoom, lon, lat):
  x, y = degreesToMercatorMeters(lon, lat)
  size = TileLayer.TSIZE1 / 2 ** (zoom - 1)
  tx = int((x + TileLayer.TSIZE1) / size)
  ty = int((TileLayer.TSIZE1 - y) / size)
  return tx, ty

class Tile:
  def __init__(self, zoom, x, y, data=None):
    self.zoom = zoom
    self.x = x
    self.y = y
    self.data = data

class Tiles:

  def __init__(self, zoom, xmin, ymin, xmax, ymax, tilesize, yOriginTop=1): #TODO: + layerDefinition
    self.zoom = zoom
    self.xmin = xmin
    self.ymin = ymin
    self.xmax = xmax
    self.ymax = ymax
    self.tilesize = tilesize
    self.yOriginTop = yOriginTop

    self.tiles = {}
    self.cachedImage = None

  def addTile(self, url, tile):
    self.tiles[url] = tile
    self.cachedImage = None

  def setImageData(self, url, data):
    if url in self.tiles:
      self.tiles[url].data = data
    self.cachedImage = None

  def image(self):
    if self.cachedImage:
      return self.cachedImage
    width = (self.xmax - self.xmin + 1) * self.tilesize
    height = (self.ymax - self.ymin + 1) * self.tilesize
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    p = QPainter(image)
    for tile in self.tiles.values():
      if tile.data is None:
        continue

      x = tile.x - self.xmin
      y = tile.y - self.ymin
      rect = QRect(x * self.tilesize, y * self.tilesize, self.tilesize, self.tilesize)

      timg = QImage()
      timg.loadFromData(tile.data)
      p.drawImage(rect, timg)
    self.cachedImage = image
    return image

  def extent(self):
    size = TileLayer.TSIZE1 / 2 ** (self.zoom - 1)
    topLeft = QPointF(self.xmin * size - TileLayer.TSIZE1, TileLayer.TSIZE1 - self.ymin * size)
    bottomRight = QPointF((self.xmax + 1) * size - TileLayer.TSIZE1, TileLayer.TSIZE1 - (self.ymax + 1) * size)
    return QRectF(topLeft, bottomRight)

class BoundingBox:
  def __init__(self, xmin, ymin, xmax, ymax):
    self.xmin = xmin
    self.ymin = ymin
    self.xmax = xmax
    self.ymax = ymax

  def toQgsRectangle(self):
    return QgsRectangle(self.xmin, self.ymin, self.xmax, self.ymax)

  def toString(self, digitsAfterPoint=None):
    if digitsAfterPoint is None:
      return "%f,%f,%f,%f" % (self.xmin, self.ymin, self.xmax, self.ymax)
    return "%.{0}f,%.{0}f,%.{0}f,%.{0}f".format(digitsAfterPoint) % (self.xmin, self.ymin, self.xmax, self.ymax)

  @classmethod
  def degreesToMercatorMeters(cls, bbox):
    xmin, ymin = degreesToMercatorMeters(bbox.xmin, bbox.ymin)
    xmax, ymax = degreesToMercatorMeters(bbox.xmax, bbox.ymax)
    return BoundingBox(xmin, ymin, xmax, ymax)

  @classmethod
  def degreesToTileRange(cls, zoom, bbox):
    xmin, ymin = degreesToTile(zoom, bbox.xmin, bbox.ymax)
    xmax, ymax = degreesToTile(zoom, bbox.xmax, bbox.ymin)
    return BoundingBox(xmin, ymin, xmax, ymax)

  @classmethod
  def fromString(cls, s):
    a = map(float, s.split(","))
    return BoundingBox(a[0], a[1], a[2], a[3])

class TileServiceInfo:
  def __init__(self, title, providerName, serviceUrl, yOriginTop=1, zmin=DefaultSettings.ZMIN, zmax=DefaultSettings.ZMAX, bbox=None):
    self.title = title
    self.providerName = providerName
    self.serviceUrl = serviceUrl
    self.yOriginTop = yOriginTop
    self.zmin = zmin
    self.zmax = zmax
    self.bbox = bbox

  def __str__(self):
    return "%s (%s)" % (self.title, self.serviceUrl)

  def toArrayForTableView(self):
    extent = ""
    if self.bbox:
      extent = self.bbox.toString(2)
    return [self.title, self.providerName, self.serviceUrl, "%d-%d" % (self.zmin, self.zmax), extent, self.yOriginTop]

  @classmethod
  def createEmptyInfo(cls):
    return TileServiceInfo("", "")

class TileLayer(QgsPluginLayer):

  LAYER_TYPE = "TileLayer"
  TILE_SIZE = 256       #TODO: move into TileServiceInfoi
  TSIZE1 = 20037508.342789244     #TODO: move into TileServiceInfoi
  MAX_TILE_COUNT = 64
  RENDER_HINT = QPainter.SmoothPixmapTransform    #QPainter.Antialiasing

  def __init__(self, layerDef, iface=None):
    QgsPluginLayer.__init__(self, TileLayer.LAYER_TYPE, layerDef.title)
    self.layerDef = layerDef
    self.iface = iface
    crs = QgsCoordinateReferenceSystem()
    crs.createFromOgcWmsCrs("EPSG:3857")
    self.setCrs(crs)
    if layerDef.bbox:
      self.setExtent(BoundingBox.degreesToMercatorMeters(layerDef.bbox).toQgsRectangle())
    else:
      self.setExtent(QgsRectangle(-TileLayer.TSIZE1, -TileLayer.TSIZE1, TileLayer.TSIZE1, TileLayer.TSIZE1))
    self.setValid(True)
    self.tiles = None
    self.downloader = Downloader(self)
    #QObject.connect(self.downloader, SIGNAL("fileFetched(QString, QByteArray"), self.fileFetched)
    self.setTransparency(DefaultSettings.TRANSPARENCY)
    self.setBlendingMode(DefaultSettings.BLENDING_MODE)

  def setBlendingMode(self, modeName):
    self.blendingModeName = modeName
    self.blendingMode = getattr(QPainter, "CompositionMode_" + modeName, 0)

  def setTransparency(self, transparency):
    self.transparency = transparency

  def draw(self, rendererContext):
    if rendererContext.extent().isEmpty():
      qDebug("Drawing is skipped because map extent is empty.")
      return True

    painter = rendererContext.painter()
    if not self.isCurrentCrsSupported(rendererContext):
      painter.drawText(5, 10, "TileLayer is available only in EPSG:3857 or EPSG:900913")
      return True

    # calculate zoom level
    mpp1 = TileLayer.TSIZE1 / self.TILE_SIZE
    zoom = int(math.ceil(math.log(mpp1 / rendererContext.mapToPixel().mapUnitsPerPixel(), 2) + 1))
    zoom = min(zoom, self.layerDef.zmax)
    #zoom = max(self.layerDef.zmin, min(zoom, self.layerDef.zmax))
    if zoom < self.layerDef.zmin:
      msg = u"{0}: Current zoom level ({1}) is smaller than zmin ({2}).".format(self.layerDef.title, zoom, self.layerDef.zmin)   #TODO: English
      self.iface.messageBar().pushMessage(self.__class__.__name__, msg, QgsMessageBar.INFO, 3)
      return True

    # calculate tile range (yOrigin is top)
    size = TileLayer.TSIZE1 / 2 ** (zoom - 1)
    ulx = int((rendererContext.extent().xMinimum() + TileLayer.TSIZE1) / size)
    uly = int((TileLayer.TSIZE1 - rendererContext.extent().yMaximum()) / size)
    lrx = int((rendererContext.extent().xMaximum() + TileLayer.TSIZE1) / size)
    lry = int((TileLayer.TSIZE1 - rendererContext.extent().yMinimum()) / size)

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

    if self.layerDef.serviceUrl[0] == ":":
      # save painter state
      painter.save()
      self.drawDebugInfo(rendererContext, zoom, ulx, uly, lrx, lry)
    else:
      # create Tiles class object and throw url into it
      self.tiles = Tiles(zoom, ulx, uly, lrx, lry, self.TILE_SIZE, self.layerDef.yOriginTop)
      urls = []
      for ty in range(uly, lry + 1):
        for tx in range(ulx, lrx + 1):
          url = self.tileUrl(zoom, tx, ty)
          self.tiles.addTile(url, Tile(zoom, tx, ty))
          urls.append(url)

      if len(urls) > self.MAX_TILE_COUNT:
        msg = "Tile count is over limit (%d, max=%d)" % (len(urls), self.MAX_TILE_COUNT)
        self.iface.messageBar().pushMessage(self.__class__.__name__, msg, QgsMessageBar.WARNING, 5)
        return True

      # download tile data
      files = self.downloader.fetchFilesAsync(urls)
      for url in files.keys():
        self.tiles.setImageData(url, files[url])
      if self.iface:
        cacheHits = self.downloader.cacheHits
        downloadedCount = self.downloader.fetchSuccesses - cacheHits
        msg = "%d files downloaded. %d caches hit." % (downloadedCount, cacheHits)
        if self.downloader.fetchErrors:
          msg += " %d files failed." % (self.downloader.fetchErrors)
          if self.downloader.fetchSuccesses == 0:
            msg = u"Failed to download all %d files. Check the layer extent - %s" % (self.downloader.fetchErrors, self.name())
            self.iface.messageBar().pushMessage(self.__class__.__name__, msg, QgsMessageBar.WARNING, 5)
        self.iface.mainWindow().statusBar().showMessage(msg, 5000)

      # save painter state and apply layer style
      painter.save()
      self.prepareStyle(painter)

      # draw tiles
      self.drawTiles(rendererContext, self.tiles)
      #self.drawTilesDirectly(rendererContext, self.tiles)

    if debug_mode:
      # draw plugin icon
      image = QImage(os.path.join(os.path.dirname(QFile.decodeName(__file__)), "icon.png"))
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
    lines.append(" zoom: %d, tile extent: (%d, %d) - (%d, %d), tile count: %d * %d" % (zoom, xmin, ymin, xmax, ymax, xmax - xmin, ymax - ymin) )
    lines.append(" map extent: %s" % rendererContext.extent().toString() )
    lines.append(" center: %lf, %lf" % (rendererContext.extent().center().x(), rendererContext.extent().center().y() ) )
    lines.append(" size(proj): %d, %d" % (rendererContext.extent().width(), rendererContext.extent().height() ) )
    lines.append(" canvas size: %d, %d" % (rendererContext.painter().viewport().size().width(), rendererContext.painter().viewport().size().height() ) )
    lines.append(" logicalDpiX: %d" % rendererContext.painter().device().logicalDpiX() )
    lines.append(" outputDpi: %lf" % self.iface.mapCanvas().mapRenderer().outputDpi() )
    lines.append(" mapUnitsPerPixel: %d" % rendererContext.mapToPixel().mapUnitsPerPixel() )
    lines.append(" url: %s" % self.layerDef.serviceUrl )
    p = rendererContext.painter()
    for i, line in enumerate(lines):
      p.drawText(10, i * 20 + 20, line)

  def tileUrl(self, zoom, x, y):
    if not self.layerDef.yOriginTop:
      y = (2 ** zoom - 1) - y
    return self.layerDef.serviceUrl.replace("{z}", str(zoom)).replace("{x}", str(x)).replace("{y}", str(y))

  def getPixelRect(self, rendererContext, zoom, x, y):
    r = self.getMapRect(zoom, x, y)
    map2pix = rendererContext.mapToPixel()
    topLeft = map2pix.transform(r.xMinimum(), r.yMaximum())
    bottomRight = map2pix.transform(r.xMaximum(), r.yMinimum())
    return QRect(QPoint(round(topLeft.x()), round(topLeft.y())), QPoint(round(bottomRight.x()), round(bottomRight.y())))
    #return QRectF(QPointF(round(topLeft.x()), round(topLeft.y())), QPointF(round(bottomRight.x()), round(bottomRight.y())))
    #return QgsRectangle(topLeft, bottomRight)

  def getMapRect(self, zoom, x, y):
    size = TileLayer.TSIZE1 / 2 ** (zoom - 1)
    return QgsRectangle(x * size - TileLayer.TSIZE1, TileLayer.TSIZE1 - y * size, (x + 1) * size - TileLayer.TSIZE1, TileLayer.TSIZE1 - (y + 1) * size)

  def isCurrentCrsSupported(self, rendererContext):
    crs = rendererContext.coordinateTransform()
    if crs:
      epsg = crs.destCRS().srsid()
      if epsg == 3857 or epsg == 900913:
          return True
    return False

  def downloadEvent(self, url):
    if self.iface:
      host = QUrl(url).host()
      self.iface.messageBar().pushMessage("downloading", host + "..." + url.split("/")[-1], QgsMessageBar.INFO, 1)

  def readXml(self, node):
    element = node.toElement()
    self.layerDef.title = element.attribute("title", "")
    self.layerDef.serviceUrl = element.attribute("url", "")
    self.layerDef.yOriginTop = int(element.attribute("yOriginTop", "1"))
    self.layerDef.zmin = int(element.attribute("zmin", str(DefaultSettings.ZMIN)))
    self.layerDef.zmax = int(element.attribute("zmax", str(DefaultSettings.ZMAX)))
    bbox = element.attribute("bbox", None)
    if bbox:
      self.layerDef.bbox = BoundingBox.fromString(bbox)
      self.setExtent(BoundingBox.degreesToMercatorMeters(self.layerDef.bbox).toQgsRectangle())
    # layer style
    self.transparency = int(element.attribute("transparency", str(DefaultSettings.TRANSPARENCY)))
    self.blendingModeName = element.attribute("blend", DefaultSettings.BLENDING_MODE)
    return True

  def writeXml(self, node, doc):
    element = node.toElement();
    element.setAttribute("type", "plugin")
    element.setAttribute("name", TileLayer.LAYER_TYPE);
    element.setAttribute("title", self.layerDef.title)
    element.setAttribute("url", self.layerDef.serviceUrl)
    element.setAttribute("yOriginTop", self.layerDef.yOriginTop)
    element.setAttribute("zmin", self.layerDef.zmin)
    element.setAttribute("zmax", self.layerDef.zmax)
    if self.layerDef.bbox:
      element.setAttribute("bbox", self.layerDef.bbox.toString())
    # layer style
    if self.transparency != DefaultSettings.TRANSPARENCY:
      element.setAttribute("transparency", self.transparency)
    if self.blendingModeName != DefaultSettings.BLENDING_MODE:
      element.setAttribute("blend", self.blendingModeName)
    return True

  def metadata(self):
    lines = []
    lines.append(u"Title:\t%s" % self.layerDef.title)
    lines.append(u"Provider name:\t%s" % self.layerDef.providerName)
    lines.append(u"URL:\t%s" % self.layerDef.serviceUrl)
    if self.layerDef.bbox:
      extent = self.layerDef.bbox.toString()
    else:
      extent = "Not set"
    lines.append(u"yOrigin:\t%s (yOriginTop=%d)" % (("Bottom", "Top")[self.layerDef.yOriginTop], self.layerDef.yOriginTop))
    lines.append(u"Zoom range:\t%d - %d" % (self.layerDef.zmin, self.layerDef.zmax))
    lines.append(u"Layer Extent:\t%s" % extent)
    return "\n".join(lines)

  def log(self, msg):
    if debug_mode:
      qDebug(msg)

  def dump(self, detail=False, bbox=None):
    pass

class TileLayerType(QgsPluginLayerType):
  def __init__(self, iface):
    QgsPluginLayerType.__init__(self, TileLayer.LAYER_TYPE)
    self.iface = iface

  def createLayer(self):
    return TileLayer(TileServiceInfo.createEmptyInfo(), self.iface)

  def showLayerProperties(self, layer):
    from propertiesdialog import PropertiesDialog
    dialog = PropertiesDialog(layer)
    dialog.show()
    accepted = dialog.exec_()
    if accepted:
      layer.setTransparency(dialog.ui.spinBox_Transparency.value())
      layer.setBlendingMode(dialog.ui.comboBox_BlendingMode.currentText())
      layer.emit(SIGNAL("repaintRequested()"))
    return True
