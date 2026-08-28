# Requirements — School Holidays (Clean-Room)

> Code-unabhaengiges Anforderungsdokument (WAS/WARUM). Ziel: die Integration laesst sich allein
> hieraus als Greenfield neu bauen. Bezug: Home-Assistant-Custom-Integration (HACS),
> Datenquelle openholidaysapi.org, Stand v1.0.1.

## 1. Zweck
Home Assistant (HA) hat keine eingebaute Quelle fuer Schulferien. Viele Automationen sollen sich
an Ferientagen anders verhalten (Wecker/Wecklicht, Hausarbeiten, Bildschirmzeit, Rolllaeden,
Heizplaene). Schulferien unterscheiden sich von gesetzlichen Feiertagen: sie sind mehrwoechige
Zeitraeume, variieren pro Region (in DE pro Bundesland) und koennen normale Arbeitstage sein.
Die Integration liefert pro konfigurierter Region drei Entitaeten: "heute Ferien",
"morgen Ferien" und "naechste Ferien" (Startdatum + Details). Sie ersetzt fragile
YAML-/REST-/Template-Konstruktionen durch eine reine UI-Konfiguration ohne API-Key.

## 2. Funktionale Anforderungen

### Konfiguration (Config Flow)
- **FR1** Einrichtung ausschliesslich ueber die HA-UI (kein YAML). Zwei Schritte: (1) Land,
  (2) Bundesland/Region. Beide Auswahllisten werden live aus der Datenquelle geladen und
  alphabetisch nach lokalisiertem Namen sortiert; der Nutzer muss keine ISO-Codes kennen.
- **FR2** Hat ein Land keine Regionen (oder ist die Regionsliste nicht abrufbar), wird
  Schritt 2 uebersprungen und das ganze Land konfiguriert.
- **FR3** Ist die Laenderliste im Schritt 1 nicht abrufbar, bricht der Flow mit einem
  verstaendlichen Grund "Dienst nicht erreichbar" ab (kein leerer Eintrag).
- **FR4** Eindeutigkeit: die Kombination Land+Region darf nur einmal existieren; ein zweiter
  Versuch bricht mit "bereits konfiguriert" ab. Mehrere verschiedene Regionen parallel sind
  ausdruecklich erlaubt (je ein Eintrag, je ein Geraet).
- **FR5** Eintragstitel = Regionsname, sonst Landesname. Gespeichert werden Landcode,
  Landname, Regionscode (optional), Regionsname und die zur Einrichtung genutzte
  UI-Sprache (2-Buchstaben-Code aus der HA-Sprache, Fallback EN).
- **FR6** Options-Flow ("Konfigurieren"): Aktualisierungsintervall in Stunden, Bereich 1-168,
  Default 12. Eine Aenderung laedt den Eintrag neu. Land/Region sind nachtraeglich NICHT
  aenderbar (Eintrag loeschen und neu anlegen).

### Datenbeschaffung
- **FR7** Ferienzeitraeume werden fuer ein Fenster von heute bis heute+400 Tage abgefragt
  (deckt ein volles Schuljahr plus Puffer), gefiltert auf Land und ggf. Region, Namen in
  der gespeicherten Sprache.
- **FR8** Jeder Zeitraum wird auf Start, Ende (jeweils Datum, inklusiv) und Namen reduziert.
  Name: Text in der gewuenschten Sprache, sonst erster verfuegbarer Text, sonst leer.
  Zeitraeume mit unlesbarem Datum werden verworfen; Ergebnis aufsteigend nach Start sortiert.
- **FR9** Abfrage periodisch gemaess Intervall (FR6); Erstabfrage beim Laden des Eintrags.

### Ableitung / Entitaeten
- **FR10** Pro Eintrag ein Geraet (Name = Region bzw. Land, Hersteller "openholidaysapi.org",
  Modell "School holidays") mit genau drei Entitaeten, benannt nach dem Geraetenamen-Schema
  (Praefix Region):
  - binary_sensor "School holidays today": an, wenn heute in einem Zeitraum liegt.
  - binary_sensor "School holidays tomorrow": an, wenn morgen in einem Zeitraum liegt.
  - sensor "Next school holiday" (device_class date, KEIN state_class): Startdatum des
    laufenden oder naechsten Zeitraums; unbekannt, wenn keiner vorliegt.
