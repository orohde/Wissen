/* Wissen! – web UI (vanilla JS, Fundamental Styles) */
'use strict';

// ------------------------------------------------------------------ i18n

const I18N = {
  de: {
    "api.keys": "API-Schlüssel",
    "api.keys.hint": "Jedes Programm bekommt seinen eigenen Schlüssel, dann lässt sich einer allein widerrufen. „Lesen und schreiben“ öffnet alles wie ein Administrator, „Nur lesen“ zeigt alle Bereiche, ändert aber nichts.",
    "api.col.name": "Name",
    "api.col.right": "Recht",
    "api.col.made": "Angelegt",
    "api.col.last": "Zuletzt benutzt",
    "api.none2": "Noch kein Schlüssel. Die API geht dann nur mit angemeldetem Browser.",
    "api.name.ph": "Name, z. B. Claude oder Home Assistant",
    "api.right.write": "Lesen und schreiben",
    "api.right.read": "Nur lesen",
    "api.add": "Schlüssel anlegen",
    "api.fresh": "Das ist der neue Schlüssel. Jetzt kopieren – er wird nur einmal gezeigt.",
    "api.never": "noch nie",
    "api.renew": "Neu erzeugen",
    "api.renew.q": "Neuen Schlüssel für „{name}“ erzeugen? Der bisherige gilt sofort nicht mehr.",
    "api.del.q2": "Schlüssel „{name}“ löschen? Programme, die ihn benutzen, kommen dann nicht mehr hinein.",
    "api.saved": "„{name}“ gespeichert.",
    "err.a key with this name exists": "Einen Schlüssel mit diesem Namen gibt es schon.",
    "err.name must have 1 to 60 characters": "Der Name braucht 1 bis 60 Zeichen.",
    "kind.all": "Seiten und PDFs",
    "kind.pages": "Nur Seiten",
    "kind.pdfs": "Nur PDFs",
    "kind.page": "Seite",
    "kind.pdf": "PDF",
    "page.source": "Markdown",
    "login.user": "Benutzer",
    "login.pass": "Passwort",
    "login.submit": "Anmelden",
    "login.error": "Anmeldung fehlgeschlagen.",
    "app.logout": "Abmelden",
    "search.placeholder": "Suchen …",
    "list.recursive": "mit Unterordnern",
    "list.empty": "Keine Dokumente.",
    "list.more": "Mehr laden",
    "col.date": "Datum",
    "col.title": "Titel",
    "col.area": "Bereich",
    "sort.by": "Nach {col} sortieren",
    "home.tip": "Zur Startseite",
    "sort.best": "Beste Treffer zuerst",
    "sort.best.tip": "Suchergebnisse nach Übereinstimmung statt nach Datum ordnen – Treffer im Titel stehen oben",
    "pv.open": "Öffnen",
    "pv.download": "Herunterladen",
    "pv.none": "Für diesen Dateityp gibt es keine Vorschau.",
    "pv.bottom": "Lesebereich unten anzeigen",
    "pv.right": "Lesebereich rechts anzeigen",
    "pv.lay.bottom": "Unten",
    "pv.lay.right": "Rechts",
    "pv.gofolder": "Im Ordnerbaum zeigen",
    "st.trash": "Papierkorb",
    "st.trash.days": "Endgültig löschen nach",
    "st.trash.unit": "Tagen",
    "st.trash.hint": "Gelöschte Dokumente liegen im Papierkorb (.papierkorb im Archiv). Nach dieser Frist löscht Wissen! sie einmal am Tag endgültig. 0 heißt: nie.",
    "acc.lang": "Sprache",
    "acc.lang.hint": "Gilt für dieses Konto auf allen Geräten.",
    "tree.all": "Alle Ordner",
    "tree.root": "Hauptordner",
    "tree.expand": "Alle aufklappen",
    "tree.collapse": "Alle zuklappen",
    "list.search": "Suche",
    "tags.title": "Tags",
    "tags.ph": "Tag …",
    "tags.new": "+ Tag",
    "tags.add": "Tag hinzufügen",
    "tags.remove": "Tag entfernen",
    "tags.clearsel": "Auswahl aufheben",
    "tags.selall": "Alle auswählen",
    "tags.sel": "{n} ausgewählt",
    "tags.filter": "Tag",
    "tags.done": "{n} Dokument(e) geändert.",
    "tags.del": "Tag entfernen",
    "status.docs": "{n} Dokumente",
    "status.scan": "eingelesen {t}",
    "status.scanning": "liest ein …",
    "count.of": "{n} von {total}",
    "area.none": "(ohne)",
    "status.texts": "Texte {done}/{total}",
    "upd.btn": "Neue Version {v}",
    "upd.title": "Neue Version {v}",
    "upd.intro": "Installiert ist Version {cur}. Deine Dokumente und Einstellungen bleiben beim Update erhalten – sie liegen in deinen Ordnern und im Datenordner, nicht im Container.",
    "upd.how": "So aktualisierst du",
    "upd.notes": "Was ist neu",
    "upd.release": "Alle Änderungen ↗",
    "upd.close": "Schließen",
    "upd.unraid": "Docker → Compose → Stack „Wissen“ → „Compose Up“, nachdem das neue Image gebaut ist.",
    "upd.forgejo": "Normalerweise nichts zu tun: Nach jedem Push baut der Forgejo-Workflow das Image und startet Wissen! neu. Steht dieser Hinweis länger da, ist der Lauf hängen geblieben – in Forgejo unter „Actions“ nachsehen.",
    "upd.compose": "im Ordner mit dem Quellcode",
    "upd.card": "Neue Versionen",
    "upd.f.on": "Einmal am Tag nach neuen Versionen sehen",
    "upd.f.hint": "Wissen! fragt dafür bei version.worldgate.de nach. Übertragen werden nur App-Name, installierte Version und Installationsart (z. B. Docker) – keine Kennung, keine Dokumente, keine Namen. Dort werden nur Tagessummen gezählt. Dauerhaft abschalten lässt es sich auch mit VERSIONSPRUEFUNG=0.",
    "upd.f.locked": "Abgeschaltet über VERSIONSPRUEFUNG=0.",
    "upd.check": "Jetzt prüfen",
    "upd.checked": "Geprüft.",
    "upd.state.new": "Version {v} ist verfügbar (installiert: {cur}).",
    "upd.state.ok": "Aktuell: Version {cur} (zuletzt geprüft am {d}).",
    "upd.state.never": "Installiert: Version {cur}. Noch nicht geprüft.",
    "upd.state.err": "Die letzte Prüfung am {d} hat nicht geklappt (kein Internet?). Wissen! versucht es morgen wieder.",
    "upd.state.off": "Installiert: Version {cur}. Die Prüfung ist aus.",
    "set.title": "Einstellungen",
    "set.account": "Mein Konto",
    "set.users": "Benutzer",
    "set.system": "System",
    "set.ai": "KI",
    "set.back": "← Zurück zum Archiv",
    "set.storage": "Ablage",
    "st.intro": "Wo das Archiv liegt, wie lange der Papierkorb aufbewahrt und wie die Bereiche heißen. Für den Archivordner stehen die Ordner zur Auswahl, die dem Container zur Verfügung stehen.",
    "st.area.new": "Neuer Bereich",
    "st.area.name.ph": "Kurzname, z. B. haus",
    "st.area.label.ph": "Anzeigename, z. B. Haus Musterweg",
    "st.area.add": "Bereich anlegen",
    "st.area.hint2": "Ein Bereich ist ein Hauptordner im Archiv und muss keinem Konto gehören. Wer ihn sehen oder befüllen darf, legst du danach unter Benutzer fest.",
    "st.area.added": "Bereich „{name}“ angelegt. Rechte vergibst du unter Einstellungen → Benutzer.",
    "st.area.del": "Leeren Bereich entfernen",
    "st.area.del.q": "Leeren Bereich „{name}“ entfernen?",
    "err.invalid area name": "Kurzname: Kleinbuchstaben, Ziffern, Punkt, Binde- oder Unterstrich.",
    "err.area exists": "Diesen Bereich gibt es schon.",
    "err.area contains documents": "In diesem Bereich liegen Dokumente, er lässt sich nicht entfernen.",
    "dm.menu": "Dokument-Menü",
    "dm.open": "Öffnen",
    "dm.download": "Herunterladen",
    "dm.folder": "Im Ordnerbaum zeigen",
    "start.pinned": "Angepinnt",
    "start.recent": "Zuletzt geändert",
    "start.all": "Alle Dokumente →",
    "start.nopins": "Noch nichts angepinnt. Über den Stern an einem Dokument oder das Menü ⋯ in der Liste heftest du es hier an.",
    "start.norecent": "Noch keine Dokumente.",
    "start.changed": "geändert {d}",
    "ed.edit": "Bearbeiten",
    "ed.save": "Speichern",
    "ed.done": "Fertig",
    "ed.cancel": "Abbrechen",
    "ed.preview": "Vorschau",
    "ed.src": "Quelltext",
    "ed.dirty": "Ungespeicherte Änderungen",
    "ed.saved": "Gespeichert",
    "ed.saving": "Speichert …",
    "ed.discard": "Die ungespeicherten Änderungen verwerfen?",
    "ed.lost": "Die Sperre ist an {by} gegangen. Sichere deinen Text, bevor du die Seite verlässt.",
    "ed.upload": "Lädt {name} hoch …",
    "ed.menu": "Mehr",
    "new.page": "Neue Seite",
    "new.title": "Titel",
    "new.area": "Bereich",
    "new.folder": "Ordner",
    "new.folder.ph": "z. B. Haushalt/Küche – leer für den Hauptordner",
    "new.ok": "Anlegen",
    "dm.rename": "Umbenennen …",
    "dm.move": "Verschieben …",
    "dm.trash": "In den Papierkorb",
    "dm.editpage": "Bearbeiten",
    "rn.title": "Umbenennen",
    "rn.ok": "Umbenennen",
    "mv.title": "Verschieben",
    "mv.ok": "Verschieben",
    "tr.q": "„{title}“ in den Papierkorb legen?",
    "tr.hint": "Im Papierkorb bleibt das Dokument {days} Tage und lässt sich so lange zurückholen.",
    "tr.ok": "In den Papierkorb",
    "tr.done": "„{title}“ liegt im Papierkorb.",
    "tr.undo": "Zurückholen",
    "tr.back": "„{title}“ ist wieder da.",
    "rn.done": "Umbenannt in „{title}“.",
    "mv.done": "Verschoben nach {folder}.",
    "err.locked": "Wird gerade von {by} bearbeitet.",
    "err.lock required": "Die Bearbeitungssperre fehlt. Bitte „Bearbeiten“ erneut wählen.",
    "err.page changed meanwhile": "Die Seite wurde inzwischen an anderer Stelle geändert. Kopiere deinen Text, lade die Seite neu und füge ihn wieder ein.",
    "err.target exists": "Am Ziel liegt schon eine Datei mit diesem Namen.",
    "err.already in this folder": "Das Dokument liegt schon in diesem Ordner.",
    "err.nothing changed": "Es hat sich nichts geändert.",
    "err.no write access": "Dafür fehlt das Schreibrecht.",
    "err.archive is read-only": "Das Archiv ist nur lesend eingehängt – Ordner mit Dokumenten lassen sich erst nach dem Import umbenennen.",
    "err.invalid folder name": "Ungültiger Ordnername: {name}",
    "err.file too large": "Die Datei ist zu groß (höchstens 50 MB).",
    "err.file not found": "Die Datei wurde nicht gefunden.",
    "ed.rich": "Formatiert",
    "ed.mode": "Ansicht beim Bearbeiten",
    "ed.loading": "Editor wird geladen …",
    "ed.unsafe": "Diese Änderung lässt sich in der formatierten Ansicht nicht verlustfrei speichern. Du bist jetzt im Quelltext – bitte prüfe die Stelle und speichere dort.",
    "ed.loadfail": "Der Editor konnte nicht geladen werden.",
    "tb.bold": "Fett",
    "tb.italic": "Kursiv",
    "tb.strike": "Durchgestrichen",
    "tb.code": "Code im Text",
    "tb.h1": "Überschrift 1",
    "tb.h2": "Überschrift 2",
    "tb.h3": "Überschrift 3",
    "tb.text": "Normaler Absatz",
    "tb.bullets": "Aufzählung",
    "tb.numbers": "Nummerierte Liste",
    "tb.task": "Aufgabe (Kästchen)",
    "tb.indent": "Einrücken",
    "tb.outdent": "Ausrücken",
    "tb.quote": "Zitat",
    "tb.codeblock": "Codeblock",
    "tb.rule": "Trennlinie",
    "tb.link": "Link",
    "tb.image": "Bild oder Datei einfügen",
    "tb.table": "Tabelle einfügen",
    "tb.rowadd": "Zeile darunter",
    "tb.coladd": "Spalte rechts",
    "tb.rowdel": "Zeile löschen",
    "tb.coldel": "Spalte löschen",
    "tb.tabledel": "Tabelle löschen",
    "tb.undo": "Rückgängig",
    "tb.redo": "Wiederholen",
    "link.title": "Link einfügen",
    "link.url": "Adresse",
    "link.ok": "Einfügen",
    "zoom.tip": "Schriftgröße (Doppelklick: zurück auf 100 %)",
    "width.tip": "Lesebreite (Doppelklick: zurück auf 85 %)",
    "trash.title": "Papierkorb",
    "trash.open": "Papierkorb",
    "trash.empty": "Der Papierkorb ist leer.",
    "trash.note": "Was hier liegt, wird nach {days} Tagen endgültig gelöscht.",
    "trash.note.never": "Der Papierkorb wird nicht automatisch geleert.",
    "trash.col.title": "Titel",
    "trash.col.place": "Lag in",
    "trash.col.deleted": "Gelöscht am",
    "trash.col.left": "Bleibt noch",
    "trash.days": "{n} Tage",
    "trash.day": "1 Tag",
    "trash.today": "wird heute geleert",
    "trash.view": "Ansehen",
    "trash.restore": "Zurückholen",
    "ver.menu": "Versionen …",
    "ver.title": "Versionen: {title}",
    "ver.none": "Von dieser Seite gibt es noch keine früheren Fassungen.",
    "ver.diff": "Vergleich mit jetzt",
    "ver.text": "Text dieser Fassung",
    "ver.restore": "Diese Fassung zurückholen",
    "ver.same": "Diese Fassung unterscheidet sich nicht vom jetzigen Stand.",
    "ver.legend": "Rot: stand in dieser Fassung und fehlt jetzt. Grün: ist seitdem dazugekommen.",
    "ver.restore.q": "Die Fassung vom {at} zurückholen? Der jetzige Stand bleibt als Version erhalten.",
    "ver.restored": "Die Fassung vom {at} ist wieder die Seite.",
    "ver.close": "Schließen",
    "ver.before": "Stand vor dem Speichern",
    "pin.on": "An die Startseite pinnen",
    "pin.off": "Von der Startseite lösen",
    "pin.done": "„{title}“ ist angepinnt.",
    "pin.undone": "„{title}“ ist gelöst.",
    "pin.undo": "Rückgängig",
    "err.too many pins": "Mehr als 200 Dokumente lassen sich nicht anpinnen.",
    "err.unknown area": "Bitte einen Bereich wählen.",
    "err.cannot delete": "Die Datei ließ sich nicht löschen (Eingangsordner schreibgeschützt?).",
    "err.title missing": "Bitte einen Titel eingeben.",
    "err.AI is disabled": "KI ist in den Einstellungen nicht eingeschaltet.",
    "st.areas": "Bereiche",
    "st.areas.hint": "Anzeigename je Bereich. Leer lassen = Anzeigename des gleichnamigen Kontos bzw. der Ordnername.",
    "st.archive": "Archivordner",
    "st.path": "Pfad",
    "st.browse": "Durchsuchen",
    "st.ok.rw": "vorhanden · lesbar · beschreibbar",
    "st.ok.ro": "vorhanden · nur lesbar",
    "st.missing": "nicht vorhanden oder nicht lesbar",
    "st.files": "{n} Dateien darin",
    "st.saved": "Gespeichert.",
    "st.choose": "Diesen Ordner wählen",
    "st.up": "eine Ebene höher",
    "st.roots": "Verfügbare Ordner",
    "st.nodirs": "keine Unterordner",
    "err.archive folder not readable": "Der Archivordner ist nicht vorhanden oder nicht lesbar.",
    "err.absolute path required": "Bitte einen vollständigen Pfad angeben (beginnt mit /).",
    "ai.intro": "Wie Wissen! mit künstlicher Intelligenz zusammenarbeitet.",
    "mcp.title": "Zugang für KI-Assistenten (MCP)",
    "mcp.hint": "Über diesen Zugang kann ein KI-Assistent wie Claude in Wissen! suchen, lesen und – mit einem Schlüssel, der schreiben darf – Seiten anlegen und ändern. Rechte, Sperre, Versionen und Papierkorb gelten dabei wie in der Oberfläche.",
    "mcp.on": "MCP-Zugang einschalten",
    "mcp.url": "Adresse",
    "mcp.keys": "Der Assistent meldet sich mit einem API-Schlüssel an. Schlüssel legst du unter Einstellungen → API an, nur lesend oder lesend und schreibend.",
    "mcp.keys.link": "Zu den API-Schlüsseln",
    "mcp.saved.on": "Der MCP-Zugang ist eingeschaltet.",
    "mcp.saved.off": "Der MCP-Zugang ist ausgeschaltet.",
    "ai.enabled": "Fragen ans Archiv mit KI beantworten",
    "ask.set.title": "Fragen ans Archiv",
    "ask.set.hint": "Stellst du im Suchfeld eine Frage, sucht Wissen! die passenden Stellen aus deinen Seiten und PDFs heraus und lässt die KI daraus antworten – mit Quellenangabe. An den Anbieter gehen nur die Frage und diese Textstellen, nie das ganze Archiv und nie ein ausgenommener Bereich. Die KI schreibt nichts in dein Archiv.",
    "ask.btn": "KI fragen",
    "ask.btn.tip": "Die Frage aus dem Suchfeld von der KI aus dem Archiv beantworten lassen (Eingabetaste)",
    "ask.title": "Antwort aus dem Archiv",
    "ask.loading": "Suche die passenden Stellen und frage die KI …",
    "ask.none": "Dazu habe ich im Archiv keine passende Stelle gefunden. Versuch es mit anderen Worten oder der normalen Suche.",
    "ask.sources": "Quellen",
    "ask.page": "Seite {n}",
    "ask.close": "Schließen",
    "ask.note": "Antwort von {model} in {seconds} s aus {n} Textstellen. Die KI kann sich irren – die Quellen zeigen, wo es steht.",
    "ai.provider": "Anbieter",
    "ai.openai": "Anderer OpenAI-kompatibler Server",
    "ai.ollama": "Ollama (eigener Server)",
    "ai.baseurl": "Server-Adresse",
    "ai.model": "Modell",
    "ai.key": "API-Schlüssel",
    "ai.clearkey": "Entfernen",
    "ai.limit": "Monatslimit (USD)",
    "ai.exclude": "Nie an die KI senden",
    "ai.test": "Verbindung testen",
    "ai.key.set": "gespeichert ({hint}) – leer lassen = unverändert",
    "ai.key.none": "noch kein Schlüssel hinterlegt",
    "ai.key.local": "bei lokalen Servern meist nicht nötig",
    "ai.price": "{input} $ / {output} $ je 1 Mio. Token (Eingabe / Ausgabe)",
    "ai.price.none": "Preis unbekannt – Verbrauch wird nur in Token gezählt",
    "ai.usage": "{month}: {cost} $ verbraucht, {calls} Anfragen",
    "ai.saved": "Gespeichert.",
    "ai.testing": "Teste …",
    "ai.test.ok": "Antwort von {model} in {seconds} s: „{text}“ ({cost} $)",
    "err.no API key": "Es ist kein API-Schlüssel hinterlegt.",
    "err.API key rejected": "Der API-Schlüssel wurde abgelehnt.",
    "err.monthly limit reached": "Das Monatslimit ist erreicht.",
    "err.no server address": "Es fehlt die Server-Adresse.",
    "err.cannot reach the Anthropic API": "Die Anthropic-API ist nicht erreichbar.",
    "err.unknown model": "Das Modell „{model}“ kennt der Anbieter nicht.",
    "err.not an Anthropic key": "Das ist kein Anthropic-Schlüssel (er beginnt mit sk-ant-). Hat ein Passwortmanager das Feld gefüllt?",
    "ai.other": "Anderes Modell eingeben …",
    "ai.reload": "Liste neu laden",
    "ai.models.loading": "Frage verfügbare Modelle ab …",
    "ai.models.live": "{n} Modelle vom Anbieter abgefragt",
    "ai.models.builtin": "Eingebaute Liste – Abfrage beim Anbieter nicht möglich: {reason}",
    "acc.who": "Angemeldet als {name}",
    "acc.old": "Aktuelles Passwort",
    "acc.new": "Neues Passwort",
    "acc.change": "Passwort ändern",
    "acc.ok": "Passwort geändert.",
    "login.code": "Code aus der App",
    "login.code.hint": "Oder einer deiner Wiederherstellungscodes.",
    "login.need.code": "Bitte den Code aus deiner Authenticator-App eingeben.",
    "login.bad.code": "Der Code stimmt nicht oder wurde schon benutzt.",
    "login.locked": "Zu viele Fehlversuche. Bitte in {s} Sekunden noch einmal versuchen.",
    "login.need.2fa": "Von außen geht die Anmeldung nur mit zweitem Faktor. Richte ihn im Heimnetz unter Einstellungen → Mein Konto ein.",
    "acc.ok.out": "Passwort geändert. {n} andere Geräte wurden abgemeldet.",
    "mfa.title": "Zweiter Faktor",
    "mfa.state.on": "Eingeschaltet. Von außen fragt Wissen! nach dem Code aus der App. Noch {n} Wiederherstellungscodes übrig.",
    "mfa.state.off": "Nicht eingerichtet. Mit einem zweiten Faktor reicht ein gestohlenes Passwort nicht mehr, um von außen hineinzukommen.",
    "mfa.setup": "Einrichten",
    "mfa.scan": "Scanne den Code mit einer Authenticator-App (zum Beispiel Bitwarden, 2FAS, Aegis oder Google Authenticator) und gib dann die sechs Ziffern ein, die sie anzeigt.",
    "mfa.manual": "Oder von Hand eingeben:",
    "mfa.confirm": "Einschalten",
    "mfa.codes.hint": "Deine Wiederherstellungscodes. Mit jedem kommst du einmal hinein, falls das Telefon weg ist. Lege sie jetzt sicher ab, zum Beispiel im Passwortmanager. Wissen! zeigt sie nicht noch einmal.",
    "mfa.copy": "Kopieren",
    "mfa.copied": "Kopiert.",
    "mfa.done": "Ich habe sie gesichert",
    "mfa.renew": "Neue Wiederherstellungscodes",
    "mfa.off": "Zweiten Faktor ausschalten",
    "mfa.code.or": "Code oder Wiederherstellungscode",
    "mfa.off.btn": "Ausschalten",
    "mfa.off.q": "Zweiten Faktor wirklich ausschalten? Von außen reicht dann wieder das Passwort.",
    "mfa.off.ok": "Der zweite Faktor ist aus.",
    "ses.title": "Angemeldete Geräte",
    "ses.others": "Alle anderen abmelden",
    "ses.this": "dieses Gerät",
    "ses.out": "von außen",
    "ses.in": "Heimnetz",
    "ses.mfa": "mit Code",
    "ses.seen": "zuletzt {time}",
    "ses.since": "angemeldet {time}",
    "ses.end": "Abmelden",
    "ses.ended": "{n} Geräte abgemeldet.",
    "usr.mfa": "Zweiter Faktor",
    "usr.mfa.on": "an",
    "usr.mfa.off": "aus",
    "usr.signout": "Auf allen Geräten abmelden",
    "usr.resettotp": "Zweiten Faktor zurücksetzen (wenn das Telefon verloren ist)",
    "set.security": "Sicherheit",
    "setup.intro": "Willkommen! Noch gibt es kein Konto. Lege jetzt den ersten Administrator an – weitere Konten folgen später unter Einstellungen → Benutzer.",
    "setup.name": "Anzeigename",
    "setup.pass2": "Passwort wiederholen",
    "setup.hint": "Mindestens 12 Zeichen. Den zweiten Faktor richtest du danach unter Mein Konto ein.",
    "setup.submit": "Konto anlegen",
    "setup.mismatch": "Die beiden Passwörter sind nicht gleich.",
    "setup.short": "Das Passwort braucht mindestens 12 Zeichen.",
    "setup.badname": "Benutzername: nur Kleinbuchstaben, Ziffern, Punkt, Binde- und Unterstrich.",
    "setup.outside": "Die Ersteinrichtung geht nur aus dem Heimnetz. Öffne Wissen! zu Hause oder über das VPN.",
    "setup.done": "Es gibt schon ein Konto – bitte anmelden.",
    "sys.work": "Hintergrundarbeit",
    "sys.f.ocr": "Texterkennung für Scans",
    "sys.f.ocr.hint": "Liest Text aus gescannten Seiten, damit die Suche sie findet. Aus: nur Dokumente mit eingebettetem Text werden durchsuchbar.",
    "sys.f.lang": "Sprachen",
    "sys.f.pages": "Höchstens Seiten je Dokument",
    "sys.f.rescan": "Neu einlesen alle (Min.)",
    "sys.f.workers": "Dokumente gleichzeitig lesen",
    "sys.f.hint": "Änderungen gelten sofort, ohne Neustart. Schon gelesene Dokumente werden nicht noch einmal gelesen.",
    "sys.f.defaults": "Standardwerte",
    "sys.f.langs": "Installiert: {list}. Mehrere mit + verbinden, z. B. deu+eng.",
    "sys.f.nolangs": "Tesseract ist nicht installiert, Texterkennung ist nicht möglich.",
    "sys.f.cpus": "Der Rechner hat {n} Kerne. Mehr gleichzeitig ist schneller, belastet den Server aber stärker.",
    "sec.nets": "Heimnetz",
    "sec.nets.hint": "Adressbereiche, die als „zu Hause“ gelten (LAN, VPN). Alles andere ist „von außen“. Leer lassen für die Vorgabe.",
    "sec.nets.here": "Deine Adresse gerade: {ip} ({where}).",
    "sec.nets.in": "zählt als Heimnetz",
    "sec.nets.out": "zählt als außen",
    "err.own address": "Deine eigene Adresse {ip} zählte dann nicht mehr als Heimnetz. Nimm ihren Bereich mit auf.",
    "err.not a network": "„{net}“ ist kein Adressbereich (Beispiel: 192.168.1.0/24).",
    "err.range": "Bitte eine Zahl von {low} bis {high}.",
    "err.languages like deu+eng": "Sprachen bitte wie deu+eng angeben.",
    "set.api": "API",
    "api.intro": "Alles, was die Oberfläche kann, geht auch per REST-API unter /api/, für Skripte, Kurzbefehle oder Home Assistant.",
    "api.copy": "Kopieren",
    "api.del": "Löschen",
    "api.copied": "Schlüssel kopiert",
    "api.ref": "Beschreibung aller Endpunkte",
    "api.ref.hint": "Wissen! beschreibt seine API selbst: jeder Endpunkt mit Parametern und Antwort, direkt im Browser ausprobierbar (mit deiner Anmeldung).",
    "api.open": "API-Beschreibung öffnen",
    "api.guide": "Anleitung mit Beispielen",
    "sec.policy": "Anmeldung",
    "sec.ext": "Von außen nur mit zweitem Faktor",
    "sec.ext.hint": "Konten ohne zweiten Faktor können sich dann nur noch im Heimnetz anmelden. Einschalten lässt sich das erst, wenn dein eigenes Konto einen hat.",
    "sec.int": "Zweiten Faktor auch im Heimnetz verlangen",
    "sec.int.hint": "Sonst reicht zu Hause das Passwort. Von außen fragt Wissen! immer nach dem Code, wenn ein Konto einen zweiten Faktor hat.",
    "sec.without": "Noch ohne zweiten Faktor: {names}. Diese Konten kommen dann nur noch im Heimnetz hinein.",
    "sec.ntfy": "Benachrichtigungen per ntfy",
    "sec.url": "Topic-Adresse",
    "sec.token": "Zugangs-Token",
    "sec.token.set": "gespeichert – leer lassen = unverändert",
    "sec.when": "Melden bei",
    "sec.n.ext": "jeder Anmeldung von außen",
    "sec.n.lock": "gesperrtem Konto nach Fehlversuchen",
    "sec.n.2fa": "Änderungen am zweiten Faktor und benutzten Wiederherstellungscodes",
    "sec.test": "Testnachricht",
    "sec.test.ok": "Testnachricht verschickt.",
    "sec.saved": "Gespeichert.",
    "sec.where.in": "Du bist gerade im Heimnetz angemeldet.",
    "sec.where.out": "Du bist gerade von außen angemeldet.",
    "err.invalid code": "Der Code stimmt nicht.",
    "err.second factor already on": "Der zweite Faktor ist schon eingeschaltet.",
    "err.no second factor being set up": "Bitte die Einrichtung neu beginnen.",
    "err.set up your own second factor first": "Richte zuerst für dein eigenes Konto den zweiten Faktor ein, sonst sperrst du dich von außen aus.",
    "err.ntfy address must start with http:// or https://": "Die ntfy-Adresse muss mit http:// oder https:// beginnen.",
    "err.cross-site request refused": "Anfrage von einer fremden Seite abgelehnt.",
    "err.only for personal accounts": "Das geht nur mit einem persönlichen Konto.",
    "err.not configured": "Erst eine Topic-Adresse eintragen und speichern.",
    "usr.new": "Neuer Benutzer",
    "usr.edit": "Benutzer {name} bearbeiten",
    "usr.name": "Benutzer",
    "usr.display": "Anzeigename",
    "usr.pass": "Passwort",
    "usr.pass.keep": "leer lassen = unverändert",
    "usr.role": "Rolle",
    "usr.areas": "Bereiche",
    "usr.admin": "Administrator (sieht alle Bereiche, darf Einstellungen ändern)",
    "usr.adminrole": "Admin",
    "usr.userrole": "Benutzer",
    "usr.all": "alle",
    "usr.none": "keine",
    "usr.delete.q": "Benutzer {name} wirklich löschen?",
    "perm.none": "kein Zugriff",
    "perm.read": "lesen",
    "perm.write": "lesen + schreiben",
    "btn.cancel": "Abbrechen",
    "btn.save": "Speichern",
    "btn.edit": "Bearbeiten",
    "btn.delete": "Löschen",
    "sys.version": "Version",
    "sys.docs": "Dokumente",
    "sys.scan": "Zuletzt eingelesen",
    "sys.texts": "Texte erkannt",
    "sys.ocr": "Seiten per Texterkennung",
    "sys.ocrstate": "Texterkennung (OCR)",
    "sys.on": "aktiv",
    "sys.off": "nicht verfügbar",
    "sys.err.title": "Dokumente ohne lesbaren Text",
    "sys.err.hint": "Diese Dokumente lassen sich öffnen, nur ihr Text fehlt in der Volltextsuche. Über Titel und Ordner findest du sie trotzdem.",
    "sys.err.password": "mit Passwort geschützt – den Text kann Wissen! nicht lesen",
    "sys.err.missing": "Datei fehlte beim Lesen – wird neu versucht",
    "sys.err.damaged": "Datei beschädigt oder kein gültiges PDF",
    "sys.err.other": "Unbekannter Fehler",
    "sys.err.retry": "Erneut lesen",
    "sys.err.retried": "{n} Dokument(e) werden neu gelesen.",
    "sys.errors": "Fehler beim Lesen",
    "sys.mode": "Archiv",
    "sys.readonly": "nur lesend",
    "sys.writable": "beschreibbar",
    "sys.rescan": "Ordner jetzt neu einlesen",
    "sys.rescan.ok": "Einlesen gestartet.",
    "err.user exists": "Diesen Benutzer gibt es schon.",
    "err.invalid user name": "Nur Kleinbuchstaben, Ziffern, . _ - erlaubt.",
    "err.last administrator": "Der letzte Administrator kann nicht entfernt werden.",
    "err.wrong password": "Aktuelles Passwort stimmt nicht.",
    "err.cannot delete yourself": "Du kannst dich nicht selbst löschen.",
    "err.cannot remove your own admin role": "Die eigene Admin-Rolle kann man nicht abgeben.",
    "err.password too short (min. 12)": "Das Passwort braucht mindestens 12 Zeichen.",
  },
  en: {
    "api.keys": "API keys",
    "api.keys.hint": "Give every program its own key, so one can be revoked on its own. “Read and write” opens everything like an administrator, “Read only” shows all areas but changes nothing.",
    "api.col.name": "Name",
    "api.col.right": "Right",
    "api.col.made": "Created",
    "api.col.last": "Last used",
    "api.none2": "No key yet. The API then only works with a signed-in browser.",
    "api.name.ph": "Name, e.g. Claude or Home Assistant",
    "api.right.write": "Read and write",
    "api.right.read": "Read only",
    "api.add": "Create key",
    "api.fresh": "This is the new key. Copy it now – it is shown only once.",
    "api.never": "never",
    "api.renew": "Renew",
    "api.renew.q": "Create a new key for “{name}”? The current one stops working at once.",
    "api.del.q2": "Delete the key “{name}”? Programs using it can no longer get in.",
    "api.saved": "“{name}” saved.",
    "err.a key with this name exists": "There is already a key with this name.",
    "err.name must have 1 to 60 characters": "The name needs 1 to 60 characters.",
    "kind.all": "Pages and PDFs",
    "kind.pages": "Pages only",
    "kind.pdfs": "PDFs only",
    "kind.page": "Page",
    "kind.pdf": "PDF",
    "page.source": "Markdown",
    "login.user": "User",
    "login.pass": "Password",
    "login.submit": "Sign in",
    "login.error": "Sign-in failed.",
    "app.logout": "Sign out",
    "search.placeholder": "Search …",
    "list.recursive": "include subfolders",
    "list.empty": "No documents.",
    "list.more": "Load more",
    "col.date": "Date",
    "col.title": "Title",
    "col.area": "Area",
    "sort.by": "Sort by {col}",
    "home.tip": "To the start page",
    "sort.best": "Best matches first",
    "sort.best.tip": "Order search results by match instead of date – hits in the title come first",
    "pv.open": "Open",
    "pv.download": "Download",
    "pv.none": "No preview for this file type.",
    "pv.bottom": "Show reading pane below",
    "pv.right": "Show reading pane on the right",
    "pv.lay.bottom": "Below",
    "pv.lay.right": "Right",
    "pv.gofolder": "Show in the folder tree",
    "st.trash": "Trash",
    "st.trash.days": "Delete for good after",
    "st.trash.unit": "days",
    "st.trash.hint": "Deleted documents go to the trash (.papierkorb in the archive). After this period Wissen! deletes them for good, once a day. 0 means never.",
    "acc.lang": "Language",
    "acc.lang.hint": "For this account, on all devices.",
    "tree.all": "All folders",
    "tree.root": "Main folder",
    "tree.expand": "Expand all",
    "tree.collapse": "Collapse all",
    "list.search": "Search",
    "tags.title": "Tags",
    "tags.ph": "Tag …",
    "tags.new": "+ tag",
    "tags.add": "Add tag",
    "tags.remove": "Remove tag",
    "tags.clearsel": "Clear selection",
    "tags.selall": "Select all",
    "tags.sel": "{n} selected",
    "tags.filter": "Tag",
    "tags.done": "{n} document(s) changed.",
    "tags.del": "Remove tag",
    "status.docs": "{n} documents",
    "status.scan": "scanned {t}",
    "status.scanning": "scanning …",
    "count.of": "{n} of {total}",
    "area.none": "(none)",
    "status.texts": "Texts {done}/{total}",
    "upd.btn": "New version {v}",
    "upd.title": "New version {v}",
    "upd.intro": "Installed: version {cur}. Your documents and settings are kept during the update – they live in your folders and the data folder, not in the container.",
    "upd.how": "How to update",
    "upd.notes": "What’s new",
    "upd.release": "All changes ↗",
    "upd.close": "Close",
    "upd.unraid": "Docker → Compose → stack “Wissen” → “Compose Up”, once the new image is built.",
    "upd.forgejo": "Usually nothing to do: after every push the Forgejo workflow builds the image and restarts Wissen!. If this notice stays, the run got stuck – look under “Actions” in Forgejo.",
    "upd.compose": "in the folder with the source code",
    "upd.card": "New versions",
    "upd.f.on": "Look for new versions once a day",
    "upd.f.hint": "Wissen! asks version.worldgate.de. Only the app name, the installed version and the kind of installation (e.g. Docker) are sent – no identifier, no documents, no names. Only daily totals are counted there. Switch it off for good with VERSIONSPRUEFUNG=0.",
    "upd.f.locked": "Switched off by VERSIONSPRUEFUNG=0.",
    "upd.check": "Check now",
    "upd.checked": "Checked.",
    "upd.state.new": "Version {v} is available (installed: {cur}).",
    "upd.state.ok": "Up to date: version {cur} (last checked {d}).",
    "upd.state.never": "Installed: version {cur}. Not checked yet.",
    "upd.state.err": "The last check on {d} failed (no internet?). Wissen! tries again tomorrow.",
    "upd.state.off": "Installed: version {cur}. The check is off.",
    "set.title": "Settings",
    "set.account": "My account",
    "set.users": "Users",
    "set.system": "System",
    "set.ai": "AI",
    "set.back": "← Back to the archive",
    "set.storage": "Storage",
    "st.intro": "Where the archive lives, how long the trash keeps things and what the areas are called. The archive folder is picked from the folders available to the container.",
    "st.area.new": "New area",
    "st.area.name.ph": "Short name, e.g. house",
    "st.area.label.ph": "Display name, e.g. House Sample Road",
    "st.area.add": "Create area",
    "st.area.hint2": "An area is a top folder in the archive and does not have to belong to an account. Who may see or fill it is set afterwards under Users.",
    "st.area.added": "Area “{name}” created. Grant rights under Settings → Users.",
    "st.area.del": "Remove empty area",
    "st.area.del.q": "Remove the empty area “{name}”?",
    "err.invalid area name": "Short name: lowercase letters, digits, dot, hyphen or underscore.",
    "err.area exists": "This area already exists.",
    "err.area contains documents": "This area holds documents and cannot be removed.",
    "dm.menu": "Document menu",
    "dm.open": "Open",
    "dm.download": "Download",
    "dm.folder": "Show in the folder tree",
    "start.pinned": "Pinned",
    "start.recent": "Last changed",
    "start.all": "All documents →",
    "start.nopins": "Nothing pinned yet. Use the star on a document or the ⋯ menu in the list to pin it here.",
    "start.norecent": "No documents yet.",
    "start.changed": "changed {d}",
    "ed.edit": "Edit",
    "ed.save": "Save",
    "ed.done": "Done",
    "ed.cancel": "Cancel",
    "ed.preview": "Preview",
    "ed.src": "Source",
    "ed.dirty": "Unsaved changes",
    "ed.saved": "Saved",
    "ed.saving": "Saving …",
    "ed.discard": "Discard the unsaved changes?",
    "ed.lost": "The lock went to {by}. Keep a copy of your text before you leave the page.",
    "ed.upload": "Uploading {name} …",
    "ed.menu": "More",
    "new.page": "New page",
    "new.title": "Title",
    "new.area": "Area",
    "new.folder": "Folder",
    "new.folder.ph": "e.g. Household/Kitchen – empty for the main folder",
    "new.ok": "Create",
    "dm.rename": "Rename …",
    "dm.move": "Move …",
    "dm.trash": "Move to trash",
    "dm.editpage": "Edit",
    "rn.title": "Rename",
    "rn.ok": "Rename",
    "mv.title": "Move",
    "mv.ok": "Move",
    "tr.q": "Move “{title}” to the trash?",
    "tr.hint": "It stays in the trash for {days} days and can be put back until then.",
    "tr.ok": "Move to the trash",
    "tr.done": "“{title}” is in the trash.",
    "tr.undo": "Put back",
    "tr.back": "“{title}” is back.",
    "rn.done": "Renamed to “{title}”.",
    "mv.done": "Moved to {folder}.",
    "err.locked": "Being edited by {by} right now.",
    "err.lock required": "The editing lock is missing. Please choose “Edit” again.",
    "err.page changed meanwhile": "The page was changed elsewhere meanwhile. Copy your text, reload the page and paste it again.",
    "err.target exists": "A file with this name already exists there.",
    "err.already in this folder": "The document is in this folder already.",
    "err.nothing changed": "Nothing changed.",
    "err.no write access": "You have no write access for this.",
    "err.archive is read-only": "The archive is mounted read-only – folders with documents can be renamed after the import.",
    "err.invalid folder name": "Invalid folder name: {name}",
    "err.file too large": "The file is too large (50 MB at most).",
    "err.file not found": "The file was not found.",
    "ed.rich": "Formatted",
    "ed.mode": "View while editing",
    "ed.loading": "Loading the editor …",
    "ed.unsafe": "This change cannot be saved from the formatted view without loss. You are in the source now – please check the spot and save there.",
    "ed.loadfail": "The editor could not be loaded.",
    "tb.bold": "Bold",
    "tb.italic": "Italic",
    "tb.strike": "Strikethrough",
    "tb.code": "Inline code",
    "tb.h1": "Heading 1",
    "tb.h2": "Heading 2",
    "tb.h3": "Heading 3",
    "tb.text": "Plain paragraph",
    "tb.bullets": "Bullet list",
    "tb.numbers": "Numbered list",
    "tb.task": "Task (checkbox)",
    "tb.indent": "Indent",
    "tb.outdent": "Outdent",
    "tb.quote": "Quote",
    "tb.codeblock": "Code block",
    "tb.rule": "Divider",
    "tb.link": "Link",
    "tb.image": "Insert picture or file",
    "tb.table": "Insert table",
    "tb.rowadd": "Row below",
    "tb.coladd": "Column to the right",
    "tb.rowdel": "Delete row",
    "tb.coldel": "Delete column",
    "tb.tabledel": "Delete table",
    "tb.undo": "Undo",
    "tb.redo": "Redo",
    "link.title": "Insert link",
    "link.url": "Address",
    "link.ok": "Insert",
    "zoom.tip": "Text size (double click: back to 100 %)",
    "width.tip": "Reading width (double click: back to 85 %)",
    "trash.title": "Trash",
    "trash.open": "Trash",
    "trash.empty": "The trash is empty.",
    "trash.note": "What lies here is deleted for good after {days} days.",
    "trash.note.never": "The trash is not emptied automatically.",
    "trash.col.title": "Title",
    "trash.col.place": "Was in",
    "trash.col.deleted": "Deleted on",
    "trash.col.left": "Stays for",
    "trash.days": "{n} days",
    "trash.day": "1 day",
    "trash.today": "emptied today",
    "trash.view": "View",
    "trash.restore": "Put back",
    "ver.menu": "Versions …",
    "ver.title": "Versions: {title}",
    "ver.none": "There are no earlier versions of this page yet.",
    "ver.diff": "Compare with now",
    "ver.text": "Text of this version",
    "ver.restore": "Restore this version",
    "ver.same": "This version does not differ from the page as it is now.",
    "ver.legend": "Red: was in this version and is gone now. Green: added since.",
    "ver.restore.q": "Restore the version of {at}? The current text is kept as a version.",
    "ver.restored": "The version of {at} is the page again.",
    "ver.close": "Close",
    "ver.before": "Text before the save",
    "pin.on": "Pin to the start page",
    "pin.off": "Remove from the start page",
    "pin.done": "“{title}” is pinned.",
    "pin.undone": "“{title}” is no longer pinned.",
    "pin.undo": "Undo",
    "err.too many pins": "No more than 200 documents can be pinned.",
    "err.unknown area": "Please choose an area.",
    "err.cannot delete": "The file could not be deleted (inbox folder read-only?).",
    "err.title missing": "Please enter a title.",
    "err.AI is disabled": "AI is not switched on in the settings.",
    "st.areas": "Areas",
    "st.areas.hint": "Display name per area. Leave empty to use the matching account’s display name or the folder name.",
    "st.archive": "Archive folder",
    "st.path": "Path",
    "st.browse": "Browse",
    "st.ok.rw": "exists · readable · writable",
    "st.ok.ro": "exists · read-only",
    "st.missing": "missing or not readable",
    "st.files": "{n} files inside",
    "st.saved": "Saved.",
    "st.choose": "Choose this folder",
    "st.up": "one level up",
    "st.roots": "Available folders",
    "st.nodirs": "no subfolders",
    "err.archive folder not readable": "The archive folder is missing or not readable.",
    "err.absolute path required": "Please enter a full path (starting with /).",
    "ai.intro": "How Wissen! works together with artificial intelligence.",
    "mcp.title": "Access for AI assistants (MCP)",
    "mcp.hint": "Through this access an AI assistant such as Claude can search and read in Wissen! and – with a key that may write – create and change pages. Rights, the editing lock, versions and the trash apply as in the interface.",
    "mcp.on": "Switch MCP access on",
    "mcp.url": "Address",
    "mcp.keys": "The assistant signs in with an API key. Keys are made under Settings → API, read-only or read and write.",
    "mcp.keys.link": "To the API keys",
    "mcp.saved.on": "MCP access is on.",
    "mcp.saved.off": "MCP access is off.",
    "ai.enabled": "Answer questions to the archive with AI",
    "ask.set.title": "Questions to the archive",
    "ask.set.hint": "When you type a question into the search field, Wissen! picks the fitting passages from your pages and PDFs and lets the AI answer from them – naming its sources. Only the question and these passages go to the provider, never the whole archive and never an excluded area. The AI writes nothing into your archive.",
    "ask.btn": "Ask the AI",
    "ask.btn.tip": "Have the AI answer the question in the search field from the archive (Enter)",
    "ask.title": "Answer from the archive",
    "ask.loading": "Looking for the fitting passages and asking the AI …",
    "ask.none": "I found no fitting passage in the archive. Try other words or the ordinary search.",
    "ask.sources": "Sources",
    "ask.page": "page {n}",
    "ask.close": "Close",
    "ask.note": "Answer by {model} in {seconds} s from {n} passages. The AI can be wrong – the sources show where it says so.",
    "ai.provider": "Provider",
    "ai.openai": "Other OpenAI-compatible server",
    "ai.ollama": "Ollama (own server)",
    "ai.baseurl": "Server address",
    "ai.model": "Model",
    "ai.key": "API key",
    "ai.clearkey": "Remove",
    "ai.limit": "Monthly limit (USD)",
    "ai.exclude": "Never send to the AI",
    "ai.test": "Test connection",
    "ai.key.set": "stored ({hint}) – leave empty to keep",
    "ai.key.none": "no key stored yet",
    "ai.key.local": "usually not needed for local servers",
    "ai.price": "{input} $ / {output} $ per million tokens (input / output)",
    "ai.price.none": "unknown price – usage is counted in tokens only",
    "ai.usage": "{month}: {cost} $ spent, {calls} requests",
    "ai.saved": "Saved.",
    "ai.testing": "Testing …",
    "ai.test.ok": "Answer from {model} in {seconds} s: “{text}” ({cost} $)",
    "err.no API key": "No API key stored.",
    "err.API key rejected": "The API key was rejected.",
    "err.monthly limit reached": "The monthly limit has been reached.",
    "err.no server address": "The server address is missing.",
    "err.cannot reach the Anthropic API": "The Anthropic API cannot be reached.",
    "err.unknown model": "The provider does not know the model “{model}”.",
    "err.not an Anthropic key": "This is not an Anthropic key (those start with sk-ant-). Did a password manager fill the field?",
    "ai.other": "Enter another model …",
    "ai.reload": "Reload list",
    "ai.models.loading": "Asking for available models …",
    "ai.models.live": "{n} models from the provider",
    "ai.models.builtin": "Built-in list – could not ask the provider: {reason}",
    "acc.who": "Signed in as {name}",
    "acc.old": "Current password",
    "acc.new": "New password",
    "acc.change": "Change password",
    "acc.ok": "Password changed.",
    "login.code": "Code from the app",
    "login.code.hint": "Or one of your recovery codes.",
    "login.need.code": "Please enter the code from your authenticator app.",
    "login.bad.code": "The code is wrong or was already used.",
    "login.locked": "Too many failed attempts. Please try again in {s} seconds.",
    "login.need.2fa": "From outside, signing in needs a second factor. Set it up at home under Settings → My account.",
    "acc.ok.out": "Password changed. {n} other devices were signed out.",
    "mfa.title": "Second factor",
    "mfa.state.on": "On. From outside, Wissen! asks for the code from the app. {n} recovery codes left.",
    "mfa.state.off": "Not set up. With a second factor, a stolen password is no longer enough to get in from outside.",
    "mfa.setup": "Set up",
    "mfa.scan": "Scan the code with an authenticator app (for example Bitwarden, 2FAS, Aegis or Google Authenticator), then enter the six digits it shows.",
    "mfa.manual": "Or enter it by hand:",
    "mfa.confirm": "Turn on",
    "mfa.codes.hint": "Your recovery codes. Each gets you in once if your phone is gone. Store them safely now, for example in your password manager. Wissen! will not show them again.",
    "mfa.copy": "Copy",
    "mfa.copied": "Copied.",
    "mfa.done": "I have saved them",
    "mfa.renew": "New recovery codes",
    "mfa.off": "Turn off second factor",
    "mfa.code.or": "Code or recovery code",
    "mfa.off.btn": "Turn off",
    "mfa.off.q": "Really turn off the second factor? From outside, the password alone will be enough again.",
    "mfa.off.ok": "The second factor is off.",
    "ses.title": "Signed-in devices",
    "ses.others": "Sign out all others",
    "ses.this": "this device",
    "ses.out": "from outside",
    "ses.in": "home network",
    "ses.mfa": "with code",
    "ses.seen": "last seen {time}",
    "ses.since": "signed in {time}",
    "ses.end": "Sign out",
    "ses.ended": "{n} devices signed out.",
    "usr.mfa": "Second factor",
    "usr.mfa.on": "on",
    "usr.mfa.off": "off",
    "usr.signout": "Sign out on all devices",
    "usr.resettotp": "Reset second factor (if the phone is lost)",
    "set.security": "Security",
    "setup.intro": "Welcome! There is no account yet. Create the first administrator now – more accounts follow later under Settings → Users.",
    "setup.name": "Display name",
    "setup.pass2": "Repeat password",
    "setup.hint": "At least 12 characters. Set up the second factor afterwards under My account.",
    "setup.submit": "Create account",
    "setup.mismatch": "The two passwords differ.",
    "setup.short": "The password needs at least 12 characters.",
    "setup.badname": "User name: lowercase letters, digits, dot, hyphen and underscore only.",
    "setup.outside": "The first setup only works from the home network. Open Wissen! at home or through the VPN.",
    "setup.done": "There is an account already – please sign in.",
    "sys.work": "Background work",
    "sys.f.ocr": "Text recognition for scans",
    "sys.f.ocr.hint": "Reads text from scanned pages so the search finds them. Off: only documents with embedded text become searchable.",
    "sys.f.lang": "Languages",
    "sys.f.pages": "At most pages per document",
    "sys.f.rescan": "Rescan every (min.)",
    "sys.f.workers": "Documents read at the same time",
    "sys.f.hint": "Changes apply at once, no restart. Documents already read are not read again.",
    "sys.f.defaults": "Defaults",
    "sys.f.langs": "Installed: {list}. Join several with +, e.g. deu+eng.",
    "sys.f.nolangs": "Tesseract is not installed, text recognition is not possible.",
    "sys.f.cpus": "The machine has {n} cores. More at once is faster but loads the server more.",
    "sec.nets": "Home network",
    "sec.nets.hint": "Address ranges that count as “at home” (LAN, VPN). Everything else is “outside”. Leave empty for the default.",
    "sec.nets.here": "Your address right now: {ip} ({where}).",
    "sec.nets.in": "counts as home",
    "sec.nets.out": "counts as outside",
    "err.own address": "Your own address {ip} would then no longer count as home. Include its range.",
    "err.not a network": "“{net}” is not an address range (example: 192.168.1.0/24).",
    "err.range": "Please a number from {low} to {high}.",
    "err.languages like deu+eng": "Please give languages like deu+eng.",
    "set.api": "API",
    "api.intro": "Everything the interface does is also available through the REST API under /api/, for scripts, shortcuts or Home Assistant.",
    "api.copy": "Copy",
    "api.del": "Delete",
    "api.copied": "Key copied",
    "api.ref": "All endpoints",
    "api.ref.hint": "Wissen! describes its own API: every endpoint with parameters and response, to try out right in the browser (with your sign-in).",
    "api.open": "Open API reference",
    "api.guide": "Guide with examples",
    "sec.policy": "Sign-in",
    "sec.ext": "From outside only with a second factor",
    "sec.ext.hint": "Accounts without a second factor can then sign in only from the home network. This can only be turned on once your own account has one.",
    "sec.int": "Ask for the second factor at home too",
    "sec.int.hint": "Otherwise the password is enough at home. From outside, Wissen! always asks for the code if an account has a second factor.",
    "sec.without": "Still without a second factor: {names}. These accounts will then only get in from the home network.",
    "sec.ntfy": "Notifications via ntfy",
    "sec.url": "Topic address",
    "sec.token": "Access token",
    "sec.token.set": "saved – leave empty = unchanged",
    "sec.when": "Notify on",
    "sec.n.ext": "every sign-in from outside",
    "sec.n.lock": "an account locked after failed attempts",
    "sec.n.2fa": "changes to the second factor and used recovery codes",
    "sec.test": "Test message",
    "sec.test.ok": "Test message sent.",
    "sec.saved": "Saved.",
    "sec.where.in": "You are signed in from the home network.",
    "sec.where.out": "You are signed in from outside.",
    "err.invalid code": "The code is wrong.",
    "err.second factor already on": "The second factor is already on.",
    "err.no second factor being set up": "Please start the setup again.",
    "err.set up your own second factor first": "Set up the second factor for your own account first, or you would lock yourself out from outside.",
    "err.ntfy address must start with http:// or https://": "The ntfy address must start with http:// or https://.",
    "err.cross-site request refused": "Request from a foreign page refused.",
    "err.only for personal accounts": "This only works with a personal account.",
    "err.not configured": "Enter a topic address and save first.",
    "usr.new": "New user",
    "usr.edit": "Edit user {name}",
    "usr.name": "User",
    "usr.display": "Display name",
    "usr.pass": "Password",
    "usr.pass.keep": "leave empty = unchanged",
    "usr.role": "Role",
    "usr.areas": "Areas",
    "usr.admin": "Administrator (sees all areas, may change settings)",
    "usr.adminrole": "Admin",
    "usr.userrole": "User",
    "usr.all": "all",
    "usr.none": "none",
    "usr.delete.q": "Really delete user {name}?",
    "perm.none": "no access",
    "perm.read": "read",
    "perm.write": "read + write",
    "btn.cancel": "Cancel",
    "btn.save": "Save",
    "btn.edit": "Edit",
    "btn.delete": "Delete",
    "sys.version": "Version",
    "sys.docs": "Documents",
    "sys.scan": "Last scan",
    "sys.texts": "Texts extracted",
    "sys.ocr": "Pages via OCR",
    "sys.ocrstate": "Text recognition (OCR)",
    "sys.on": "active",
    "sys.off": "not available",
    "sys.err.title": "Documents without readable text",
    "sys.err.hint": "These documents open fine, only their text is missing from the full-text search. Title and folder still find them.",
    "sys.err.password": "password-protected – Wissen! cannot read the text",
    "sys.err.missing": "file was missing while reading – will be retried",
    "sys.err.damaged": "file damaged or not a valid PDF",
    "sys.err.other": "Unknown error",
    "sys.err.retry": "Read again",
    "sys.err.retried": "{n} document(s) are being read again.",
    "sys.errors": "Read errors",
    "sys.mode": "Archive",
    "sys.readonly": "read-only",
    "sys.writable": "writable",
    "sys.rescan": "Rescan folders now",
    "sys.rescan.ok": "Scan started.",
    "err.user exists": "This user already exists.",
    "err.invalid user name": "Only lowercase letters, digits, . _ - allowed.",
    "err.last administrator": "The last administrator cannot be removed.",
    "err.wrong password": "Current password is wrong.",
    "err.cannot delete yourself": "You cannot delete yourself.",
    "err.cannot remove your own admin role": "You cannot give up your own admin role.",
    "err.password too short (min. 12)": "The password needs at least 12 characters.",
  },
};
const LANGS = ['de', 'en', 'fr', 'it'];
// the account's choice (remembered in this browser), else the browser language
let LANG = (() => {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem('wissen.lang')); } catch { /* none */ }
  if (LANGS.includes(saved)) return saved;
  const nav = (navigator.language || 'de').slice(0, 2).toLowerCase();
  return LANGS.includes(nav) ? nav : 'en';
})();
const t = (key, vars = {}) =>
  ((I18N[LANG] || {})[key] || (LANG !== 'de' && I18N.en[key]) || I18N.de[key] || key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');

function applyI18n() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => { el.title = t(el.dataset.i18nTitle); });
}

