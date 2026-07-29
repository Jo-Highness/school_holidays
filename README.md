<h1 align="center">🎒 School Holidays</h1>

<p align="center">
  <b>Know if today is a school holiday — anywhere, for any region — right inside Home Assistant.</b><br>
  <i>Weiß, ob heute Schulferien sind — für jedes Land und Bundesland — direkt in Home Assistant.</i><br>
  <i>Sabe si hoy hay vacaciones escolares — en cualquier país y región — dentro de Home Assistant.</i>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.4%2B-41BDF5.svg" alt="Home Assistant 2024.4+">
  <img src="https://img.shields.io/badge/data-openholidaysapi.org-informational.svg" alt="openholidaysapi.org">
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20DE%20%7C%20ES%20%7C%20FR-informational.svg" alt="Languages">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT">
</p>

<p align="center">
  <a href="#-english">🇬🇧 English</a> ·
  <a href="#-deutsch">🇩🇪 Deutsch</a> ·
  <a href="#-español">🇪🇸 Español</a>
</p>

---

Wake-up lights, alarms, chores, screen-time, blinds — so many home automations should
simply behave differently on a school holiday. **School Holidays** gives you one reliable
`on/off` sensor for exactly that: pick your **country** and **state/region** in a dropdown,
and get a robust *"is today a school holiday?"* signal you can drop straight into any
automation. Data comes from the free, official **[openholidaysapi.org](https://openholidaysapi.org)**
— no API key, dozens of countries.

---

## 🇬🇧 English

### What you get

- ✅ **`binary_sensor` — School holidays today** — `on` while today is within a holiday period.
- 📅 **`binary_sensor` — School holidays tomorrow** — perfect for *"prepare tonight"* logic.
- ⭐ **`sensor` — Next school holiday** — the upcoming (or current) break, with `holiday_name`, `start_date`, `end_date` and `days_until` attributes.

### Why it's better than a REST/template hack

- 🌍 **Pick country + region in the UI** — a clean two-step dropdown, no editing YAML, no ISO codes to memorise.
- 🛡️ **Robust by design** — a proper async client with a **midnight rollover** (the sensor flips exactly at 00:00) and **keeps its last known data if the API is briefly unreachable** — it won't suddenly go `unknown` and break your automations.
- 🔁 **Multiple regions at once** — add one entry per country/region (e.g. two federal states) side by side.
- 🌐 **Multilingual** — UI and entity names in English, German, Spanish and French; holiday names are requested in your Home Assistant language.
- 🧩 **Zero dependencies, no API key.**

### Installation

1. **HACS** → ⋮ → *Custom repositories* → add this repo as category **Integration**.
2. Search for *School Holidays* and **download** it.
3. **Restart** Home Assistant.
4. *Settings → Devices & Services → Add Integration → "School Holidays"* → pick your country, then your state/region.

> **Manual:** copy `custom_components/school_holidays/` into `<config>/custom_components/` and restart HA.

### Use it in an automation

```yaml
# Only run the "school morning" wake-up on actual school days.
trigger:
  - platform: time
    at: "06:45:00"
condition:
  - condition: state
    entity_id: binary_sensor.school_holidays_today
    state: "off"
action:
  - service: scene.turn_on
    target: { entity_id: scene.school_wakeup }
```

---

## 🇩🇪 Deutsch

### Was du bekommst

- ✅ **`binary_sensor` — Schulferien heute** — `on`, solange heute in einer Ferienperiode liegt.
- 📅 **`binary_sensor` — Schulferien morgen** — ideal für *„heute Abend schon vorbereiten"*.
- ⭐ **`sensor` — Nächste Schulferien** — die kommenden (oder laufenden) Ferien, mit Attributen `holiday_name`, `start_date`, `end_date`, `days_until`.

### Warum besser als REST/Template-Basteleien

- 🌍 **Land + Bundesland in der Oberfläche wählen** — sauberes Zwei-Schritt-Dropdown, kein YAML, keine ISO-Codes.
- 🛡️ **Robust gebaut** — echter async-Client mit **Mitternachts-Rollover** (der Sensor schaltet punktgenau um 00:00) und **behält den letzten Stand, wenn die API kurz nicht erreichbar ist** — er wird nicht plötzlich `unknown` und bricht deine Automationen.
- 🔁 **Mehrere Regionen gleichzeitig** — pro Land/Bundesland ein Eintrag (z. B. zwei Bundesländer).
- 🌐 **Mehrsprachig** — Oberfläche und Entitätsnamen in Deutsch, Englisch, Spanisch, Französisch; Feriennamen in deiner HA-Sprache.
- 🧩 **Keine Abhängigkeiten, kein API-Key.**

### Installation

1. **HACS** → ⋮ → *Benutzerdefinierte Repositories* → dieses Repo als Kategorie **Integration** hinzufügen.
2. *School Holidays* suchen und **herunterladen**.
3. Home Assistant **neu starten**.
4. *Einstellungen → Geräte & Dienste → Integration hinzufügen → „School Holidays"* → Land und dann Bundesland/Region wählen.

> **Manuell:** Ordner `custom_components/school_holidays/` nach `<config>/custom_components/` kopieren und HA neu starten.

---

## 🇪🇸 Español

### Qué obtienes

- ✅ **`binary_sensor` — Vacaciones escolares hoy** — `on` mientras hoy esté dentro de un periodo vacacional.
- 📅 **`binary_sensor` — Vacaciones escolares mañana** — ideal para preparar todo la noche anterior.
- ⭐ **`sensor` — Próximas vacaciones escolares** — las próximas (o actuales) vacaciones, con atributos `holiday_name`, `start_date`, `end_date`, `days_until`.

### Por qué es mejor que un apaño REST/plantilla

- 🌍 **Elige país + región en la interfaz** — un desplegable de dos pasos, sin YAML ni códigos ISO.
- 🛡️ **Robusto por diseño** — cliente asíncrono con **cambio a medianoche** (el sensor cambia justo a las 00:00) y **conserva los últimos datos si la API no responde un momento** — no se queda en `unknown` ni rompe tus automatizaciones.
- 🔁 **Varias regiones a la vez** — una entrada por país/región.
- 🌐 **Multilingüe** — interfaz y nombres de entidades en español, inglés, alemán y francés.
- 🧩 **Sin dependencias ni clave de API.**

### Instalación

1. **HACS** → ⋮ → *Repositorios personalizados* → añade este repo con la categoría **Integración**.
2. Busca *School Holidays* y **descárgalo**.
3. **Reinicia** Home Assistant.
4. *Ajustes → Dispositivos y servicios → Añadir integración → "School Holidays"* → elige país y luego estado/región.

> **Manual:** copia `custom_components/school_holidays/` en `<config>/custom_components/` y reinicia HA.

---

## Data & credits

Holiday data © **[openholidaysapi.org](https://openholidaysapi.org)** (Open Data). This project
is not affiliated with the API provider. Licensed under **MIT**.
