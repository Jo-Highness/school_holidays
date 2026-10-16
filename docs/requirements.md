# Requirements — School Holidays (Clean-Room)

> Code-unabhängiges Anforderungsdokument (WAS/WARUM). Ziel: Die Integration lässt sich allein
> hieraus als Greenfield neu bauen. Bezug: Home-Assistant-Custom-Integration (HACS),
> Datenquelle openholidaysapi.org, Stand v1.1.0.

## 1. Zweck
Home Assistant (HA) hat keine eingebaute Quelle für Schulferien. Viele Automationen sollen sich
an Ferientagen anders verhalten (Wecker/Wecklicht, Hausarbeiten, Bildschirmzeit, Rollläden,
Heizpläne). Schulferien unterscheiden sich von gesetzlichen Feiertagen: Sie sind mehrwöchige
Zeiträume, variieren pro Region (in DE pro Bundesland) und können normale Arbeitstage sein.
Die Integration liefert pro konfigurierter Region die Entitäten „heute Ferien“,
„morgen Ferien“ und „nächste Ferien“ (Startdatum + Details) sowie eine Diagnose-Entität
„letzte erfolgreiche Aktualisierung“. Sie ersetzt fragile YAML-/REST-/Template-Konstruktionen
durch eine reine UI-Konfiguration ohne API-Key.

## 2. Funktionale Anforderungen

### Konfiguration (Config Flow)
- **FR1** Einrichtung ausschließlich über die HA-UI (kein YAML). Zwei Schritte: (1) Land,
  (2) Bundesland/Region. Beide Auswahllisten werden live aus der Datenquelle geladen
  (Beschriftung in der HA-Sprache) und alphabetisch nach lokalisiertem Namen sortiert; der
  Nutzer muss keine ISO-Codes kennen.
- **FR2** Liefert die Datenquelle für ein Land eine leere Regionsliste, wird Schritt 2
  übersprungen und das ganze Land konfiguriert. Ist die Regionsliste dagegen NICHT abrufbar
  (Fehler), bricht der Flow mit „Dienst nicht erreichbar“ ab — es wird kein Eintrag für das
  ganze Land angelegt (würde z. B. in DE die Ferien aller Bundesländer vermischen).
- **FR3** Ist die Länderliste im Schritt 1 nicht abrufbar, bricht der Flow mit einem
  verständlichen Grund „Dienst nicht erreichbar“ ab (kein leerer Eintrag).
- **FR4** Eindeutigkeit: Die Kombination Land+Region darf nur einmal existieren; ein zweiter
  Versuch bricht mit „bereits konfiguriert“ ab. Mehrere verschiedene Regionen parallel sind
  ausdrücklich erlaubt (je ein Eintrag, je ein Gerät).
- **FR5** Eintragstitel = Regionsname, sonst Landesname. Gespeichert werden Landcode,
  Landname, Regionscode (optional), Regionsname und die Sprache der Feriennamen. Neue
  Einträge speichern `auto` (= HA-Sprache folgen); Einträge aus Versionen < 1.1.0 behalten
  ihren damals fest gespeicherten 2-Buchstaben-Code.
- **FR6** Options-Flow („Konfigurieren“): Aktualisierungsintervall in Stunden, Bereich 1–168,
  Default 24; Sprache der Feriennamen (`auto` oder ISO-639-1-Code, Freitext erlaubt). Eine
  Änderung lädt den Eintrag neu. Alle Felder haben Beschreibungstexte.
- **FR6a** Neu konfigurieren („Reconfigure“): Land/Region eines bestehenden Eintrags lassen
  sich ändern, ohne ihn zu löschen. Eintrags-ID, Entitäten und Entity-IDs bleiben erhalten;
  Titel, unique_id und Gerätename folgen der neuen Region. Ist die Zielregion bereits als
  anderer Eintrag konfiguriert, Abbruch „bereits konfiguriert“.

### Datenbeschaffung
- **FR7** Ferienzeiträume werden für ein Fenster von heute bis heute+400 Tage abgefragt
  (deckt ein volles Schuljahr plus Puffer), gefiltert auf Land und ggf. Region, Namen in
  der wirksamen Sprache (bei `auto`: aktuelle HA-Sprache, regionale Tags wie `de-CH`
  werden auf `DE` reduziert).
- **FR8** Jeder Zeitraum wird auf Start, Ende (jeweils Datum, inklusiv) und Namen reduziert.
  Name: Text in der gewünschten Sprache, sonst erster verfügbarer Text, sonst leer.
  Zeiträume mit unlesbarem Datum werden verworfen; Ergebnis aufsteigend nach Start sortiert.
