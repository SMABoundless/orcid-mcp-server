#!/usr/bin/env python3
"""
ORCID MCP Server for Claude Desktop

Provides Claude Desktop with tools to search the ORCID registry,
read researcher profiles, retrieve works, and export citations.

ORCID Public API v3.0 docs:
  https://github.com/ORCID/ORCID-Source/blob/main/orcid-api-web/README.md
"""

import os
from typing import Optional
from mcp.server.fastmcp import FastMCP
import httpx

# ── Configuration ──────────────────────────────────────────────────────────

CLIENT_ID = os.environ.get("ORCID_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET", "")
BASE_URL = "https://pub.orcid.org/v3.0"
TOKEN_URL = "https://orcid.org/oauth/token"

mcp = FastMCP("ORCID")

# ── Token management ──────────────────────────────────────────────────────

_access_token: str = ""


async def _get_token() -> str:
    """Obtain a /read-public access token via client credentials."""
    global _access_token
    if _access_token:
        return _access_token

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials",
                "scope": "/read-public",
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        _access_token = resp.json()["access_token"]
        return _access_token


async def _get(url: str, params: dict = None) -> dict:
    """Make an authenticated GET request to the ORCID API."""
    token = await _get_token()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            params=params or {},
        )
        resp.raise_for_status()
        return resp.json()


# ── Helpers ────────────────────────────────────────────────────────────────

def _format_search_result(i: int, result: dict) -> str:
    """Format an expanded-search result."""
    orcid = result.get("orcid-id", "")
    given = result.get("given-names", "")
    family = result.get("family-names", "")
    credit = result.get("credit-name", "")
    institutions = result.get("institution-name", [])
    if isinstance(institutions, str):
        institutions = [institutions]

    name = credit if credit else f"{given} {family}".strip()
    line = f"{i}. {name}"
    if orcid:
        line += f"\n   ORCID: https://orcid.org/{orcid}"
    if institutions:
        line += f"\n   Affiliations: {'; '.join(institutions[:5])}"
    return line


def _format_work(i: int, work_summary: dict) -> str:
    """Format a single work summary from an ORCID record."""
    title_obj = work_summary.get("title", {})
    title = ""
    if title_obj:
        title_val = title_obj.get("title", {})
        title = title_val.get("value", "") if isinstance(title_val, dict) else str(title_val)

    work_type = work_summary.get("type", "")
    pub_date = work_summary.get("publication-date") or {}
    year = ""
    if pub_date and pub_date.get("year"):
        year = pub_date["year"].get("value", "")

    journal = work_summary.get("journal-title")
    journal_name = ""
    if journal:
        journal_name = journal.get("value", "") if isinstance(journal, dict) else str(journal)

    # External identifiers (DOI, etc.)
    ext_ids = work_summary.get("external-ids", {})
    ext_id_list = ext_ids.get("external-id", []) if ext_ids else []
    doi = ""
    for eid in ext_id_list:
        if eid.get("external-id-type") == "doi":
            doi = eid.get("external-id-value", "")
            break

    line = f"{i}. {title or 'Untitled'}"
    if journal_name:
        line += f"\n   Source: {journal_name}"
    if year:
        line += f"\n   Year: {year}"
    if work_type:
        line += f"\n   Type: {work_type}"
    if doi:
        line += f"\n   DOI: https://doi.org/{doi}"
    return line


def _work_to_ris(work_summary: dict) -> str:
    """Convert an ORCID work summary to RIS format."""
    title_obj = work_summary.get("title", {})
    title = ""
    if title_obj:
        title_val = title_obj.get("title", {})
        title = title_val.get("value", "") if isinstance(title_val, dict) else str(title_val)

    work_type = work_summary.get("type", "")
    ris_type = "JOUR" if "journal" in work_type.lower() else "GEN"

    pub_date = work_summary.get("publication-date") or {}
    year = ""
    if pub_date and pub_date.get("year"):
        year = pub_date["year"].get("value", "")

    journal = work_summary.get("journal-title")
    journal_name = ""
    if journal:
        journal_name = journal.get("value", "") if isinstance(journal, dict) else str(journal)

    ext_ids = work_summary.get("external-ids", {})
    ext_id_list = ext_ids.get("external-id", []) if ext_ids else []
    doi = ""
    for eid in ext_id_list:
        if eid.get("external-id-type") == "doi":
            doi = eid.get("external-id-value", "")
            break

    lines = [f"TY  - {ris_type}"]
    if title:
        lines.append(f"TI  - {title}")
    if journal_name:
        lines.append(f"JO  - {journal_name}")
    if year:
        lines.append(f"PY  - {year}")
    if doi:
        lines.append(f"DO  - {doi}")
    lines.append("ER  - ")
    return "\n".join(lines)


