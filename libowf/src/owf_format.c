/*
 * libowf: the table of formats, finding a file's format, and reading and
 * writing files.
 * MIT, Copyright (c) 2026 Dalsin Limited.
 */
#include "owf_internal.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const owf_format *const formats[] = {
    &owf_format_odt,
    &owf_format_html,
    &owf_format_ftxt,
    &owf_format_prowrite,
    &owf_format_ansi,
    &owf_format_text,
    &owf_format_amiga_text,
};

#define NFORMATS ((int)(sizeof formats / sizeof formats[0]))

const char *owf_error_text(int error)
{
    switch (error) {
    case OWF_OK: return "no error";
    case OWF_ERR_IO: return "the file could not be read or written";
    case OWF_ERR_FORMAT: return "not a document format OpenWrite knows";
    case OWF_ERR_CORRUPT: return "the document is damaged";
    case OWF_ERR_MEMORY: return "not enough memory";
    case OWF_ERR_UNSUPPORTED: return "OpenWrite cannot do that with this format yet";
    default: return "unknown error";
    }
}

int owf_format_count(void)
{
    return NFORMATS;
}

const owf_format *owf_format_at(int index)
{
    return index >= 0 && index < NFORMATS ? formats[index] : NULL;
}

static int same_word(const char *a, const char *b)
{
    while (*a && *b) {
        if (tolower((unsigned char)*a) != tolower((unsigned char)*b))
            return 0;
        a++;
        b++;
    }
    return *a == *b;
}

const owf_format *owf_format_named(const char *name)
{
    int i;
    for (i = 0; i < NFORMATS; i++)
        if (same_word(formats[i]->name, name))
            return formats[i];
    return NULL;
}

/* 1 when ext is one of the space-separated words in list. */
static int in_list(const char *list, const char *ext)
{
    size_t n = strlen(ext);
    while (*list) {
        size_t w = strcspn(list, " ");
        if (w == n) {
            size_t i;
            for (i = 0; i < n && tolower((unsigned char)list[i]) == tolower((unsigned char)ext[i]); i++)
                ;
            if (i == n)
                return 1;
        }
        list += w;
        while (*list == ' ')
            list++;
    }
    return 0;
}

const owf_format *owf_format_for_filename(const char *filename)
{
    const char *dot = strrchr(filename, '.');
    int i;

    /* An AmigaDOS name may have a dot in a drawer's name. */
    if (!dot || strchr(dot, '/') || strchr(dot, ':'))
        return NULL;
    for (i = 0; i < NFORMATS; i++)
        if (formats[i]->export && in_list(formats[i]->extensions, dot + 1))
            return formats[i];
    return NULL;
}

int owf_import_memory(const unsigned char *data, size_t length, const char *format,
                      owf_doc **doc_out, owf_report *report, const owf_format **used)
{
    const owf_format *f = NULL;
    owf_doc *doc;
    int i, best = 0, result;

    *doc_out = NULL;
    if (format) {
        f = owf_format_named(format);
        if (!f || !f->import)
            return OWF_ERR_UNSUPPORTED;
    } else {
        for (i = 0; i < NFORMATS; i++) {
            int score;
            if (!formats[i]->detect || !formats[i]->import)
                continue;
            score = formats[i]->detect(data, length);
            if (score > best) {
                best = score;
                f = formats[i];
            }
        }
        if (!f)
            return OWF_ERR_FORMAT;
    }
    doc = owf_doc_new();
    if (!doc)
        return OWF_ERR_MEMORY;
    result = f->import(data, length, doc, report);
    if (result != OWF_OK) {
        owf_doc_free(doc);
        return result;
    }
    if (used)
        *used = f;
    *doc_out = doc;
    return OWF_OK;
}

int owf_import_file(const char *path, const char *format, owf_doc **doc,
                    owf_report *report, const owf_format **used)
{
    FILE *fh = fopen(path, "rb");
    unsigned char *data;
    long size;
    int result;

    *doc = NULL;
    if (!fh)
        return OWF_ERR_IO;
    if (fseek(fh, 0, SEEK_END) != 0 || (size = ftell(fh)) < 0 || fseek(fh, 0, SEEK_SET) != 0) {
        fclose(fh);
        return OWF_ERR_IO;
    }
    data = malloc((size_t)size + 1);
    if (!data) {
        fclose(fh);
        return OWF_ERR_MEMORY;
    }
    if (size && fread(data, 1, (size_t)size, fh) != (size_t)size) {
        free(data);
        fclose(fh);
        return OWF_ERR_IO;
    }
    fclose(fh);
    data[size] = 0;
    result = owf_import_memory(data, (size_t)size, format, doc, report, used);
    free(data);
    return result;
}

int owf_export_file(const owf_doc *doc, const char *path, const char *format, owf_report *report)
{
    const owf_format *f = format ? owf_format_named(format) : owf_format_for_filename(path);
    unsigned char *data;
    size_t length;
    FILE *fh;
    int result;

    if (!f)
        return format ? OWF_ERR_UNSUPPORTED : OWF_ERR_FORMAT;
    if (!f->export)
        return OWF_ERR_UNSUPPORTED;
    result = f->export(doc, &data, &length, report);
    if (result != OWF_OK)
        return result;
    fh = fopen(path, "wb");
    if (!fh) {
        free(data);
        return OWF_ERR_IO;
    }
    if (length && fwrite(data, 1, length, fh) != length)
        result = OWF_ERR_IO;
    if (fclose(fh) != 0)
        result = OWF_ERR_IO;
    free(data);
    return result;
}