// --------------------------------------------------------------- storage

const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem('wissen.' + key); return v === null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem('wissen.' + key, JSON.stringify(value)); } catch { /* ignore */ }
  },
};

// ------------------------------------------------------------------- api

async function api(path, options = {}) {
  const res = await fetch('api/' + path, {
    credentials: 'same-origin',
    headers: options.body ? { 'Content-Type': 'application/json' } : {},
    ...options,
  });
  if (res.status === 401) { showLogin(); throw new Error('unauthorized'); }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    let info = null;
    try { detail = (await res.json()).detail || detail; } catch { /* keep */ }
    if (detail && typeof detail === 'object') { info = detail; detail = detail.code || `${res.status}`; }
    const err = new Error(detail);
    err.status = res.status;
    err.info = info;
    throw err;
  }
  return res.json();
}

// ----------------------------------------------------------------- state

const PAGE = 200;
const AREA_COLORS = ['#0070f2', '#c35500', '#188918', '#a100c2', '#d20a0a', '#007c87', '#5d36ff', '#8f6a00'];

const State = {
  areas: [],          // [{name, count}]
  active: new Set(),  // selected areas
  folder: store.get('folder', ''),
  recursive: store.get('recursive', true),
  kind: store.get('kind', ''),   // '' = pages and PDFs, 'md' = only pages, 'pdf' = only PDFs
  sort: 'date',           // date/title/area; searches too are sorted, newest first by default
  desc: true,
  best: false,            // while searching: best hits first instead of the column order
  query: '',
  open: new Set(store.get('open', [])),
  items: [],
  total: 0,
  selected: null,
  me: null,
  tags: new Set(),    // tag filter (all must match)
  sel: new Set(),     // ids ticked in the list
  tagList: [],        // [{name, count}]
  pins: [],           // documents pinned to the start page, in their order
};

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const areaColor = name => AREA_COLORS[Math.max(0, State.areas.findIndex(a => a.name === name)) % AREA_COLORS.length];
const areaLabel = name => {
  if (!name) return t('area.none');
  const area = State.areas.find(a => a.name === name);
  return (area && area.label) || name;
};
const highlight = s => esc(s).replace(/\x02/g, '<mark>').replace(/\x03/g, '</mark>');
const errText = e => {
  if (e.info && e.info.code === 'locked') return t('err.locked', { by: e.info.by });
  const bad = /^invalid folder name: (.+)$/.exec(e.message);
  if (bad) return t('err.invalid folder name', { name: bad[1] });
  const k = 'err.' + e.message;
  if (I18N[LANG][k]) return t(k);
  const m = /^unknown model: (.+)$/.exec(e.message);
  if (m) return t('err.unknown model', { model: m[1] });
  const own = /^your own address (.+) would no longer count as home$/.exec(e.message);
  if (own) return t('err.own address', { ip: own[1] });
  const net = /^not a network: (.+)$/.exec(e.message);
  if (net) return t('err.not a network', { net: net[1] });
  const range = /^(\w+) must be between (\d+) and (\d+)$/.exec(e.message);
  if (range) return t('err.range', { low: range[2], high: range[3] });
  return e.message;
};

