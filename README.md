# ORCID MCP Server

An MCP (Model Context Protocol) server that provides tools for searching the [ORCID](https://orcid.org) registry, reading researcher profiles, retrieving publications, and exporting citations in RIS and BibTeX formats.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and the ORCID Public API v3.0.

## Tools

| Tool | Description |
|------|-------------|
| `orcid_search` | Search for researchers by name, affiliation, keyword, DOI, or advanced Solr query |
| `orcid_read_record` | Read a researcher's full profile (bio, employment, education, keywords) |
| `orcid_read_works` | Get publications from a researcher's ORCID record |
| `orcid_export_ris` | Export retrieved works as RIS (for Zotero, EndNote, etc.) |
| `orcid_export_bibtex` | Export retrieved works as BibTeX |

## Setup

### 1. Get ORCID API credentials

Register for free public API credentials at [ORCID Developer Tools](https://info.orcid.org/documentation/integration-guide/registering-a-public-api-client/).

### 2. Install

```bash
cd orcid-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example env file and add your credentials:

```bash
cp .env.example .env
# Edit .env with your ORCID_CLIENT_ID and ORCID_CLIENT_SECRET
```

### 4. Add to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "orcid-mcp": {
      "command": "/path/to/orcid-mcp-server/venv/bin/python",
      "args": ["/path/to/orcid-mcp-server/server.py"],
      "env": {
        "ORCID_CLIENT_ID": "your-client-id",
        "ORCID_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Or if using Claude Code CLI:

```bash
claude mcp add orcid-mcp \
  /path/to/orcid-mcp-server/venv/bin/python \
  /path/to/orcid-mcp-server/server.py \
  -e ORCID_CLIENT_ID=your-client-id \
  -e ORCID_CLIENT_SECRET=your-client-secret
```

## Usage examples

Once connected, you can ask Claude things like:

- "Search ORCID for researchers at Northwestern University working on machine learning"
- "Look up the ORCID profile for 0000-0002-1825-0097"
- "Get the publications for this researcher and export them as RIS for Zotero"

## License

MIT

<!-- mcp-name: io.github.SMABoundless/orcid -->
