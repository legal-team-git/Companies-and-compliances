"""Rule-based Severity classifier (High / Medium / Low) for compliance library rows.

Transparent, deterministic heuristic - NOT a per-row researched fact (no source
citation is claimed). Based on: (1) keyword scan of compliance_name/description/
acts_rules for consequences known to be severe (imprisonment, prosecution,
licence cancellation/suspension, debarment, business-stopping default) or known
to be minor (register maintenance, display, procedural notices); (2) fallback by
compliance_type when no keyword matches.

Documented so the basis for every classification is inspectable, not a black box.
"""
import re

HIGH_KEYWORDS = [
    'imprisonment', 'prosecution', 'criminal', 'debarment', 'disqualif',
    'cancellation of licence', 'cancellation of registration', 'suspension of licence',
    'revocation of licence', 'revocation of registration', 'money laundering', 'pmla',
    'customer kyc', 'customer due diligence', 'capital adequacy', 'solvency',
    'crr maintenance', 'slr maintenance',
    'fraud', 'explosives', 'arms act', 'defence industrial licence', 'scomet',
    'drug licence', 'drug manufacturing licence', 'banking licence', 'insurance licence',
    'consent to operate', 'consent to establish', 'hazardous waste', 'fire noc',
    'fire safety', 'factory licence', 'mining lease', 'pollution control',
    'posh', 'sexual harassment', 'child labour', 'bonded labour', 'human trafficking',
    'aml', 'anti-money laundering', 'sanctions', 'export control',
]
LOW_KEYWORDS = [
    'register maintenance', 'maintain register', 'maintain a register', 'notice board',
    'display of', 'signage', 'statutory register', 'minutes book', 'attendance register',
    'record maintenance', 'maintain records', 'internal register', 'update register',
]

# Default severity by compliance_type when no keyword overrides it.
TYPE_DEFAULT = {
    'One-Time/Registration': 'Medium',
    'Licence-Renewal': 'High',
    'Recurring-Monthly': 'Medium',
    'Recurring-Quarterly': 'Medium',
    'Recurring-Annual': 'Medium',
    'Event-Based': 'Medium',
    'Continuous/Ongoing': 'Medium',
}

FILL = {'High': 'FFC7CE', 'Medium': 'FFEB9C', 'Low': 'C6EFCE'}  # red / amber / green tints
FONT = {'High': '9C0006', 'Medium': '9C6500', 'Low': '006100'}


def classify(row):
    text = ' '.join([row.get('compliance_name', ''), row.get('description', ''),
                      row.get('acts_rules', ''), row.get('form_or_filing', '')]).lower()
    for kw in HIGH_KEYWORDS:
        if kw in text:
            return 'High'
    for kw in LOW_KEYWORDS:
        if kw in text:
            return 'Low'
    return TYPE_DEFAULT.get(row.get('compliance_type', '').strip(), 'Medium')