function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  if (LANG === 'de') return `${d}.${m}.${y}`;
  return LANG === 'en' ? iso : `${d}/${m}/${y}`;
}

// ----------------------------------------------------------------- theme

const THEMES = ['system', 'light', 'dark'];
function applyTheme(theme) {
  const dark = theme === 'dark' || (theme === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
  $('theme-dark').disabled = !dark;
  $('theme-light').disabled = dark;
  $('btn-theme').textContent = { system: '◐', light: '☀', dark: '☾' }[theme];
}
let theme = store.get('theme', 'system');
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => applyTheme(theme));

// ----------------------------------------------------------------- views

async function showLogin() {
  $('view-app').hidden = true;
  $('view-login').hidden = false;
  let setup = { needed: false, home: true };
  try { setup = await (await fetch('api/setup')).json(); } catch { /* keep the sign-in */ }
  $('login-form').hidden = setup.needed;
  $('setup-form').hidden = !setup.needed;
  if (setup.needed && !setup.home) {
    $('setup-error').textContent = t('setup.outside');
    $('setup-error').hidden = false;
  }
  $(setup.needed ? 'setup-user' : 'login-user').focus();
}

async function showApp() {
  $('view-login').hidden = true;
  $('view-app').hidden = false;
  State.me = await api('me');
  if (LANGS.includes(State.me.language) && State.me.language !== LANG) {
    store.set('lang', State.me.language);       // the account's language wins
    if (store.get('lang', null) === State.me.language) { location.reload(); return; }
  }
  document.querySelectorAll('.admin-only').forEach(el => { el.hidden = !State.me.is_admin; });
  setView({ zoom: State.me.zoom, width: State.me.width }, false);      // as this account left it
  for (const id of ['btn-new', 'start-new']) $(id).hidden = !(State.me.write_areas || []).length;
  const areas = await api('areas');
  State.areas = areas;
  const saved = store.get('areas', null);
  State.active = new Set(areas.map(a => a.name).filter(n => !saved || saved.includes(n)));
  if (!State.active.size) State.active = new Set(areas.map(a => a.name));
  $('chk-recursive').checked = State.recursive;
  renderChips();
  // opening Wissen! lands on the start page; "#/" stays the archive list
  if (!location.hash || location.hash === '#') history.replaceState(null, '', '#/start');
  route();
  await loadOpen();
  await Promise.all([loadTree(), loadDocs(), loadStatus(), loadTags(), loadPins().catch(() => null)]);
  loadUpdate();
}

// ----------------------------------------------------------------- chips

function renderChips() {
  const box = $('area-chips');
  box.innerHTML = '';
  if (State.areas.length < 2) return;
  for (const area of State.areas) {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip';
    chip.setAttribute('aria-pressed', State.active.has(area.name));
    chip.innerHTML = `<span class="chip__dot" style="--dot:${areaColor(area.name)}"></span>${esc(areaLabel(area.name))}`;
    chip.addEventListener('click', () => {
      if (State.active.has(area.name)) State.active.delete(area.name); else State.active.add(area.name);
      if (!State.active.size) State.active.add(area.name);
      store.set('areas', [...State.active]);
      renderChips();
      loadTree();
      loadDocs();
      loadTags();
    });
    box.appendChild(chip);
  }
}

const areaParam = () => 'areas=' + encodeURIComponent([...State.active].join(','));

// ------------------------------------------------------------------ tree

let treeData = null;

async function loadTree() {
  treeData = await api('tree?' + areaParam());
  renderTree();
}

function renderTree() {
  const box = $('tree');
  box.innerHTML = '';
  const all = { ...treeData, name: t('tree.all'), path: '' };
  addNode(box, all, 0);
}

function addNode(box, node, depth) {
  const hasKids = node.children.length > 0;
  const isOpen = depth === 0 || State.open.has(node.path);
  const row = document.createElement('div');
  row.className = 'tree-row' + (node.path === State.folder ? ' is-selected' : '');
  row.style.setProperty('--depth', depth);
  row.setAttribute('role', 'treeitem');
  const dots = State.active.size > 1 && node.areas.length < State.active.size
    ? `<span class="tree-dots">${node.areas.map(a => `<span class="area-dot" style="--dot:${areaColor(a)}" title="${esc(areaLabel(a))}"></span>`).join('')}</span>`
    : '';
  if (!node.count && depth > 0) row.classList.add('is-empty');
  row.innerHTML =
    `<span class="tree-caret${isOpen ? ' is-open' : ''}">${hasKids && depth > 0 ? '›' : ''}</span>` +
    `<span class="tree-name">${esc(node.name)}</span>${dots}` +
    `<span class="tree-count">${node.count}</span>`;
  box.appendChild(row);

  row.querySelector('.tree-caret').addEventListener('click', ev => {
    if (!hasKids || depth === 0) return;
    ev.stopPropagation();
    toggleOpen(node.path);
  });
  row.addEventListener('click', () => {
    if (hasKids && depth > 0 && State.folder === node.path) { toggleOpen(node.path); return; }
    if (hasKids && depth > 0) State.open.add(node.path);
    selectFolder(node.path);
  });

  if (hasKids && isOpen) node.children.forEach(child => addNode(box, child, depth + 1));
}

