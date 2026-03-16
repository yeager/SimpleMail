# SimpleMail 📬

**Tillgänglig e-postklient med piktogramstöd och uppläsning**

SimpleMail är en e-postklient byggd med GTK4/Adwaita, designad för personer med
kognitiva funktionshinder. Appen har stora knappar, tydliga ikoner (piktogram),
text-till-tal-stöd och ett enkelt gränssnitt på svenska.

## Funktioner

- **Piktogramstöd** — Stora, tydliga ikoner för alla åtgärder (ARASAAC-kompatibel design)
- **Uppläsning** — Text-till-tal för att lyssna på e-post
- **Stort gränssnitt** — Stor text, stora knappar, hög kontrast
- **Svenska** — Svenskt gränssnitt med engelsk fallback
- **Säker** — Lösenord lagras i systemets nyckelring (keyring)
- **IMAP/SMTP** — Fungerar med alla standard-e-postleverantörer

## Installation

### Förutsättningar

**Ubuntu/Debian:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
    libgirepository1.0-dev espeak-ng
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-cairo espeak-ng
```

**Arch Linux:**
```bash
sudo pacman -S python-gobject gtk4 libadwaita python-cairo espeak-ng
```

**macOS (Homebrew):**
```bash
brew install pygobject3 gtk4 libadwaita espeak
```

### Installera SimpleMail

```bash
# Klona repot
git clone https://github.com/yeager/SimpleMail.git
cd SimpleMail

# Installera Python-beroenden
pip install -r requirements.txt

# Kompilera översättningar (valfritt)
mkdir -p simplemail/locale/sv/LC_MESSAGES
msgfmt po/sv.po -o simplemail/locale/sv/LC_MESSAGES/simplemail.mo

# Installera
pip install -e .
```

### Köra direkt

```bash
python -m simplemail.app
```

### Desktop-integration

```bash
cp data/simplemail.desktop ~/.local/share/applications/
cp data/icons/simplemail.svg ~/.local/share/icons/hicolor/scalable/apps/
update-desktop-database ~/.local/share/applications/
```

## Användning

1. **Starta** SimpleMail
2. **Inställningar** (kugghjulet) — Ange IMAP/SMTP-server, e-post och lösenord
3. **Anslut** — Tryck på Anslut-knappen
4. **Läs** — Klicka på ett meddelande i listan
5. **Lyssna** — Tryck på "Läs upp" för att höra meddelandet
6. **Svara** — Tryck på Svara-knappen
7. **Skriv nytt** — Tryck på "Skriv nytt"

## Vanliga e-postinställningar

| Leverantör | IMAP-server | IMAP-port | SMTP-server | SMTP-port |
|-----------|-------------|-----------|-------------|-----------|
| Gmail | imap.gmail.com | 993 | smtp.gmail.com | 587 |
| Outlook | outlook.office365.com | 993 | smtp.office365.com | 587 |
| Yahoo | imap.mail.yahoo.com | 993 | smtp.mail.yahoo.com | 587 |

> **Gmail:** Kräver "Applösenord" — skapa ett under Google-kontoinställningar.

## Översättning

SimpleMail använder gettext för lokalisering. För att lägga till ett nytt språk:

```bash
# Skapa ny .po-fil baserad på mallen
cp po/simplemail.pot po/XX.po
# Redigera po/XX.po med dina översättningar
# Kompilera
msgfmt po/XX.po -o simplemail/locale/XX/LC_MESSAGES/simplemail.mo
```

## Licens

GPL-3.0
