import uuid
import json
import os
import sys
from urllib.parse import parse_qs, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
sys.path.insert(0, os.path.join(ADDON.getAddonInfo('path'),'resources','lib'))
from radio import Radio
from batch import entries_for, append_entries


def main():
    handle = int(sys.argv[1])
    query = parse_qs(sys.argv[2].lstrip('?'))
    account = ADDON.getSetting('username')
    if not account or not ADDON.getSetting('password'):
        ADDON.openSettings()
        account = ADDON.getSetting('username')
    try:
        radio = Radio()
        radio.login(account, ADDON.getSetting('password'))
        if 'station' not in query:
            for station in radio.stations():
                label = xbmcgui.ListItem(label=station['stationName'])
                uri = sys.argv[0]+'?'+urlencode({'station':station['stationToken']})
                xbmcplugin.addDirectoryItem(handle,uri,label,True)
        else:
            station = query['station'][0]
            entries = entries_for(radio, station)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            playlist.clear()
            metadata = append_entries(playlist, entries)
            home=xbmcgui.Window(10000)
            home.setProperty('melodica.slim.batch',json.dumps({'station':station,'session':uuid.uuid4().hex,'items':metadata}))
            xbmc.Player().play(playlist)
        xbmcplugin.endOfDirectory(handle,cacheToDisc=False)
    except Exception as err:
        # The request URL can contain ephemeral credentials. Present only the outcome.
        xbmcgui.Dialog().notification('Melodica','Could not load this station or sign in ('+type(err).__name__+').')
        xbmcplugin.endOfDirectory(handle,succeeded=False,cacheToDisc=False)


if __name__ == '__main__':
    main()