function toggleOpen(path) {
  if (State.open.has(path)) State.open.delete(path); else State.open.add(path);
  saveOpen();
  renderTree();
}

// Which folders are expanded is kept per person on the server (and in the
// browser as a fallback), so it follows the account to other devices.
let saveOpenTimer = null;
function saveOpen() {
  store.set('open', [...State.open]);
  clearTimeout(saveOpenTimer);
  saveOpenTimer = setTimeout(flushOpen, 600);
}
function flushOpen() {
  if (!saveOpenTimer) return;
  saveOpenTimer = null;
  fetch('api/me/prefs', {
    method: 'PUT', keepalive: true, headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tree_open: [...State.open] }),
  }).catch(() => {});
}
addEventListener('pagehide', flushOpen);

async function loadOpen() {
  try {
    const prefs = await api('me/prefs');
    if (prefs.tree_open.length || !State.open.size) State.open = new Set(prefs.tree_open);
    else saveOpen();                       // first time: take over what this browser had
  } catch { /* keep the browser's copy */ }
  openAncestors(State.folder);
}

function openAncestors(path) {
  const parts = path ? path.split('/') : [];
  for (let i = 1; i < parts.length; i++) State.open.add(parts.slice(0, i).join('/'));
}

function setAllOpen(open) {
  if (!treeData) return;
  if (open) {
    const walk = node => node.children.forEach(c => { if (c.children.length) { State.open.add(c.path); walk(c); } });
    walk(treeData);
  } else {
    State.open.clear();
  }
  saveOpen();
  renderTree();
}

// logo and name: back to the archive, all folders, no search, filter or preview
function goHome() {
  closePreview();
  State.best = false;
  $('chk-best').checked = false;
  selectFolder('');
  if (location.hash !== '#/start') location.hash = '#/start'; else loadStart();
}

function selectFolder(path) {
  State.folder = path;
  store.set('folder', path);
  openAncestors(path);
  saveOpen();
  $('search').value = '';
  State.query = '';
  State.tags.clear();
  $('tree-panel').classList.remove('is-open');
  renderTree();
  loadDocs();
  loadTags();
}

// ----------------------------------------------------------------- list

let listToken = 0;

async function loadDocs(append = false) {
  const token = ++listToken;
  const offset = append ? State.items.length : 0;
  const searching = State.query.trim().length > 0;
  const params = [
    areaParam(),
    // a search or a tag filter always covers the whole archive (of the chosen areas)
    'folder=' + encodeURIComponent(searching || State.tags.size ? '' : State.folder),
    'recursive=' + (searching || State.recursive),
    'tags=' + encodeURIComponent([...State.tags].join(',')),
    'kind=' + State.kind,
    'q=' + encodeURIComponent(State.query),
    'sort=' + (bestFirst() ? 'relevance' : State.sort),
    'desc=' + State.desc,
    'limit=' + PAGE,
    'offset=' + offset,
  ].join('&');
  const data = await api('documents?' + params);
  if (token !== listToken) return;
  State.items = append ? State.items.concat(data.items) : data.items;
  State.total = data.total;
  renderList();
}

// clicking a column head sorts by it, clicking again turns the order round
function bestFirst() { return State.best && State.query.trim().length > 0; }

function setSort(key) {
  if (bestFirst()) {  // a column click wins over "best hits first"
    State.best = false;
    $('chk-best').checked = false;
    State.desc = key === 'date';
    State.sort = key;
    return loadDocs();
  }
  if (State.sort === key) State.desc = !State.desc;
  else State.desc = key === 'date';  // dates newest first, names A–Z
  State.sort = key;
  loadDocs();
}

function renderSortHeads() {
  const current = bestFirst() ? '' : State.sort;
  $('best-wrap').hidden = !State.query.trim();
  document.querySelectorAll('[data-sort-col]').forEach(th => {
    const on = th.dataset.sortCol === current;
    th.classList.toggle('is-sorted', on);
    th.setAttribute('aria-sort', on ? (State.desc ? 'descending' : 'ascending') : 'none');
    th.querySelector('.sort-arrow').textContent = on ? (State.desc ? '▼' : '▲') : '';
    th.querySelector('.sort-head').title = t('sort.by', { col: t('col.' + th.dataset.sortCol) });
  });
}

function renderList() {
  renderSortHeads();
  const searching = State.query.trim().length > 0 || State.tags.size > 0;
  const folderName = State.folder ? State.folder.split('/').pop() : t('tree.all');
  $('list-title').textContent = State.query.trim() ? `${t('list.search')}: ${State.query}`
    : (State.tags.size ? t('tags.filter') + ':' : folderName);
  $('list-tagfilter').innerHTML = [...State.tags].map(tag =>
    `<button type="button" class="tag tag--filter" data-tag="${esc(tag)}" title="${esc(t('tags.del'))}">${esc(tag)} ×</button>`).join('');
  $('list-tagfilter').querySelectorAll('[data-tag]').forEach(b => b.addEventListener('click', () => toggleTagFilter(b.dataset.tag)));
  $('list-count').textContent = State.items.length < State.total
    ? t('count.of', { n: State.items.length, total: State.total })
    : t('status.docs', { n: State.total });

  const rows = $('doc-rows');
  rows.innerHTML = '';
  const showFolder = searching || State.recursive;
  for (const doc of State.items) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row' + (State.selected && State.selected.id === doc.id ? ' is-selected' : '');
    const sub = (showFolder && (searching || doc.folder !== State.folder)
      ? `<div class="doc-folder">${esc(doc.folder || t('tree.root'))}</div>` : '') +
      (doc.snippet ? `<div class="doc-snippet">${highlight(doc.snippet)}</div>` : '');
    const shownTags = [...new Set([...(doc.page_tags || []), ...(doc.tags || [])])];
    const tags = shownTags.length
      ? `<div class="tag-row">${shownTags.map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div>` : '';
    tr.innerHTML =
      `<td class="fd-table__cell col-check"><input type="checkbox"${State.sel.has(doc.id) ? ' checked' : ''} aria-label="${esc(doc.title)}"></td>` +
      `<td class="fd-table__cell col-date">${esc(formatDate(doc.date))}</td>` +
      `<td class="fd-table__cell"><div class="doc-title"><span class="doc-kind doc-kind--${esc(doc.ext)}" title="${esc(t(doc.ext === 'md' ? 'kind.page' : 'kind.pdf'))}">${doc.ext === 'md' ? '¶' : 'PDF'}</span>${esc(doc.title)}</div>${tags}${sub}</td>` +
      `<td class="fd-table__cell col-area"><span class="doc-area"><span class="area-dot" style="--dot:${areaColor(doc.area)}"></span>${esc(areaLabel(doc.area))}</span></td>` +
      `<td class="fd-table__cell col-menu"><button type="button" class="doc-menu" title="${esc(t('dm.menu'))}" aria-label="${esc(t('dm.menu'))}">⋯</button></td>`;
    const box = tr.querySelector('.col-check input');
    box.addEventListener('click', ev => ev.stopPropagation());
    box.addEventListener('change', () => {
      if (box.checked) State.sel.add(doc.id); else State.sel.delete(doc.id);
      renderBulk();
    });
    tr.querySelector('.col-check').addEventListener('click', ev => ev.stopPropagation());
    tr.addEventListener('click', () => openPreview(doc));
    const menuBtn = tr.querySelector('.doc-menu');
    menuBtn.addEventListener('click', ev => { ev.stopPropagation(); docMenu(menuBtn, doc); });
    tr.querySelector('.col-menu').addEventListener('click', ev => ev.stopPropagation());
    rows.appendChild(tr);
  }
  renderBulk();
  $('list-empty').hidden = State.items.length > 0;
  $('btn-more').hidden = State.items.length >= State.total;
}

// --------------------------------------------------------------- layout

const Layout = {
  treeWidth: store.get('treeWidth', null),       // px
  pvPos: store.get('previewPos', 'right'),        // 'right' | 'bottom'
  pvSize: store.get('previewSize', {}),           // { right: px, bottom: px }
};

function applyLayout() {
  const root = document.documentElement.style;
  if (Layout.treeWidth) root.setProperty('--tree-w', Layout.treeWidth + 'px');
  const bottom = Layout.pvPos === 'bottom';
  $('work').classList.toggle('work--bottom', bottom);
  const size = Layout.pvSize[Layout.pvPos];
  if (size) $('preview').style.setProperty('--pv-size', size + 'px');
  else $('preview').style.removeProperty('--pv-size');
  const btn = $('pv-layout');
  btn.textContent = (bottom ? '\u25E8 ' : '\u2B13 ') + t(bottom ? 'pv.lay.right' : 'pv.lay.bottom');
  btn.title = t(bottom ? 'pv.right' : 'pv.bottom');
  btn.setAttribute('aria-label', btn.title);
}

function makeSplitter(handle, onMove, onEnd) {
  handle.addEventListener('pointerdown', ev => {
    ev.preventDefault();
    handle.setPointerCapture(ev.pointerId);
    handle.classList.add('is-dragging');
    document.body.classList.add('is-resizing');
    const move = e => onMove(e);
    const up = () => {
      handle.releasePointerCapture(ev.pointerId);
      handle.classList.remove('is-dragging');
      document.body.classList.remove('is-resizing');
      handle.removeEventListener('pointermove', move);
      handle.removeEventListener('pointerup', up);
      handle.removeEventListener('pointercancel', up);
      onEnd();
    };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
    handle.addEventListener('pointercancel', up);
  });
}

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function initLayout() {
  applyLayout();
  makeSplitter($('split-tree'), e => {
    const left = $('archive-layout').getBoundingClientRect().left;
    Layout.treeWidth = Math.round(clamp(e.clientX - left, 160, window.innerWidth * 0.5));
    document.documentElement.style.setProperty('--tree-w', Layout.treeWidth + 'px');
  }, () => store.set('treeWidth', Layout.treeWidth));

  makeSplitter($('split-preview'), e => {
    const box = $('work').getBoundingClientRect();
    const size = Layout.pvPos === 'bottom'
      ? clamp(box.bottom - e.clientY, 160, box.height - 120)
      : clamp(box.right - e.clientX, 260, box.width - 260);
    Layout.pvSize[Layout.pvPos] = Math.round(size);
    $('preview').style.setProperty('--pv-size', Layout.pvSize[Layout.pvPos] + 'px');
  }, () => store.set('previewSize', Layout.pvSize));

  // double click resets to the default size
  $('split-tree').addEventListener('dblclick', () => {
    Layout.treeWidth = null;
    store.set('treeWidth', null);
    document.documentElement.style.removeProperty('--tree-w');
  });
  $('split-preview').addEventListener('dblclick', () => {
    delete Layout.pvSize[Layout.pvPos];
    store.set('previewSize', Layout.pvSize);
    applyLayout();
  });

  const sideSplitter = (handleId, varName, storeKey, fromRight) => {
    const saved = store.get(storeKey, null);
    if (saved) document.documentElement.style.setProperty(varName, saved + 'px');
    let width = saved;
    makeSplitter($(handleId), e => {
      const box = $(handleId).parentElement.getBoundingClientRect();
      width = Math.round(clamp(fromRight ? box.right - e.clientX : e.clientX - box.left, 180, box.width * 0.6));
      document.documentElement.style.setProperty(varName, width + 'px');
    }, () => store.set(storeKey, width));
    $(handleId).addEventListener('dblclick', () => {
      store.set(storeKey, null);
      document.documentElement.style.removeProperty(varName);
    });
  };

  $('pv-layout').addEventListener('click', () => {
    Layout.pvPos = Layout.pvPos === 'bottom' ? 'right' : 'bottom';
    store.set('previewPos', Layout.pvPos);
    applyLayout();
  });
}

// -------------------------------------------------------------- preview

function openPreview(doc) {
  State.selected = doc;
  const url = `api/documents/${doc.id}/file`;
  $('pv-title').textContent = doc.title;
  // the folder is a link: jump to it in the tree, the preview stays open
  $('pv-sub').innerHTML = [formatDate(doc.date), areaLabel(doc.area)].filter(Boolean).map(esc)
    .concat(`<a href="#" class="pv-folder" title="${esc(t('pv.gofolder'))}">${esc((doc.folder || t('tree.root')).replaceAll('/', ' › '))}</a>`)
    .join(' · ');
  $('pv-sub').querySelector('.pv-folder').addEventListener('click', ev => {
    ev.preventDefault();
    const keep = State.selected;
    selectFolder(doc.folder || '');
    if (matchMedia('(max-width: 900px)').matches) closePreview();   // phone: the preview covers the list
    else State.selected = keep;
    setTimeout(() => document.querySelector('.tree-row.is-selected')?.scrollIntoView({ block: 'nearest' }), 300);
  });
  tagEditor($('pv-tags'), doc.tags || [], async tags => {
    const r = await api(`documents/${doc.id}/tags`, { method: 'PUT', body: JSON.stringify({ tags }) });
    doc.tags = r.tags;
    State.items.filter(x => x.sha256 === doc.sha256).forEach(x => { x.tags = r.tags; });
    renderList();
    loadTags();
    return r.tags;
  });
  $('pv-open').href = doc.ext === 'md' ? `#/seite/${doc.id}` : url;
  if (doc.ext === 'md') $('pv-open').removeAttribute('target'); else { $('pv-open').target = '_blank'; $('pv-open').rel = 'noopener'; }
  $('pv-download').href = url + '?download=true';
  paintPin($('pv-pin'), doc);
  $('pv-pin').onclick = () => togglePin(doc);
  const body = $('pv-body');
  body.classList.toggle('preview__body--page', doc.ext === 'md');
  if (doc.ext === 'pdf') body.innerHTML = `<iframe src="${url}#view=FitH" title="${esc(doc.title)}"></iframe>`;
  else if (doc.ext === 'md') showPage(body, doc);
  else body.innerHTML = `<p class="preview__none">${esc(t('pv.none'))}</p>`;
  $('preview').hidden = false;
  $('split-preview').hidden = false;
  renderList();
}

function closePreview() {
  State.selected = null;
  $('preview').hidden = true;
  $('split-preview').hidden = true;
  $('pv-body').innerHTML = '';
  renderList();
}

// --------------------------------------------------------------- status

let statusTimer = null;
async function loadStatus() {
  clearTimeout(statusTimer);
  try {
    const s = await api('status');
    State.status = s;
    paintAskButton();
    const time = s.last_scan ? new Date(s.last_scan).toLocaleString(LANG, { dateStyle: 'short', timeStyle: 'short' }) : '–';
    const texts = s.texts && s.texts.done < s.texts.total ? ' · ' + t('status.texts', s.texts) : '';
    $('status').textContent = s.scanning && !s.last_scan
      ? t('status.scanning')
      : `${t('status.docs', { n: s.total })} · ${t('status.scan', { t: time })}${texts} · v${s.version}`;
    if (s.scanning && !s.last_scan) statusTimer = setTimeout(async () => { await loadStatus(); await showApp(); }, 3000);
    else statusTimer = setTimeout(loadStatus, texts ? 15000 : 60000);
  } catch { /* shown elsewhere */ }
}

// -------------------------------------------------------------- settings

const PANES = { konto: 'account', benutzer: 'users', ablage: 'storage', ki: 'ai', sicherheit: 'security', api: 'api', system: 'system' };
const ADMIN_PANES = new Set(['users', 'storage', 'ai', 'security', 'api', 'system']);

function route() {
  if (!State.me) return;
  const m = location.hash.match(/^#\/einstellungen(?:\/([a-z]+))?/);
  const page = location.hash.match(/^#\/seite\/([0-9a-z]{6,64})/);
  if (Edit.on) {
    if (page && page[1] === Edit.doc.id) return;          // still on the page being edited
    if (Edit.dirty() && !confirm(t('ed.discard'))) { location.hash = '#/seite/' + Edit.doc.id; return; }
    endEdit();
  }
  const inSettings = !!m;
  const start = /^#\/start/.test(location.hash);
  const trash = /^#\/papierkorb/.test(location.hash);
  $('settings').hidden = !inSettings;
  $('pagepage').hidden = !page;
  $('startpage').hidden = !start;
  $('trashpage').hidden = !trash;
  const other = inSettings || !!page || start || trash;
  $('archive-toolbar').hidden = other;
  $('archive-layout').hidden = other;
  if (page) { openPageView(page[1]); return; }
  if (start) { loadStart(); return; }
  if (trash) { loadTrash(); return; }
  if (!inSettings) return;
  let pane = PANES[m && m[1]] || 'account';
  if (ADMIN_PANES.has(pane) && !State.me.is_admin) pane = 'account';
  $('acc-who').textContent = t('acc.who', { name: State.me.display_name || State.me.name });
  showPane(pane);
}

function showPane(pane) {
  document.querySelectorAll('.set-link').forEach(a => a.classList.toggle('is-active', a.dataset.pane === pane));
  document.querySelectorAll('.set-pane').forEach(p => { p.hidden = p.dataset.pane !== pane; });
  if (pane !== 'users') $('usr-form').hidden = true;
  if (pane === 'users') loadUsers();
  if (pane === 'account') loadAccountSecurity();
  if (pane === 'security') loadSecurity();
  if (pane === 'api') loadApiKey();
  if (pane === 'ai') { loadMcp(); loadAI(); }
  if (pane === 'storage') loadStorage();
  if (pane === 'system') loadSystem();
}

function setMsg(el, text, ok) {
  el.textContent = text;
  el.className = 'form-msg ' + (ok ? 'is-ok' : 'is-error');
}

let users = [];
let editing = null;   // null = new user, else name

async function loadUsers() {
  users = await api('users');
  const rows = $('usr-rows');
  rows.innerHTML = '';
  for (const u of users) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    const areas = u.is_admin ? t('usr.all')
      : (Object.entries(u.areas).map(([a, p]) => `${areaLabel(a)} (${t('perm.' + p)})`).join(', ') || t('usr.none'));
    tr.innerHTML =
      `<td class="fd-table__cell"><div class="doc-title">${esc(u.display_name || u.name)}</div><div class="doc-folder">${esc(u.name)}</div></td>` +
      `<td class="fd-table__cell"><span class="role-badge">${t(u.is_admin ? 'usr.adminrole' : 'usr.userrole')}</span></td>` +
      `<td class="fd-table__cell">${esc(areas)}</td>` +
      `<td class="fd-table__cell"><span class="mfa-badge${u.totp ? '' : ' is-off'}">${t(u.totp ? 'usr.mfa.on' : 'usr.mfa.off')}</span></td>` +
      `<td class="fd-table__cell usr-actions">` +
      `<button class="fd-button fd-button--transparent" data-act="edit">${t('btn.edit')}</button>` +
      (u.name === State.me.name ? '' : `<button class="fd-button fd-button--transparent fd-button--negative" data-act="del">${t('btn.delete')}</button>`) +
      `</td>`;
    tr.querySelector('[data-act="edit"]').addEventListener('click', () => editUser(u));
    tr.querySelector('[data-act="del"]')?.addEventListener('click', () => deleteUser(u));
    rows.appendChild(tr);
  }
}

function editUser(u) {
  editing = u ? u.name : null;
  const form = $('usr-form');
  form.hidden = false;
  $('usr-msg').textContent = '';
  $('usr-form-title').textContent = u ? t('usr.edit', { name: u.name }) : t('usr.new');
  $('usr-name').value = u ? u.name : '';
  $('usr-name').disabled = !!u;
  $('usr-display').value = u ? u.display_name : '';
  $('usr-pass').value = '';
  $('usr-pass').required = !u;
  $('usr-pass').placeholder = u ? t('usr.pass.keep') : '';
  $('usr-admin').checked = u ? u.is_admin : false;
  $('usr-signout').checked = false;
  $('usr-reset-totp').checked = false;
  document.querySelectorAll('.usr-existing').forEach(el => { el.hidden = !u; });
  document.querySelectorAll('.usr-mfa-reset').forEach(el => { el.hidden = !(u && u.totp); });
  const box = $('usr-areas');
  box.innerHTML = '';
  for (const area of State.areas) {
    const label = document.createElement('span');
    label.innerHTML = `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(areaLabel(area.name))}`;
    const select = document.createElement('select');
    select.dataset.area = area.name;
    for (const p of ['none', 'read', 'write']) {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = t('perm.' + p);
      select.appendChild(opt);
    }
    select.value = (u && u.areas[area.name]) || 'none';
    box.append(label, select);
  }
  syncAdminAreas();
  (u ? $('usr-display') : $('usr-name')).focus();
}

function syncAdminAreas() {
  const admin = $('usr-admin').checked;
  $('usr-areas').querySelectorAll('select').forEach(s => { s.disabled = admin; });
}

async function saveUser(ev) {
  ev.preventDefault();
  const areas = {};
  $('usr-areas').querySelectorAll('select').forEach(s => { if (s.value !== 'none') areas[s.dataset.area] = s.value; });
  const body = {
    display_name: $('usr-display').value,
    is_admin: $('usr-admin').checked,
    areas,
  };
  if ($('usr-pass').value) body.password = $('usr-pass').value;
  try {
    if (editing) {
      if ($('usr-signout').checked) body.sign_out = true;
      if ($('usr-reset-totp').checked) body.reset_totp = true;
      await api('users/' + encodeURIComponent(editing), { method: 'PATCH', body: JSON.stringify(body) });
    } else {
      body.name = $('usr-name').value.trim().toLowerCase();
      await api('users', { method: 'POST', body: JSON.stringify(body) });
    }
    $('usr-form').hidden = true;
    await loadUsers();
  } catch (e) {
    setMsg($('usr-msg'), errText(e), false);
  }
}

async function deleteUser(u) {
  if (!confirm(t('usr.delete.q', { name: u.name }))) return;
  try {
    await api('users/' + encodeURIComponent(u.name), { method: 'DELETE' });
    await loadUsers();
  } catch (e) {
    alert(errText(e));
  }
}

// ------------------------------------------------- second factor, devices

const fmtTime = ts => new Date(ts * 1000).toLocaleString(LANG, { dateStyle: 'short', timeStyle: 'short' });

function mfaView(mode) {
  // mode: 'off' | 'setup' | 'codes' | 'on'
  $('mfa-start').hidden = mode !== 'off';
  $('mfa-setup').hidden = mode !== 'setup';
  $('mfa-codes').hidden = mode !== 'codes';
  $('mfa-on').hidden = mode !== 'on';
  document.querySelectorAll('#mfa-card .form-msg').forEach(el => { el.textContent = ''; });
}

async function loadAccountSecurity() {
  if (State.me.name === 'api') { $('mfa-card').hidden = true; return; }
  if (!$('mfa-codes').hidden || !$('mfa-setup').hidden) { loadSessions(); return; }   // mid-setup: keep it
  State.me = await api('me');
  $('mfa-state').textContent = State.me.totp
    ? t('mfa.state.on', { n: State.me.recovery_left }) : t('mfa.state.off');
  mfaView(State.me.totp ? 'on' : 'off');
  loadSessions();
}

async function loadSessions() {
  const list = await api('me/sessions');
  const rows = $('ses-rows');
  rows.innerHTML = '';
  for (const s of list) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    const where = [s.external ? t('ses.out') : t('ses.in'), s.ip, s.mfa ? t('ses.mfa') : ''].filter(Boolean).join(' · ');
    tr.innerHTML =
      `<td class="fd-table__cell"><div class="doc-title">${esc(s.device)}${s.current ? ` <span class="mfa-badge">${t('ses.this')}</span>` : ''}</div>` +
      `<div class="doc-folder">${esc(where)}</div></td>` +
      `<td class="fd-table__cell"><div class="doc-folder">${esc(t('ses.seen', { time: fmtTime(s.last_seen) }))}</div>` +
      `<div class="doc-folder">${esc(t('ses.since', { time: fmtTime(s.created) }))}</div></td>` +
      `<td class="fd-table__cell ses-act">` +
      (s.current ? '' : `<button class="fd-button fd-button--transparent" type="button">${t('ses.end')}</button>`) + `</td>`;
    tr.title = s.agent;
    tr.querySelector('button')?.addEventListener('click', async () => {
      await api('me/sessions/' + encodeURIComponent(s.id), { method: 'DELETE' });
      loadSessions();
    });
    rows.appendChild(tr);
  }
  $('ses-others').hidden = list.length < 2;
}

