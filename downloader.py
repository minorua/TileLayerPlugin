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
from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import *
import os
import datetime

debug_mode = 1

class Downloader(QObject):

  MAX_CONNECTION = 2

  def __init__(self, parent=None):
    QObject.__init__(self, parent)
    self.queue = []
    self.requestingUrls = []
    self.replies = []

    self.eventLoop = QEventLoop()
    self.async = False
    self.fetchedFiles = {}
    self.clearCounts()

  def clearCounts(self):
    self.fetchSuccesses = 0
    self.fetchErrors = 0
    self.cacheHits = 0

  def replyFinished(self):
    reply = self.sender()
    url = reply.url().toString()
    self.log("replyFinished: %s" % url)
    if self.async and not url in self.fetchedFiles:
      self.fetchedFiles[url] = None
    self.requestingUrls.remove(url)
    self.replies.remove(reply)

    if reply.error() == QNetworkReply.NoError:
      httpStatusCode = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
      self.fetchSuccesses += 1
      if reply.attribute(QNetworkRequest.SourceIsFromCacheAttribute):
        self.cacheHits += 1

      if reply.isReadable():
        data = reply.readAll()
        if self.async:
          self.fetchedFiles[url] = data
        else:
          self.emit(SIGNAL('fileFetched(QString, QByteArray)'), url, data)
      else:
        if httpStatusCode is not None:
          qDebug("http status code: %d" % httpStatusCode)
    else:
      self.fetchErrors += 1

    reply.deleteLater()

    if self.async and len(self.queue) + len(self.requestingUrls) == 0:
      self.log("eventLoop.quit()")
      self.eventLoop.quit()

    if len(self.queue) > 0:
      self.fetchNext()
    self.log("replyFinished End: %s" % url)

  def fetchNext(self):
    if len(self.queue) == 0:
      return
    url = self.queue.pop(0)
    self.log("fetchNext: %s" % url)

    request = QNetworkRequest(QUrl(url))
    #request.setRawHeader("User-Agent", "QGIS/2.x TileLayerPlugin/0.x")
    reply = QgsNetworkAccessManager.instance().get(request)
    reply.finished.connect(self.replyFinished)
    self.requestingUrls.append(url)
    self.replies.append(reply)
    return reply

  def fetchFilesAsync(self, urlList):
    self.log("fetchFilesAsync()")
    self.async = True
    self.fetchedFiles = {}
    self.clearCounts()
    for url in urlList:
      self.addToQueue(url)

    for i in range(self.MAX_CONNECTION):
      self.fetchNext()

    self.log("eventLoop.exec_()")
    self.eventLoop.exec_()
    self.log("files fetched")
    return self.fetchedFiles

  def addToQueue(self, url):
    if url in self.queue:
      return False
    self.queue.append(url)
    return True

  def queueCount(self):
    return len(self.queue)

  def log(self, msg):
    if debug_mode:
      qDebug(msg)

### TODO: sync fetching
  def startFetch(self):
    self.fetchNext()

  def clear(self):
    self.queue = []
    self.requestingUrls = []

  def fetch(self, url):
    self.async = False
    if not url in self.queue:
      self.queue.append(url)
    self.fetchNext()

  def fetchFiles(self, urlList):
    self.async = False
    for url in urlList:
      if not url in self.queue:
        self.queue.append(url)
    self.fetchNext()
