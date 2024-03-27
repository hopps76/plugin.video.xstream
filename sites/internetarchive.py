# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
# showGenre:    48 Stunden
# showEntries:   6 Stunden

import json

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'internetarchive'
SITE_NAME = 'Internet Archive'
SITE_ICON = 'internetarchive.png'

# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'archive.org')
URL_MAIN = 'https://' + DOMAIN
URL_MOVIE = URL_MAIN + '/details/'
URL_SEARCH = URL_MAIN + '/advancedsearch.php?q=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    #params = ParameterHandler() ToDo: Reserviert für zukünftige Menü-Einträge
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl + '%20AND%20mediatype%3Amovies&fl%5B%5D=description&fl%5B%5D=genre&fl%5B%5D=identifier&fl%5B%5D=language&fl%5B%5D=title&fl%5B%5D=year&rows=500&output=json', ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())  # Lade JSON aus dem Request der URL
    if not jSearch: return  # # Wenn Suche erfolglos - Abbruch
    aResults = jSearch['response']['docs']
    total = len(aResults)
    if len(aResults) == 0:
        if not sGui: oGui.showInfo()
        return

    # Filter nach eingestellter Sprache in xstream laden
    sLanguage = cConfig().getSetting('prefLanguage')

    for i in aResults:
        sId = i['identifier']  # ID des Films / Serie für die weitere URL
        sName = i['title']  # Name des Films / Serie

        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')

        # Resultate aus JSON nach voreingestellter Sprache filtern (Deutsch, Englisch, alle Sprachen)
        if 'language' in i and i['language'] != '':
            sLang = i['language']
            if sLanguage == '1': # Voreingestellte Sprache Deutsch in settings.xml
                if not sLang in ['ger', 'german']:
                   continue
            if sLanguage == '2':  # Voreingestellte Sprache Englisch in settings.xml
                if not sLang in ['eng', 'english']:
                    continue
            if sLanguage == '0': # Alle Sprachen
                if not sLang in ['ger', 'eng', 'english', '']:
                    continue
        else:
            continue
        oGuiElement.setLanguage(i['language'])



        #if 'is_series' in i: isTvshow = i['is_series']  # Wenn True dann Serie ToDo Prüfen wie sich Serien verhalten
        #oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        #oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        if 'year' in i and len(str(i['year'])) == 4: # Suche bei year nach 4 stelliger Zahl
            oGuiElement.setYear(i['year'])
        if 'description' in i and i['description'] != '':
            oGuiElement.setDescription(i['description'])  # Suche nach Desc wenn nicht leer dann setze GuiElement



        #oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setMediaType('movie')
        # Parameter übergeben
        params.setParam('entryUrl', URL_MOVIE + sId)
        params.setParam('sName', sName)
        #oGui.addFolder(oGuiElement, params, isTvshow, total)
        #oGui.addFolder(oGuiElement, params, total)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        #oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    hosters = []
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, aResult = cParser().parse(sHtmlContent, 'itemprop="embedUrl".*?href="([^"]+)')
    if isMatch:
        for sUrl in aResult:
            if sUrl.startswith('//'):
                sUrl = 'https:' + sUrl
        hoster = {'link': sUrl, 'name': cParser.urlparse(sUrl)}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if 'youtube' in sUrl:
        import xbmc
        if not xbmc.getCondVisibility('System.HasAddon(%s)' % 'plugin.video.youtube'):
            xbmc.executebuiltin('InstallAddon(%s)' % 'plugin.video.youtube')
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
     showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)