import csv
R = 'data/'

# industry -> (canonical_sector, fin_tag)   [priority over broad sector map]
INDUSTRY_MAP = {
    'Aerospace & Defense': ('Defence & Aerospace', ''), 'Ship Building & Allied Services': ('Defence & Aerospace', ''),
    'Explosives': ('Chemicals & Fertilisers', ''),
    'Pharmaceuticals': ('Pharma', ''), 'Biotechnology': ('Biotechnology & Life Sciences', ''), 'Pharmacy Retail': ('Retail', ''),
    'Medical Equipment & Supplies': ('Medical Devices', ''), 'Healthcare Service Provider': ('Healthcare', ''),
    'Hospital': ('Healthcare', ''), 'Healthcare Research, Analytics & Technology': ('Healthcare', ''), 'Wellness': ('Healthcare', ''),
    'Public Sector Bank': ('Banking', 'BANK_COMM'), 'Private Sector Bank': ('Banking', 'BANK_COMM'), 'Other Bank': ('Banking', 'BANK_COMM'),
    'Financial Institution': ('NBFC', 'NBFC'), 'Housing Finance Company': ('NBFC', 'HFC'), 'Non Banking Financial Company (NBFC)': ('NBFC', 'NBFC'),
    'Microfinance Institutions': ('NBFC', 'MFI'), 'Financial Technology (Fintech)': ('Payments & Fintech', 'DIGITAL_LENDING'),
    'Financial Products Distributor': ('Securities/Capital Markets', 'SEC_IA'), 'Other Financial Services': ('NBFC', 'NBFC'),
    'Investment Company': ('Securities/Capital Markets', 'SEC_AMC'), 'Asset Management Company': ('Securities/Capital Markets', 'SEC_AMC'),
    'Stockbroking & Allied': ('Securities/Capital Markets', 'SEC_BROKER'), 'Depositories, Clearing Houses and Other Intermediaries': ('Securities/Capital Markets', 'SEC_DP'),
    'Exchange and Data Platform': ('Securities/Capital Markets', 'SEC_MII'), 'Ratings': ('Securities/Capital Markets', 'SEC_CRA'),
    'Insurance Distributors': ('Insurance', 'INS_BROKER'), 'General Insurance': ('Insurance', 'INS_GEN'), 'Life Insurance': ('Insurance', 'INS_LIFE'),
    'Holding Company': ('Diversified Conglomerates/Holding Companies', ''),
    'Computers - Software & Consulting': ('IT/ITeS', ''), 'IT Enabled Services': ('IT/ITeS', ''), 'Software Products': ('IT/ITeS', ''),
    'Business Process Outsourcing (BPO)/ Knowledge Process Outsourcing (KPO)': ('IT/ITeS', ''), 'Computers Hardware & Equipments': ('Electronics & Semiconductors', ''),
    'Consumer Electronics': ('Consumer Durables & Appliances', ''),
    'Telecom - Cellular & Fixed line services': ('Telecom', ''), 'Telecom - Infrastructure': ('Telecom', ''),
    'Telecom -  Equipment & Accessories': ('Telecom', ''), 'Other Telecom Services': ('Telecom', ''),
    'Cement & Cement Products': ('Cement & Building Materials', ''), 'Other Construction Materials': ('Cement & Building Materials', ''),
    'Ceramics': ('Cement & Building Materials', ''), 'Granites & Marbles': ('Cement & Building Materials', ''), 'Sanitary Ware': ('Cement & Building Materials', ''),
    'Civil Construction': ('Construction & Infrastructure', ''), 'Residential, Commercial Projects': ('Real Estate', ''),
    'Real Estate related services': ('Real Estate', ''), 'Road AssetsToll, Annuity, Hybrid-Annuity': ('Roads & Highways', ''),
    'Iron & Steel': ('Metals & Steel', ''), 'Iron & Steel Products': ('Metals & Steel', ''), 'Pig Iron': ('Metals & Steel', ''),
    'Sponge Iron': ('Metals & Steel', ''), 'Ferro & Silica Manganese': ('Metals & Steel', ''), 'Aluminium': ('Metals & Steel', ''),
    'Aluminium, Copper & Zinc Products': ('Metals & Steel', ''), 'Copper': ('Metals & Steel', ''), 'Zinc': ('Metals & Steel', ''),
    'Diversified Metals': ('Metals & Steel', ''), 'Precious Metals': ('Metals & Steel', ''), 'Castings & Forgings': ('Metals & Steel', ''),
    'Electrodes & Refractories': ('Metals & Steel', ''), 'Coal': ('Coal & Mining', ''), 'Industrial Minerals': ('Coal & Mining', ''),
    'Trading - Coal': ('Coal & Mining', ''), 'Trading - Minerals': ('Coal & Mining', ''), 'Trading - Metals': ('Metals & Steel', ''),
    'Commodity Chemicals': ('Chemicals & Fertilisers', ''), 'Specialty Chemicals': ('Chemicals & Fertilisers', ''), 'Dyes And Pigments': ('Chemicals & Fertilisers', ''),
    'Fertilizers': ('Chemicals & Fertilisers', ''), 'Pesticides & Agrochemicals': ('Chemicals & Fertilisers', ''), 'Petrochemicals': ('Chemicals & Fertilisers', ''),
    'Industrial Gases': ('Chemicals & Fertilisers', ''), 'Printing Inks': ('Chemicals & Fertilisers', ''), 'Carbon Black': ('Chemicals & Fertilisers', ''),
    'Paints': ('Chemicals & Fertilisers', ''), 'Trading - Chemicals': ('Chemicals & Fertilisers', ''),
    'Refineries & Marketing': ('Oil & Gas', ''), 'Oil Exploration & Production': ('Oil & Gas', ''), 'Oil Equipment & Services': ('Oil & Gas', ''),
    'Offshore Support Solution Drilling': ('Oil & Gas', ''), 'Gas Transmission/Marketing': ('Oil & Gas', ''), 'LPG/CNG/PNG/LNG Supplier': ('Oil & Gas', ''),
    'Oil Storage & Transportation': ('Oil & Gas', ''), 'Lubricants': ('Oil & Gas', ''), 'Trading - Gas': ('Oil & Gas', ''),
    'Power Generation': ('Power', ''), 'Power - Transmission': ('Power', ''), 'Power Distribution': ('Power', ''), 'Power Trading': ('Power', ''),
    'Integrated Power Utilities': ('Power', ''), 'Heavy Electrical Equipment': ('Capital Goods & Engineering', ''), 'Other Electrical Equipment': ('Capital Goods & Engineering', ''),
    'Cables - Electricals': ('Capital Goods & Engineering', ''), 'Compressors, Pumps & Diesel Engines': ('Capital Goods & Engineering', ''),
    'Industrial Products': ('Capital Goods & Engineering', ''), 'Other Industrial Products': ('Capital Goods & Engineering', ''),
    'Abrasives & Bearings': ('Capital Goods & Engineering', ''), 'Plastic Products - Industrial': ('Chemicals & Fertilisers', ''),
    'Plastic Products - Consumer': ('Consumer Durables & Appliances', ''),
    '2/3 Wheelers': ('Automobile', ''), 'Commercial Vehicles': ('Automobile', ''), 'Passenger Cars & Utility Vehicles': ('Automobile', ''),
    'Auto Components & Equipments': ('Automobile', ''), 'Construction Vehicles': ('Automobile', ''), 'Tractors': ('Automobile', ''),
    'Auto Dealer': ('Automobile', ''), 'Cycles': ('Automobile', ''), 'Tyres & Rubber Products': ('Automobile', ''), 'Rubber': ('Automobile', ''),
    'Dealers-Commercial Vehicles, Tractors, Construction Vehicles': ('Automobile', ''), 'Railway Wagons': ('Railways', ''),
    'Trading - Auto components': ('Automobile', ''),
    'Diversified FMCG': ('FMCG', ''), 'Packaged Foods': ('Food Processing & Beverages', ''), 'Breweries & Distilleries': ('Food Processing & Beverages', ''),
    'Cigarettes & Tobacco Products': ('FMCG', ''), 'Edible Oil': ('Food Processing & Beverages', ''), 'Dairy Products': ('Fisheries, Dairy & Animal Husbandry', ''),
    'Animal Feed': ('Agriculture', ''), 'Tea & Coffee': ('Agriculture', ''), 'Sugar': ('Food Processing & Beverages', ''), 'Meat Products including Poultry': ('Food Processing & Beverages', ''),
    'Seafood': ('Fisheries, Dairy & Animal Husbandry', ''), 'Other Food Products': ('Food Processing & Beverages', ''), 'Other Beverages': ('Food Processing & Beverages', ''),
    'Other Agricultural Products': ('Agriculture', ''), 'Personal Care': ('FMCG', ''), 'Household Products': ('FMCG', ''), 'Houseware': ('Consumer Durables & Appliances', ''),
    'Household Appliances': ('Consumer Durables & Appliances', ''), 'Furniture, Home Furnishing': ('Consumer Durables & Appliances', ''), 'Stationary': ('Paper, Packaging & Printing', ''),
    'Garments & Apparels': ('Textiles & Apparel', ''), 'Other Textile Products': ('Textiles & Apparel', ''), 'Jute & Jute Products': ('Textiles & Apparel', ''),
    'Footwear': ('Leather & Footwear', ''), 'Leather And Leather Products': ('Leather & Footwear', ''), 'Trading - Textile Products': ('Textiles & Apparel', ''),
    'Gems, Jewellery And Watches': ('Gems & Jewellery', ''), 'Paper & Paper Products': ('Paper, Packaging & Printing', ''), 'Packaging': ('Paper, Packaging & Printing', ''),
    'Forest Products': ('Paper, Packaging & Printing', ''), 'Plywood Boards/ Laminates': ('Paper, Packaging & Printing', ''), 'Printing & Publication': ('Paper, Packaging & Printing', ''),
    'Glass - Consumer': ('Consumer Durables & Appliances', ''), 'Glass - Industrial': ('Capital Goods & Engineering', ''),
    'Hotels & Resorts': ('Hospitality & Tourism', ''), 'Restaurants': ('Hospitality & Tourism', ''), 'Tour, Travel Related Services': ('Hospitality & Tourism', ''),
    'Amusement Parks/ Other Recreation': ('Hospitality & Tourism', ''), 'Airline': ('Aviation', ''), 'Airport & Airport services': ('Aviation', ''),
    'Port & Port services': ('Shipping/Ports', ''), 'Shipping': ('Shipping/Ports', ''), 'Dredging': ('Shipping/Ports', ''),
    'Logistics Solution Provider': ('Logistics & Warehousing', ''), 'Road Transport': ('Logistics & Warehousing', ''), 'Transport Related Services': ('Logistics & Warehousing', ''),
    'E-Retail/ E-Commerce': ('E-commerce', ''), 'Internet & Catalogue Retail': ('E-commerce', ''), 'Diversified Retail': ('Retail', ''),
    'Speciality Retail': ('Retail', ''), 'Trading & Distributors': ('Import/Export Trading & SEZ/EOU', ''), 'Distributors': ('Import/Export Trading & SEZ/EOU', ''),
    'Media & Entertainment': ('Media & Entertainment', ''), 'TV Broadcasting & Software Production': ('Media & Entertainment', ''),
    'Print Media': ('Media & Entertainment', ''), 'Electronic Media': ('Media & Entertainment', ''), 'Advertising & Media Agencies': ('Media & Entertainment', ''),
    'Film Production, Distribution & Exhibition': ('Media & Entertainment', ''), 'Digital Entertainment': ('Media & Entertainment', ''),
    'Web based media and service': ('Media & Entertainment', ''), 'Education': ('Education', ''), 'E-Learning': ('Education', ''),
    'Consulting Services': ('Consulting & Professional Services', ''), 'Diversified Commercial Services': ('Consulting & Professional Services', ''),
    'Diversified': ('Diversified Conglomerates/Holding Companies', ''), 'Waste Management': ('Water, Waste Management & Environmental Services', ''),
    'Water Supply & Management': ('Water, Waste Management & Environmental Services', ''),
}

