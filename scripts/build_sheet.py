"""Build the single-sheet workbook: one row per company, compliances mapped by rules.
Inputs : data/unified_companies.csv, data/work/class_out_*.csv, data/work/nse_out_*.csv, data/library/*.csv
Output : India_Companies_Compliance_Master.xlsx + data/work/excluded_non_companies.csv + data/work/build_report.txt
"""
import csv, glob, re, collections, sys
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
R = 'data/'
csv.field_size_limit(10**8)

# ---------------- load ----------------
U = list(csv.DictReader(open(R + 'unified_companies.csv', encoding='utf-8')))


def _norm(n):
    n = n.lower(); n = re.sub(r'\(.*?\)', ' ', n); n = n.replace('&', ' and ')
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    n = re.sub(r'\b(limited|ltd|private|pvt|the|company|co|corporation|corp|india|of)\b', ' ', n)
    return re.sub(r'\s+', ' ', n).strip()


# Classification files are joined by NAME (not raw id) because unified_companies.csv IDs are
# reassigned on every rebuild (file set changes shift alphabetical ordering) - id-based lookup
# silently collides with unrelated companies across rebuilds. Each class_in/class_out pair is
# internally self-consistent (generated together), so join on id WITHIN a pair, then key the
# merged result by normalized company name for lookup against the current unified table.
CL_BY_NAME = {}
for out_f in sorted(glob.glob(R + 'work/class_out_*.csv')):
    in_f = out_f.replace('class_out_', 'class_in_')
    try:
        names_by_id = {r['id']: r['name'] for r in csv.DictReader(open(in_f, encoding='utf-8'))}
    except FileNotFoundError:
        continue
    for r in csv.DictReader(open(out_f, encoding='utf-8')):
        nm = names_by_id.get(r['id'])
        if nm:
            CL_BY_NAME[_norm(nm)] = r
CANON_SECTORS = {l.strip() for l in open(R + 'work/SECTOR_CANON.txt', encoding='utf-8') if l.strip()}
SC = {}
p = R + 'official/screener_classification.csv'
for r in csv.DictReader(open(p, encoding='utf-8')):
    if r['status'] == 'ok': SC[r['symbol']] = r
SCMAP = {}
try:
    for r in csv.DictReader(open(R + 'work/screener_sector_map.csv', encoding='utf-8')):
        SCMAP[r['symbol']] = r
except FileNotFoundError:
    pass

def lib(name):
    return list(csv.DictReader(open(R + f'library/{name}.csv', encoding='utf-8')))
CROSS, IND, FIN = lib('cross_sector'), lib('industrial'), lib('financial')

# tag descriptions for conditional notes
TAGDESC = {}
for l in open(R + 'library/TAGS.txt', encoding='utf-8'):
    m = re.match(r'([A-Z][A-Z0-9_ /]+?)\s{2,}(.+)', l.strip())
    if m:
        for t in re.split(r'\s*/\s*', m.group(1).strip()):
            TAGDESC[t.strip()] = m.group(2).strip()

DEPT = {'Legal': 'Legal & Regulatory', 'HR': 'HR', 'Finance': 'Finance & Accounts', 'Tax': 'Tax',
        'Secretariat': 'Company Secretarial', 'Secretarial': 'Company Secretarial', 'EHS': 'EHS & Environment',
        'Environment': 'EHS & Environment', 'IT/Data': 'IT & Information Security', 'IT/InfoSec': 'IT & Information Security',
        'Operations': 'Operations', 'Quality/Regulatory': 'Quality & Regulatory Affairs', 'Compliance': 'Risk & Compliance',
        'Risk': 'Risk & Compliance', 'Credit Risk': 'Risk & Compliance', 'Audit': 'Internal Audit', 'Treasury': 'Treasury & Forex',
        'Forex': 'Treasury & Forex', 'Customer Service': 'Customer Service', 'Security': 'Security',
        'Priority Sector': 'Risk & Compliance', 'Actuarial': 'Actuarial'}

# ---------------- sector helpers ----------------
MFG = {'Pharma', 'Biotechnology & Life Sciences', 'Medical Devices', 'Defence & Aerospace', 'Electronics & Semiconductors',
       'Chemicals & Fertilisers', 'Cement & Building Materials', 'Metals & Steel', 'Automobile', 'Textiles & Apparel',
       'Leather & Footwear', 'Gems & Jewellery', 'Paper, Packaging & Printing', 'Consumer Durables & Appliances',
       'Capital Goods & Engineering', 'FMCG', 'Food Processing & Beverages', 'Power', 'Renewable Energy', 'Oil & Gas',
       'Space & Satellite', 'Agriculture'}
