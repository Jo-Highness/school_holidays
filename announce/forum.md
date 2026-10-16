# School Holidays – Schulferien als Sensoren in Home Assistant

*(Vorschlag für Kategorie „Share your Projects!")*

## Titelvorschlag

**School Holidays – custom integration for school-holiday sensors (openholidaysapi.org)**

## Beschreibung

`School Holidays` ist eine Custom-Integration, die die aktuellen und kommenden
Schulferien für ein wählbares Land und eine Region als Sensoren in Home Assistant
bereitstellt. Land und Region werden über die UI ausgewählt; ein API-Key wird
nicht benötigt.

Der praktische Nutzen: Automationen an Schulferien knüpfen – zum Beispiel den
Wecker in den Ferien ausschalten, Benachrichtigungen auslösen oder einen
Countdown bis zu den nächsten Ferien anzeigen.

## Bereitgestellte Entitäten

- `binary_sensor` **today** – ist heute Schulferien-Tag (an/aus)
- `binary_sensor` **tomorrow** – ist morgen Schulferien-Tag (an/aus)
- `sensor` **next_holiday** – Startdatum der nächsten Schulferien
  (`device_class: date`), mit Attribut `days_until` (Tage bis dahin)

## Funktionen

- Konfiguration von Land und Region komplett über die UI, nachträglich änderbar
  (Neu konfigurieren)
- Einstellbares Update-Intervall (Standard: 24 Stunden)
- Datenquelle: [openholidaysapi.org](https://www.openholidaysapi.org/) –
  freies Open-Data-Projekt (ODbL), kein API-Key erforderlich
- Oberfläche in Englisch, Deutsch, Spanisch und Französisch (en/de/es/fr)
- Lizenz: MIT
- Mindestens Home Assistant 2025.2

## Screenshots

<!-- Bilder hier einfügen. Empfohlen:
     1. Screenshot des Config-Flow (Land-/Region-Auswahl)
     2. Screenshot der drei Entitäten (today / tomorrow / next_holiday mit days_until)
     3. Optional: kleine Beispiel-Automation oder Dashboard-Karte
     Auf community.home-assistant.io per Drag-and-Drop oder über den Upload-Button einfügen. -->

*[Screenshot 1: Config-Flow – Auswahl von Land und Region]*

*[Screenshot 2: Entitäten today / tomorrow / next_holiday]*

## Installation (Kurzfassung)

Installation über HACS als Custom Repository:

- In HACS als Custom Repository hinzufügen:
  `https://github.com/Jo-Highness/school_holidays` (Kategorie: Integration)
- Oder direkt per Deeplink:
  <https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=school_holidays&category=integration>

Nach der Installation die Integration über *Einstellungen → Geräte & Dienste →
Integration hinzufügen* einrichten und Land/Region wählen.

GitHub: <https://github.com/Jo-Highness/school_holidays>

## Einschränkungen (ehrlich)

- Die Datenabdeckung hängt vollständig von
  [openholidaysapi.org](https://www.openholidaysapi.org/) ab. Nicht jedes Land
  bzw. jede Region ist dort mit gleicher Vollständigkeit hinterlegt – vor dem
  produktiven Einsatz prüfen, ob die eigene Region abgedeckt ist.
- Die Integration liefert **nur Schulferien**, keine gesetzlichen Feiertage.

Rückmeldungen und Fehlerberichte gern über die GitHub-Issues.
