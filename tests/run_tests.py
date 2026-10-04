#!/usr/bin/env python3
"""OpenWrite's filter tests: run_tests.py path/to/owconvert

Builds sample documents from the formats' specifications (IFF FTXT, ProWrite's
IFF WORD, ANSI and plain text), converts each to text, HTML, ODT and FTXT,
and checks the results. Then feeds every cut-short copy of each sample to the
converter, which must answer with an error or a document, never crash.

Real files from the original programs replace and add to these samples as the
format lab makes them (docs/FORMATS.md, section 4).
MIT, Copyright (c) 2026 Dalsin Limited.
"""
import os
import struct
import subprocess
import sys
import tempfile
import xml.dom.minidom
import zipfile

OWCONVERT = os.path.abspath(sys.argv[1])
failures = []


def check(name, condition, detail=""):
    if not condition:
        failures.append(f"{name}: {detail}")
        print(f"FAIL {name} {detail}")


def chunk(cid, data):
    out = cid.encode("ascii") + struct.pack(">I", len(data)) + data
    return out + (b"\0" if len(data) & 1 else b"")


def form(ftype, chunks):
    body = ftype.encode("ascii") + b"".join(chunks)
    return b"FORM" + struct.pack(">I", len(body)) + body


def ftxt_sample():
    fons_times = bytes([1, 0, 2, 2]) + b"times\0"
    fons_courier = bytes([2, 0, 1, 1]) + b"courier\0"
    chrs = (b"Hello \x9b1mbold\x9b22m and \x9b3mitalic\x9b23m, \x1b[4munderlined\x1b[24m.\n"
            b"Caf\xe9 in \x9b11mTimes\x9b10m and \x9b12mCourier\x9b10m.\n"
            b"Before\x0cAfter\tTab\n"
            b"\x9b31mRed\x9b39m plain\n")
    return form("FTXT", [chunk("FONS", fons_times), chunk("FONS", fons_courier), chunk("CHRS", chrs)])


def para(left_indent=0, left_margin=0, right_margin=0, spacing=0, justify=0, font=0, style=0, misc=0, colour=0):
    return struct.pack(">HHHBBBBBBI", left_indent, left_margin, right_margin, spacing, justify, font, style, misc, colour, 0)


def fscc(*changes):
    return b"".join(struct.pack(">HBBBBH", loc, font, style, misc, colour, 0) for loc, font, style, misc, colour in changes)


def prowrite_sample():
    chunks = [
        chunk("FONT", struct.pack(">BxH", 0, 12) + b"times\0"),
        chunk("FONT", struct.pack(">BxH", 1, 18) + b"helvetica\0"),
        chunk("COLR", bytes(range(8))),
        chunk("DOC ", struct.pack(">HBBI", 1, 0, 0, 0)),
        chunk("PARA", para(justify=1, font=1, style=2)),
        chunk("TEXT", b"Title"),
        chunk("PARA", para(left_indent=360, spacing=0x10)),
        chunk("TABS", struct.pack(">HBB", 1440, 2, 0)),
        # "Body bold red text, page " then the page number: bold from 5,
        # red (not bold) from 9, plain from 13.
        chunk("TEXT", b"Body bold red text, page \x80"),
        chunk("FSCC", fscc((5, 0, 2, 0, 0), (9, 0, 0, 0, 1), (13, 0, 0, 0, 0))),
        chunk("TEXT", b"a\tb"),
        chunk("PAGE", b""),
        chunk("TEXT", b"Next page"),
        chunk("HEAD", struct.pack(">BBI", 3, 0, 0)),
        chunk("PARA", para()),
        chunk("TEXT", b"Header \x80"),
        chunk("FOOT", struct.pack(">BBI", 3, 1, 0)),
        chunk("TEXT", b"Footer \x81"),
        chunk("PCTS", bytes([3, 0])),
        chunk("PINF", struct.pack(">HHHHHBBBB", 16, 8, 1, 100, 100, 0, 1, 0, 0)),
        chunk("BODY", bytes(48)),
    ]
    return form("WORD", chunks)


