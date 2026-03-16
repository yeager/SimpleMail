"""Internationalization support for SimpleMail."""

import gettext
import locale
import os

DOMAIN = "simplemail"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locale")


def setup_i18n():
    """Set up gettext translations, defaulting to Swedish."""
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    lang = os.environ.get("LANGUAGE", os.environ.get("LANG", "sv_SE"))

    try:
        translation = gettext.translation(
            DOMAIN, localedir=LOCALE_DIR, languages=[lang[:2], "sv"]
        )
        translation.install()
        return translation.gettext
    except FileNotFoundError:
        # Fallback: return Swedish strings directly
        return _swedish_fallback


# Swedish fallback strings when .mo files are not compiled
_SWEDISH = {
    "SimpleMail": "SimpleMail",
    "Inbox": "Inkorg",
    "Compose": "Skriv nytt",
    "Reply": "Svara",
    "Delete": "Ta bort",
    "Read Aloud": "Läs upp",
    "Stop Reading": "Sluta läsa",
    "Settings": "Inställningar",
    "Send": "Skicka",
    "To:": "Till:",
    "Subject:": "Ämne:",
    "Message:": "Meddelande:",
    "Refresh": "Uppdatera",
    "From:": "Från:",
    "Date:": "Datum:",
    "Loading...": "Laddar...",
    "No messages": "Inga meddelanden",
    "Connect": "Anslut",
    "Disconnect": "Koppla från",
    "Connected": "Ansluten",
    "Not connected": "Ej ansluten",
    "Email Settings": "E-postinställningar",
    "IMAP Server:": "IMAP-server:",
    "IMAP Port:": "IMAP-port:",
    "SMTP Server:": "SMTP-server:",
    "SMTP Port:": "SMTP-port:",
    "Email:": "E-post:",
    "Password:": "Lösenord:",
    "Save": "Spara",
    "Cancel": "Avbryt",
    "Message sent!": "Meddelandet skickat!",
    "Error": "Fel",
    "Could not send message": "Kunde inte skicka meddelandet",
    "Could not connect": "Kunde inte ansluta",
    "Could not load messages": "Kunde inte ladda meddelanden",
    "Are you sure you want to delete this message?": "Är du säker på att du vill ta bort detta meddelande?",
    "Delete Message": "Ta bort meddelande",
    "Mark as Read": "Markera som läst",
    "Mark as Unread": "Markera som oläst",
    "Welcome to SimpleMail!": "Välkommen till SimpleMail!",
    "Select a message to read it": "Välj ett meddelande för att läsa det",
    "About": "Om",
    "Accessible email client with pictogram support": "Tillgänglig e-postklient med piktogramstöd",
}


def _swedish_fallback(msg):
    """Return Swedish translation or original string."""
    return _SWEDISH.get(msg, msg)