function showRecoveryCodes(codes) {
  $('mfa-code-list').textContent = codes.join('\n');
  mfaView('codes');
}

function initAccountSecurity() {
  $('mfa-start').addEventListener('submit', async ev => {
    ev.preventDefault();
    try {
      const r = await api('me/totp/setup', { method: 'POST', body: JSON.stringify({ password: $('mfa-pass').value }) });
      $('mfa-pass').value = '';
      $('mfa-qr').src = r.qr;
      $('mfa-secret').textContent = r.secret;
      mfaView('setup');
      $('mfa-code').value = '';
      $('mfa-code').focus();
    } catch (e) { setMsg($('mfa-msg-start'), errText(e), false); }
  });
  $('mfa-abort').addEventListener('click', () => { mfaView('off'); });
  $('mfa-confirm').addEventListener('submit', async ev => {
    ev.preventDefault();
    try {
      const r = await api('me/totp/enable', { method: 'POST', body: JSON.stringify({ code: $('mfa-code').value }) });
      showRecoveryCodes(r.recovery_codes);
    } catch (e) { setMsg($('mfa-msg-confirm'), errText(e), false); }
  });
  $('mfa-copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('mfa-code-list').textContent); toast(esc(t('mfa.copied')), null, 2500); }
    catch { /* select-all on the list still works */ }
  });
  $('mfa-done').addEventListener('click', () => { $('mfa-codes').hidden = true; loadAccountSecurity(); });
  $('mfa-renew').addEventListener('submit', async ev => {
    ev.preventDefault();
    try {
      const r = await api('me/totp/recovery', { method: 'POST', body: JSON.stringify({ code: $('mfa-renew-code').value }) });
      $('mfa-renew-code').value = '';
      showRecoveryCodes(r.recovery_codes);
    } catch (e) { setMsg($('mfa-msg-renew'), errText(e), false); }
  });
  $('mfa-off-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    if (!confirm(t('mfa.off.q'))) return;
    try {
      await api('me/totp/disable', { method: 'POST',
        body: JSON.stringify({ password: $('mfa-off-pass').value, code: $('mfa-off-code').value }) });
      $('mfa-off-pass').value = ''; $('mfa-off-code').value = '';
      toast(esc(t('mfa.off.ok')), null, 4000);
      loadAccountSecurity();
    } catch (e) { setMsg($('mfa-msg-off'), errText(e), false); }
  });
  $('ses-others').addEventListener('click', async () => {
    const r = await api('me/sessions/others', { method: 'POST' });
    toast(esc(t('ses.ended', { n: r.signed_out })), null, 4000);
    loadSessions();
  });
}

// ---------------------------------------------------------------- security

let security = null;

async function loadSecurity() {
  security = await api('security');
  $('sec-where').textContent = t(State.me.external ? 'sec.where.out' : 'sec.where.in');
  $('sec-nets').value = security.internal_networks;
  $('sec-nets').placeholder = security.networks_default;
  $('sec-nets-here').textContent = t('sec.nets.here', { ip: security.client_ip, where: t(State.me.external ? 'sec.nets.out' : 'sec.nets.in') });
  $('sec-ext').checked = security.require_2fa_external;
  $('sec-int').checked = security.require_2fa_internal;
  $('sec-url').value = security.ntfy_url;
  $('sec-token').value = '';
  $('sec-token').placeholder = security.has_ntfy_token ? t('sec.token.set') : 'tk_…';
  $('sec-clear-token').hidden = !security.has_ntfy_token;
  $('sec-n-ext').checked = security.notify_external_login;
  $('sec-n-lock').checked = security.notify_lockout;
  $('sec-n-2fa').checked = security.notify_2fa_changes;
  const without = security.without_2fa;
  $('sec-without').hidden = !without.length;
  $('sec-without').textContent = t('sec.without', { names: without.join(', ') });
  $('sec-msg').textContent = '';
}

async function saveSecurity(extra = {}) {
  const body = {
    internal_networks: $('sec-nets').value.trim(),
    require_2fa_external: $('sec-ext').checked,
    require_2fa_internal: $('sec-int').checked,
    ntfy_url: $('sec-url').value.trim(),
    notify_external_login: $('sec-n-ext').checked,
    notify_lockout: $('sec-n-lock').checked,
    notify_2fa_changes: $('sec-n-2fa').checked,
    ...extra,
  };
  if ($('sec-token').value.trim()) body.ntfy_token = $('sec-token').value.trim();
  await api('security', { method: 'PUT', body: JSON.stringify(body) });
  await loadSecurity();
}

function initSecurity() {
  $('sec-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    try { await saveSecurity(); setMsg($('sec-msg'), t('sec.saved'), true); }
    catch (e) { setMsg($('sec-msg'), errText(e), false); }
  });
  $('sec-clear-token').addEventListener('click', async () => {
    try { await saveSecurity({ clear_ntfy_token: true }); } catch (e) { setMsg($('sec-msg'), errText(e), false); }
  });
  $('sec-test').addEventListener('click', async () => {
    try {
      await saveSecurity();
      await api('security/test', { method: 'POST' });
      setMsg($('sec-msg'), t('sec.test.ok'), true);
    } catch (e) { setMsg($('sec-msg'), errText(e), false); }
  });
}

function showFreshKey(name, token) {
  $('api-fresh').hidden = !token;
  $('api-key').value = token || '';
  $('api-example').textContent = `curl -H "Authorization: Bearer ${token || '…'}" \\\n     "${location.origin}/api/documents?q=entkalken&limit=5"`;
  if (token) $('api-key').select();
}

const shortTime = iso => iso ? new Date(iso).toLocaleString(LANG, { dateStyle: 'short', timeStyle: 'short' }) : '–';

async function loadApiKey() {
  $('api-guide').href = 'api/docs';
  showFreshKey('', '');
  $('api-msg').textContent = '';
  const keys = await api('security/api-keys');
  $('api-none').hidden = keys.length > 0;
  const rows = $('api-rows');
  rows.innerHTML = '';
  for (const k of keys) {
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    tr.innerHTML =
      `<td class="fd-table__cell"><b>${esc(k.name)}</b> <span class="field-hint">…${esc(k.hint)}</span></td>` +
      `<td class="fd-table__cell"><select class="fd-input api-right-sel">` +
      `<option value="write"${k.right === 'write' ? ' selected' : ''}>${esc(t('api.right.write'))}</option>` +
      `<option value="read"${k.right === 'read' ? ' selected' : ''}>${esc(t('api.right.read'))}</option></select></td>` +
      `<td class="fd-table__cell">${esc(shortTime(k.made))}</td>` +
      `<td class="fd-table__cell">${esc(k.last ? shortTime(k.last) : t('api.never'))}</td>` +
      `<td class="fd-table__cell api-actions"><button type="button" class="fd-button fd-button--transparent" data-k="renew">${esc(t('api.renew'))}</button>` +
      `<button type="button" class="fd-button fd-button--transparent fd-button--negative" data-k="del">${esc(t('api.del'))}</button></td>`;
    tr.querySelector('.api-right-sel').addEventListener('change', async ev => {
      try {
        await api('security/api-keys/' + k.id, { method: 'PATCH', body: JSON.stringify({ right: ev.target.value }) });
        setMsg($('api-msg'), t('api.saved', { name: k.name }), true);
      } catch (e) { setMsg($('api-msg'), errText(e), false); }
    });
    tr.querySelector('[data-k="renew"]').addEventListener('click', async () => {
      if (!confirm(t('api.renew.q', { name: k.name }))) return;
      const r = await api(`security/api-keys/${k.id}/renew`, { method: 'POST' });
      await loadApiKey();
      showFreshKey(r.name, r.token);
    });
    tr.querySelector('[data-k="del"]').addEventListener('click', async () => {
      if (!confirm(t('api.del.q2', { name: k.name }))) return;
      await api('security/api-keys/' + k.id, { method: 'DELETE' });
      loadApiKey();
    });
    rows.appendChild(tr);
  }
}

function initApiKey() {
  $('api-copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('api-key').value); toast(esc(t('api.copied')), null, 2500); }
    catch { $('api-key').select(); }
  });
  const add = async () => {
    const name = $('api-name').value.trim();
    if (!name) { $('api-name').focus(); return; }
    try {
      const r = await api('security/api-keys', { method: 'POST', body: JSON.stringify({ name, right: $('api-right').value }) });
      $('api-name').value = '';
      await loadApiKey();
      showFreshKey(r.name, r.token);
    } catch (e) { setMsg($('api-msg'), errText(e), false); }
  };
  $('api-add').addEventListener('click', add);
  $('api-name').addEventListener('keydown', ev => { if (ev.key === 'Enter') { ev.preventDefault(); add(); } });
}

async function loadSystem() {
  const s = await api('status');
  const time = s.last_scan ? new Date(s.last_scan).toLocaleString(LANG) : '–';
  const rows = [
    ['sys.version', s.version],
    ['sys.mode', t(s.readonly ? 'sys.readonly' : 'sys.writable')],
    ['sys.docs', s.total],
    ['sys.scan', `${time} (${s.last_scan_seconds ?? '–'} s)`],
    ['sys.texts', `${s.texts.done} / ${s.texts.total}`],
    ['sys.ocrstate', t(s.ocr ? 'sys.on' : 'sys.off')],
    ['sys.ocr', s.texts.ocr_pages],
    ['sys.errors', s.texts.errors],
  ];
  $('sys-info').innerHTML = rows.map(([k, v]) => `<dt>${esc(t(k))}</dt><dd>${esc(v)}</dd>`).join('');
  loadTextErrors();
  if (State.me.is_admin) showSystemSettings(await api('system/settings'));
  if (State.me.is_admin) showUpdateCard(await loadUpdate());
}

// --------------------------------------------------------------- update check (version.worldgate.de)

function updDate(d) { return d ? new Date(d + 'T12:00').toLocaleDateString(LANG) : '–'; }

async function loadUpdate() {
  const btn = $('btn-update');
  btn.hidden = true;
  if (!State.me.is_admin) return null;
  let u;
  try { u = await api('update'); } catch { return null; }
  if (u.on && u.newer) {
    btn.textContent = t('upd.btn', { v: u.latest });
    btn.hidden = false;
    btn.onclick = () => openUpdateDialog(u);
  }
  return u;
}

function openUpdateDialog(u) {
  $('upd-dlg-title').textContent = t('upd.title', { v: u.latest });
  $('upd-dlg-intro').textContent = t('upd.intro', { cur: u.installed });
  $('upd-dlg-notes').textContent = u.notes || '–';
  const link = $('upd-dlg-link');
  link.hidden = !u.url;
  link.href = u.url || '#';
  $('upd-dlg').showModal();
}

function showUpdateCard(u) {
  if (!u) return;
  $('upd-on').checked = u.on;
  $('upd-on').disabled = u.locked;
  $('upd-check').disabled = !u.on;
  let state;
  if (u.locked) state = t('upd.f.locked');
  else if (!u.on) state = t('upd.state.off', { cur: u.installed });
  else if (u.newer) state = t('upd.state.new', { v: u.latest, cur: u.installed });
  else if (u.error) state = t('upd.state.err', { d: updDate(u.checked) });
  else if (u.checked) state = t('upd.state.ok', { cur: u.installed, d: updDate(u.checked) });
  else state = t('upd.state.never', { cur: u.installed });
  $('upd-state').textContent = state;
}

function bindUpdate() {
  $('upd-dlg-close').addEventListener('click', () => $('upd-dlg').close());
  $('upd-on').addEventListener('change', async () => {
    try {
      showUpdateCard(await api('update', { method: 'PUT', body: JSON.stringify({ on: $('upd-on').checked }) }));
      setMsg($('upd-msg'), t('sec.saved'), true);
      loadUpdate();
    } catch (e) { setMsg($('upd-msg'), errText(e), false); }
  });
  $('upd-check').addEventListener('click', async () => {
    try {
      showUpdateCard(await api('update/check', { method: 'POST' }));
      setMsg($('upd-msg'), t('upd.checked'), true);
      loadUpdate();
    } catch (e) { setMsg($('upd-msg'), errText(e), false); }
  });
}

function showSystemSettings(c) {
  $('sys-ocr').checked = c.ocr;
  $('sys-lang').value = c.ocr_lang;
  $('sys-pages').value = c.ocr_max_pages;
  $('sys-rescan-min').value = c.rescan_minutes;
  $('sys-workers').value = c.text_workers;
  $('sys-lang-hint').textContent = c.languages.length ? t('sys.f.langs', { list: c.languages.join(', ') }) : t('sys.f.nolangs');
  $('sys-workers-hint').textContent = t('sys.f.cpus', { n: c.cpus });
  $('sys-defaults').onclick = () => showSystemSettings({ ...c, ...c.defaults });
}

async function saveSystemSettings(ev) {
  ev.preventDefault();
  try {
    showSystemSettings(await api('system/settings', { method: 'PUT', body: JSON.stringify({
      ocr: $('sys-ocr').checked,
      ocr_lang: $('sys-lang').value.trim(),
      ocr_max_pages: Number($('sys-pages').value),
      rescan_minutes: Number($('sys-rescan-min').value),
      text_workers: Number($('sys-workers').value),
    }) }));
    setMsg($('sys-msg'), t('sec.saved'), true);
  } catch (e) { setMsg($('sys-msg'), errText(e), false); }
}

async function loadTextErrors() {
  const box = $('sys-errors');
  let items = [];
  try { items = (await api('text-errors')).items; } catch { /* keep empty */ }
  box.hidden = !items.length;
  if (!items.length) return;
  $('sys-err-list').innerHTML = items.map(d =>
    `<li><a href="#" data-id="${esc(d.id)}">${esc(d.title)}</a> <span class="doc-folder">${esc(areaLabel(d.area))} · ${esc(d.folder || t('tree.root'))}</span>` +
    `<div class="sys-err-why">${esc(t('sys.err.' + d.reason))}</div></li>`).join('');
  $('sys-err-list').querySelectorAll('a[data-id]').forEach(a => a.addEventListener('click', async ev => {
    ev.preventDefault();
    location.hash = '#/';
    openPreview(await api('documents/' + a.dataset.id));
  }));
  $('sys-err-retry').hidden = !State.me.is_admin;
}

// --------------------------------------------------------------- storage

let storage = null;

function statusHtml(s, files) {
  if (!s || !s.readable) return `<span class="status-bad">✕ ${esc(t('st.missing'))}</span>`;
  const base = s.writable ? `<span class="status-ok">✓ ${esc(t('st.ok.rw'))}</span>` : `<span class="status-warn">● ${esc(t('st.ok.ro'))}</span>`;
  return files == null ? base : `${base} · ${esc(t('st.files', { n: files }))}`;
}

async function loadStorage() {
  storage = await api('storage');
  $('st-archive').value = storage.archive_path;
  $('st-archive-status').innerHTML = statusHtml(storage.archive);
  $('st-trash-days').value = storage.trash_days ?? 30;
  $('st-msg').textContent = '';
  renderAreaLabels();
}

function renderAreaLabels() {
  const box = $('st-areas');
  box.innerHTML = '';
  for (const area of State.areas.filter(a => a.name)) {
    const label = document.createElement('label');
    label.className = 'fd-form-label';
    label.innerHTML = `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(area.name)}`;
    const input = document.createElement('input');
    input.className = 'fd-input';
    input.dataset.area = area.name;
    input.value = storage.area_labels[area.name] || '';
    input.placeholder = area.label;
    const cell = document.createElement('div');
    cell.className = 'inline';
    cell.appendChild(input);
    if (!area.count) {                      // an empty area may go again
      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'fd-button fd-button--transparent';
      del.textContent = '✕';
      del.title = t('st.area.del');
      del.addEventListener('click', async () => {
        if (!confirm(t('st.area.del.q', { name: area.label || area.name }))) return;
        try {
          await api('areas/' + encodeURIComponent(area.name), { method: 'DELETE' });
          State.areas = await api('areas'); renderChips(); renderAreaLabels();
        } catch (e) { toast(esc(errText(e))); }
      });
      cell.appendChild(del);
    }
    box.append(label, cell);
  }
}

async function saveStorage(ev) {
  ev.preventDefault();
  try {
    storage = await api('storage', { method: 'PUT', body: JSON.stringify({
      archive_path: $('st-archive').value.trim(),
      area_labels: Object.fromEntries([...$('st-areas').querySelectorAll('input')].map(i => [i.dataset.area, i.value.trim()])),
      trash_days: Math.max(0, parseInt($('st-trash-days').value || '0', 10)),
    }) });
    State.areas = await api('areas');
    renderChips();
    renderTree();
    renderList();
    $('st-archive-status').innerHTML = statusHtml(storage.archive);
    setMsg($('st-msg'), t('st.saved'), true);
    loadStatus();
  } catch (e) {
    setMsg($('st-msg'), errText(e), false);
  }
}

// inline folder picker: lists the container's mounted folders, then their subfolders
async function showPicker(inputId) {
  const picker = document.querySelector(`.picker[data-for="${inputId}"]`);
  if (!picker.hidden) { picker.hidden = true; return; }
  picker.hidden = false;
  const input = $(inputId);
  const render = async path => {
    let html;
    if (!path) {
      const roots = await api('fs/roots');
      html = `<div class="picker-bar"><span class="picker-path">${esc(t('st.roots'))}</span></div><div class="picker-list">` +
        roots.map(r => `<button type="button" class="picker-item" data-go="${esc(r.path)}">📁 ${esc(r.path)}</button>`).join('') + '</div>';
    } else {
      let d;
      try { d = await api('fs/list?path=' + encodeURIComponent(path)); } catch { return render(''); }
      html = `<div class="picker-bar"><span class="picker-path" title="${esc(d.path)}">${esc(d.path)}</span>` +
        `<button type="button" class="fd-button fd-button--emphasized" data-choose="${esc(d.path)}">${esc(t('st.choose'))}</button></div>` +
        `<div class="picker-list"><button type="button" class="picker-item" data-go="${esc(d.parent || '')}">↑ ${esc(t('st.up'))}</button>` +
        (d.dirs.length ? d.dirs.map(n => `<button type="button" class="picker-item" data-go="${esc(d.path.replace(/\/$/, '') + '/' + n)}">📁 ${esc(n)}</button>`).join('')
          : `<div class="picker-empty">${esc(t('st.nodirs'))}</div>`) + '</div>';
    }
    picker.innerHTML = html;
    picker.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => render(b.dataset.go)));
    picker.querySelector('[data-choose]')?.addEventListener('click', ev => {
      input.value = ev.currentTarget.dataset.choose;
      picker.hidden = true;
    });
  };
  render(input.value.trim());
}

// -------------------------------------------------------------------- AI

let aiConfig = null;

// the switch for the MCP endpoint (the AI provider settings further down are parked)
async function loadMcp() {
  $('mcp-msg').textContent = '';
  $('mcp-url').textContent = new URL('api/mcp', location.href.split('#')[0]).href;
  try { $('mcp-on').checked = (await api('system/settings')).mcp; } catch (e) { setMsg($('mcp-msg'), errText(e), false); }
}

async function saveMcp() {
  const on = $('mcp-on').checked;
  try {
    const saved = await api('system/settings', { method: 'PUT', body: JSON.stringify({ mcp: on }) });
    $('mcp-on').checked = saved.mcp;
    setMsg($('mcp-msg'), t(saved.mcp ? 'mcp.saved.on' : 'mcp.saved.off'), true);
  } catch (e) {
    $('mcp-on').checked = !on;
    setMsg($('mcp-msg'), errText(e), false);
  }
}

