# OpenWrite

A word processor for AmigaOS 3.2 that opens and saves today's documents
(DOCX and ODT) and opens the documents written with the Amiga's own word
processors: ProWrite, Final Writer, Wordworth, Final Copy, Excellence!,
Kindwords, Textcraft and the rest. It prints, saves PDF, and works like an
Amiga program: a GadTools window, Amiga keys, the clipboard and ARexx.

We, 4 October 2026: "let's do the OpenWrite project", a word processor "that
can import any of the Amiga formats, along with DOCX and the OpenDocument
formats".

Status, 4 October 2026: designed (version 0.1). `DESIGN.md` is the design and
`docs/FORMATS.md` the list of formats.

Its editor is WebCore, the engine inside WebKit, from our OpenBrowser port
(`DalsinAI/openamigabrowser`). Its file formats are a separate C library,
**libowf**, with a Shell command, **C:OWConvert**, that converts documents on
any Amiga, a 68000 included.

Part of the Open family: it builds on OpenBrowser, OpenGadTools and
OpenPrint rather than bundling its own versions of them.

## Licence

MIT, Copyright (c) 2026 Dalsin Limited (`LICENSE`). The parts it builds on
keep their own licences (`THIRD_PARTY.md`).

If you use or build on this work, we ask (we do not require) that you credit
Dalsin Limited and AmigaChrome, for example "based on OpenWrite by
Dalsin Limited".
