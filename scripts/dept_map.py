"""Map every free-text department label used across the 3 library files to one of the
20 standard department codes in data/library/DEPARTMENTS.csv."""

DEPT_MAP = {
    'Secretariat': 'CS', 'Secretarial': 'CS',
    'Legal': 'LEGAL',
    'Tax': 'TAX',
    'HR': 'HR',
    'Finance': 'FIN',
    'Environment': 'EHS', 'EHS': 'EHS',
    'IT/Data': 'ITSEC', 'IT/InfoSec': 'ITSEC',
    'Quality/Regulatory': 'QA',
    'Operations': 'OPS',
    'Security': 'SEC',
    'Compliance': 'RISK',
    'Risk': 'RISK', 'Credit Risk': 'CRED',
    'Audit': 'AUDIT',
    'Treasury': 'TRSY', 'Forex': 'TREAS',
    'Customer Service': 'CUST',
    'Priority Sector': 'RISK',
    'Actuarial': 'ACT',
}


def to_code(raw):
    return DEPT_MAP.get(raw.strip(), 'OPS')