SAMPLES = {
    "sample.ftxt": ftxt_sample(),
    "sample.pw": prowrite_sample(),
    "sample.ans": b"\x1b[1mBold\x1b[0m normal \x1b[32mgreen\x1b[0m\n",
    "latin1.txt": b"Caf\xe9\r\nLine two\r\n",
    "utf8.txt": "﻿Café — UTF-8\n".encode("utf-8"),
}


def run(*args):
    return subprocess.run([OWCONVERT, *args], capture_output=True, timeout=60)


def convert(work, name, ext, extra=()):
    src = os.path.join(work, name)
    dst = os.path.join(work, name + "." + ext)
    r = run("--report", *extra, src, dst)
    check(f"{name}->{ext} exit", r.returncode == 0, (r.stdout + r.stderr).decode("utf-8", "replace"))
    try:
        with open(dst, "rb") as f:
            return f.read(), r.stdout.decode("utf-8", "replace")
    except OSError:
        return b"", ""


def check_odt(name, data):
    path = name + ".check.odt"
    with open(path, "wb") as f:
        f.write(data)
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile as e:
        check(f"{name} odt zip", False, str(e))
        return {}
    infos = z.infolist()
    check(f"{name} odt mimetype first", infos[0].filename == "mimetype", infos[0].filename)
    check(f"{name} odt mimetype stored", infos[0].compress_type == zipfile.ZIP_STORED)
    check(f"{name} odt mimetype", z.read("mimetype") == b"application/vnd.oasis.opendocument.text")
    check(f"{name} odt zip test", z.testzip() is None)
    parts = {}
    for part in ("content.xml", "styles.xml", "meta.xml", "META-INF/manifest.xml"):
        try:
            text = z.read(part).decode("utf-8")
            xml.dom.minidom.parseString(text)
            parts[part] = text
        except KeyError:
            check(f"{name} odt has {part}", False)
        except Exception as e:  # not well-formed
            check(f"{name} odt {part} well-formed", False, str(e))
    return parts


def check_docx(name, data):
    path = name + ".check.docx"
    with open(path, "wb") as f:
        f.write(data)
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile as e:
        check(f"{name} docx zip", False, str(e))
        return {}
    check(f"{name} docx zip test", z.testzip() is None)
    parts = {}
    for info in z.infolist():
        text = z.read(info.filename).decode("utf-8")
        try:
            xml.dom.minidom.parseString(text)
        except Exception as e:
            check(f"{name} docx {info.filename} well-formed", False, str(e))
        parts[info.filename] = text
    for part in ("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml",
                 "word/_rels/document.xml.rels", "docProps/core.xml", "docProps/app.xml"):
        check(f"{name} docx has {part}", part in parts)
    # Every relationship's target is in the package, and every part has a content type.
    import re
    types = parts.get("[Content_Types].xml", "")
    for rels, base in (("_rels/.rels", ""), ("word/_rels/document.xml.rels", "word/")):
        for target in re.findall(r'Target="([^"]+)"', parts.get(rels, "")):
            check(f"{name} docx target {target}", base + target in parts)
    for part in parts:
        if not part.endswith(".rels") and part != "[Content_Types].xml":
            check(f"{name} docx type for {part}", ('PartName="/' + part + '"') in types or part.endswith(".xml"))
    return parts


