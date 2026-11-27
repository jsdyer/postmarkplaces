"""Build the postal office directory and name timelines from the reviewed edition."""
from collections import defaultdict
from datetime import date, timedelta
from html import escape
import json
import re
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

BASE = "https://coolcode.ca/postmarkplaces/"
LAC = "https://www.canada.ca/en/library-archives/collection/research-help/postal-heritage/post-offices-postmasters.html"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def a(label, href):
    return f'<a href="{escape(href, quote=True)}">{escape(label)}</a>'


def name_of(office):
    return " → ".join(row["name"] for row in office["names"])


def start_date(office, row):
    return row["from"] or "Before " + office["before"][:4]


def events(office):
    timeline = {}
    for i, row in enumerate(office["names"]):
        timeline[start_date(office, row)] = ("Renamed " if i else "Opened as ") + row["name"] + "."
    if office.get("closed"):
        timeline[office["closed"]] = "Office closed."
    timeline.update(office.get("events", []))
    return timeline


def office_index(office):
    return "records/offices/" + office["id"] + "/"


def report(office):
    label = "Halifax heritage report, PDF page 23" if office["region"] == "Dartmouth, NS" else "Township of Langley heritage report, printed page 64"
    return a(label, office["source"])


def item_list(items):
    return '<ul class="record-list">' + "".join("<li>" + s + "</li>" for s in items) + "</ul>"