async function loadAI() {
  aiConfig = await api('ai');
  $('ai-enabled').checked = aiConfig.enabled;
  $('ai-provider').value = aiConfig.provider;
  $('ai-baseurl').value = aiConfig.base_url;
  fillModels(aiConfig.models.map(m => ({ ...m })), aiConfig.model);
  loadModels();
  $('ai-limit').value = aiConfig.monthly_limit_usd;
  $('ai-key').value = '';
  $('ai-msg').textContent = '';
  const box = $('ai-exclude');
  box.innerHTML = '';
  for (const area of State.areas) {
    const label = document.createElement('label');
    label.className = 'check';
    label.innerHTML = `<input type="checkbox" value="${esc(area.name)}"${aiConfig.excluded_areas.includes(area.name) ? ' checked' : ''}> ` +
      `<span class="area-dot" style="--dot:${areaColor(area.name)}"></span> ${esc(areaLabel(area.name))}`;
    box.appendChild(label);
  }
  syncAIForm();
}

function syncAIForm() {
  if (!aiConfig) return;
  const openai = $('ai-provider').value !== 'anthropic';
  document.querySelectorAll('.ai-openai-only').forEach(el => { el.hidden = !openai; });
  $('ai-key').placeholder = aiConfig.key_set ? t('ai.key.set', { hint: aiConfig.key_hint })
    : (openai ? t('ai.key.local') : t('ai.key.none'));
  $('ai-clear-key').hidden = !aiConfig.key_set;
  const price = aiConfig.prices[currentModel()];
  $('ai-price').textContent = price && !openai ? t('ai.price', price) : t('ai.price.none');
  const u = aiConfig.month_usage;
  $('ai-usage').textContent = t('ai.usage', { month: aiConfig.month, cost: (u.cost || 0).toFixed(2), calls: u.calls || 0 });
}

const OTHER = '__other__';

function fillModels(models, current) {
  const sel = $('ai-model-select');
  const list = models.slice();
  if (current && !list.some(m => m.id === current)) list.unshift({ id: current, label: current });
  sel.innerHTML = list.map(m => {
    const price = aiConfig.prices[m.id];
    const suffix = m.label !== m.id ? ` – ${m.id}` : '';
    return `<option value="${esc(m.id)}">${esc(m.label)}${esc(suffix)}${price ? ` (${price.input} / ${price.output} $)` : ''}</option>`;
  }).join('') + `<option value="${OTHER}">${esc(t('ai.other'))}</option>`;
  sel.value = current && list.length ? current : (list[0] ? list[0].id : OTHER);
  $('ai-model').hidden = sel.value !== OTHER;
}

let modelsToken = 0;
async function loadModels() {
  const token = ++modelsToken;
  $('ai-models-note').textContent = t('ai.models.loading');
  try {
    const res = await api('ai/models');
    if (token !== modelsToken) return;
    const keep = currentModel() || aiConfig.model;
    if (res.models.length) fillModels(res.models, keep);
    $('ai-models-note').textContent = res.source === 'provider'
      ? t('ai.models.live', { n: res.models.length })
      : t('ai.models.builtin', { reason: errText(new Error(res.error)) });
    syncAIForm();
  } catch (e) {
    $('ai-models-note').textContent = errText(e);
  }
}

function currentModel() {
  const sel = $('ai-model-select');
  return sel.value === OTHER ? $('ai-model').value.trim() : sel.value;
}

function aiPayload() {
  const body = {
    enabled: $('ai-enabled').checked,
    provider: $('ai-provider').value,
    base_url: $('ai-baseurl').value.trim(),
    model: currentModel(),
    monthly_limit_usd: Number($('ai-limit').value || 0),
    excluded_areas: [...$('ai-exclude').querySelectorAll('input:checked')].map(i => i.value),
  };
  if ($('ai-key').value.trim()) body.api_key = $('ai-key').value.trim();
  return body;
}

async function saveAI(ev) {
  if (ev) ev.preventDefault();
  try {
    aiConfig = await api('ai', { method: 'PUT', body: JSON.stringify(aiPayload()) });
    const keyChanged = !!$('ai-key').value.trim();
    $('ai-key').value = '';
    syncAIForm();
    setMsg($('ai-msg'), t('ai.saved'), true);
    loadStatus();                              // whether questions can be asked shows in the list at once
    if (keyChanged) loadModels();
    return true;
  } catch (e) {
    setMsg($('ai-msg'), errText(e), false);
    return false;
  }
}

async function testAI() {
  if (!(await saveAI())) return;
  setMsg($('ai-msg'), t('ai.testing'), true);
  try {
    const r = await api('ai/test', { method: 'POST' });
    setMsg($('ai-msg'), t('ai.test.ok', { model: r.model, seconds: r.seconds, text: r.text, cost: r.cost.toFixed(4) }), true);
    aiConfig = await api('ai');
    syncAIForm();
  } catch (e) {
    setMsg($('ai-msg'), errText(e), false);
  }
}

// ----------------------------------------------------------------- wire

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

document.addEventListener('DOMContentLoaded', async () => {
  applyI18n();
  applyTheme(theme);
  initLayout();

  $('btn-theme').addEventListener('click', () => {
    theme = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    store.set('theme', theme);
    applyTheme(theme);
  });

  $('login-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    const error = $('login-error');
    error.hidden = true;
    const body = { username: $('login-user').value.trim(), password: $('login-pass').value };
    const code = $('login-code').value.trim();
    if (!$('login-code-box').hidden && code) body.code = code;
    const res = await fetch('api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let detail = '';
      try { detail = (await res.json()).detail || ''; } catch { /* keep */ }
      const msg = {
        'code required': 'login.need.code', 'invalid code': 'login.bad.code',
        'second factor required outside': 'login.need.2fa', 'locked': 'login.locked',
      }[detail] || 'login.error';
      if (detail === 'code required' || detail === 'invalid code') {
        $('login-code-box').hidden = false;
        $('login-code').value = '';
        $('login-code').focus();
      }
      error.textContent = t(msg, { s: res.headers.get('Retry-After') || '60' });
      error.hidden = false;
      return;
    }
    $('login-pass').value = '';
    $('login-code').value = '';
    $('login-code-box').hidden = true;
    showApp();
  });

  $('setup-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    const error = $('setup-error');
    error.hidden = true;
    if ($('setup-pass').value !== $('setup-pass2').value) {
      error.textContent = t('setup.mismatch');
      error.hidden = false;
      return;
    }
    const res = await fetch('api/setup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: $('setup-user').value.trim(), display_name: $('setup-name').value.trim(),
                             password: $('setup-pass').value }),
    });
    if (!res.ok) {
      let detail = '';
      try { detail = (await res.json()).detail || ''; } catch { /* keep */ }
      error.textContent = detail.startsWith('password too short') ? t('setup.short')
        : detail === 'invalid user name' ? t('setup.badname')
        : detail === 'first setup only from the home network' ? t('setup.outside')
        : detail === 'already set up' ? t('setup.done') : detail || t('login.error');
      error.hidden = false;
      if (detail === 'already set up') setTimeout(showLogin, 1500);
      return;
    }
    $('setup-pass').value = $('setup-pass2').value = '';
    showApp();
  });

  $('acc-logout').addEventListener('click', () => $('btn-logout').click());
  $('btn-logout').addEventListener('click', async () => {
    await fetch('api/logout', { method: 'POST' });
    showLogin();
  });

  $('search').addEventListener('input', debounce(ev => {
    State.query = ev.target.value;
    if (State.query.trim() && location.hash !== '#/') location.hash = '#/';   // a search shows its hits in the list
    paintAskButton();
    loadDocs();
  }, 250));
  // Enter in the search field asks the AI – where that is switched on and the text reads like a question
  $('search').addEventListener('keydown', ev => {
    if (ev.key !== 'Enter' || !canAsk(ev.target.value)) return;
    ev.preventDefault();
    State.query = ev.target.value;
    if (location.hash !== '#/') location.hash = '#/';
    askArchive();
  });
  $('btn-ask').addEventListener('click', askArchive);
  $('ask-close').addEventListener('click', closeAsk);

  $('chk-recursive').addEventListener('change', ev => {
    State.recursive = ev.target.checked;
    store.set('recursive', State.recursive);
    loadDocs();
  });

  $('btn-more').addEventListener('click', () => loadDocs(true));
  window.addEventListener('hashchange', route);
  $('st-form').addEventListener('submit', saveStorage);
  initPicker();
  initTags();
  $('settings').addEventListener('click', ev => {
    const btn = ev.target.closest('[data-pick]');
    if (btn) showPicker(btn.dataset.pick);
  });
  $('ai-form').addEventListener('submit', saveAI);
  $('ai-test').addEventListener('click', testAI);
  $('ai-provider').addEventListener('change', async () => {
    syncAIForm();
    if (await saveAI()) loadModels();
  });
  $('ai-model').addEventListener('input', syncAIForm);
  $('ai-model-select').addEventListener('change', () => {
    $('ai-model').hidden = $('ai-model-select').value !== OTHER;
    if (!$('ai-model').hidden) $('ai-model').focus();
    syncAIForm();
  });
  $('ai-reload-models').addEventListener('click', async () => { if (await saveAI()) loadModels(); });
  $('ai-clear-key').addEventListener('click', async () => {
    aiConfig = await api('ai', { method: 'PUT', body: JSON.stringify({ clear_key: true }) });
    syncAIForm();
  });
  $('usr-new').addEventListener('click', () => editUser(null));
  $('usr-cancel').addEventListener('click', () => { $('usr-form').hidden = true; });
  $('usr-form').addEventListener('submit', saveUser);
  $('usr-admin').addEventListener('change', syncAdminAreas);
  $('sys-form').addEventListener('submit', saveSystemSettings);
  bindUpdate();
  $('sys-rescan').addEventListener('click', async () => {
    await api('rescan', { method: 'POST' });
    $('sys-rescan').textContent = t('sys.rescan.ok');
    setTimeout(() => { $('sys-rescan').textContent = t('sys.rescan'); loadSystem(); }, 4000);
  });
  $('pw-form').addEventListener('submit', async ev => {
    ev.preventDefault();
    try {
      const r = await api('me/password', { method: 'POST', body: JSON.stringify({ old: $('pw-old').value, new: $('pw-new').value }) });
      $('pw-old').value = ''; $('pw-new').value = '';
      setMsg($('pw-msg'), r.signed_out ? t('acc.ok.out', { n: r.signed_out }) : t('acc.ok'), true);
      if (r.signed_out) loadSessions();
    } catch (e) {
      setMsg($('pw-msg'), errText(e), false);
    }
  });
  $('pv-close').addEventListener('click', closePreview);
  $('acc-lang').value = LANG;
  $('acc-lang').addEventListener('change', async () => {
    const language = $('acc-lang').value;
    try { await api('me/prefs', { method: 'PUT', body: JSON.stringify({ language }) }); } catch { /* keep local */ }
    store.set('lang', language);
    location.reload();
  });
  initAccountSecurity();
  initSecurity();
  initApiKey();
  initPage();
  $('st-area-add').addEventListener('click', async () => {
    const name = $('st-area-name').value.trim().toLowerCase();
    if (!name) { $('st-area-name').focus(); return; }
    try {
      const r = await api('areas', { method: 'POST', body: JSON.stringify({ name, label: $('st-area-label').value.trim() }) });
      $('st-area-name').value = ''; $('st-area-label').value = '';
      State.areas = await api('areas');
      State.active.add(r.name);
      store.set('areas', [...State.active]);
      storage = await api('storage');
      renderChips(); renderAreaLabels();
      toast(esc(t('st.area.added', { name: r.label })), null, 6000);
    } catch (e) { toast(esc(errText(e))); }
  });
  $('sys-err-retry').addEventListener('click', async () => {
    const r = await api('text-errors/retry', { method: 'POST' });
    toast(esc(t('sys.err.retried', { n: r.retried })), null, 4000);
    setTimeout(loadSystem, 4000);
  });
  $('btn-tree').addEventListener('click', () => $('tree-panel').classList.toggle('is-open'));
  $('tree-expand').addEventListener('click', () => setAllOpen(true));
  $('tree-collapse').addEventListener('click', () => setAllOpen(false));
  document.addEventListener('keydown', ev => {
    if (ev.key !== 'Escape') return;
    if (!$('settings').hidden || !$('pagepage').hidden) location.hash = '#/';
    else if (State.selected) closePreview();
  });

  try {
    await api('me');
    await showApp();
  } catch {
    showLogin();
  }
});


// ------------------------------------------------------------ folder picker
// A large, searchable folder list for inputs with data-picker="<datalist id>" – the browser's
// own datalist popup is tiny (Safari) and cannot be styled. The datalist stays the source.
const Picker = { input: null, box: null, items: [], active: -1 };

function pickerOptions(input) {
  const list = document.getElementById(input.dataset.picker);
  return list ? [...list.options].map(o => o.value) : [];
}

function pickerRender() {
  const { input, box } = Picker;
  const all = pickerOptions(input);
  const q = input.value.trim().toLowerCase();
  const exact = all.some(f => f.toLowerCase() === q);
  const words = exact ? [] : q.split(/[\s/]+/).filter(Boolean);
  Picker.items = all.filter(f => words.every(w => f.toLowerCase().includes(w)));
  Picker.active = Picker.items.findIndex(f => f.toLowerCase() === q);
  if (!Picker.items.length) { box.hidden = true; return; }
  box.innerHTML = Picker.items.map((f, i) => {
    const cut = f.lastIndexOf('/');
    const head = cut >= 0 ? `<span class="picker-head">${esc(f.slice(0, cut + 1))}</span>` : '';
    return `<div class="picker-item${i === Picker.active ? ' active' : ''}" data-i="${i}" role="option">${head}${esc(f.slice(cut + 1))}</div>`;
  }).join('');
  const r = input.getBoundingClientRect();
  const below = window.innerHeight - r.bottom - 12;
  const above = r.top - 12;
  const up = below < 240 && above > below;
  box.style.left = `${Math.max(8, Math.min(r.left, window.innerWidth - Math.max(r.width, 420) - 8))}px`;
  box.style.minWidth = `${Math.max(r.width, 420)}px`;
  box.style.maxHeight = `${Math.min(window.innerHeight * 0.6, up ? above : below)}px`;
  box.style.top = up ? '' : `${r.bottom + 4}px`;
  box.style.bottom = up ? `${window.innerHeight - r.top + 4}px` : '';
  box.hidden = false;
  pickerScroll();
}

function pickerScroll() {
  const el = Picker.box.querySelector('.picker-item.active');
  if (el) el.scrollIntoView({ block: 'nearest' });
}

function pickerChoose(i) {
  const { input } = Picker;
  input.value = Picker.items[i];
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  Picker.box.hidden = true;
}

function initPicker() {
  const box = document.createElement('div');
  box.className = 'picker';
  box.setAttribute('role', 'listbox');
  box.hidden = true;
  document.body.appendChild(box);
  Picker.box = box;
  // mousedown, not click: keep the focus in the input
  box.addEventListener('mousedown', e => {
    const el = e.target.closest('.picker-item');
    e.preventDefault();
    if (el) pickerChoose(+el.dataset.i);
  });
  document.addEventListener('focusin', e => {
    if (e.target.matches('input[data-picker]') && !e.target.disabled) { Picker.input = e.target; pickerRender(); }
  });
  document.addEventListener('focusout', e => {
    if (e.target === Picker.input) box.hidden = true;
  });
  document.addEventListener('input', e => {
    if (e.target === Picker.input && document.activeElement === e.target) pickerRender();
  });
  document.addEventListener('keydown', e => {
    if (e.target !== Picker.input) return;
    if (box.hidden && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) { pickerRender(); e.preventDefault(); return; }
    if (box.hidden) return;
    const n = Picker.items.length;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      Picker.active = (Picker.active + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
      box.querySelectorAll('.picker-item').forEach((el, i) => el.classList.toggle('active', i === Picker.active));
      pickerScroll();
      e.preventDefault();
    } else if (e.key === 'Enter' && Picker.active >= 0) {
      pickerChoose(Picker.active);
      e.preventDefault();
    } else if (e.key === 'Escape') {
      box.hidden = true;
      e.preventDefault();
    }
  });
  window.addEventListener('resize', () => { box.hidden = true; });
  document.addEventListener('scroll', e => { if (!box.contains(e.target)) box.hidden = true; }, true);
}


// ------------------------------------------------------------------- tags

async function loadTags() {
  try {
    State.tagList = await api('tags?' + areaParam());
  } catch { return; }
  $('tag-list').innerHTML = State.tagList.map(x => `<option value="${esc(x.name)}">`).join('');
  const plain = State.tagList;
  $('tag-panel').hidden = !plain.length;
  const shut = store.get('tagsShut', false);
  $('tag-panel').classList.toggle('is-shut', shut);
  $('tag-head').setAttribute('aria-expanded', !shut);
  $('tag-head').querySelector('.tree-caret').classList.toggle('is-open', !shut);
  $('tag-head').querySelector('.tag-panel__n').textContent = plain.length;
  const cloud = $('tag-cloud');
  cloud.innerHTML = plain.map(x =>
    `<button type="button" class="tag tag--cloud" data-tag="${esc(x.name)}" aria-pressed="${State.tags.has(x.name)}">` +
    `${esc(x.name)} <span class="tag__n">${x.count}</span></button>`).join('');
  cloud.querySelectorAll('[data-tag]').forEach(b => b.addEventListener('click', () => toggleTagFilter(b.dataset.tag)));
}

function toggleTagFilter(tag) {
  if (State.tags.has(tag)) State.tags.delete(tag); else State.tags.add(tag);
  $('tree-panel').classList.remove('is-open');
  loadDocs();
  loadTags();
}

// Chips with × plus an input (folder-picker style suggestions from #tag-list).
// onSave(tags) persists and returns the stored tags. box.flush() adds what is still typed.
function tagEditor(box, tags, onSave) {
  let current = [...tags];
  let keepFocus = false;
  const render = () => {
    const focused = keepFocus || box.contains(document.activeElement);
    keepFocus = false;
    box.innerHTML = current.map((x, i) =>
      `<span class="tag">${esc(x)}<button type="button" class="tag__x" data-i="${i}" aria-label="${esc(t('tags.del'))}">×</button></span>`).join('') +
      `<input class="tag-input" data-picker="tag-list" autocomplete="off" placeholder="${esc(t('tags.new'))}">`;
    box.querySelectorAll('.tag__x').forEach(b => b.addEventListener('click', () => save(current.filter((_, i) => i !== +b.dataset.i))));
    const input = box.querySelector('input');
    input.addEventListener('keydown', ev => {
      if (ev.key === 'Enter' || ev.key === ',') {
        if (ev.key === 'Enter' && !Picker.box.hidden && Picker.active >= 0) return;   // the picker takes it
        ev.preventDefault();
        add(input.value);
      } else if (ev.key === 'Backspace' && !input.value && current.length) {
        save(current.slice(0, -1));
      }
    });
    input.addEventListener('change', () => add(input.value));
    if (focused) input.focus();
  };
  const add = value => {
    const tag = value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim();
    const input = box.querySelector('input');
    if (!tag || current.some(x => x.toLowerCase() === tag.toLowerCase())) { if (input) input.value = ''; return; }
    save([...current, tag]);
  };
  const save = async next => {
    keepFocus = box.contains(document.activeElement);
    try {
      current = await onSave(next);
    } catch (e) {
      alert(errText(e));
    }
    render();
  };
  box.flush = () => {
    const input = box.querySelector('input');
    const tag = input ? input.value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim() : '';
    return tag && !current.some(x => x.toLowerCase() === tag.toLowerCase()) ? [...current, tag] : current;
  };
  render();
}

function renderBulk() {
  const visible = new Set(State.items.map(d => d.id));
  [...State.sel].forEach(id => { if (!visible.has(id)) State.sel.delete(id); });
  $('bulk').hidden = !State.sel.size;
  $('bulk-count').textContent = t('tags.sel', { n: State.sel.size });
  const all = $('chk-all');
  all.checked = State.items.length > 0 && State.sel.size === State.items.length;
  all.indeterminate = State.sel.size > 0 && !all.checked;
}

async function bulkTag(mode) {
  const tag = $('bulk-tag').value.replace(/[,#]/g, ' ').replace(/\s+/g, ' ').trim();
  if (!tag || !State.sel.size) { $('bulk-tag').focus(); return; }
  try {
    const r = await api('tags/change', { method: 'POST', body: JSON.stringify({ ids: [...State.sel], [mode]: [tag] }) });
    setMsg($('bulk-msg'), t('tags.done', { n: r.changed }), true);
    $('bulk-tag').value = '';
    await Promise.all([loadDocs(), loadTags()]);
  } catch (e) {
    setMsg($('bulk-msg'), errText(e), false);
  }
}

function initTags() {
  document.querySelectorAll('[data-sort]').forEach(b => b.addEventListener('click', () => setSort(b.dataset.sort)));
  $('chk-all').addEventListener('change', ev => {
    State.items.forEach(d => { if (ev.target.checked) State.sel.add(d.id); else State.sel.delete(d.id); });
    renderList();
  });
  $('bulk-add').addEventListener('click', () => bulkTag('add'));
  $('bulk-remove').addEventListener('click', () => bulkTag('remove'));
  $('bulk-clear').addEventListener('click', () => { State.sel.clear(); renderList(); });
  $('home').addEventListener('click', ev => { ev.preventDefault(); goHome(); });
  $('chk-best').addEventListener('change', ev => { State.best = ev.target.checked; loadDocs(); });
  $('sel-kind').value = State.kind;
  $('sel-kind').addEventListener('change', ev => { State.kind = ev.target.value; store.set('kind', State.kind); loadDocs(); });
  $('tag-head').addEventListener('click', () => { store.set('tagsShut', !store.get('tagsShut', false)); loadTags(); });
  $('bulk-tag').addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && (Picker.box.hidden || Picker.active < 0)) { ev.preventDefault(); bulkTag('add'); }
  });
}


// ------------------------------------------------- move, trash, undo

const canWrite = doc => !!doc && (State.me.write_areas || []).includes(doc.area);

