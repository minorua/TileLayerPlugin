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
from PyQt4.QtCore import Qt, QPoint, QPointF, QRect, QRectF, qDebug
from qgis.core import QGis, QgsCoordinateTransform, QgsGeometry, QgsPoint, QgsRectangle

def drawDebugInformation(layer, renderContext, zoom, xmin, ymin, xmax, ymax):
  self = layer
  mapSettings = self.iface.mapCanvas().mapSettings() if self.plugin.apiChanged23 else self.iface.mapCanvas().mapRenderer()

  lines = []
  lines.append("TileLayer")
  lines.append(" zoom: %d, tile matrix extent: (%d, %d) - (%d, %d), tile count: %d * %d" % (zoom, xmin, ymin, xmax, ymax, xmax - xmin, ymax - ymin))

  extent = renderContext.extent()
  lines.append(" map extent (renderContext): %s" % extent.toString())
  lines.append(" map center (renderContext): %lf, %lf" % (extent.center().x(), extent.center().y()))
  lines.append(" map size: %f, %f" % (extent.width(), extent.height()))
  lines.append(" map extent (map canvas): %s" % self.iface.mapCanvas().extent().toString())

  map2pixel = renderContext.mapToPixel()
  painter = renderContext.painter()
  viewport = painter.viewport()
  mapExtent = QgsRectangle(map2pixel.toMapCoordinatesF(0, 0), map2pixel.toMapCoordinatesF(viewport.width(), viewport.height()))
  lines.append(" map extent (calculated): %s" % mapExtent.toString())
  lines.append(" map center (calc rect): %lf, %lf" % (mapExtent.center().x(), mapExtent.center().y()))

  center = map2pixel.toMapCoordinatesF(0.5 * viewport.width(), 0.5 * viewport.height())
  lines.append(" map center (calc pt): %lf, %lf" % (center.x(), center.y()))

  lines.append(" viewport size (pixel): %d, %d" % (viewport.width(), viewport.height()))
  lines.append(" window size (pixel): %d, %d" % (painter.window().width(), painter.window().height()))
  lines.append(" outputSize (pixel): %d, %d" % (mapSettings.outputSize().width(), mapSettings.outputSize().height()))

  device = painter.device()
  lines.append(" deviceSize (pixel): %f, %f" % (device.width(), device.height()))
  lines.append(" logicalDpi: %f, %f" % (device.logicalDpiX(), device.logicalDpiY()))
  lines.append(" outputDpi: %f" % mapSettings.outputDpi())
  lines.append(" mapToPixel: %s" % map2pixel.showParameters())

  mupp = map2pixel.mapUnitsPerPixel()
  lines.append(" map units per pixel: %f" % mupp)
  lines.append(" meters per pixel (renderContext): %f" % (extent.width() / viewport.width()))
  transform = renderContext.coordinateTransform()
  if transform:
    mpp = mupp * {QGis.Feet: 0.3048, QGis.Degrees: self.layerDef.TSIZE1 / 180}.get(transform.destCRS().mapUnits(), 1)
    lines.append(" meters per pixel (calc 1): %f" % mpp)

    cx, cy = 0.5 * viewport.width(), 0.5 * viewport.height()
    geometry = QgsGeometry.fromPolyline([map2pixel.toMapCoordinatesF(cx - 0.5, cy), map2pixel.toMapCoordinatesF(cx + 0.5, cy)])
    geometry.transform(QgsCoordinateTransform(transform.destCRS(), transform.sourceCrs()))    # project CRS to layer CRS (EPSG:3857)
    mpp = geometry.length()
    lines.append(" meters per pixel (calc center pixel): %f" % mpp)

  lines.append(" scaleFactor: %f" % renderContext.scaleFactor())
  lines.append(" rendererScale: %f" % renderContext.rendererScale())

  scaleX, scaleY = self.getScaleToVisibleExtent(renderContext)
  lines.append(" scale: %f, %f" % (scaleX, scaleY))

  # draw information
  textRect = painter.boundingRect(QRect(QPoint(0, 0), viewport.size()), Qt.AlignLeft, "Q")
  for i, line in enumerate(lines):
    painter.drawText(10, (i + 1) * textRect.height(), line)
    self.log(line)

  # diagonal
  painter.drawLine(QPointF(0, 0), QPointF(painter.viewport().width(), painter.viewport().height()))
  painter.drawLine(QPointF(painter.viewport().width(), 0), QPointF(0, painter.viewport().height()))

  # credit label
  margin, paddingH, paddingV = (3, 4, 3)
  credit = "This is credit"
  rect = QRect(0, 0, painter.viewport().width() - margin, painter.viewport().height() - margin)
  textRect = painter.boundingRect(rect, Qt.AlignBottom | Qt.AlignRight, credit)
  bgRect = QRect(textRect.left() - paddingH, textRect.top() - paddingV, textRect.width() + 2 * paddingH, textRect.height() + 2 * paddingV)
  painter.drawRect(bgRect)
  painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, credit)
