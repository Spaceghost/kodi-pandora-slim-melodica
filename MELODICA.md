# Pandora Slim for Melodica

Install the Melodica ZIP from https://spacegho.st/melodica/apps/#kodi-pandora-slim using Kodi’s **Add-ons → Install from zip file**. In the add-on settings enter the Pandora login associated with your Melodica account. Choose a station to play its mix. Add a client token from https://spacegho.st/scrobble/account/ and enable Spaceghost Scrobbles in settings to send listening history to https://spacegho.st/scrobble/. The account’s scrobbling preference also applies.

This Python 3 edition follows the original Slim station browser and uses its GPLv3 artwork and metadata from upstream revision 1bd9d85. The bundled Melodica protocol library handles tuner requests. See the release for supported native platforms.


The ZIP contains libraries for 32- and 64-bit Windows, Intel and ARM64 macOS, and x86-64 and ARM64 Linux. The Python add-on uses Kodi 19 or later. To rebuild the libraries from source with Zig, run `melodica/build-native.sh`. The Linux x86-64 library, station requests, audio retrieval and service listening events were exercised against the Melodica test tuner.