def main():
    base = os.environ.get("OWF_TEST_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build", "tests")
    os.makedirs(base, exist_ok=True)
    work = tempfile.mkdtemp(prefix="owf-", dir=base)
    for name, data in SAMPLES.items():
        with open(os.path.join(work, name), "wb") as f:
            f.write(data)
    os.chdir(work)

    # IFF FTXT
    text, _ = convert(work, "sample.ftxt", "txt")
    check("ftxt text", text == "Hello bold and italic, underlined.\nCafé in Times and Courier.\nBefore\n\fAfter\tTab\nRed plain\n".encode(),
          repr(text))
    html, _ = convert(work, "sample.ftxt", "html")
    h = html.decode()
    for want in ("<b>bold</b>", "<i>italic</i>", "<u>underlined</u>", "Café", "'Liberation Serif', 'times', serif",
                 "'Liberation Mono', 'courier', monospace", "color: #cc0000", "class=\"ow-page-break\"", "<span class=\"ow-tab\">\t</span>"):
        check("ftxt html has " + want, want in h)
    odt, _ = convert(work, "sample.ftxt", "odt")
    parts = check_odt("ftxt", odt)
    c = parts.get("content.xml", "")
    for want in ("fo:font-weight=\"bold\"", "fo:font-style=\"italic\"", "style:text-underline-style=\"solid\"",
                 "fo:break-before=\"page\"", "<text:tab/>", "fo:color=\"#cc0000\"", "Café"):
        check("ftxt odt has " + want, want in c)

    # ProWrite (IFF WORD)
    text, report = convert(work, "sample.pw", "txt")
    check("prowrite text", text == b"Title\nBody bold red text, page #\na\tb\n\fNext page\n", repr(text))
    check("prowrite report pictures", "1 picture(s) are not brought across yet" in report, report)
    html, _ = convert(work, "sample.pw", "html")
    h = html.decode()
    for want in ("text-align: center", "<b>Title</b>", "font-size: 18pt", "'Liberation Sans', 'helvetica', sans-serif",
                 "<b>bold</b>", "color: #cc0000\"> red</span>", "text-indent: 36pt", "line-height: 200%", "data-ow-tabs=\"2880:right\"",
                 "data-field=\"page\"", "<div class=\"ow-header\" data-first-page=\"0\">", "Header ",
                 "<div class=\"ow-footer\" data-first-page=\"1\">", "data-field=\"date\""):
        check("prowrite html has " + want, want in h)
    odt, report = convert(work, "sample.pw", "odt")
    parts = check_odt("prowrite", odt)
    c = parts.get("content.xml", "")
    s = parts.get("styles.xml", "")
    for want in ("Title", "<text:page-number text:select-page=\"current\">", "style:type=\"right\"", "style:position=\"144pt\"",
                 "fo:line-height=\"200%\"", "fo:text-indent=\"36pt\"", "fo:break-before=\"page\"", "style:font-name=\"Liberation Sans\"",
                 "fo:font-size=\"18pt\"", "fo:color=\"#cc0000\""):
        check("prowrite odt content has " + want, want in c)
    for want in ("<style:header>", "Header ", "<style:footer>", "<text:date/>", "fo:page-width="):
        check("prowrite odt styles has " + want, want in s)
    check("prowrite odt report header", "The header is also on the first page" in report, report)

    docx, report = convert(work, "sample.pw", "docx")
    parts = check_docx("prowrite", docx)
    d = parts.get("word/document.xml", "")
    for want in ("<w:jc w:val=\"center\"/>", "<w:b/>", "<w:sz w:val=\"36\"/>", "w:ascii=\"Liberation Sans\"",
                 "<w:color w:val=\"CC0000\"/>", "<w:t xml:space=\"preserve\"> red</w:t>", "<w:tab w:val=\"right\" w:pos=\"2880\"/>",
                 "w:line=\"480\" w:lineRule=\"auto\"", "<w:ind w:firstLine=\"720\"/>", "<w:pageBreakBefore/>",
                 "<w:fldSimple w:instr=\" PAGE \">", "<w:headerReference w:type=\"default\" r:id=\"rId2\"/>",
                 "<w:footerReference w:type=\"first\" r:id=\"rId3\"/>", "<w:titlePg/>", "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"):
        check("prowrite docx document has " + want, want in d)
    check("prowrite docx no first header", "<w:headerReference w:type=\"first\"" not in d, d[-600:])
    check("prowrite docx header", "Header " in parts.get("word/header1.xml", ""))
    check("prowrite docx footer date", "<w:fldSimple w:instr=\" DATE \">" in parts.get("word/footer1.xml", ""))
    check("prowrite docx rels", "header1.xml" in parts.get("word/_rels/document.xml.rels", ""))
    check("prowrite docx types", "wordprocessingml.header+xml" in parts.get("[Content_Types].xml", ""))
    # Elements in w:pPr and w:rPr must be in the schema's order.
    order_ppr = ["pStyle", "pageBreakBefore", "tabs", "spacing", "ind", "jc"]
    order_rpr = ["rFonts", "b", "i", "strike", "color", "sz", "u", "vertAlign"]
    import re
    for block, order in (("pPr", order_ppr), ("rPr", order_rpr)):
        for m in re.finditer(r"<w:%s>(.*?)</w:%s>" % (block, block), d):
            names = re.findall(r"<w:(\w+)", m.group(1))
            names = [n for n in names if n in order]
            check(f"docx {block} order", names == sorted(names, key=order.index), m.group(0))
    docx, _ = convert(work, "sample.ftxt", "docx")
    parts = check_docx("ftxt", docx)
    check("ftxt docx text", "Caf\u00e9" in parts.get("word/document.xml", ""))
    check("ftxt docx no header part", "word/header1.xml" not in parts)

    # ProWrite -> FTXT -> text keeps the words
    ftxt, _ = convert(work, "sample.pw", "ftxt")
    with open(os.path.join(work, "round.ftxt"), "wb") as f:
        f.write(ftxt)
    text, _ = convert(work, "round.ftxt", "txt")
    check("prowrite->ftxt->text", text == b"Title\nBody bold red text, page \na\tb\n\fNext page\n", repr(text))

    # ANSI and plain text
    html, _ = convert(work, "sample.ans", "html")
    check("ansi bold", "<b>Bold</b>" in html.decode(), html)
    check("ansi green", "color: #008800" in html.decode(), html)
    text, report = convert(work, "latin1.txt", "txt")
    check("latin1 text", text == "Café\nLine two\n".encode(), repr(text))
    check("latin1 report", "ISO-8859-1" in report, report)
    with open(os.path.join(work, "pages.txt"), "wb") as f:
        f.write(b"One\n\fTwo\fThree\n")
    text, _ = convert(work, "pages.txt", "txt")
    check("text page breaks", text == b"One\n\fTwo\n\fThree\n", repr(text))
    text, _ = convert(work, "utf8.txt", "asc", ("--format", "amiga-text"))
    check("utf8 to amiga text", text == b"Caf\xe9 ? UTF-8\n", repr(text))

    # Unknown output and broken input
    r = run(os.path.join(work, "sample.pw"), os.path.join(work, "out.xyz"))
    check("unknown extension refused", r.returncode == 10, r.stdout)
    with open(os.path.join(work, "binary.bin"), "wb") as f:
        f.write(bytes(range(256)))
    r = run(os.path.join(work, "binary.bin"), os.path.join(work, "out.txt"))
    check("binary refused", r.returncode == 10, r.stdout)

    # Every cut-short sample: an answer, never a crash.
    cuts = 0
    for name, data in SAMPLES.items():
        for n in range(len(data)):
            path = os.path.join(work, "cut.bin")
            with open(path, "wb") as f:
                f.write(data[:n])
            r = run(path, os.path.join(work, "cut.html"))
            cuts += 1
            if r.returncode not in (0, 10):
                check(f"{name} cut at {n}", False, f"exit {r.returncode}: {(r.stdout + r.stderr)[-400:]!r}")
                break
    print(f"{cuts} cut-short files tried")

    print(f"{'FAILED' if failures else 'passed'}: {len(failures)} failure(s); files in {work}")
    sys.exit(1 if failures else 0)


main()