function toast(html, action, ms = 8000) {
  const box = $('toast');
  clearTimeout(box._timer);
  box.innerHTML = `<span>${html}</span>`;
  if (action) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'fd-button fd-button--transparent toast__action';
    b.textContent = action.label;
    b.addEventListener('click', () => { box.hidden = true; action.run(); });
    box.appendChild(b);
  }
  const x = document.createElement('button');
  x.type = 'button';
  x.className = 'fd-button fd-button--transparent toast__close';
  x.textContent = '✕';
  x.addEventListener('click', () => { box.hidden = true; });
  box.appendChild(x);
  box.hidden = false;
  box._timer = setTimeout(() => { box.hidden = true; }, ms);
}

async function refreshArchive() {
  await Promise.all([loadDocs(), loadTree(), loadStatus()].map(p => p.catch(() => null)));
}

// ------------------------------------------------- a small dialog that asks

// fields: [{key, label, value, placeholder, options: [{value, label}]}]; resolves to the values, or null
function ask({ title, text = '', ok, fields = [], run }) {
  const dlg = $('ask-dlg');
  $('ask-title').textContent = title;
  $('ask-text').textContent = text;
  $('ask-text').hidden = !text;
  $('ask-ok').textContent = ok;
  $('ask-error').hidden = true;
  const box = $('ask-fields');
  box.innerHTML = '';
  box.hidden = !fields.length;
  for (const f of fields) {
    const label = document.createElement('label');
    label.className = 'fd-form-label';
    label.htmlFor = 'askf-' + f.key;
    label.textContent = f.label;
    let input;
    if (f.options) {
      input = document.createElement('select');
      f.options.forEach(o => input.add(new Option(o.label, o.value)));
    } else {
      input = document.createElement('input');
      input.autocomplete = 'off';
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    input.className = 'fd-input';
    input.id = 'askf-' + f.key;
    input.value = f.value ?? '';
    box.append(label, input);
  }
  return new Promise(resolve => {
    const form = $('ask-form');
    const finish = value => {
      form.onsubmit = null;
      dlg.onclose = null;
      $('ask-cancel').onclick = null;
      if (dlg.open) dlg.close();
      resolve(value);
    };
    form.onsubmit = async ev => {
      ev.preventDefault();
      const values = Object.fromEntries(fields.map(f => [f.key, $('askf-' + f.key).value.trim()]));
      if (!run) return finish(values);
      $('ask-ok').disabled = true;
      try {
        finish(await run(values));
      } catch (e) {            // the dialog stays open, so the entry can be corrected
        $('ask-error').textContent = errText(e);
        $('ask-error').hidden = false;
      } finally { $('ask-ok').disabled = false; }
    };
    $('ask-cancel').onclick = () => finish(null);
    dlg.onclose = () => finish(null);
    dlg.showModal();
    const first = box.querySelector('input, select');
    if (first) { first.focus(); if (first.select) first.select(); } else $('ask-ok').focus();
  });
}

// ------------------------------------------------- new page, rename, move, trash

const writeAreas = () => State.areas.filter(a => (State.me.write_areas || []).includes(a.name));

async function afterChange(doc) {
  await Promise.all([refreshArchive(), loadPins().catch(() => null)]);
  if (!$('startpage').hidden) loadStart();
  if (!$('pagepage').hidden && Page.doc && doc && Page.doc.id === doc.id && !Edit.on) openPageView(doc.id);
  if (State.selected && doc && State.selected.id === doc.id) closePreview();
}

async function newPage() {
  const areas = writeAreas();
  if (!areas.length) return;
  const first = areas.find(a => State.active.has(a.name)) || areas[0];
  const fields = [{ key: 'title', label: t('new.title') }];
  if (areas.length > 1) fields.push({ key: 'area', label: t('new.area'), value: first.name, options: areas.map(a => ({ value: a.name, label: areaLabel(a.name) })) });
  fields.push({ key: 'folder', label: t('new.folder'), value: $('startpage').hidden ? State.folder : '', placeholder: t('new.folder.ph') });
  const doc = await ask({ title: t('new.page'), ok: t('new.ok'), fields,
    run: v => api('pages', { method: 'POST', body: JSON.stringify({ area: v.area || first.name, folder: v.folder, title: v.title }) }) });
  if (!doc) return;
  refreshArchive();
  Edit.auto = doc.id;
  location.hash = '#/seite/' + doc.id;
}

async function renameDoc(doc) {
  const done = await ask({ title: t('rn.title'), ok: t('rn.ok'), fields: [{ key: 'title', label: t('new.title'), value: doc.title }],
    run: v => api(`documents/${doc.id}/rename`, { method: 'POST', body: JSON.stringify({ title: v.title }) }) });
  if (!done) return;
  toast(esc(t('rn.done', { title: done.title })));
  afterChange(done);
}

async function moveDoc(doc) {
  const areas = writeAreas();
  const fields = [];
  if (areas.length > 1) fields.push({ key: 'area', label: t('new.area'), value: doc.area, options: areas.map(a => ({ value: a.name, label: areaLabel(a.name) })) });
  fields.push({ key: 'folder', label: t('new.folder'), value: doc.folder, placeholder: t('new.folder.ph') });
  const done = await ask({ title: `${t('mv.title')}: ${doc.title}`, ok: t('mv.ok'), fields,
    run: v => api(`documents/${doc.id}/move`, { method: 'POST', body: JSON.stringify({ folder: v.folder, area: v.area || doc.area }) }) });
  if (!done) return;
  toast(esc(t('mv.done', { folder: [areaLabel(done.area), ...(done.folder ? done.folder.split('/') : [])].join(' › ') })));
  afterChange(done);
}

async function trashDoc(doc) {
  let days = 30;
  try { days = (await api('trash')).days; } catch { /* keep */ }
  const done = await ask({ title: t('tr.q', { title: doc.title }), text: days > 0 ? t('tr.hint', { days }) : '', ok: t('tr.ok'),
    run: () => api(`documents/${doc.id}/trash`, { method: 'POST' }) });
  if (!done) return;
  if (!$('pagepage').hidden && Page.doc && Page.doc.id === doc.id) location.hash = '#/';
  if (State.selected && State.selected.id === doc.id) closePreview();
  await afterChange(null);
  toast(esc(t('tr.done', { title: doc.title })), { label: t('tr.undo'), run: async () => {
    try {
      const back = await api('trash/restore', { method: 'POST', body: JSON.stringify({ trash_path: done.trash_path }) });
      toast(esc(t('tr.back', { title: back.title })));
      afterChange(null);
    } catch (e) { toast(esc(errText(e))); }
  } }, 15000);
}

// ------------------------------------------------- questions to the archive

const Ask = { token: 0, question: '' };
// a question is more than a search word: several words, or a question mark
const canAsk = text => !!(State.status && State.status.ask) && (/\?\s*$/.test(text) || text.trim().split(/\s+/).length >= 3);

function paintAskButton() {
  $('btn-ask').hidden = !canAsk(State.query);
  if (State.query.trim() !== Ask.question) closeAsk();       // the answer belongs to the question it was given for
}

function closeAsk() {
  Ask.token++;
  Ask.question = '';
  $('ask-box').hidden = true;
}

async function askArchive() {
  const question = State.query.trim();
  if (question.length < 3) return;
  const token = ++Ask.token;
  Ask.question = question;
  $('ask-box').hidden = false;
  $('ask-question').textContent = question;
  $('ask-answer').innerHTML = `<p class="ask-wait">${esc(t('ask.loading'))}</p>`;
  $('ask-sources').hidden = true;
  $('ask-note').hidden = true;
  let data;
  try {
    data = await api('ask', { method: 'POST', body: JSON.stringify({ question, areas: [...State.active].join(',') }) });
  } catch (e) {
    if (token === Ask.token) $('ask-answer').innerHTML = `<p class="ask-error">${esc(errText(e))}</p>`;
    return;
  }
  if (token !== Ask.token) return;
  if (!data.found) { $('ask-answer').innerHTML = `<p>${esc(t('ask.none'))}</p>`; return; }
  const byNumber = new Map(data.sources.map(s => [s.n, s]));
  // the answer is the model's text: rendered as Markdown, cleaned, its [n] turned into links to the sources
  const html = DOMPurify.sanitize(marked.parse(data.answer, { gfm: true, breaks: false }));
  $('ask-answer').innerHTML = html.replace(/\[(\d{1,2})\]/g, (all, n) =>
    (byNumber.has(Number(n)) ? `<button type="button" class="ask-ref" data-n="${Number(n)}">${Number(n)}</button>` : all));
  const cited = data.sources.filter(s => s.cited);
  const box = $('ask-sources');
  box.innerHTML = `<h4 class="ask-sources__title">${esc(t('ask.sources'))}</h4>`;
  for (const s of cited.length ? cited : data.sources.slice(0, 3)) {
    const where = [areaLabel(s.area), ...(s.folder ? s.folder.split('/') : [])].join(' › ');
    const spot = s.page ? t('ask.page', { n: s.page }) : s.heading;
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'ask-source';
    item.dataset.n = s.n;
    item.innerHTML = `<span class="ask-ref ask-ref--static">${s.n}</span>` +
      `<span class="ask-source__main"><span class="ask-source__title"><span class="doc-kind doc-kind--${esc(s.ext)}">${s.ext === 'md' ? '¶' : 'PDF'}</span>${esc(s.title)}` +
      `${spot ? ` <span class="ask-source__spot">· ${esc(spot)}</span>` : ''}</span>` +
      `<span class="ask-source__where">${esc(where)}</span><span class="ask-source__text">${esc(s.excerpt)}</span></span>`;
    item.addEventListener('click', () => openSource(s));
    box.appendChild(item);
  }
  box.hidden = false;
  $('ask-answer').querySelectorAll('.ask-ref').forEach(b => b.addEventListener('click', () => {
    const target = box.querySelector(`.ask-source[data-n="${b.dataset.n}"]`);
    if (target) { target.scrollIntoView({ block: 'nearest' }); target.classList.add('is-flash'); setTimeout(() => target.classList.remove('is-flash'), 1200); }
    else openSource(byNumber.get(Number(b.dataset.n)));
  }));
  $('ask-note').textContent = t('ask.note', { model: data.model, seconds: data.seconds, n: data.sources.length });
  $('ask-note').hidden = false;
}

// a page opens in the reading view, a PDF at the page the passage stands on
function openSource(s) {
  if (s.ext === 'md') { location.hash = '#/seite/' + s.id; return; }
  window.open(`api/documents/${s.id}/file${s.page ? '#page=' + s.page : ''}`, '_blank', 'noopener');
}

// ------------------------------------------------- trash

const when = iso => new Date(iso).toLocaleString(LANG, { dateStyle: 'medium', timeStyle: 'short' });

async function loadTrash() {
  document.title = t('trash.title') + ' – Wissen!';
  let data;
  try { data = await api('trash'); } catch (e) { toast(esc(errText(e))); return; }
  $('trash-note').textContent = data.days > 0 ? t('trash.note', { days: data.days }) : t('trash.note.never');
  const rows = $('trash-rows');
  rows.innerHTML = '';
  const today = new Date(new Date().toISOString().slice(0, 10));
  for (const item of data.items) {
    const left = data.days > 0 ? data.days - Math.round((today - new Date(item.deleted)) / 86400000) : null;
    const tr = document.createElement('tr');
    tr.className = 'fd-table__row';
    const place = [areaLabel(item.area), ...(item.folder ? item.folder.split('/') : [])].join(' › ');
    tr.innerHTML =
      `<td class="fd-table__cell"><div class="doc-title"><span class="doc-kind doc-kind--${esc(item.ext)}">${item.ext === 'md' ? '¶' : 'PDF'}</span>${esc(item.title)}</div></td>` +
      `<td class="fd-table__cell"><span class="doc-area"><span class="area-dot" style="--dot:${areaColor(item.area)}"></span>${esc(place)}</span></td>` +
      `<td class="fd-table__cell col-date">${esc(formatDate(item.deleted))}</td>` +
      `<td class="fd-table__cell">${left === null ? '–' : esc(left <= 0 ? t('trash.today') : left === 1 ? t('trash.day') : t('trash.days', { n: left }))}</td>` +
      `<td class="fd-table__cell trash-actions">` +
        `<button type="button" class="fd-button fd-button--transparent" data-k="view">${esc(t('trash.view'))}</button>` +
        ((State.me.write_areas || []).includes(item.area) ? `<button type="button" class="fd-button" data-k="restore">${esc(t('trash.restore'))}</button>` : '') +
      `</td>`;
    tr.querySelector('[data-k=view]').addEventListener('click', () => viewTrashed(item));
    tr.querySelector('[data-k=restore]')?.addEventListener('click', async () => {
      try {
        const back = await api('trash/restore', { method: 'POST', body: JSON.stringify({ trash_path: item.trash_path }) });
        toast(esc(t('tr.back', { title: back.title })));
        loadTrash();
        afterChange(null);
      } catch (e) { toast(esc(errText(e))); }
    });
    rows.appendChild(tr);
  }
  $('trash-table').hidden = !data.items.length;
  $('trash-empty').hidden = data.items.length > 0;
}

// a binned PDF opens in its own tab; a binned page is shown as it read (its pictures are in the trash too)
async function viewTrashed(item) {
  const url = 'api/trash/file?path=' + encodeURIComponent(item.trash_path);
  if (item.ext !== 'md') { window.open(url, '_blank', 'noopener'); return; }
  try {
    const res = await fetch(url, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(`${res.status}`);
    const text = await res.text();
    Ver.doc = null;
    $('ver-title').textContent = `${t('trash.title')}: ${item.title}`;
    $('ver-list').hidden = true;
    document.querySelector('#ver-dlg .ver-bar').hidden = true;
    $('ver-legend').hidden = true;
    const view = $('ver-view');
    view.className = 'ver-view md';
    view.innerHTML = DOMPurify.sanitize(marked.parse(splitHead(text), { gfm: true, breaks: false }));
    view.querySelectorAll('img').forEach(img => img.remove());
    view.querySelectorAll('a[href]').forEach(a => { a.removeAttribute('href'); });
    $('ver-dlg').showModal();
  } catch (e) { toast(esc(errText(e))); }
}

// ------------------------------------------------- versions of a page

const Ver = { doc: null, items: [], current: null, loaded: null, mode: 'diff' };

async function openVersions(doc) {
  let items;
  try { items = (await api(`documents/${doc.id}/versions`)).items; } catch (e) { toast(esc(errText(e))); return; }
  if (!items.length) { toast(esc(t('ver.none'))); return; }
  Ver.doc = doc;
  Ver.items = items;
  $('ver-title').textContent = t('ver.title', { title: doc.title });
  $('ver-list').hidden = false;
  document.querySelector('#ver-dlg .ver-bar').hidden = false;
  $('ver-restore').hidden = !canWrite(doc);
  const list = $('ver-list');
  list.innerHTML = '';
  for (const item of items) {
    const li = document.createElement('li');
    li.innerHTML = `<button type="button" class="ver-item" data-v="${esc(item.v)}">` +
      `<span class="ver-item__at">${esc(when(item.at))}</span>` +
      `<span class="ver-item__by">${esc(t('ver.before'))} · ${esc(item.by)}</span></button>`;
    li.firstChild.addEventListener('click', () => showVersion(item));
    list.appendChild(li);
  }
  $('ver-dlg').showModal();
  showVersion(items[0]);
}

async function showVersion(item) {
  Ver.current = item;
  document.querySelectorAll('.ver-item').forEach(b => b.classList.toggle('is-selected', b.dataset.v === item.v));
  try {
    Ver.loaded = await api(`documents/${Ver.doc.id}/versions/${item.v}?compare=true`);
  } catch (e) { toast(esc(errText(e))); return; }
  if (Ver.current === item) paintVersion();
}

function paintVersion() {
  const view = $('ver-view');
  const diff = Ver.mode === 'diff';
  $('ver-mode-diff').setAttribute('aria-pressed', diff);
  $('ver-mode-text').setAttribute('aria-pressed', !diff);
  $('ver-legend').hidden = !diff || !Ver.loaded.diff;
  view.scrollTop = 0;
  if (!diff) {
    view.className = 'ver-view md';
    renderPage(view, Ver.doc, Ver.loaded.text);
    return;
  }
  view.className = 'ver-view ver-view--diff';
  if (!Ver.loaded.diff) { view.innerHTML = `<p class="start-hint">${esc(t('ver.same'))}</p>`; return; }
  // unified diff from the version to the page as it is now: "-" was there then, "+" came since
  view.innerHTML = Ver.loaded.diff.split('\n').slice(2).map(line => {
    const kind = line.startsWith('@@') ? 'hunk' : line.startsWith('-') ? 'del' : line.startsWith('+') ? 'add' : 'same';
    const text = kind === 'hunk' ? '⋯' : line.slice(1);
    return `<div class="diff-line diff-line--${kind}">${esc(text) || '&nbsp;'}</div>`;
  }).join('');
}

async function restoreVersion() {
  const item = Ver.current, doc = Ver.doc;
  if (!item || !doc || !confirm(t('ver.restore.q', { at: when(item.at) }))) return;
  try {
    await api(`documents/${doc.id}/versions/${item.v}/restore`, { method: 'POST' });
  } catch (e) { toast(esc(errText(e))); return; }
  $('ver-dlg').close();
  toast(esc(t('ver.restored', { at: when(item.at) })));
  afterChange(doc);
}

function initVersions() {
  $('ver-close').addEventListener('click', () => $('ver-dlg').close());
  $('ver-mode-diff').addEventListener('click', () => { Ver.mode = 'diff'; if (Ver.loaded) paintVersion(); });
  $('ver-mode-text').addEventListener('click', () => { Ver.mode = 'text'; if (Ver.loaded) paintVersion(); });
  $('ver-restore').addEventListener('click', restoreVersion);
}

// ------------------------------------------------- editing a page

const HEARTBEAT = 4 * 60 * 1000;   // the lock runs out after ten minutes without one
const Edit = {
  on: false, auto: null, doc: null, version: '', saved: '', beat: null,
  preview: store.get('ed.preview', true),
  mode: 'source',        // 'source' = markdown text, 'rich' = formatted (WYSIWYG)
  rich: null,            // the formatted editor while it is open
  richBase: '',          // the text it was opened with
  richChanged: false,    // something was changed in it since
  dirty() {
    if (!this.on) return false;
    if (this.rich) return this.richChanged || this.richBase !== this.saved;
    return $('ed-text').value !== this.saved;
  },
};

let richBundle = null;
function loadRichBundle() {
  richBundle ||= new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = 'vendor/milkdown/wissen-editor.js';
    s.onload = resolve;
    s.onerror = () => { richBundle = null; reject(new Error('editor bundle')); };
    document.head.appendChild(s);
  });
  return richBundle;
}

// the text as it would be saved now; from the formatted view only what was touched is rewritten.
// null: the formatted view cannot write this change faithfully – the source is shown instead
function editText() {
  if (!Edit.rich) return $('ed-text').value;
  if (!Edit.richChanged) return Edit.richBase;
  const result = Edit.rich.save();
  if (result.safe) return result.text;
  closeRich(result.text);
  toast(esc(t('ed.unsafe')), null, 60000);
  return null;
}

function closeRich(text) {
  if (!Edit.rich) return;
  try { Edit.rich.destroy(); } catch { /* gone already */ }
  Edit.rich = null;
  $('ed-rich-page').innerHTML = '';
  $('ed-text').value = text;
  Edit.mode = 'source';
  paintEdit();
  paintEditView();
}

async function openRich() {
  const text = $('ed-text').value;
  $('ed-state').textContent = t('ed.loading');
  try {
    await loadRichBundle();
    const doc = Edit.doc;
    Edit.rich = await WissenEditor.create($('ed-rich-page'), text, {
      onChange: () => { if (!Edit.richChanged) { Edit.richChanged = true; paintEdit(); } },
      onSelect: where => { $('ed-table-tools').hidden = !where.table; },
      imageUrl: src => (isExternal(src) ? src : assetUrl(doc, src)),
    });
  } catch (e) {
    toast(esc(t('ed.loadfail')));
    paintEdit();
    return false;
  }
  Edit.richBase = text;
  Edit.richChanged = false;
  Edit.mode = 'rich';
  $('ed-table-tools').hidden = true;
  paintEdit();
  Edit.rich.focus();
  return true;
}

async function setEditMode(mode, remember = true) {
  if (!Edit.on || mode === Edit.mode) return;
  if (mode === 'rich') { if (!await openRich()) return; }
  else {
    const text = editText();
    if (text !== null) closeRich(text);
  }
  if (remember && Edit.mode === mode && State.me.editor !== mode) {
    State.me.editor = mode;
    api('me/prefs', { method: 'PUT', body: JSON.stringify({ editor: mode }) }).catch(() => null);
  }
}

function paintEdit() {
  $('ed-state').textContent = Edit.dirty() ? t('ed.dirty') : t('ed.saved');
  $('ed-state').classList.toggle('is-dirty', Edit.dirty());
  $('ed-save').disabled = !Edit.dirty();
  const rich = !!Edit.rich;
  $('ed-mode-source').setAttribute('aria-pressed', !rich);
  $('ed-mode-rich').setAttribute('aria-pressed', rich);
  $('ed-tools').hidden = !rich;
  $('ed-rich').hidden = !rich;
  $('ed-text').hidden = rich;
  $('ed-preview').hidden = rich;                 // the formatted view is its own preview
  $('ed-preview').setAttribute('aria-pressed', Edit.preview);
  $('ed-view').hidden = rich || !Edit.preview;
}

// the preview keeps step with the source: as far down the one, as far down the other
function syncEditView() {
  const area = $('ed-text'), view = $('ed-view');
  if (!Edit.on || Edit.rich || !Edit.preview) return;
  const room = area.scrollHeight - area.clientHeight;
  view.scrollTop = room > 0 ? area.scrollTop / room * (view.scrollHeight - view.clientHeight) : 0;
}