- **FR9** Abfrage periodisch gemäß Intervall (FR6); Erstabfrage beim Laden des Eintrags.
  Bei Sprache `auto` löst eine Änderung der HA-Sprache eine erneute Abfrage aus.

### Ableitung / Entitäten
- **FR10** Pro Eintrag ein Gerät vom Typ „Dienst“ (Name = Region bzw. Land, sonst
  übersetzter Fallback-Name; Hersteller „openholidaysapi.org“, Modell „School holidays“) mit
  folgenden Entitäten (Namen übersetzt, Präfix = Gerätename):
  - binary_sensor „Schulferien heute“: an, wenn heute in einem Zeitraum liegt.
  - binary_sensor „Schulferien morgen“: an, wenn morgen in einem Zeitraum liegt.
  - sensor „Nächste Schulferien“ (device_class date, KEIN state_class): Startdatum des
    laufenden oder nächsten Zeitraums; unbekannt, wenn keiner vorliegt.
  - sensor „Letzte erfolgreiche Aktualisierung“ (device_class timestamp, Kategorie
    Diagnose).
- **FR11** Attribute: Jeder Binärsensor trägt `holiday_name`, `start_date`, `end_date` des
  Zeitraums, der SEINEN Tag abdeckt (heute bzw. morgen; None außerhalb). Der Datumssensor
  trägt `holiday_name`, `start_date`, `end_date`, `days_until` (ganze Tage von heute bis
  Start; 0 während eines laufenden Zeitraums).
- **FR12** „Nächster“ Zeitraum = der heute laufende, sonst der früheste mit Start > heute.
- **FR13** Datumsgrenzen inklusiv: Start- und Endtag zählen als Ferientag; der Tag nach dem
  Ende nicht. „Heute“ ist das lokale Datum der HA-Zeitzone.
- **FR14** Mitternachts-Rollover: Kurz nach lokalem 00:00 werden heute/morgen/nächste aus den
  zwischengespeicherten Zeiträumen neu berechnet, OHNE Netzwerkzugriff, damit die Sensoren
  exakt an der Tagesgrenze umschalten, auch wenn die Quelle gerade nicht erreichbar ist.
- **FR15** Icons per `icons.json`: heute `mdi:school-outline`, morgen
  `mdi:calendar-arrow-right`, nächste `mdi:calendar-star`, letzte Aktualisierung
  `mdi:cloud-check-outline`. Eindeutige IDs je Entität aus Eintrags-ID + Schlüssel
  (today/tomorrow/next_holiday/last_successful_update), stabil über Neustarts.
- **FR16** Entladen des Eintrags entfernt Plattformen, Mitternachts-Timer, Sprach-Listener
  und Koordinator rückstandsfrei. Löschen des Eintrags entfernt zugehörige Reparaturhinweise.
- **FR17** Diagnose-Download (Config-Entry-Diagnostics): Eintragsdaten, Optionen, wirksame
  Sprache, Intervall, Zeitpunkt der letzten erfolgreichen Aktualisierung, Status des
  Reparaturhinweises, abgeleitete Daten.

### Übersetzung
- **FR18** UI-Texte (Flow-Schritte inkl. Feldbeschreibungen, Abbruchgründe, Optionen,
  Entitäts- und Gerätenamen, Reparaturhinweis) in EN, DE, ES, FR; EN ist die Basis.
  Feriennamen kommen aus der Quelle in der wirksamen Sprache, soweit verfügbar.

## 3. Nicht-funktionale Anforderungen
- **NFR1 (Robustheit)** Schlägt eine Aktualisierung fehl, nachdem bereits Daten vorliegen,
  bleiben die letzten bekannten Zeiträume aktiv (Warnung im Log); Entitäten werden NICHT
  unavailable. Liegt die letzte erfolgreiche Aktualisierung mehr als 7 Tage zurück, wird ein
  Reparaturhinweis (Warnung) erzeugt; die Daten bleiben trotzdem aktiv, da das 400-Tage-Fenster
  den aktuellen Tag weiterhin abdeckt. Der Hinweis verschwindet bei der nächsten erfolgreichen
  Aktualisierung. Schlägt die ALLERERSTE Abfrage fehl, wird der Eintrag als „nicht bereit“
  gemeldet, sodass HA automatisch erneut versucht; es entstehen nie leere/irreführende Sensoren.
