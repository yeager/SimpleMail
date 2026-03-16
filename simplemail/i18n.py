import gettext
import locale
import os

DOMAIN = "simplemail"
LOCALEDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locale")

# System locale dirs
SYSTEM_LOCALEDIRS = [
    LOCALEDIR,
    "/usr/share/locale",
    "/usr/local/share/locale",
]

try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    pass

# Find locale dir with our translations
for d in SYSTEM_LOCALEDIRS:
    if os.path.isdir(d):
        gettext.bindtextdomain(DOMAIN, d)
        break
else:
    gettext.bindtextdomain(DOMAIN, LOCALEDIR)

gettext.textdomain(DOMAIN)
_ = gettext.gettext

