# Third-party parts

OpenWrite's own code and documents are MIT, Copyright (c) 2026 Dalsin
Limited (`LICENSE`). Nothing below is in this repository yet; this is what
OpenWrite will build on, and the licence each keeps.

| Part | What for | Licence | How |
| --- | --- | --- | --- |
| WebCore, WTF and JavaScriptCore (WebKit), through OpenBrowser | The editor | LGPL-2 and BSD-style | Linked at build time; a built OpenWrite ships with source and relinking notes, as OpenBrowser does |
| ICU 78.3 | Unicode for WebCore | Unicode License v3 | Linked |
| cairo and pixman (`openamigacairo`) | Drawing, PDF | LGPL-2.1 or MPL-1.1 (cairo); MIT (pixman) | Linked |
| FreeType, HarfBuzz, fontconfig | Fonts and text shaping | FreeType License; MIT; MIT-style | Linked |
| zlib | Zip containers (ODT, DOCX) | zlib | Linked |
| libpng, libjpeg (`openamigaimage`) | Pictures inside documents | libpng; IJG | Linked |
| Hunspell (phase W5) | Spelling | MPL-1.1 (of its MPL/GPL/LGPL choice) | Linked |
| Liberation fonts, Carlito | Fonts shipped with OpenWrite | SIL Open Font License 1.1 | Shipped as files |
| Caladea | Font shipped with OpenWrite | Apache-2.0 | Shipped as files |
| DejaVu fonts | Font shipped with OpenWrite | DejaVu Fonts License (free) | Shipped as files |

**Reference only** (read for understanding; no code copied unless its
licence allows, and then with credit):

| Work | Licence | For |
| --- | --- | --- |
| fw2odf (github.com/hornc/fw2odf) | MIT | The Final Writer format |
| libwpd, libmwaw (Document Liberation Project) | MPL-2.0 / LGPL | WordPerfect and old word processor formats |
| The IFF specifications (EA IFF 85; New Horizons' FORM WORD) | Published specifications | IFF FTXT and ProWrite |