POLLUTING = MFG | {'Coal & Mining', 'Water, Waste Management & Environmental Services', 'Hospitality & Tourism', 'Healthcare',
                   'Construction & Infrastructure', 'Real Estate', 'Shipping/Ports', 'Railways'}
SECTOR_ATTR = {
    'FACTORY': MFG, 'IMPORT_EXPORT': MFG | {'Retail', 'E-commerce', 'Import/Export Trading & SEZ/EOU', 'Logistics & Warehousing', 'Shipping/Ports'},
    'POLLUTING': POLLUTING, 'HAZ_WASTE': {'Pharma', 'Chemicals & Fertilisers', 'Metals & Steel', 'Oil & Gas', 'Healthcare',
                                        'Electronics & Semiconductors', 'Automobile', 'Coal & Mining', 'Biotechnology & Life Sciences',
                                        'Water, Waste Management & Environmental Services', 'Defence & Aerospace'},
    'GST_ECOM': {'E-commerce'}, 'FOOD_BIZ': {'FMCG', 'Food Processing & Beverages', 'Hospitality & Tourism', 'Retail', 'E-commerce', 'Fisheries, Dairy & Animal Husbandry', 'Agriculture'},
    'PACKAGED_GOODS': {'FMCG', 'Food Processing & Beverages', 'Consumer Durables & Appliances', 'Pharma', 'Chemicals & Fertilisers', 'Textiles & Apparel', 'Retail', 'E-commerce'},
    'REAL_ESTATE_PROJECT': {'Real Estate'}, 'EWASTE': {'Electronics & Semiconductors', 'Consumer Durables & Appliances', 'IT/ITeS', 'Telecom', 'Automobile'},
    'PLASTIC_PACK': {'FMCG', 'Food Processing & Beverages', 'Consumer Durables & Appliances', 'Retail', 'E-commerce', 'Chemicals & Fertilisers', 'Pharma', 'Paper, Packaging & Printing'},
    'BATTERY': {'Automobile', 'Electronics & Semiconductors', 'Renewable Energy', 'Consumer Durables & Appliances'},
    'INTERMEDIARY': {'E-commerce', 'Media & Entertainment', 'IT/ITeS', 'Payments & Fintech', 'Gaming & Betting', 'Telecom', 'Data Centres & Cloud', 'Education'},
    'PMLA_REPORTING_ENTITY': {'Banking', 'Banking - Cooperative Banks', 'Banking - Regional Rural Banks', 'NBFC', 'Payments & Fintech',
                              'Insurance', 'Securities/Capital Markets', 'Asset Reconstruction & Financial Services',
                              'Real Estate', 'Gems & Jewellery', 'Gaming & Betting'},
    'FCRA': {'Section 8/NGO'},
    'HAS_DATA': set(), 'HAS_IT_SYSTEMS': set(), 'CHARITABLE': {'Section 8/NGO'},
}
ALL_DATA_SECTORS_EXCLUDED = set()  # HAS_DATA / HAS_IT_SYSTEMS true for every company (any organisation holds personal data)
SIZE_SOFT_TRUE_IF_BIG = {'EMP_ANY', 'EMP10', 'EMP20', 'EMP50', 'EMP100', 'GST_REG', 'TDS_DEDUCTOR', 'TURNOVER_GST_THRESHOLD',
                         'AUDIT_APPLICABLE', 'AATO_5CR', 'AATO_10CR', 'TCS_COLLECTOR'}  # only TDS/GST/EMP true for listed & PSU
BIG_TRUE = {'EMP_ANY', 'EMP10', 'EMP20', 'EMP50', 'EMP100', 'GST_REG', 'TDS_DEDUCTOR', 'TURNOVER_GST_THRESHOLD', 'AUDIT_APPLICABLE', 'AATO_5CR', 'AATO_10CR'}
EMP_ANY_FORMS = {'EMP_ANY', 'TDS_DEDUCTOR'}  # any operating company employs / deducts TDS
HARD = {'COMPANY', 'PUBLIC_CO', 'PRIVATE_CO', 'OPC', 'LLP', 'SEC8', 'PARTNERSHIP', 'TRUST_SOCIETY', 'COOP', 'FOREIGN_CO',
        'LISTED', 'GOVT_CO', 'PSU', 'MNC', 'NBFC_ENTITY'}