const paintEditView = debounce(async () => {
  if (!(Edit.on && Edit.preview && !Edit.rich)) return;
  await renderPage($('ed-view'), Edit.doc, $('ed-text').value);
  syncEditView();
}, 300);

// How large and how wide pages read. The last setting belongs to the account, so it is the
// same in every browser; it is sent a moment after the slider comes to rest.
const View = { zoom: 100, width: 85 };
const saveView = debounce(() => {
  if (State.me) api('me/prefs', { method: 'PUT', body: JSON.stringify({ zoom: View.zoom, width: View.width }) }).catch(() => null);
}, 600);

function setView({ zoom = View.zoom, width = View.width } = {}, save = true) {
  View.zoom = clamp(Math.round(Number(zoom) / 10) * 10 || 100, 80, 250);
  View.width = clamp(Math.round(Number(width) / 5) * 5 || 85, 40, 100);
  const root = document.documentElement.style;
  root.setProperty('--md-zoom', View.zoom / 100);
  root.setProperty('--md-width', View.width + '%');
  document.querySelectorAll('.zoom__range').forEach(r => { r.value = View.zoom; r.title = `${t('zoom.tip')} – ${View.zoom} %`; });
  document.querySelectorAll('.width__range').forEach(r => { r.value = View.width; r.title = `${t('width.tip')} – ${View.width} %`; });
  if (save) saveView();
  syncEditView();
}

async function startEdit() {
  const doc = Page.doc;
  if (!doc || Edit.on) return;
  let content;
  try {
    await api(`documents/${doc.id}/lock`, { method: 'POST' });
    content = await api(`documents/${doc.id}/content`);
  } catch (e) { toast(esc(errText(e))); return; }
  Edit.on = true;
  Edit.doc = doc;
  Edit.version = content.version;
  Edit.saved = content.body;
  $('ed-text').value = content.body;
  $('ed-title').textContent = doc.title;
  for (const id of ['page-body', 'page-meta']) $(id).hidden = true;
  document.querySelector('#pagepage .page-bar').hidden = true;
  $('page-editor').hidden = false;
  $('pagepage').classList.add('is-editing');
  Edit.mode = 'source';
  paintEdit();
  paintEditView();
  $('ed-text').focus();
  $('ed-text').setSelectionRange(0, 0);
  $('ed-text').scrollTop = 0;
  if (State.me.editor === 'rich') setEditMode('rich', false);    // the view this account used last
  Edit.beat = setInterval(async () => {
    try { await api(`documents/${doc.id}/lock`, { method: 'POST' }); }
    catch (e) { if (e.info && e.info.code === 'locked') toast(esc(t('ed.lost', { by: e.info.by })), null, 60000); }
  }, HEARTBEAT);
}

async function saveEdit() {
  if (!Edit.dirty()) return true;
  const text = editText();
  if (text === null) return false;
  if (text === Edit.saved) {                      // changed and changed back: nothing to write
    if (Edit.rich) { Edit.richChanged = false; Edit.richBase = text; }
    paintEdit();
    return true;
  }
  $('ed-state').textContent = t('ed.saving');
  try {
    const r = await api(`documents/${Edit.doc.id}/content`, { method: 'PUT',
      body: JSON.stringify({ text, body_only: true, base_version: Edit.version }) });
    Edit.version = r.version;
    Edit.saved = text;
    if (Edit.rich) { Edit.richChanged = false; Edit.richBase = text; }
    paintEdit();
    return true;
  } catch (e) {
    paintEdit();
    toast(esc(errText(e)), null, 20000);
    return false;
  }
}

// leave the editor: the lock goes back, the reading view comes back
function endEdit(reload = false) {
  if (!Edit.on) return;
  const doc = Edit.doc;
  clearInterval(Edit.beat);
  if (Edit.rich) { try { Edit.rich.destroy(); } catch { /* gone already */ } Edit.rich = null; $('ed-rich-page').innerHTML = ''; }
  Edit.on = false;
  fetch(`api/documents/${doc.id}/lock`, { method: 'DELETE', credentials: 'same-origin', keepalive: true }).catch(() => null);
  $('page-editor').hidden = true;
  $('pagepage').classList.remove('is-editing');
  for (const id of ['page-body', 'page-meta']) $(id).hidden = false;
  document.querySelector('#pagepage .page-bar').hidden = false;
  $('ed-text').value = '';
  $('ed-view').innerHTML = '';
  if (reload) { openPageView(doc.id); refreshArchive(); if (!$('startpage').hidden) loadStart(); }
}

// put text where the cursor is (undo keeps working where the browser supports it)
function insertText(area, text) {
  area.focus();
  if (!document.execCommand || !document.execCommand('insertText', false, text)) {
    area.setRangeText(text, area.selectionStart, area.selectionEnd, 'end');
    area.dispatchEvent(new Event('input', { bubbles: true }));
  }
}

async function uploadAssets(files) {
  for (const file of files) {
    toast(esc(t('ed.upload', { name: file.name })), null, 60000);
    try {
      const res = await fetch(`api/documents/${Edit.doc.id}/asset?name=${encodeURIComponent(file.name || 'bild.png')}`,
        { method: 'POST', credentials: 'same-origin', body: file });
      if (!res.ok) {
        let detail = `${res.status}`;
        try { detail = (await res.json()).detail || detail; } catch { /* keep */ }
        throw new Error(detail);
      }
      const { link } = await res.json();
      const label = (file.name || '').replace(/\.[^.]+$/, '').replace(/[\[\]]/g, '');
      if (Edit.rich && file.type.startsWith('image/')) Edit.rich.image(safeDecode(link), label);
      else if (Edit.rich) Edit.rich.link(link);
      else insertText($('ed-text'), `${file.type.startsWith('image/') ? '!' : ''}[${label}](${link})\n`);
      $('toast').hidden = true;
    } catch (e) { toast(esc(errText(e)), null, 20000); }
  }
}

function initEdit() {
  const area = $('ed-text');
  $('page-edit').addEventListener('click', startEdit);
  $('ed-save').addEventListener('click', saveEdit);
  $('ed-done').addEventListener('click', async () => { if (await saveEdit()) endEdit(true); });
  $('ed-cancel').addEventListener('click', () => {
    if (Edit.dirty() && !confirm(t('ed.discard'))) return;
    endEdit(true);
  });
  $('ed-preview').addEventListener('click', () => {
    Edit.preview = !Edit.preview;
    store.set('ed.preview', Edit.preview);
    paintEdit();
    paintEditView();
  });
  area.addEventListener('input', () => { paintEdit(); paintEditView(); });
  area.addEventListener('scroll', syncEditView, { passive: true });
  document.querySelectorAll('.zoom__range').forEach(r => {
    r.addEventListener('input', () => setView({ zoom: r.value }));
    r.addEventListener('dblclick', () => setView({ zoom: 100 }));
  });
  document.querySelectorAll('.width__range').forEach(r => {
    r.addEventListener('input', () => setView({ width: r.value }));
    r.addEventListener('dblclick', () => setView({ width: 85 }));
  });
  setView({}, false);
  area.addEventListener('keydown', ev => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 's') { ev.preventDefault(); saveEdit(); }
    else if (ev.key === 'Tab' && !ev.shiftKey && !ev.metaKey && !ev.ctrlKey && !ev.altKey) { ev.preventDefault(); insertText(area, '  '); }
  });
  area.addEventListener('paste', ev => {
    const files = [...(ev.clipboardData?.files || [])];
    if (files.length) { ev.preventDefault(); uploadAssets(files); }
  });
  area.addEventListener('dragover', ev => { if (ev.dataTransfer?.types.includes('Files')) ev.preventDefault(); });
  area.addEventListener('drop', ev => {
    const files = [...(ev.dataTransfer?.files || [])];
    if (files.length) { ev.preventDefault(); uploadAssets(files); }
  });
  $('ed-mode-source').addEventListener('click', () => setEditMode('source'));
  $('ed-mode-rich').addEventListener('click', () => setEditMode('rich'));
  $('ed-tools').addEventListener('mousedown', ev => { if (ev.target.closest('.ed-tool')) ev.preventDefault(); });   // keep the cursor in the text
  $('ed-tools').addEventListener('click', async ev => {
    const tool = ev.target.closest('.ed-tool')?.dataset.tool;
    if (!tool || !Edit.rich) return;
    if (tool === 'image') { $('ed-file').click(); return; }
    if (tool === 'link') {
      const v = await ask({ title: t('link.title'), ok: t('link.ok'), fields: [{ key: 'url', label: t('link.url'), placeholder: 'https://' }] });
      if (v && v.url && Edit.rich) Edit.rich.link(v.url);
      return;
    }
    if (tool === 'task') Edit.rich.task(); else Edit.rich.run(tool);
  });
  $('ed-file').addEventListener('change', ev => {
    const files = [...ev.target.files];
    ev.target.value = '';
    if (files.length) uploadAssets(files);
  });
  const richBox = $('ed-rich');
  richBox.addEventListener('keydown', ev => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 's') { ev.preventDefault(); saveEdit(); }
  });
  richBox.addEventListener('paste', ev => {
    const files = [...(ev.clipboardData?.files || [])];
    if (files.length) { ev.preventDefault(); ev.stopPropagation(); uploadAssets(files); }
  }, true);
  richBox.addEventListener('drop', ev => {
    const files = [...(ev.dataTransfer?.files || [])];
    if (files.length) { ev.preventDefault(); ev.stopPropagation(); uploadAssets(files); }
  }, true);
  addEventListener('beforeunload', ev => { if (Edit.dirty()) { ev.preventDefault(); ev.returnValue = ''; } });
  addEventListener('pagehide', () => {
    if (Edit.on) fetch(`api/documents/${Edit.doc.id}/lock`, { method: 'DELETE', credentials: 'same-origin', keepalive: true }).catch(() => null);
  });
  $('btn-new').addEventListener('click', newPage);
  $('start-new').addEventListener('click', newPage);
}

// ------------------------------------------------- start page and pins

// a pin holds on to the fixed id of a page; a PDF has none, so to its content
const pinKey = doc => (doc.sha256.startsWith(doc.id) ? doc.sha256 : doc.id);
const isPinned = doc => !!doc && State.pins.some(p => p.pin === pinKey(doc));

async function loadPins() {
  State.pins = (await api('me/pins')).items;
  paintPin($('pv-pin'), State.selected);
  paintPin($('page-pin'), Page.doc);
}

function paintPin(btn, doc) {
  const on = isPinned(doc);
  btn.textContent = on ? '★' : '☆';
  btn.setAttribute('aria-pressed', on);
  btn.title = t(on ? 'pin.off' : 'pin.on');
  btn.setAttribute('aria-label', btn.title);
}

async function togglePin(doc, quiet = false) {
  const pinned = !isPinned(doc);
  try {
    await api(`documents/${doc.id}/pin`, { method: 'PUT', body: JSON.stringify({ pinned }) });
    await loadPins();
  } catch (e) { toast(esc(errText(e))); return; }
  if (!$('startpage').hidden) loadStart();
  if (!quiet) {
    toast(esc(t(pinned ? 'pin.done' : 'pin.undone', { title: doc.title })),
      { label: t('pin.undo'), run: () => togglePin(doc, true) });
  }
}

// a page opens in the reading view, a PDF in the archive with its preview
function openDoc(doc) {
  if (doc.ext === 'md') { location.hash = '#/seite/' + doc.id; return; }
  location.hash = '#/';
  openPreview(doc);
}

function startCard(doc, withDate) {
  const card = document.createElement('div');
  card.className = 'start-card';
  const place = [areaLabel(doc.area), ...(doc.folder ? doc.folder.split('/') : [])].join(' › ');
  const when = withDate && doc.changed ? t('start.changed', { d: formatDate(doc.changed.slice(0, 10)) }) : '';
  card.innerHTML =
    `<a class="start-card__link" href="${doc.ext === 'md' ? '#/seite/' + esc(doc.id) : '#/'}">` +
      `<span class="start-card__title"><span class="doc-kind doc-kind--${esc(doc.ext)}">${doc.ext === 'md' ? '¶' : 'PDF'}</span>${esc(doc.title)}</span>` +
      `<span class="start-card__sub"><span class="area-dot" style="--dot:${areaColor(doc.area)}"></span>${esc(place)}</span>` +
      (when ? `<span class="start-card__when">${esc(when)}</span>` : '') +
    `</a>` +
    `<button type="button" class="fd-button fd-button--transparent pin-btn start-card__pin"></button>`;
  card.querySelector('.start-card__link').addEventListener('click', ev => { ev.preventDefault(); openDoc(doc); });
  const pin = card.querySelector('.start-card__pin');
  paintPin(pin, doc);
  pin.addEventListener('click', () => togglePin(doc));
  return card;
}

let startToken = 0;
async function loadStart() {
  const token = ++startToken;
  document.title = 'Wissen!';
  let pins, recent;
  try {
    [pins, recent] = await Promise.all([api('me/pins'), api('documents?recursive=true&sort=changed&desc=true&limit=8')]);
  } catch { return; }
  if (token !== startToken) return;
  State.pins = pins.items;
  const box = $('start-pins');
  box.innerHTML = '';
  State.pins.forEach(doc => box.appendChild(startCard(doc, false)));
  $('start-nopins').hidden = State.pins.length > 0;
  const list = $('start-recent');
  list.innerHTML = '';
  recent.items.forEach(doc => list.appendChild(startCard(doc, true)));
  $('start-norecent').hidden = recent.items.length > 0;
}

// ------------------------------------------------- document menu (⋯)

function docMenu(anchor, doc) {
  document.querySelector('.fo-menu')?.remove();
  const menu = document.createElement('div');
  menu.className = 'fo-menu';
  menu.setAttribute('role', 'menu');
  const url = `api/documents/${doc.id}/file`;
  menu.innerHTML =
    `<a role="menuitem" href="${esc(doc.ext === 'md' ? '#/seite/' + doc.id : url)}"${doc.ext === 'md' ? '' : ' target="_blank" rel="noopener"'}>${esc(t('dm.open'))}</a>` +
    `<a role="menuitem" href="${esc(url)}?download=true">${esc(t('dm.download'))}</a>` +
    `<button type="button" role="menuitem" data-k="folder">${esc(t('dm.folder'))}</button>` +
    `<button type="button" role="menuitem" data-k="pin">${esc(t(isPinned(doc) ? 'pin.off' : 'pin.on'))}</button>` +
    (doc.ext === 'md' ? `<button type="button" role="menuitem" data-k="versions">${esc(t('ver.menu'))}</button>` : '') +
    (canWrite(doc) ? (doc.ext === 'md' ? `<button type="button" role="menuitem" data-k="edit">${esc(t('dm.editpage'))}</button>` : '') +
      `<button type="button" role="menuitem" data-k="rename">${esc(t('dm.rename'))}</button>` +
      `<button type="button" role="menuitem" data-k="move">${esc(t('dm.move'))}</button>` +
      `<button type="button" role="menuitem" data-k="trash">${esc(t('dm.trash'))}</button>` : '');
  document.body.appendChild(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.left = Math.max(8, Math.min(r.right - menu.offsetWidth, innerWidth - menu.offsetWidth - 8)) + 'px';
  menu.style.top = (r.bottom + 4 + menu.offsetHeight > innerHeight ? r.top - menu.offsetHeight - 4 : r.bottom + 4) + 'px';
  const close = ev => { if (!menu.contains(ev.target)) { menu.remove(); removeEventListener('pointerdown', close, true); } };
  addEventListener('pointerdown', close, true);
  menu.addEventListener('click', ev => {
    const el = ev.target.closest('[role=menuitem]');
    if (!el) return;
    menu.remove();
    removeEventListener('pointerdown', close, true);
    const k = el.dataset.k;
    if (k === 'pin') togglePin(doc);
    if (k === 'edit') {
      if (Page.doc && Page.doc.id === doc.id && !$('pagepage').hidden) startEdit();
      else { Edit.auto = doc.id; location.hash = '#/seite/' + doc.id; }
    }
    if (k === 'versions') openVersions(doc);
    if (k === 'rename') renameDoc(doc);
    if (k === 'move') moveDoc(doc);
    if (k === 'trash') trashDoc(doc);
    if (k === 'folder') {
      selectFolder(doc.folder || '');
      setTimeout(() => document.querySelector('.tree-row.is-selected')?.scrollIntoView({ block: 'nearest' }), 300);
    }
  });
}


// ------------------------------------------------------------------ pages
// A page is a Markdown file. It is rendered in the browser (marked), cleaned (DOMPurify),
// and its relative links are bent: pictures come from the page's folder via the API,
// links to other pages open them here, links to a PDF (with #page=N) open the PDF.

const CALLOUTS = { NOTE: 'note', TIP: 'tip', IMPORTANT: 'important', WARNING: 'warning', CAUTION: 'caution', INFO: 'note' };

function splitHead(text) {
  const m = /^﻿?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)/.exec(text);
  return m ? text.slice(m[0].length) : text;
}

// a link in Markdown is usually already %-encoded ("Bild%20eins.png"); decode each part once,
// then encode it again, so neither "Bild eins.png" nor "Bild%20eins.png" ends up as %2520
const safeDecode = part => { try { return decodeURIComponent(part); } catch { return part; } };
const assetUrl = (doc, rel) => `api/documents/${doc.id}/asset/${rel.split('/').map(p => encodeURIComponent(safeDecode(p))).join('/')}`;

const isExternal = href => /^([a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href);

function resolvePath(base, rel) {
  const parts = base.split('/').slice(0, -1);
  for (const p of rel.split('/')) {
    if (p === '..') parts.pop(); else if (p && p !== '.') parts.push(p);
  }
  return parts.join('/');
}

async function renderPage(box, doc, text) {
  const html = marked.parse(splitHead(text), { gfm: true, breaks: false });
  box.innerHTML = DOMPurify.sanitize(html, { ADD_ATTR: ['target'] });
  // the title lives in the head block; a page without its own first heading shows it on top
  if (!box.firstElementChild || box.firstElementChild.tagName !== 'H1') {
    const h1 = document.createElement('h1');
    h1.textContent = doc.title;
    box.prepend(h1);
  }
  // pictures and attachments from the page's own folder
  box.querySelectorAll('img[src]').forEach(img => {
    const src = img.getAttribute('src');
    if (!isExternal(src)) img.src = assetUrl(doc, src);
    img.loading = 'lazy';
  });
  box.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (isExternal(href)) {
      if (!href.startsWith('#')) { a.target = '_blank'; a.rel = 'noopener'; }
      return;
    }
    const [file, frag] = href.split('#');
    const target = resolvePath(doc.path, safeDecode(file));
    a.href = '#';
    a.addEventListener('click', async ev => {
      ev.preventDefault();
      try {
        const hit = await api('documents/by-path?path=' + encodeURIComponent(target));
        if (hit.ext === 'md') location.hash = '#/seite/' + hit.id;
        else window.open(`api/documents/${hit.id}/file${frag ? '#' + frag : ''}`, '_blank', 'noopener');
      } catch {
        window.open(assetUrl(doc, href.split('#')[0]), '_blank', 'noopener');
      }
    });
  });
  // > [!NOTE] … as a coloured box
  box.querySelectorAll('blockquote').forEach(q => {
    const first = q.querySelector('p');
    const m = first && /^\s*\[!(\w+)\]\s*/.exec(first.innerHTML);
    if (!m || !CALLOUTS[m[1].toUpperCase()]) return;
    first.innerHTML = first.innerHTML.slice(m[0].length);
    q.classList.add('callout', 'callout--' + CALLOUTS[m[1].toUpperCase()]);
  });
  box.querySelectorAll('input[type=checkbox]').forEach(c => { c.disabled = true; });
}

async function showPage(box, doc) {
  box.innerHTML = '';
  const page = document.createElement('div');
  page.className = 'md md--preview';
  box.appendChild(page);
  try {
    const res = await fetch(`api/documents/${doc.id}/file`, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(res.statusText);
    if (State.selected !== doc) return;
    await renderPage(page, doc, await res.text());
  } catch (e) {
    page.innerHTML = `<p class="preview__none">${esc(errText(e))}</p>`;
  }
}

const Page = { doc: null, text: '', source: false };

async function openPageView(id) {
  const body = $('page-body');
  body.innerHTML = '';
  try {
    const doc = await api('documents/' + id);
    const res = await fetch(`api/documents/${doc.id}/file`, { credentials: 'same-origin' });
    Page.doc = doc;
    Page.text = await res.text();
    document.title = doc.title + ' – Wissen!';
    $('page-crumbs').innerHTML = [areaLabel(doc.area), ...(doc.folder ? doc.folder.split('/') : [])]
      .map(esc).join(' › ');
    $('page-download').href = `api/documents/${doc.id}/file?download=true`;
    paintPin($('page-pin'), doc);
    $('page-pin').onclick = () => togglePin(doc);
    $('page-edit').hidden = !canWrite(doc);
    $('page-menu').onclick = () => docMenu($('page-menu'), doc);
    $('page-meta').textContent = [doc.date ? formatDate(doc.date) : '', ...(doc.page_tags || []).map(x => '#' + x)]
      .filter(Boolean).join(' · ');
    paintPageView();
    if (Edit.auto === doc.id) { Edit.auto = null; startEdit(); }
  } catch (e) {
    body.innerHTML = `<p class="preview__none">${esc(errText(e))}</p>`;
  }
}

function paintPageView() {
  const body = $('page-body');
  $('page-source').setAttribute('aria-pressed', Page.source);
  body.classList.toggle('page-body--source', Page.source);
  if (Page.source) body.innerHTML = `<pre class="md-source">${esc(Page.text)}</pre>`;
  else renderPage(body, Page.doc, Page.text);
}

function initPage() {
  $('mcp-on').addEventListener('change', saveMcp);
  initEdit();
  initVersions();
  $('page-source').addEventListener('click', () => { Page.source = !Page.source; paintPageView(); });
  addEventListener('hashchange', () => { if (!/^#\/seite\//.test(location.hash)) document.title = 'Wissen!'; });
}