def write_records(stage):
    edition = json.loads((stage / "data/edition.json").read_text())
    offices = sorted(edition["offices"], key=lambda o: name_of(o).casefold())
    areas, names = defaultdict(list), defaultdict(list)
    pages = {}
    for office in offices:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", office["id"]):
            raise ValueError("Invalid office ID")
        areas[office["region"]].append(office)
        for index, row in enumerate(office["names"]):
            names[row["name"]].append((office, index))
    shared = {n: v for n, v in names.items() if len({o["id"] for o, _ in v}) > 1}

    def render(path, title, summary, body):
        if path in pages:
            raise ValueError("Duplicate office directory URL: " + path)
        pages[path] = title
        rel = "../" * path.count("/")
        files = stage / path
        files.mkdir(parents=True, exist_ok=True)
        url = BASE + path
        content = f'''<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Postmark Places</title><meta name="description" content="{escape(summary, quote=True)}"><link rel="canonical" href="{url}">
<link rel="stylesheet" href="{rel}style.css"><script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head><body data-tool-id="postmarkplaces">
<a href="#main" class="skip">Skip to record</a><header>{a("CoolCode","https://coolcode.ca/")}{a("Postmark finder",rel)}</header>
<main id="main" class="postal-record"><div class="mast"><p class="kicker">{a("Postal histories",rel+"records/")}</p><h1>{escape(title)}</h1><p class="intro">{escape(summary)}</p></div>{body(rel)}</main>
<footer>Source documents checked {escape(edition["retrieved"][:10])} · {a("Download the postal history data (JSON)",rel+"data/edition.json")} · {a("Search Library and Archives Canada",LAC)} · {a("Report a correction","https://coolcode.ca/report/?tool=postmarkplaces")}</footer></body></html>'''
        (files / "index.html").write_text(content, encoding="utf-8")

    def office_link(office, rel):
        return a(name_of(office), rel + office_index(office))

    def area_link(region, rel):
        return a(region + " postal timeline", rel + "records/areas/" + slug(region) + "/")

    def name_link(name, rel):
        return a("Trace the “" + name + "” postmark", rel + "records/names/" + slug(name) + "/")

    def office_body(o, rel):
        history = events(o)
        html = '<section><h2>Office history</h2>' + item_list(f'<strong>{escape(when)}</strong> · {escape(what)}' for when, what in history.items())
        if not o.get("closed"):
            html += "<p>This source gives no closure date.</p>"
        html += '<p>' + report(o) + '</p></section><section><h2>Follow this record</h2>'
        related = [a("Open this office in the postmark finder", rel + "?" + urlencode({"office":o["id"]}))]
        related.extend(name_link(row["name"], rel) for row in o["names"] if row["name"] in shared)
        if o.get("closed"):
            related.extend("Closed on the same date · " + office_link(other, rel) for other in areas[o["region"]]
                           if other["id"] != o["id"] and other.get("closed") == o["closed"])
        # Dated local openings give even single-name offices a route into other histories.
        first_date = o["names"][0]["from"]
        if first_date and len(first_date) == 10:
            dated = [(member["names"][0]["from"], member) for member in areas[o["region"]]
                     if member["id"] != o["id"] and len(member["names"][0]["from"] or "") == 10]
            before = [entry for entry in dated if entry[0] < first_date]
            after = [entry for entry in dated if entry[0] > first_date]
            for label, neighbours, nearest in (("Previous recorded opening", before, max), ("Next recorded opening", after, min)):
                if neighbours:
                    when = nearest(day for day, _ in neighbours)
                    related.extend(f"{label} in this area · {escape(when)} · " + office_link(member, rel)
                                   for day, member in neighbours if day == when)
        related.append(area_link(o["region"], rel))
        if o["id"] == "aldergrove":
            related.append(a("See enrolment at Aldergrove’s school in Schoolhouse Ledger","https://coolcode.ca/schoolhouseledger/schools/aldergrove/"))
        if o["id"] == "dartmouth":
            related.append(a("Compare historical aerial views in Halifax Time Lens","https://coolcode.ca/halifaxtimelens/"))
        return html + item_list(related) + "</section>"

    for o in offices:
        initial = o["names"][0]
        start = start_date(o, initial)
        desc = f'{o["region"]}. Recorded as {initial["name"]} {"before " + o["before"][:4] if not initial["from"] else "from " + start}.'
        if len(o["names"]) > 1:
            desc += f' Renamed {o["names"][-1]["name"]} on {o["names"][-1]["from"]}.'
        elif o.get("closed"):
            desc += f' Its recorded closure was {o["closed"]}.'
        render(office_index(o), name_of(o) + " post office", desc, lambda rel: office_body(o, rel))

    for name, entries in sorted(shared.items()):
        def handovers(rel):
            rows = []
            names_ending, names_starting = set(), set()
            for o, i in sorted(entries, key=lambda v: v[0]["names"][v[1]]["from"] or ""):
                row = o["names"][i]
                end = o["names"][i+1]["from"] if i+1 < len(o["names"]) else o.get("closed")
                if row["from"]:
                    names_starting.add(row["from"])
                if end:
                    names_ending.add(end)
                bound = "until " + end if end else "no later change documented"
                rows.append(f'<tr><th scope="row">{office_link(o,rel)}</th><td>{escape(start_date(o,row))}</td><td>{escape(bound)}</td></tr>')
            switches = []
            for day in sorted(names_starting & names_ending):
                if len(day) == 10:
                    previous = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
                    for sample in [previous, day]:
                        switches.append(a("Match an envelope dated " + sample,
                                          rel + "?" + urlencode({"name": name, "date": sample})))
            return ('<section><h2>When each office used the name</h2><div class="tablewrap"><table><thead><tr><th>Office history</th><th>From</th><th>Next change</th></tr></thead><tbody>'
                    + "".join(rows) + '</tbody></table></div><p>The new name applies on the recorded change date. An open end means the excerpt gives no later event.</p><p>'
                    + report(entries[0][0]) + '</p></section><section><h2>Match the date on an envelope</h2><p>'
                    + a("Find this postmark across all dates",rel + "?" + urlencode({"name": name})) + '</p>'
                    + (item_list(switches) if switches else '') + '</section>')
        render("records/names/" + slug(name) + "/", name + " on Canadian postmarks",
               f"{len(entries)} documented office histories use the name {name}. Compare when each used it and follow the individual office records.", handovers)

    for region, members in sorted(areas.items()):
        def chronology(rel):
            lines = sorted((date, o["id"], what, o) for o in members for date, what in events(o).items())
            lines.sort(key=lambda line: line[0].removeprefix("Before ") + ("!" if line[0].startswith("Before ") else ""))
            return ('<section><h2>Documented changes</h2>' + item_list(f'<strong>{escape(d)}</strong> · {escape(w)} {office_link(o,rel)}' for d, _, w, o in lines)
                    + '<p>' + report(members[0]) + '</p></section>')
        render("records/areas/" + slug(region) + "/", region + " postal timeline",
               f"Follow the dates and places in {len(members)} documented post-office {'history' if len(members)==1 else 'histories'} from {region}.", chronology)

    def directory(rel):
        return ('<section><h2>When a name changed hands</h2>' + item_list(name_link(n, rel) for n in sorted(shared))
                + '</section><section><h2>Office histories by area</h2>' + "".join('<h3>' + area_link(region, rel) + '</h3>' + item_list(office_link(o,rel) for o in members)
                for region, members in sorted(areas.items())) + '</section>')
    render("records/", "Canadian post-office histories", "Look up an office, follow a reused postmark name or read a local postal timeline in Langley and Dartmouth.", directory)
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in sorted(pages):
        ET.SubElement(ET.SubElement(root,"url"), "loc").text = BASE + path
    ET.ElementTree(root).write(stage / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    return len(pages)
