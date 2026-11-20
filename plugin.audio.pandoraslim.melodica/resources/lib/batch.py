"""Build Kodi list items for one tuner batch, including station inserts."""
import hashlib
import xbmcgui


def entries_for(radio, station):
    tracks = radio.playlist(station)
    entries = []
    for song in tracks:
        insert = 'adToken' in song
        if insert:
            song = radio.call('ad.getAdMetadata',{'adToken':song['adToken'],'returnAdTrackingTokens':True})
        options = song.get('audioUrlMap',{})
        stream = next((options[q]['audioUrl'] for q in ('highQuality','mediumQuality','lowQuality') if options.get(q,{}).get('audioUrl')), '')
        if not stream:
            extra = song.get('additionalAudioUrl',[])
            stream = extra if isinstance(extra,str) else next(iter(extra), '')
        if not stream: continue
        if stream.startswith('http://'): stream='https://'+stream[7:]
        title = 'Advertisement' if insert else song.get('songName','')
        artist = '' if insert else song.get('artistName','')
        album = song.get('albumName','')
        item = xbmcgui.ListItem(label=title, path=stream)
        item.setInfo('music',{'title':title,'artist':artist,'album':album})
        item.setArt({'thumb':song.get('albumArtUrl',song.get('imageUrl',''))})
        entries.append((stream,item,{'title':title,'artist':artist,'album':album,'insert':insert,
                        'ad_tokens':song.get('adTrackingTokens',[]) if insert else []}))
    if not entries:
        raise ValueError("The station returned no audio")
    return entries


def append_entries(playlist, entries):
    metadata = {}
    for stream, item, meta in entries:
        playlist.add(stream, item)
        metadata[hashlib.sha256(stream.encode()).hexdigest()] = meta
    return metadata
