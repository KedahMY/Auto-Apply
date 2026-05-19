"""
All HKUST job board filter options, scraped from the live site.
Each dict maps display label → URL param value.
URL params: BN[], JN[], EMT[], WL[], awards[], EM[], L[]
Checkboxes: TEC=1, AJOB=1, NCHI=1
"""

BUSINESS_NATURE = {
    "Accounting": "1",
    "Advertising / Marketing / Market Research / Public Relations": "2",
    "Aviation / Transport / Logistics": "3",
    "Banking/Finance - Commercial Banks": "5",
    "Banking/Finance - Investment Banks": "40",
    "Banking/Finance - Other Financial & Investment Institutions or Financial Services": "7",
    "Banking/Finance - Private Equities / Hedge Funds / Asset Management": "6",
    "Beauty / Health Care / Fitness": "8",
    "Biotechnology / Chemicals / Laboratory / Testing Services": "9",
    "Catering / Food & Beverage": "10",
    "Charity / NGO / Quasi-government / Professional Bodies": "11",
    "Civil Service / Government": "54",
    "Construction / Construction Engineering Consultancy / Architecture / Surveying": "4",
    "Education / Research / Training": "14",
    "Engineering / Technical Services": "15",
    "Environmental Science": "16",
    "Fast Moving Consumer Goods": "17",
    "General Business Services / Other Consulting Services": "18",
    "HKUST": "52",
    "Hospitality / Hotels / Tourism / Entertainment": "20",
    "HR / Recruitment Services": "19",
    "Information Technology / FinTech": "21",
    "Insurance": "22",
    "Internet / Digital / e-Commerce": "23",
    "Internship Program Organizers": "53",
    "Legal Services": "24",
    "Management Consulting": "26",
    "Manufacturing": "25",
    "Media / Publishing": "27",
    "Medical Services / Pharmaceutical": "28",
    "Motor Vehicles": "29",
    "Multi-nature Conglomerates": "30",
    "Others": "35",
    "Property Management / Real Estate Development": "31",
    "Retail / Wholesale / Trading / Import & Export": "32",
    "Telecommunication": "33",
    "Utilities / Energy / Power": "34",
}

JOB_NATURE = {
    "Accounting / Auditing / Tax": "1",
    "Administration - Non-private Sector": "2",
    "Administration - Private Sector": "3",
    "Architecture / Interior Design": "4",
    "Banking and Finance Executive": "5",
    "Civil Service / Government": "33",
    "Community / Social Worker": "6",
    "Creative / Design / Artist": "7",
    "Customer Services - Retail / Hotel / Tourism and Others": "8",
    "Disciplinary Forces": "9",
    "Engineering - Biological / Chemical / Electronic / Industrial / Mechanical and others": "11",
    "Engineering - Construction / Building Services": "10",
    "Human Resources / Training / Recruitment": "12",
    "IT / Programming": "13",
    "Journalist / Editor / Translation / Copy Writing / Communications": "14",
    "Legal / Compliance": "15",
    "Library Officer / Library Assistant": "16",
    "Logistics / Supply Chain": "17",
    "Management Consultant / Business Analyst": "18",
    "Management Trainee / Graduate Trainee": "19",
    "Marketing / Market Research": "20",
    "Medical Practitioners / Therapist / Pharmacist": "21",
    "Merchandising / Buying": "22",
    "Miscellaneous": "23",
    "Others": "31",
    "PR / Event Management": "24",
    "Quality Control": "25",
    "Research & Development": "26",
    "Research Assistant / Technicians": "27",
    "Sales / Account Servicing / Business Development": "28",
    "Surveying": "29",
    "Teaching": "30",
}

EMPLOYMENT_TYPE = {
    "ASEAN Internship": "6",
    "Co-op": "13",
    "Government Summer Job (PSSSIP)": "8",
    "Graduate Job": "3",
    "Internship (above minimum wage)": "14",
    "Internship (below minimum wage)": "15",
    "On-Campus Internship": "9",
    "STEM Internship": "11",
    "Unpaid Work": "16",
    "Volunteer Work": "17",
    "UPOP Internship": "12",
    "Others": "5",
}

WORKING_LOCATION = {
    "Belt and Road Countries": "24",
    "Brunei Darussalam": "5",
    "Cambodia": "6",
    "Chinese Mainland": "4",
    "Europe": "16",
    "Hong Kong": "1",
    "Indonesia": "7",
    "Japan": "14",
    "Korea": "20",
    "Laos": "8",
    "Macau": "2",
    "Malaysia": "9",
    "Myanmar": "18",
    "Others": "19",
    "Philippines": "12",
    "Singapore": "3",
    "Switzerland": "21",
    "Taiwan, China": "23",
    "Thailand": "11",
    "USA": "17",
    "Various Locations": "15",
    "Vietnam": "13",
    "Virtual": "22",
}

QUALIFICATION = {
    "Undergraduate": "bachelor",
    "Taught Postgraduate": "master",
    "Research Postgraduate": "phd",
}

EMPLOYMENT_MODE = {
    "Full Time": "FT",
    "Part Time": "PT",
}

LANGUAGE = {
    "English (Writing)": "wen",
    "English (Speaking)": "sen",
    "Chinese (Writing)": "zh",
    "Cantonese (Speaking)": "zh-hk",
    "Putonghua (Speaking)": "zh-cn",
    "Others": "other",
}

# Ordered list of all filter groups for sequential display
FILTER_GROUPS = [
    ("Business Nature",   "BN[]",       BUSINESS_NATURE,   True),   # (label, param, options, multi)
    ("Job Nature",        "JN[]",       JOB_NATURE,        True),
    ("Employment Type",   "EMT[]",      EMPLOYMENT_TYPE,   True),
    ("Working Location",  "WL[]",       WORKING_LOCATION,  True),
    ("Qualification",     "awards[]",   QUALIFICATION,     True),
    ("Employment Mode",   "EM[]",       EMPLOYMENT_MODE,   True),
    ("Language",          "L[]",        LANGUAGE,          True),
]
