# Postmark Places

[Open the postmark finder](https://coolcode.ca/postmarkplaces/)

Look up the name and date on an envelope. Trace documented office names, see when a name changed hands, or browse all histories from the Township of Langley and Dartmouth.

<!-- coolcode:guide -->
Compare the “Langley Prairie” postmark in 1910 and 1912. The earlier office became Murrayville on May 16, 1911, the day a different office took the Langley Prairie name. Browse Dartmouth’s history to see how its post office moved between a general store and a purpose-built building. Approximate openings and undocumented closures are labelled on the cards.
<!-- /coolcode:guide -->

## Sources and dating

- The Township of Langley’s [Our Shared History](https://www.tol.ca/en/the-township/resources/about-the-township/history-heritage/TOL-Our-Shared-History-Background-Document-Final.pdf#page=65), printed p. 64 (PDF p. 65), lists eleven offices. Local office identifiers preserve the two separate Langley Prairie offices and link each name to its own sequence. The earlier Langley office opened before 1872. A date earlier than 1872 yields a possible match.
- [Halifax’s heritage research on 53 Queen Street](https://www.halifax.ca/sites/default/files/documents/business/planning-development/applications/24619-h-2020.07.24-heritageregistrationstaffreport.pdf#page=23), PDF p. 23, documents Dartmouth’s official post-office status in 1870, its postmaster, site changes and the 1894 brick building. Only years are known for these entries. A date within the opening year is marked possible.
- [Parks Canada’s postal service commemoration](https://www.pc.gc.ca/apps/dfhd/page_nhs_eng.aspx?i=50422&id=1061) provides the separate Halifax mail-service context. [Library and Archives Canada](https://www.canada.ca/en/library-archives/collection/research-help/postal-heritage/post-offices-postmasters.html) supplies a national collection for further research.
- The finder uses a new name from the effective renaming date. It removes the office from date matches on the recorded closure date. Where the source omits a later event, matches remain candidates. The selected period ends in 1968, the latest explicit event in this extract. The records do not authenticate a cancellation or establish contemporary operations.

## Refresh and development

`sources/records.json` contains the reviewed histories. The monthly workflow checks the two complete source reports against their recorded fingerprints. Changed documents require reviewing the transcriptions before updating the edition. The displayed retrieval date describes the source check.

Searches and dates stay in the browser. Run `python3 scripts/refresh.py` to retrieve and verify, `node --test tests/*.test.mjs` and `python3 -m unittest discover -s tests` to check the application, and `python3 scripts/build.py` for an offline build. Serve `dist/`. With Playwright Chromium installed, run `python3 tests/browser_smoke.py` to exercise it.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
