# Security Policy

## Supported versions

Only the **latest** released version of School Holidays receives fixes. Please
update to the newest release before reporting an issue.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue with
exploit details.

- Preferred: use GitHub's **[Security Advisories](https://github.com/Jo-Highness/school_holidays/security/advisories/new)**
  ("Report a vulnerability") on this repository.
- Alternatively, open a minimal public issue asking a maintainer to get in touch,
  **without** including sensitive details.

Please include the affected version, Home Assistant version, and steps to
reproduce. We aim to acknowledge reports promptly and will coordinate a fix and
disclosure timeline with you.

## Scope & data handling

This integration is intentionally small and low-risk:

- It only performs outbound HTTPS requests to the public
  **[openholidaysapi.org](https://openholidaysapi.org)** API.
- It requires **no API key** and stores **no credentials or secrets**.
- It transmits no personal data; the only configuration stored is your chosen
  country and region.