- **NFR2 (Keine Geheimnisse)** Datenquelle ohne API-Key; keine Credentials, keine Secrets im
  Repo oder in der Konfiguration.
- **NFR3 (Fairness gegenüber der Quelle)** Polling-Intervall mindestens 1 h, Default 24 h;
  Timeout pro Anfrage ca. 20 s; nur die drei benötigten Endpunkte; HA-gemeinsame HTTP-Session
  nutzen. Fehlerbehandlung gezielt (Netzwerkfehler, Timeout, ungültiges JSON), kein
  pauschales Abfangen aller Ausnahmen.
- **NFR4 (Testbarkeit)** Die reine Datumslogik (Parsen, Namenswahl, Ferientag-Prüfung,
  aktueller/nächster Zeitraum, Tage-bis) ist ohne HA-Laufzeit testbar; Flow, Reconfigure,
  Optionen, Setup/Unload, Mitternachts-Rollover, Attribute, Reparaturhinweis, Sprache und
  Fehlerpfade sind mit dem HA-Test-Framework abgedeckt. Netzwerk wird in Tests immer gemockt.
- **NFR5 (Kompatibilität/HACS)** Custom Integration für HA >= 2025.2, Typ „service“,
  iot_class cloud_polling, keine Zusatz-Python-Abhängigkeiten, config_flow aktiv.
  HACS-fähig (hacs.json mit render_readme), hassfest- und HACS-Action-konform.
  Eigene Marken-Icons (icon/dark_icon, 1x/2x) werden im Integrationsordner mitgeliefert.
  Bestehende unique_ids und Entity-IDs bleiben über Updates stabil.
- **NFR6 (Qualität/CI)** Lint+Format-Check (ruff, Zeilenlänge 100, py313-Ziel) und pytest
  mit Coverage laufen bei Push/PR; Testabhängigkeiten in `requirements_test.txt` gepinnt;
  tägliche Validierung; Release-Drafter; Dependabot (Actions + pip); Issue-/PR-Vorlagen;
  Changelog nach Keep-a-Changelog, SemVer, Lizenz MIT.
- **NFR7 (Diagnose)** Debug-Logging über den HA-Logger-Namespace der Integration
  aktivierbar; Diagnose-Download (FR17); README dokumentiert Schnellstart, Installation,
  Optionen, Entitäten (inkl. sprachabhängiger Entity-IDs), Beispiele, FAQ, Datenquelle/Lizenz
  und enthält eine deutsche Kurzanleitung.

## 4. Schnittstellen
- **Datenquelle (HTTPS, JSON, ohne Auth):** openholidaysapi.org (Open-Data-Projekt
  „OpenHolidays“, Daten unter ODbL 1.0)
  - Länderliste (Parameter: Sprachcode) -> ISO-Code + lokalisierte Namen.
  - Regionsliste (Parameter: Landcode, Sprachcode) -> Regionscode (z. B. DE-HE) + Namen.
  - Schulferien (Parameter: Landcode, Sprachcode, validFrom, validTo, optional
    Regionscode) -> Liste mit startDate, endDate, name[] als {language, text}.
  Nicht-200-Antworten, Timeouts, Netzfehler und ungültige/unerwartete Antworten werden auf
  einen einheitlichen Quellenfehler abgebildet.
- **Home Assistant:** Config-Entry mit typisiertem `runtime_data`, Config-, Reconfigure- und
  Options-Flow (UI), Plattformen binary_sensor und sensor, Geräteregistrierung (Dienst),
  Koordinator-Muster (Polling + manuelles Setzen bei Mitternacht), Issue-Registry
  (Reparaturhinweis), Diagnostics, Zeitzone/Sprache aus der HA-Konfiguration.
- **Verteilung:** GitHub-Repository als HACS-Custom-Repository, Kategorie Integration;
  Releases mit Tags vX.Y.Z.

## 5. Datenmodell
- **Eintrag (Config Entry, Version 1):** country (ISO2), country_name, subdivision
  (Code|None), subdivision_name, language (`auto` oder ISO2); Options: update_hours
  (1–168, Default 24), language (überschreibt data.language);
  unique_id = "<country>:<subdivision|->".
- **Period:** start (Datum), end (Datum), name (Text). Sortierte Liste je Eintrag,
  im Speicher gehalten (kein persistenter Cache nötig).
- **Abgeleiteter Zustand:** periods (Anzahl), today (bool), tomorrow (bool),
  current {name,start,end}|None, tomorrow_period {name,start,end}|None,
  next {name,start,end,days_until}|None, last_successful_update (Zeitpunkt|None).