IND_SECTORS = {
    'DEF': {'Defence & Aerospace', 'Space & Satellite'}, 'PHA': {'Pharma', 'Biotechnology & Life Sciences'},
    'PWR': {'Power', 'Renewable Energy'}, 'PRO': {'Legal Services', 'Consulting & Professional Services'},
    'NGO': {'Section 8/NGO'}, 'AVN': {'Aviation'}, 'SHP': {'Shipping/Ports'}, 'CHM': {'Chemicals & Fertilisers'},
    'MIN': {'Coal & Mining', 'Metals & Steel'}, 'HSP': {'Healthcare'}, 'AGR': {'Agriculture', 'Fisheries, Dairy & Animal Husbandry'},
    'TEL': {'Telecom', 'Data Centres & Cloud'}, 'OG': {'Oil & Gas'}, 'FDA': {'Food Processing & Beverages', 'FMCG', 'Hospitality & Tourism', 'Fisheries, Dairy & Animal Husbandry'},
    'EPR': {'FMCG', 'Consumer Durables & Appliances', 'Electronics & Semiconductors', 'Automobile', 'Chemicals & Fertilisers', 'Food Processing & Beverages',
            'Paper, Packaging & Printing', 'Retail', 'E-commerce', 'Pharma', 'Textiles & Apparel', 'Capital Goods & Engineering'},
    'MED': {'Media & Entertainment', 'Gaming & Betting'}, 'AUT': {'Automobile'}, 'RE': {'Real Estate'}, 'EDU': {'Education'},
    'HOS': {'Hospitality & Tourism'}, 'MDV': {'Medical Devices'}, 'CON': {'Construction & Infrastructure', 'Roads & Highways', 'Real Estate'},
    'RET': {'Retail', 'E-commerce'}, 'COP': {'Cooperative'}, 'LOG': {'Logistics & Warehousing'}, 'STL': {'Metals & Steel'},
    'TXT': {'Textiles & Apparel', 'Leather & Footwear'}, 'SPT': {'Sports'}, 'RLY': {'Railways'}, 'FMC': {'FMCG', 'Consumer Durables & Appliances'},
}
FIN_SECTORS = {'Banking', 'Banking - Cooperative Banks', 'Banking - Regional Rural Banks', 'NBFC', 'Payments & Fintech', 'Insurance',
               'Securities/Capital Markets', 'Asset Reconstruction & Financial Services'}
SECTOR_TAGS = {'SECTOR:HEALTHCARE': {'Healthcare'}, 'SECTOR:TELECOM': {'Telecom'}, 'SECTOR:BANKING': {'Banking', 'Banking - Cooperative Banks', 'Banking - Regional Rural Banks'},
               'SECTOR:POWER': {'Power', 'Renewable Energy'}}


def entity_tags(e, sector):
    et, ow, listed = e['entity_type'], e['ownership'], e['listing'].startswith('Listed')
    t = {'ALL'}
    if et in ('Public Limited', 'Private Limited', 'Government Company (PSU)', 'Section 8 Company', 'OPC'): t.add('COMPANY')
    if et == 'Public Limited' or (et == 'Government Company (PSU)' and listed) or listed: t.add('PUBLIC_CO')
    if et == 'Private Limited': t.add('PRIVATE_CO')
    if et == 'OPC': t.add('OPC')
    if et == 'LLP': t.add('LLP')
    if et == 'Section 8 Company': t.add('SEC8')
    if et in ('Partnership Firm', 'Proprietorship'): t.add('PARTNERSHIP')
    if et == 'Trust/Society' or (ow == 'Trust/Society'): t.add('TRUST_SOCIETY')
    if et == 'Cooperative Society' or ow == 'Cooperative': t.add('COOP')
    if et == 'Foreign Company Branch': t.add('FOREIGN_CO')
    if listed: t.add('LISTED')
    if ow in ('Central PSU', 'State PSU') or et == 'Government Company (PSU)': t.add('PSU'); t.add('GOVT_CO') if 'COMPANY' in t else None
    if ow == 'MNC Subsidiary' or et == 'Foreign Company Branch': t.add('MNC'); t.add('FOREIGN_INVESTMENT')
    if ow == 'Joint Venture': t.add('FOREIGN_INVESTMENT') if False else None
    return t