def _work_to_bibtex(work_summary: dict) -> str:
    """Convert an ORCID work summary to BibTeX format."""
    title_obj = work_summary.get("title", {})
    title = ""
    if title_obj:
        title_val = title_obj.get("title", {})
        title = title_val.get("value", "") if isinstance(title_val, dict) else str(title_val)

    work_type = work_summary.get("type", "")
    bib_type = "article" if "journal" in work_type.lower() else "misc"

    pub_date = work_summary.get("publication-date") or {}
    year = ""
    if pub_date and pub_date.get("year"):
        year = pub_date["year"].get("value", "")

    journal = work_summary.get("journal-title")
    journal_name = ""
    if journal:
        journal_name = journal.get("value", "") if isinstance(journal, dict) else str(journal)

    ext_ids = work_summary.get("external-ids", {})
    ext_id_list = ext_ids.get("external-id", []) if ext_ids else []
    doi = ""
    for eid in ext_id_list:
        if eid.get("external-id-type") == "doi":
            doi = eid.get("external-id-value", "")
            break

    key = f"orcid{year or 'nd'}"
    lines = [f"@{bib_type}{{{key},"]
    if title:
        lines.append(f"  title = {{{title}}},")
    if journal_name:
        lines.append(f"  journal = {{{journal_name}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    lines.append("}")
    return "\n".join(lines)


# ── Store last works results for export ──────────────────────────────────

_last_works: list = []


# ── Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
async def orcid_search(
    query: str,
    search_type: str = "name",
    count: int = 25,
) -> str:
    """
    Search the ORCID registry for researchers.

    Args:
        query: Search terms (name, keyword, affiliation, DOI, ORCID iD)
        search_type: One of: name, affiliation, keyword, doi, advanced
                     - name: searches by researcher name
                     - affiliation: searches by institution/organization name
                     - keyword: searches researcher keywords/biography
                     - doi: finds the ORCID record linked to a specific DOI
                     - advanced: pass raw Solr query (e.g. "family-name:Einstein AND keyword:Relativity")
        count: Number of results (max 100, default 25)
    """
    query_map = {
        "name": lambda q: f"given-and-family-names:{q}",
        "affiliation": lambda q: f"affiliation-org-name:{q}",
        "keyword": lambda q: f"keyword:{q}",
        "doi": lambda q: f'doi-self:"{q}"',
        "advanced": lambda q: q,
    }
    builder = query_map.get(search_type, query_map["name"])
    solr_query = builder(query)

    try:
        data = await _get(
            f"{BASE_URL}/expanded-search/",
            {"q": solr_query, "rows": min(count, 100), "start": 0},
        )

        results = data.get("expanded-result", [])
        total = data.get("num-found", 0)

        if not results:
            return f"No results found for: {query}"

        header = f"ORCID Search: {total} total results, showing {len(results)}\n"
        header += f"Query: {solr_query}\n"
        header += "=" * 60 + "\n\n"
        formatted = "\n\n".join(
            _format_search_result(i, r) for i, r in enumerate(results, 1)
        )
        return header + formatted
    except httpx.HTTPStatusError as e:
        return f"ORCID API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def orcid_read_record(orcid_id: str) -> str:
    """
    Read a researcher's full ORCID profile.

    Args:
        orcid_id: The ORCID iD (e.g. "0000-0002-1825-0097")
    """
    try:
        data = await _get(f"{BASE_URL}/{orcid_id}/record")

        # Person details
        person = data.get("person", {})
        name_obj = person.get("name", {})
        given = ""
        family = ""
        credit = ""
        if name_obj:
            gn = name_obj.get("given-names")
            given = gn.get("value", "") if isinstance(gn, dict) else (gn or "")
            fn = name_obj.get("family-name")
            family = fn.get("value", "") if isinstance(fn, dict) else (fn or "")
            cn = name_obj.get("credit-name")
            credit = cn.get("value", "") if isinstance(cn, dict) else (cn or "")

        bio_obj = person.get("biography")
        bio = ""
        if bio_obj:
            bio = bio_obj.get("content", "") if isinstance(bio_obj, dict) else str(bio_obj)

        # Keywords
        kw_obj = person.get("keywords", {})
        kw_list = kw_obj.get("keyword", []) if kw_obj else []
        keywords = [k.get("content", "") for k in kw_list if k.get("content")]

        # Researcher URLs
        urls_obj = person.get("researcher-urls", {})
        url_list = urls_obj.get("researcher-url", []) if urls_obj else []
        urls = [(u.get("url-name", ""), u.get("url", {}).get("value", "")) for u in url_list]

        # Emails
        emails_obj = person.get("emails", {})
        email_list = emails_obj.get("email", []) if emails_obj else []
        emails = [e.get("email", "") for e in email_list if e.get("email")]

        # Activities summary
        activities = data.get("activities-summary", {})

        # Employments
        emp_obj = activities.get("employments", {})
        emp_groups = emp_obj.get("affiliation-group", []) if emp_obj else []
        employments = []
        for group in emp_groups:
            summaries = group.get("summaries", [])
            for s in summaries:
                emp = s.get("employment-summary", {})
                org = emp.get("organization", {})
                org_name = org.get("name", "")
                role = emp.get("role-title", "")
                dept = emp.get("department-name", "")
                start = emp.get("start-date")
                end = emp.get("end-date")
                start_yr = start.get("year", {}).get("value", "") if start else ""
                end_yr = end.get("year", {}).get("value", "present") if end else "present"
                entry = org_name
                if role:
                    entry = f"{role}, {entry}"
                if dept:
                    entry += f" ({dept})"
                if start_yr:
                    entry += f" [{start_yr}–{end_yr}]"
                employments.append(entry)

        # Educations
        edu_obj = activities.get("educations", {})
        edu_groups = edu_obj.get("affiliation-group", []) if edu_obj else []
        educations = []
        for group in edu_groups:
            summaries = group.get("summaries", [])
            for s in summaries:
                edu = s.get("education-summary", {})
                org = edu.get("organization", {})
                org_name = org.get("name", "")
                role = edu.get("role-title", "")
                dept = edu.get("department-name", "")
                start = edu.get("start-date")
                end = edu.get("end-date")
                start_yr = start.get("year", {}).get("value", "") if start else ""
                end_yr = end.get("year", {}).get("value", "") if end else ""
                entry = org_name
                if role:
                    entry = f"{role}, {entry}"
                if dept:
                    entry += f" ({dept})"
                if start_yr:
                    entry += f" [{start_yr}–{end_yr}]" if end_yr else f" [{start_yr}–]"
                educations.append(entry)

        # Works count
        works_obj = activities.get("works", {})
        work_groups = works_obj.get("group", []) if works_obj else []
        works_count = len(work_groups)

        # Fundings count
        fund_obj = activities.get("fundings", {})
        fund_groups = fund_obj.get("group", []) if fund_obj else []
        fundings_count = len(fund_groups)

        # Build output
        display_name = credit if credit else f"{given} {family}".strip()
        output = f"Name: {display_name}\n"
        output += f"ORCID: https://orcid.org/{orcid_id}\n"
        if emails:
            output += f"Email: {'; '.join(emails)}\n"
        if bio:
            output += f"\nBiography:\n{bio}\n"
        if keywords:
            output += f"\nKeywords: {'; '.join(keywords)}\n"
        if urls:
            output += "\nLinks:\n"
            for name, url in urls:
                output += f"  - {name}: {url}\n" if name else f"  - {url}\n"
        if employments:
            output += f"\nEmployment ({len(employments)}):\n"
            for emp in employments:
                output += f"  - {emp}\n"
        if educations:
            output += f"\nEducation ({len(educations)}):\n"
            for edu in educations:
                output += f"  - {edu}\n"
        output += f"\nWorks: {works_count} items"
        if works_count > 0:
            output += " (use orcid_read_works to see them)"
        output += f"\nFunding: {fundings_count} items"

        return output
    except httpx.HTTPStatusError as e:
        return f"ORCID API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def orcid_read_works(
    orcid_id: str,
    count: int = 25,
) -> str:
    """
    Get publications from an ORCID researcher profile.

    Args:
        orcid_id: The ORCID iD (e.g. "0000-0002-1825-0097")
        count: Maximum number of works to return (default 25)
    """
    global _last_works
    try:
        data = await _get(f"{BASE_URL}/{orcid_id}/works")
        groups = data.get("group", [])

        if not groups:
            _last_works = []
            return f"No works found for ORCID {orcid_id}"

        # Each group has work-summary entries; take the first summary per group
        works = []
        for group in groups[:count]:
            summaries = group.get("work-summary", [])
            if summaries:
                works.append(summaries[0])

        _last_works = works

        header = f"Works for ORCID {orcid_id}: {len(groups)} total, showing {len(works)}\n"
        header += "=" * 60 + "\n\n"
        formatted = "\n\n".join(
            _format_work(i, w) for i, w in enumerate(works, 1)
        )
        return header + formatted
    except httpx.HTTPStatusError as e:
        return f"ORCID API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def orcid_export_ris() -> str:
    """
    Export the most recent orcid_read_works results as RIS format.
    Save output as a .ris file and import into Zotero: File -> Import.
    """
    if not _last_works:
        return "No works to export. Run orcid_read_works first."
    records = [_work_to_ris(w) for w in _last_works]
    count = len(records)
    return f"RIS Export ({count} records) — Save as .ris and import into Zotero:\n\n" + "\n\n".join(records)


@mcp.tool()
async def orcid_export_bibtex() -> str:
    """
    Export the most recent orcid_read_works results as BibTeX format.
    """
    if not _last_works:
        return "No works to export. Run orcid_read_works first."
    records = [_work_to_bibtex(w) for w in _last_works]
    count = len(records)
    return f"BibTeX Export ({count} records):\n\n" + "\n\n".join(records)


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
