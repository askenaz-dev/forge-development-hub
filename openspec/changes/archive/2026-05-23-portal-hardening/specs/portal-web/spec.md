## MODIFIED Requirements

### Requirement: Internationalization (Spanish + English)

The frontend SHALL support at minimum two locales: Spanish (`es`, default) and English (`en`). Every user-facing string MUST be externalized to message tables. A locale switcher MUST appear in the navigation. The chosen locale MUST persist via cookie and override browser language detection.

Pages SHALL live under a `[locale]` dynamic segment (`web/app/[locale]/...`) so the next-intl middleware can rewrite incoming URLs to the appropriate locale. The default locale (`es`) MUST serve without a URL prefix; other locales MUST serve under `/<locale>/...`. The locale switcher MUST function end-to-end — clicking "English" on a Spanish page MUST navigate the user to the same content in English.

#### Scenario: Default locale is Spanish

- **WHEN** a user with no locale preference visits the portal for the first time
- **THEN** the page renders in Spanish

#### Scenario: Browser language detected when no preference

- **WHEN** a user whose browser reports `Accept-Language: en` visits the portal with no locale cookie
- **THEN** the page renders in English

#### Scenario: Explicit choice persists

- **WHEN** a user clicks the locale switcher to English and reloads
- **THEN** the page renders in English regardless of browser language

#### Scenario: Default locale URL has no prefix

- **WHEN** a user visits `/` or `/skills` (no locale prefix)
- **THEN** the page renders in Spanish and the URL does not gain a prefix

#### Scenario: Non-default locale URL carries the prefix

- **WHEN** a user navigates to the English version of the skills page
- **THEN** the URL is `/en/skills` and the page renders in English

#### Scenario: Locale switcher rewrites the path

- **WHEN** a user on `/skills` clicks the English option in the locale switcher
- **THEN** the URL becomes `/en/skills` and the content re-renders in English