def eval_tags(expr, defin, sector, big):
    """returns ('yes'|'cond'|'no', [unresolved tag names])"""
    best = ('no', [])
    for term in expr.split('|'):
        tags = [x.strip() for x in term.split('&') if x.strip()]
        unresolved, ok = [], True
        for tg in tags:
            if tg in SECTOR_TAGS:
                if sector not in SECTOR_TAGS[tg]: ok = False; break
                continue
            if tg in HARD or tg == 'ALL':
                if tg not in defin: ok = False; break
                continue
            if tg in SECTOR_ATTR and SECTOR_ATTR[tg]:
                if sector in SECTOR_ATTR[tg]: continue
                if tg in ('FACTORY', 'GST_ECOM', 'FOOD_BIZ', 'REAL_ESTATE_PROJECT', 'CHARITABLE', 'PACKAGED_GOODS', 'EWASTE',
                          'PLASTIC_PACK', 'BATTERY', 'INTERMEDIARY', 'HAZ_WASTE', 'POLLUTING', 'PMLA_REPORTING_ENTITY', 'FCRA'):
                    ok = False; break  # sector/entity type says this does not apply - hard exclude, not merely conditional
                unresolved.append(tg); continue
            if tg in ('HAS_DATA', 'HAS_IT_SYSTEMS', 'EMPLOYS_WOMEN'): continue
            if tg in BIG_TRUE and big: continue
            if tg in EMP_ANY_FORMS and ('COMPANY' in defin or 'LLP' in defin): continue
            unresolved.append(tg)
        if not ok: continue
        if not unresolved: return ('yes', [])
        best = ('cond', unresolved)
    return best


def ndept(d):
    return DEPT.get(d.strip(), d.strip())


def build():
    rows_out, excluded, rep = [], [], collections.Counter()
    for e in U:
        c = CL_BY_NAME.get(_norm(e['name']), {})
        if c.get('is_company', 'Y') == 'N':
            excluded.append(e); continue
        sc = SC.get(e['ticker']) if e['ticker'] else None
        sector = (c.get('canonical_sector') or '').strip()
        fin = {x.strip() for x in (c.get('fin_tags') or '').split(',') if x.strip()}
        if not sector and e['ticker'] in SCMAP:
            sm = SCMAP[e['ticker']]
            sector = sm['canonical_sector']
            if not e['sub_sector_raw']: e['sub_sector_raw'] = sm['sub_sector']
            if sm['fin_tag']: fin.add(sm['fin_tag'])
        if not sector:
            sr = re.sub(r'\s*\(.*$', '', e['sector_raw']).strip()
            if sr in CANON_SECTORS: sector = sr
        sector = sector or 'Unclassified'
        if c.get('ownership'): e['ownership'] = c['ownership']
        state = (c.get('hq_state') or '').strip()
        defin = entity_tags(e, sector)
        big = ('LISTED' in defin) or ('PSU' in defin)
        items = []
        # 1. cross-sector
        for r in sorted(CROSS, key=lambda x: x['comp_id']):
            st, unr = eval_tags(r['applies_when'], defin, sector, big)
            if st != 'no': items.append((r, st, unr, 'Cross-sector'))
        # 2. sector-specific (industrial)
        for r in sorted(IND, key=lambda x: x['comp_id']):
            m = re.match(r'IND-([A-Z]+)-', r['comp_id'])
            code = m.group(1) if m else ''
            if sector in IND_SECTORS.get(code, set()):
                if code == 'NGO' and not ({'SEC8', 'TRUST_SOCIETY'} & defin): continue
                if code == 'COP' and 'COOP' not in defin: continue
                items.append((r, 'cond' if r['applies_when'] else 'yes', [r['applies_when']] if r['applies_when'] else [], 'Sector-specific'))
        # 3. financial
        if fin:
            for r in sorted(FIN, key=lambda x: x['comp_id']):
                tags = {x.strip() for x in re.split(r'[,&|]', r['applies_when']) if x.strip()}
                if tags & fin or ('LISTED' in tags and 'LISTED' in defin and tags <= {'LISTED', 'PUBLIC_CO', 'ALL'}) or 'ALL' in tags:
                    items.append((r, 'yes', [], 'Financial-sector'))
        # dedupe by name
        seen, fin_items = set(), []
        for it in items:
            k = it[0]['compliance_name'].strip().lower()
            if k in seen: continue
            seen.add(k); fin_items.append(it)
        rows_out.append((e, c, sector, state, fin_items, defin))
        rep[sector] += 1
    return rows_out, excluded, rep


