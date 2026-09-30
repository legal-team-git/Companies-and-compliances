# Shared schema (all agents MUST follow)

## Company CSVs -> data/companies/<agent>.csv  (UTF-8, header row, quote all fields)
Columns: name,entity_type,ownership,state_region,sector,sub_sector,listing,ticker_or_cin,hq,verification,source_note
- entity_type: Public Limited | Private Limited | LLP | Partnership Firm | Proprietorship | OPC | Section 8 Company | Statutory Corporation | Cooperative Society | Trust/Society | Government Company (PSU) | Foreign Company Branch | Other
- ownership: Private (Indian) | MNC Subsidiary | Central PSU | State PSU | Joint Venture | Cooperative | Trust/Society
- state_region: "Pan-India" or specific state/UT names separated by "; " (official state/UT names)
- sector: one of the sector list in data/library/SECTORS.txt (created by library agent; if missing use your best plain name)
- listing: Listed-NSE | Listed-BSE | Listed-NSE+BSE | Unlisted | Delisted/Unknown
- ticker_or_cin: NSE/BSE symbol or CIN ONLY if you are confident; else blank. NEVER invent a CIN.
- verification: "Search-confirmed" (a WebSearch result confirmed existence + details) | "Knowledge-based" (from model knowledge, not re-checked) | "Needs manual check"
- source_note: short (e.g. URL domain or 'well-known listed co.')
RULES: no fabrication. Only include companies you are confident really exist. Target counts are CEILINGS, not quotas - fewer accurate rows beats padding. No duplicates within your file. Official sites (MCA, SEBI, NSE, IndiaCode, Wikipedia) are egress-blocked; use WebSearch only.