## 6. Akzeptanzkriterien
- **AC1** Flow Land -> Region erzeugt einen Eintrag mit Titel = Regionsname, gespeicherten
  Codes und language `auto`; Land ohne Regionen erzeugt direkt einen Eintrag mit
  Titel = Landname und Region None.
- **AC2** Nicht erreichbare Länder- oder Regionsliste -> Abbruch „cannot_connect“;
  Doppelanlage derselben Region -> Abbruch „already_configured“.
- **AC3** Options-Flow setzt update_hours (z. B. 24) und Sprache; der Eintrag lädt neu.
- **AC4** Ein Zeitraum gestern..morgen ergibt heute=an, morgen=an, holiday_name gesetzt,
  Datumssensor = Start des Zeitraums, days_until = 0.
- **AC4a** Beginnt ein Zeitraum morgen, ist heute=aus ohne Attribute und morgen=an mit
  Name/Start/Ende DIESES Zeitraums; am letzten Ferientag ist morgen=aus ohne Attribute.
- **AC5** Grenzen: Starttag und Endtag sind Ferien, Folgetag und Lücken nicht; in einer
  Lücke zeigt „nächste“ den folgenden Zeitraum mit korrekter Tagesdifferenz; nach dem
  letzten Zeitraum ist „nächste“ unbekannt.
- **AC6** Ungültige Datensätze werden verworfen, Namensauswahl folgt der Sprache mit
  Fallback auf den ersten Namen, Leerlisten liefern aus/unbekannt statt Fehler.
- **AC7** Erste Abfrage schlägt fehl -> Eintrag im Retry-Zustand, keine Entitäten mit
  leeren Daten. Späterer Fehler nach Erfolg -> letzte Daten bleiben, Update gilt als ok;
  nach > 7 Tagen ohne Erfolg existiert ein Reparaturhinweis, der nach Erfolg verschwindet.
- **AC8** Entladen -> Eintrag NOT_LOADED, Mitternachts-Timer feuert nicht mehr.
- **AC9** Reconfigure auf eine andere Region aktualisiert Titel/Daten/unique_id bei gleicher
  Eintrags-ID; auf eine bereits anderweitig konfigurierte Region -> „already_configured“.
- **AC10** Sprache `auto` folgt der HA-Sprache (inkl. Neuabfrage bei Sprachwechsel);
  explizit gespeicherte Sprache bleibt unverändert.
- **AC11** hassfest, HACS-Validierung, ruff check/format und pytest sind grün.

## 7. Rationale
- openholidaysapi.org, weil frei, ohne Key, offen lizenziert (ODbL) und mit Regionsauflösung
  für viele Länder; dadurch keine gepflegten Datumslisten im Repo und keine YAML-Wartung.
  Es ist ein Community-Open-Data-Projekt, keine amtliche Quelle — das wird in der
  Dokumentation offen benannt.
- Zwei-Schritt-Dropdown statt Freitext, weil Nutzer keine ISO-Codes kennen und Fehleingaben
  so ausgeschlossen sind; Länder ohne Regionen werden ohne Sonderwissen durchgereicht.
- Reconfigure statt Löschen/Neuanlegen, damit Automationen und Entity-IDs bei einem
  Regionswechsel erhalten bleiben.
- Keep-last-known-data + Mitternachts-Rollover, weil Automationen (Wecker um 06:45) exakt an
  der Tagesgrenze und auch bei API-Ausfällen korrekt entscheiden müssen; der
  Reparaturhinweis macht lange Ausfälle sichtbar, ohne Automationen zu brechen.
  ConfigEntryNotReady beim Erstlauf, weil leere Sensoren schlimmer sind als ein Retry.
- 24 h Default-Intervall, weil sich Ferientermine selten ändern und die Quelle kostenlos ist.
- Region-Präfix per Gerätename und eindeutige ID Land:Region, damit mehrere Bundesländer
  parallel und kollisionsfrei betrieben werden können.
- Reine Datumslogik ohne HA-Import, damit die fachliche Kernlogik schnell und
  frameworkunabhängig getestet werden kann.
- 400-Tage-Fenster, damit „nächste Ferien“ auch am Schuljahresende über den Jahreswechsel
  hinaus stets belegt ist.
- Kein state_class am Datumssensor, weil ein Datum keine Messgröße ist und sonst
  Statistik-Warnungen in HA erzeugt.