def fmt(rows_out):
    wb = Workbook(); ws = wb.active; ws.title = 'Companies x Compliances'
    hdr = ['Sr. No.', 'Company Name', 'Company Type (Legal Form)', 'Ownership Type', 'Listing Status', 'NSE Ticker', 'ISIN', 'Sector',
           'Sub-Sector / Industry', 'State / Region of Operation', 'Head Office (HQ)', 'Departments Involved', 'Total Compliances',
           'Compliances Applicable (numbered)', 'Compliance Types (numbers refer to list)', 'Regulatory Authorities',
           'Acts, Rules & Regulations', 'Forms / Returns / Filings', 'Applicability Notes']
    ws.append(hdr)
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF'); cell.fill = PatternFill('solid', fgColor='1F3864')
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    maxlen = 0
    for i, (e, c, sector, state, items, defin) in enumerate(rows_out, 1):
        lines, types, depts, auth, acts, forms = [], collections.defaultdict(list), collections.Counter(), collections.OrderedDict(), collections.OrderedDict(), collections.OrderedDict()
        for n, (r, st, unr, src) in enumerate(items, 1):
            line = f"{n}. {r['compliance_name'].strip()}"
            if st == 'cond':
                cond = '; '.join(TAGDESC.get(u, u) for u in unr)[:160]
                line += f" [Conditional: {cond}]" if cond else ' [Conditional]'
            lines.append(line)
            types[r['compliance_type'].strip()].append(n)
            depts[ndept(r['department'])] += 1
            if r['regulatory_authority'].strip(): auth[r['regulatory_authority'].strip()] = 1
            for a in re.split(r';\s*', r['acts_rules']):
                a = a.strip()
                if a: acts[a.lower()] = a
            fm = r['form_or_filing'].strip()
            if fm: forms[fm.lower()] = fm
        comp_txt = '\n'.join(lines)
        if len(comp_txt) > 32000:
            cut = comp_txt[:31900].rsplit('\n', 1)[0]; comp_txt = cut + f"\n... (+{len(lines) - cut.count(chr(10)) - 1} more, see library files)"
        def cap(s): return s if len(s) <= 32000 else s[:31900].rsplit('\n', 1)[0] + '\n...'
        types_txt = '\n'.join(f"{t} ({len(v)}): #{', #'.join(map(str, v))}" for t, v in sorted(types.items()))
        dept_txt = '; '.join(f"{d} ({n})" for d, n in sorted(depts.items(), key=lambda x: -x[1]))
        sc = SC.get(e['ticker']) if e['ticker'] else None
        subsector = e['sub_sector_raw'] or (sc['industry'] if sc else '')
        reg = e['state_region'].strip()
        if not reg or reg == 'Pan-India': reg_txt = 'Pan-India' + (f" (HQ state: {state})" if state else '')
        else: reg_txt = reg
        if not reg and not state: reg_txt = 'Not determined'
        notes = []
        if sector == 'Unclassified': notes.append('Sector not classified: only cross-sector compliances listed')
        if any(st == 'cond' for _, st, _, _ in items): notes.append('Items marked [Conditional] depend on size/activity thresholds not known for this entity')
        notes.append('State-specific laws (Shops & Establishments, Professional Tax, LWF, Fire, Trade Licence) apply per the operating state(s)')
        if c.get('note'): notes.append(c['note'])
        ws.append([i, e['name'], e['entity_type'], e['ownership'], e['listing'], e['ticker'] if e['listing'].startswith('Listed') else '', e['isin'], sector, subsector, reg_txt, e['hq'] or state, dept_txt, len(items), comp_txt, cap(types_txt), cap('\n'.join(f"{k}. {v}" for k, v in enumerate(auth, 1))), cap('\n'.join(f"{k}. {v}" for k, v in enumerate(acts.values(), 1))), cap('\n'.join(forms.values())), '; '.join(notes)])
        maxlen = max(maxlen, len(comp_txt))
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
    for col, w in zip('ABCDEFGHIJKLMNOPQRS', [7, 38, 22, 18, 16, 12, 15, 26, 28, 26, 22, 40, 11, 80, 45, 45, 60, 50, 50]):
        ws.column_dimensions[col].width = w
    wb.save('India_Companies_Compliance_Master.xlsx')
    return maxlen


if __name__ == '__main__':
    rows_out, excluded, rep = build()
    ml = fmt(rows_out)
    w = csv.DictWriter(open(R + 'work/excluded_non_companies.csv', 'w', newline='', encoding='utf-8'), fieldnames=list(U[0].keys()), quoting=csv.QUOTE_ALL)
    w.writeheader(); w.writerows(excluded)
    tot = [len(x[4]) for x in rows_out]
    print('rows', len(rows_out), 'excluded', len(excluded), 'max compliance-cell chars', ml, 'avg items', sum(tot) // max(1, len(tot)))
    print(rep.most_common(70))