SEC_MAP = {
    'Capital Goods': 'Capital Goods & Engineering', 'Chemicals': 'Chemicals & Fertilisers', 'Healthcare': 'Healthcare',
    'Fast Moving Consumer Goods': 'FMCG', 'Information Technology': 'IT/ITeS', 'Automobile and Auto Components': 'Automobile',
    'Consumer Durables': 'Consumer Durables & Appliances', 'Consumer Services': 'Hospitality & Tourism', 'Services': 'Consulting & Professional Services',
    'Textiles': 'Textiles & Apparel', 'Construction': 'Construction & Infrastructure', 'Realty': 'Real Estate',
    'Oil, Gas & Consumable Fuels': 'Oil & Gas', 'Metals & Mining': 'Metals & Steel', 'Construction Materials': 'Cement & Building Materials',
    'Media, Entertainment & Publication': 'Media & Entertainment', 'Power': 'Power', 'Telecommunication': 'Telecom',
    'Forest Materials': 'Paper, Packaging & Printing', 'Utilities': 'Water, Waste Management & Environmental Services',
    'Diversified': 'Diversified Conglomerates/Holding Companies', 'Financial Services': 'NBFC',
}


def classify(broad, sector, bindus, indus):
    if indus in INDUSTRY_MAP:
        return INDUSTRY_MAP[indus]
    if sector in SEC_MAP:
        return SEC_MAP[sector], ''
    return 'Unclassified', ''


if __name__ == '__main__':
    rows = list(csv.DictReader(open(R + 'official/screener_classification.csv', encoding='utf-8')))
    out = {}
    unmapped = set()
    for r in rows:
        if r['status'] != 'ok':
            continue
        canon, tag = classify(r['broad_sector'], r['sector'], r['broad_industry'], r['industry'])
        if canon == 'Unclassified':
            unmapped.add(r['industry'])
        out[r['symbol']] = (canon, r['industry'], tag)
    print('mapped', len(out), 'unmapped industries:', unmapped)
    w = csv.writer(open(R + 'work/screener_sector_map.csv', 'w', newline='', encoding='utf-8'))
    w.writerow(['symbol', 'canonical_sector', 'sub_sector', 'fin_tag'])
    for k, v in out.items():
        w.writerow([k, v[0], v[1], v[2]])
