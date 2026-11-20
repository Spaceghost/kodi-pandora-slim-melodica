import hashlib
import json
import os
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()
sys.path.insert(0,os.path.join(addon.getAddonInfo('path'),'resources','lib'))
from radio import Radio, submit
from batch import entries_for, append_entries


def watch():
    monitor, player, home = xbmc.Monitor(), xbmc.Player(), xbmcgui.Window(10000)
    current = None
    refill_after = 0.0
    while not monitor.waitForAbort(1):
        try:
            if not player.isPlayingAudio():
                current = None
                continue
            player_uri = player.getPlayingFile()
            key = hashlib.sha256(player_uri.encode()).hexdigest()
            batch = json.loads(home.getProperty('melodica.slim.batch') or '{}')
            track = batch.get('items',{}).get(key)
            if not track:
                current = None
                continue
            pos, duration, wall = player.getTime(), player.getTotalTime(), time.monotonic()
            if key != current:
                current, last, tick, heard, started = key, pos, wall, 0.0, int(time.time())
                now_sent = final_sent = False
            delta, elapsed = pos-last, wall-tick
            last, tick = pos, wall
            # The station continues after Kodi reaches the end of its current batch.
            playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
            if (wall >= refill_after and playlist.getposition() >= 0 and
                    playlist.size()-playlist.getposition() <= 2):
                refill_after = wall + 15
                radio = Radio(); radio.login(addon.getSetting('username'),addon.getSetting('password'))
                more = entries_for(radio,batch['station'])
                latest = json.loads(home.getProperty('melodica.slim.batch') or '{}')
                if latest.get('session') == batch.get('session') and player.isPlayingAudio() and player.getPlayingFile() == player_uri:
                    latest['items'].update(append_entries(playlist,more))
                    home.setProperty('melodica.slim.batch',json.dumps(latest))
            if delta <= 0 or delta > elapsed + 0.5 or elapsed > 8: continue
            heard += min(delta,elapsed)
            if track.get('insert'):
                if not now_sent and track['ad_tokens']:
                    radio=Radio(); radio.login(addon.getSetting('username'),addon.getSetting('password'))
                    radio.call('ad.registerAd',{'stationId':batch['station'],'adTrackingTokens':track['ad_tokens']})
                    now_sent=True
                continue
            token = addon.getSetting('scrobble_token').strip()
            if not token or addon.getSetting('scrobbling') != 'true' or not track['artist'] or not track['title']: continue
            if not now_sent:
                now_sent=True; submit(token,track)
            if not final_sent and duration > 30 and heard >= min(duration/2,240):
                final_sent=True; submit(token,track,started)
        except (OSError,ValueError,KeyError,RuntimeError):
            continue


if __name__ == '__main__':
    watch()