- **FR11** Attribute: beide Binaersensoren tragen `holiday_name`, `start_date`, `end_date`
  des HEUTE aktiven Zeitraums (leer/None ausserhalb). Der Datumssensor traegt
  `holiday_name`, `start_date`, `end_date`, `days_until` (ganze Tage von heute bis Start;
  0 waehrend eines laufenden Zeitraums).
- **FR12** "Naechster" Zeitraum = der heute laufende, sonst der frueheste mit Start > heute.
- **FR13** Datumsgrenzen inklusiv: Start- und Endtag zaehlen als Ferientag; der Tag nach dem
  Ende nicht. "Heute" ist das lokale Datum der HA-Zeitzone.
- **FR14** Mitternachts-Rollover: kurz nach lokalem 00:00 werden heute/morgen/naechste aus den
  zwischengespeicherten Zeitraeumen neu berechnet, OHNE Netzwerkzugriff, damit die Sensoren
  exakt an der Tagesgrenze umschalten, auch wenn die Quelle gerade nicht erreichbar ist.
- **FR15** Icons: heute `mdi:school-outline`, morgen `mdi:calendar-arrow-right`, naechste
  `mdi:calendar-star`. Eindeutige IDs je Entitaet aus Eintrags-ID + Schluessel
  (today/tomorrow/next_holiday), stabil ueber Neustarts.
- **FR16** Entladen des Eintrags entfernt Plattformen, Mitternachts-Timer und Koordinator
  rueckstandsfrei.

### Uebersetzung
- **FR17** UI-Texte (Flow-Schritte, Abbruchgruende, Optionen, Entitaetsnamen) in EN, DE, ES, FR;
  EN ist die Basis. Feriennamen kommen aus der Quelle in der HA-Sprache, soweit verfuegbar.

## 3. Nicht-funktionale Anforderungen
- **NFR1 (Robustheit)** Schlaegt eine Aktualisierung fehl, nachdem bereits Daten vorliegen,
  bleiben die letzten bekannten Zeitraeume aktiv (Warnung im Log); Entitaeten werden NICHT
  unavailable. Schlaegt die ALLERERSTE Abfrage fehl, wird der Eintrag als "nicht bereit"
  gemeldet, sodass HA automatisch erneut versucht; es entstehen nie leere/irrefuehrende Sensoren.
- **NFR2 (Keine Geheimnisse)** Datenquelle ohne API-Key; keine Credentials, keine Secrets im
  Repo oder in der Konfiguration.
- **NFR3 (Fairness gegenueber der Quelle)** Polling-Intervall mindestens 1 h; Timeout pro
  Anfrage ca. 20 s; nur die drei benoetigten Endpunkte; HA-gemeinsame HTTP-Session nutzen.
- **NFR4 (Testbarkeit)** Die reine Datumslogik (Parsen, Ferientag-Pruefung, aktueller/naechster
  Zeitraum, Tage-bis) ist ohne HA-Laufzeit testbar; Flow, Setup/Unload und Fehlerpfade sind
  mit dem HA-Test-Framework abgedeckt. Netzwerk wird in Tests immer gemockt.
- **NFR5 (Kompatibilitaet/HACS)** Custom Integration fuer HA >= 2024.4, Typ "service",
  iot_class cloud_polling, keine Zusatz-Python-Abhaengigkeiten, config_flow aktiv.
  HACS-faehig (hacs.json mit render_readme), hassfest- und HACS-Action-konform.
  Eigene Marken-Icons (icon/dark_icon, 1x/2x) werden im Integrationsordner mitgeliefert.
- **NFR6 (Qualitaet/CI)** Lint+Format-Check (ruff, Zeilenlaenge 100, py311-Ziel) und pytest
  laufen bei Push/PR; taegliche Validierung; Release-Drafter; Dependabot; Issue-/PR-Vorlagen;
  Changelog nach Keep-a-Changelog, SemVer, Lizenz MIT.
- **NFR7 (Diagnose)** Debug-Logging ueber den HA-Logger-Namespace der Integration
  aktivierbar; README dokumentiert Installation, Optionen, Entitaeten, Beispiele, FAQ.

## 4. Schnittstellen
- **Datenquelle (HTTPS, JSON, ohne Auth):** openholidaysapi.org
  - Laenderliste (Parameter: Sprachcode) -> ISO-Code + lokalisierte Namen.
  - Regionsliste (Parameter: Landcode, Sprachcode) -> Regionscode (z.B. DE-HE) + Namen.
  - Schulferien (Parameter: Landcode, Sprachcode, validFrom, validTo, optional
    Regionscode) -> Liste mit startDate, endDate, name[] als {language, text}.
  Nicht-200-Antworten, Timeouts und Netzfehler werden auf einen einheitlichen
  Quellenfehler abgebildet.
