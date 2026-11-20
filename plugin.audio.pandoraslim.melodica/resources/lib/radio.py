"""Melodica tuner and Spaceghost Scrobbles transport for Kodi."""
import ctypes
import json
import platform
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RELAY = 'https://spacegho.st/melodica/api/'
LISTENS = 'https://spacegho.st/scrobble/1/submit-listens'


class Codec:
    def __init__(self):
        machine = {'amd64':'x86_64', 'arm64':'aarch64', 'i386':'x86', 'i686':'x86'}.get(platform.machine().lower(), platform.machine().lower())
        system = platform.system().lower()
        fname = {'windows':'wire.dll', 'darwin':'libwire.dylib', 'linux':'libwire.so'}[system]
        if system == 'windows' and ctypes.sizeof(ctypes.c_void_p) == 4:
            machine = 'x86'
        path = Path(__file__).parent / 'native' / (system+'-'+machine) / fname
        self.fn = ctypes.CDLL(str(path)).melodica_wire_blocks
        self.fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
        self.fn.restype = ctypes.c_int

    def transform(self, data, decrypt=False):
        key = b'R=U!LH$O2B#' if decrypt else b'6#26FRL$ZWD'
        if decrypt:
            data = bytes.fromhex(data)
        else:
            data += b'\0' * (-len(data) % 8)
        buffer = ctypes.create_string_buffer(data)
        if not self.fn(buffer, len(data), key, len(key), int(decrypt)):
            raise ValueError('Invalid tuner block')
        data = buffer.raw[:len(data)]
        return data if decrypt else data.hex().encode('ascii')


class Radio:
    def __init__(self, opener=urlopen):
        self.open = opener
        self.codec = Codec()
        self.ids, self.auth, self.access, self.offset = {}, '', '', 0

    def call(self, method, values):
        body = dict(values)
        if self.auth:
            body['userAuthToken' if 'user_id' in self.ids else 'partnerAuthToken'] = self.auth
            body['syncTime'] = int(time.time()) + self.offset
        data = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode()
        if method != 'auth.partnerLogin':
            data = self.codec.transform(data)
        query = {'method':method, **self.ids}
        if self.auth:
            query['auth_token'] = self.auth
        headers = {'Content-Type':'text/plain'}
        if self.access:
            headers['x-melodica-access'] = self.access
        req = Request(RELAY+'?'+urlencode(query), data=data, headers=headers)
        with self.open(req, timeout=15) as reply:
            record = json.load(reply)
            if record.get('stat') != 'ok':
                raise ValueError(record.get('message', 'Tuner declined the request'))
            if method == 'auth.userLogin':
                self.access = reply.headers.get('x-melodica-access','')
        return record.get('result', {})

    def login(self, email, password):
        partner = self.call('auth.partnerLogin', {'username':'android','password':'AC7IBG09A3DTSYM4R41UJWL07VLN8JI7','deviceModel':'android-generic','version':'5'})
        clock = self.codec.transform(partner['syncTime'], True)[4:].strip(b'\0')
        self.offset = int(clock[:10]) - int(time.time())
        self.ids['partner_id'] = partner['partnerId']
        self.auth = partner['partnerAuthToken']
        user = self.call('auth.userLogin', {'loginType':'user','username':email,'password':password})
        self.ids['user_id'] = user['userId']
        self.auth = user['userAuthToken']

    def stations(self):
        return self.call('user.getStationList', {'returnAllStations':True})['stations']

    def playlist(self, station):
        return self.call('station.getPlaylist', {'stationToken':station,'additionalAudioUrl':'HTTP_128_MP3'})['items']


def submit(token, track, started=None, opener=urlopen):
    info = {'submission_client':'Pandora Slim for Melodica','music_service':'pandora.com'}
    meta = {'artist_name':track['artist'],'track_name':track['title'],'additional_info':info}
    if track.get('album'): meta['release_name'] = track['album']
    listen = {'track_metadata':meta}
    if started is not None: listen['listened_at'] = started
    data = json.dumps({'listen_type':'single' if started is not None else 'playing_now','payload':[listen]}).encode()
    req = Request(LISTENS, data=data, headers={'Authorization':'Token '+token,'Content-Type':'application/json'})
    with opener(req, timeout=6) as response:
        response.read()
