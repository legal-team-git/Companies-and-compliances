import csv
R = 'data/'
SEC_MAP = {
    'Capital Goods': 'Capital Goods & Engineering', 'Chemicals': 'Chemicals & Fertilisers', 'Healthcare': 'Healthcare',
    'Fast Moving Consumer Goods': 'FMCG', 'Information Technology': 'IT/ITeS', 'Automobile and Auto Components': 'Automobile',
    'Consumer Durables': 'Consumer Durables & Appliances', 'Consumer Services': 'Hospitality & Tourism', 'Services': 'Consulting & Professional Services',
    'Textiles': 'Textiles & Apparel', 'Construction': 'Construction & Infrastructure', 'Realty': 'Real Estate',
    'Oil, Gas & Consumable Fuels': 'Oil & Gas', 'Metals & Mining': 'Metals & Steel', 'Construction Materials': 'Cement & Building Materials',
    'Media, Entertainment & Publication': 'Media & Entertainment', 'Power': 'Power', 'Telecommunication': 'Telecom',
    'Forest Materials': 'Paper, Packaging & Printing', 'Utilities': 'Water, Waste Management & Environmental Services',
    'Diversified': 'Diversified Conglomerates/Holding Companies', 'Financial Services': None,  # split below
}
INDUSTRY_FIN = {
    'Banks': ('Banking', ''), 'Finance': ('NBFC', 'NBFC'), 'Insurance': ('Insurance', ''),
    'Financial Technology (Fintech)': ('Payments & Fintech', 'DIGITAL_LENDING,PAY_PA'),
    'Capital Markets': ('Securities/Capital Markets', 'SEC_BROKER'), 'Investment Company': ('Securities/Capital Markets', 'SEC_AMC'),
    'Holding Company': ('Diversified Conglomerates/Holding Companies', ''),
}
FIN_INDUSTRY_TAGS = {
    'Public Banks': 'BANK_COMM', 'Private Banks': 'BANK_COMM', 'Housing Finance Company': 'HFC',
    'Non Banking Financial Company (NBFC)': 'NBFC', 'Microfinance Institutions': 'MFI', 'Asset Management Company': 'SEC_AMC',
    'Stock/ Commodity Brokers & related Services': 'SEC_BROKER', 'Depositories/ Custodian Services': 'SEC_DP',
    'Financial Technology (Fintech)': 'DIGITAL_LENDING', 'Specialized Finance': 'NBFC', 'Diversified Financials': 'NBFC',
    'Multi-Sector Holding Companies': '', 'Other Insurance': 'INS_GEN', 'General Insurance': 'INS_GEN', 'Life Insurance': 'INS_LIFE',
    'Investment Banking & Brokerage Services': 'SEC_MB', 'Financial Products Distributor': 'SEC_IA', 'Stockbroking & Allied': 'SEC_BROKER',
    'Exchange & Data Platform Services': 'SEC_MII',
}

def classify(broad, sector, bindus, indus):
    if sector == 'Financial Services' or broad == 'Financial Services':
        canon = 'Banking' if 'Bank' in indus else ('NBFC' if 'Finance' in indus or 'NBFC' in indus else
                 'Insurance' if 'Insurance' in indus else 'Securities/Capital Markets' if any(k in indus for k in ('Broker', 'Exchange', 'Depositor', 'Asset Management', 'Capital')) else 'NBFC')
        tag = FIN_INDUSTRY_TAGS.get(indus, '')
        return canon, tag
    return SEC_MAP.get(sector, 'Unclassified') or 'Unclassified', ''


if __name__ == '__main__':
    rows = list(csv.DictReader(open(R + 'official/screener_classification.csv', encoding='utf-8')))
    out = {}
    for r in rows:
        if r['status'] != 'ok':
            continue
        canon, tag = classify(r['broad_sector'], r['sector'], r['broad_industry'], r['industry'])
        out[r['symbol']] = (canon, r['industry'], tag)
    print('mapped', len(out))
    w = csv.writer(open(R + 'work/screener_sector_map.csv', 'w', newline='', encoding='utf-8'))
    w.writerow(['symbol', 'canonical_sector', 'sub_sector', 'fin_tag'])
    for k, v in out.items():
        w.writerow([k, v[0], v[1], v[2]])
