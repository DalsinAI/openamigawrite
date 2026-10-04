/*
 * libowf's own helpers: growing buffers, UTF-8 and character sets, IFF
 * chunks, zip writing. Not part of the public interface.
 * MIT, Copyright (c) 2026 Dalsin Limited.
 */
#ifndef OWF_INTERNAL_H
#define OWF_INTERNAL_H

#include "owf.h"

#include <stdarg.h>
#include <stddef.h>

/* ---- A growing byte buffer; after a failed allocation it stays failed ---- */

typedef struct {
    unsigned char *data;
    size_t length, capacity;
    int failed;
} owf_buf;

void owf_buf_init(owf_buf *buf);
void owf_buf_free(owf_buf *buf);
void owf_buf_put(owf_buf *buf, const void *data, size_t length);
void owf_buf_putc(owf_buf *buf, int c);
void owf_buf_puts(owf_buf *buf, const char *s);
void owf_buf_printf(owf_buf *buf, const char *fmt, ...);
/* Twips as points ("12.5pt"), without floating point. */
void owf_put_points(owf_buf *out, int twips);
/* UTF-8 text with &, <, > and " escaped for XML and HTML. */
void owf_buf_put_xml(owf_buf *buf, const char *utf8, size_t length);
void owf_buf_puts_xml(owf_buf *buf, const char *utf8);
/* Hands the contents over (NUL-terminated); the buffer is empty after. */
int owf_buf_take(owf_buf *buf, unsigned char **data, size_t *length);

/* ---- Character sets ---- */

/* One code point as UTF-8 into buf. */
void owf_buf_put_utf8(owf_buf *buf, unsigned long codepoint);
/* ISO-8859-1 (the Amiga's) bytes as UTF-8. */
void owf_buf_put_latin1(owf_buf *buf, const unsigned char *text, size_t length);
/* Windows-1252 bytes as UTF-8. */
void owf_buf_put_cp1252(owf_buf *buf, const unsigned char *text, size_t length);
/* Decodes one UTF-8 code point at *p (not beyond end) and moves *p on;
 * malformed bytes give U+FFFD. */
unsigned long owf_utf8_next(const unsigned char **p, const unsigned char *end);
/* 1 when the bytes are valid UTF-8. */
int owf_utf8_valid(const unsigned char *text, size_t length);

/* ---- Big-endian numbers (IFF) and little-endian (zip) ---- */

#define OWF_BE16(p) ((unsigned)(((p)[0] << 8) | (p)[1]))
#define OWF_BE32(p) (((unsigned long)(p)[0] << 24) | ((unsigned long)(p)[1] << 16) | \
                     ((unsigned long)(p)[2] << 8) | (unsigned long)(p)[3])
#define OWF_ID(a, b, c, d) (((unsigned long)(a) << 24) | ((unsigned long)(b) << 16) | \
                            ((unsigned long)(c) << 8) | (unsigned long)(d))

/* ---- IFF ---- */

typedef struct {
    unsigned long id;
    const unsigned char *data;
    unsigned long size;
} owf_iff_chunk;

typedef struct {
    const unsigned char *pos, *end;
    int truncated;           /* a chunk ran past the end of its FORM */
} owf_iff_reader;

/* 1 when data starts "FORM" ... type. */
int owf_iff_is_form(const unsigned char *data, size_t length, unsigned long type);
/* Starts reading the chunks inside the FORM at data; 0 if it is not one. */
int owf_iff_open(owf_iff_reader *reader, const unsigned char *data, size_t length, unsigned long type);
/* The next chunk; 0 at the end. A chunk cut short by the end of the file is
 * returned with the bytes there are, and reader->truncated set. */
int owf_iff_next(owf_iff_reader *reader, owf_iff_chunk *chunk);

/* ---- Zip archives (ODT, DOCX) ---- */

typedef struct owf_zip owf_zip;
owf_zip *owf_zip_new(owf_buf *out);
/* compress 0 stores the file as it is (ODT's mimetype must be stored). */
int owf_zip_add(owf_zip *zip, const char *name, const void *data, size_t length, int compress);
/* Writes the central directory and frees the writer. */
int owf_zip_finish(owf_zip *zip);
unsigned long owf_crc32(unsigned long crc, const unsigned char *data, size_t length);

/* ---- Shared by the importers ---- */

/* The colours of ISO 6429 (and ANSI text), 0 to 7. */
extern const unsigned long owf_iso_colours[8];

/* Formatting state while text goes into a paragraph. */
typedef struct {
    owf_doc *doc;
    owf_story *story;
    owf_para *para;          /* the paragraph being filled, or NULL */
    owf_parafmt parafmt;     /* for the next paragraph */
    owf_charfmt charfmt;
    owf_buf text;            /* text not yet added as a run */
    int failed;
} owf_builder;

void owf_builder_init(owf_builder *b, owf_doc *doc, owf_story *story);
/* Text, a tab, a line break or a field at the current formatting. */
void owf_builder_text(owf_builder *b, const char *utf8, size_t length);
void owf_builder_special(owf_builder *b, owf_run_kind kind, owf_field field);
/* Call before the character formatting changes. */
void owf_builder_flush(owf_builder *b);
/* Ends the paragraph (an empty one is still a paragraph). */
void owf_builder_end_para(owf_builder *b);
/* Finishes: flushes text and frees the builder's buffer. OWF_OK or OWF_ERR_MEMORY. */
int owf_builder_done(owf_builder *b);

/* The formats. */
extern const owf_format owf_format_text, owf_format_amiga_text, owf_format_ftxt,
    owf_format_ansi, owf_format_prowrite, owf_format_html, owf_format_odt;

#endif