- **Home Assistant:** Config-Entry + Options-Flow (UI), Plattformen binary_sensor und sensor,
  Geraeteregistrierung, Koordinator-Muster (Polling + manuelles Setzen bei Mitternacht),
  Zeitzone/Sprache aus der HA-Konfiguration.
- **Verteilung:** Git-Repo (Gitea, Mirror nach GitHub) als HACS-Custom-Repository, Kategorie
  Integration; Releases mit Tags vX.Y.Z.

## 5. Datenmodell
- **Eintrag (Config Entry):** country (ISO2), country_name, subdivision (Code|None),
  subdivision_name, language (ISO2); Options: update_hours (1-168, Default 12);
  unique_id = "<country>:<subdivision|->".
- **Period:** start (Datum), end (Datum), name (Text). Sortierte Liste je Eintrag,
  im Speicher gehalten (kein persistenter Cache noetig).
- **Abgeleiteter Zustand:** periods (Anzahl), today (bool), tomorrow (bool),
  current {name,start,end}|None, next {name,start,end,days_until}|None.

## 6. Akzeptanzkriterien
- **AC1** Flow Land -> Region erzeugt einen Eintrag mit Titel = Regionsname und gespeicherten
  Codes; Land ohne Regionen erzeugt direkt einen Eintrag mit Titel = Landname und Region None.
- **AC2** Nicht erreichbare Laenderliste -> Abbruch "cannot_connect"; Doppelanlage derselben
  Region -> Abbruch "already_configured".
- **AC3** Options-Flow setzt update_hours (z.B. 24) und der Eintrag laedt neu.
- **AC4** Ein Zeitraum gestern..morgen ergibt heute=an, morgen=an, holiday_name gesetzt,
  Datumssensor = Start des Zeitraums, days_until = 0.
- **AC5** Grenzen: Starttag und Endtag sind Ferien, Folgetag und Luecken nicht; in einer
  Luecke zeigt "naechste" den folgenden Zeitraum mit korrekter Tagesdifferenz; nach dem
  letzten Zeitraum ist "naechste" unbekannt.
- **AC6** Ungueltige Datensaetze werden verworfen, Namensauswahl folgt der Sprache mit
  Fallback auf den ersten Namen, Leerlisten liefern aus/unbekannt statt Fehler.
- **AC7** Erste Abfrage schlaegt fehl -> Eintrag im Retry-Zustand, keine Entitaeten mit
  leeren Daten. Spaeterer Fehler nach Erfolg -> letzte Daten bleiben, Update gilt als ok.
- **AC8** Entladen -> Eintrag NOT_LOADED, kein Koordinator mehr im HA-Datenspeicher.
- **AC9** hassfest, HACS-Validierung, ruff check/format und pytest sind gruen.

## 7. Rationale
- openholidaysapi.org, weil frei, offiziell, ohne Key und mit Regionsaufloesung fuer viele
  Laender; dadurch keine gepflegten Datumslisten im Repo und keine YAML-Wartung.
- Zwei-Schritt-Dropdown statt Freitext, weil Nutzer keine ISO-Codes kennen und Fehleingaben
  so ausgeschlossen sind; Laender ohne Regionen werden ohne Sonderwissen durchgereicht.
- Keep-last-known-data + Mitternachts-Rollover, weil Automationen (Wecker um 06:45) exakt an
  der Tagesgrenze und auch bei kurzen API-Ausfaellen korrekt entscheiden muessen;
  ConfigEntryNotReady beim Erstlauf, weil leere Sensoren schlimmer sind als ein Retry.
- Region-Praefix per Geraetename und eindeutige ID Land:Region, damit mehrere Bundeslaender
  parallel und kollisionsfrei betrieben werden koennen.
- Reine Datumslogik ohne HA-Import, damit die fachliche Kernlogik schnell und
  frameworkunabhaengig getestet werden kann.
- 400-Tage-Fenster, damit "naechste Ferien" auch am Schuljahresende ueber den Jahreswechsel
  hinaus stets belegt ist.
- Kein state_class am Datumssensor, weil ein Datum keine Messgroesse ist und sonst
  Statistik-Warnungen in HA erzeugt.
