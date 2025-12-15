import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import random
from datetime import datetime, timedelta

# Initialize embedding model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Database connection
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Clear existing cases
print("Clearing existing cases...")
cur.execute("DELETE FROM cases")
conn.commit()

# Read CSV
print("Reading CSV data...")
df = pd.read_csv('archive (2)/judgments.csv')
print(f"Total cases to process: {len(df)}")

def analyze_party_type(party_name):
    """Determine the type of party based on name"""
    if pd.isna(party_name):
        return 'individual'
    
    party_lower = str(party_name).lower()
    
    # Government entities
    if any(keyword in party_lower for keyword in ['state of', 'union of india', 'government', 'commissioner', 'department', 'ministry', 'chairman', 'secretary']):
        return 'government'
    
    # Companies
    if any(keyword in party_lower for keyword in ['ltd', 'limited', 'pvt', 'private', 'corporation', 'company', 'co.', 'industries', 'enterprises', 'bank', 'insurance']):
        return 'company'
    
    # Educational/Medical
    if any(keyword in party_lower for keyword in ['university', 'college', 'hospital', 'school', 'institute', 'medical']):
        return 'institution'
    
    # Associations/Unions
    if any(keyword in party_lower for keyword in ['association', 'union', 'society', 'federation', 'council']):
        return 'organization'
    
    return 'individual'

def determine_case_category(pet_type, res_type, pet_name, res_name):
    """Determine case category based on parties"""
    pet_lower = str(pet_name).lower() if not pd.isna(pet_name) else ''
    res_lower = str(res_name).lower() if not pd.isna(res_name) else ''
    
    # Criminal cases
    if 'state of' in pet_lower or 'state of' in res_lower:
        if pet_type == 'individual' or res_type == 'individual':
            return 'criminal'
    
    # Constitutional/PIL
    if pet_type == 'organization' or any(keyword in pet_lower for keyword in ['association', 'union', 'society']):
        if res_type == 'government':
            return 'constitutional'
    
    # Service/Employment
    if any(keyword in pet_lower + res_lower for keyword in ['employee', 'service', 'pension', 'retirement', 'termination']):
        return 'service'
    
    # Commercial
    if pet_type == 'company' and res_type == 'company':
        return 'commercial'
    
    # Property
    if any(keyword in pet_lower + res_lower for keyword in ['land', 'property', 'estate', 'acquisition']):
        return 'property'
    
    # Tax
    if any(keyword in pet_lower + res_lower for keyword in ['tax', 'revenue', 'customs', 'excise', 'income']):
        return 'tax'
    
    # Family
    if any(keyword in pet_lower + res_lower for keyword in ['wife', 'husband', 'divorce', 'maintenance', 'custody', 'matrimonial']):
        return 'family'
    
    # Consumer
    if any(keyword in pet_lower + res_lower for keyword in ['consumer', 'deficiency', 'compensation']):
        return 'consumer'
    
    # Civil (default)
    return 'civil'

# Criminal case templates
criminal_templates = [
    "The petitioner was accused under Section {sections} of the Indian Penal Code for {offense}. The prosecution alleged that on {date}, the accused {action}. The defense argued {defense}. After examining witness testimonies and evidence, the court {verdict}.",
    "FIR was registered against the accused for {offense} under Sections {sections} IPC. The case involved {circumstances}. The accused pleaded {plea}. The prosecution presented {evidence}. The court, after careful consideration, {verdict}.",
    "The appellant challenged the conviction under Section {sections} IPC for {offense}. The incident occurred on {date} when {incident}. The trial court had {lower_verdict}. On appeal, considering {grounds}, this court {verdict}.",
    "Criminal proceedings were initiated for {offense}. The complainant alleged that {allegation}. The accused denied the charges stating {denial}. Medical evidence showed {medical}. The court {verdict}.",
    "The case pertains to {offense} punishable under Sections {sections} IPC. The prosecution's case was that {prosecution_case}. The defense contended {defense_case}. Based on evidence and testimony, {verdict}."
]

criminal_offenses = [
    ("theft", "379", "stealing property worth Rs. {amount}", "entered the premises and removed valuable items"),
    ("cheating", "420", "fraudulent misrepresentation", "induced the complainant to invest money in a non-existent scheme"),
    ("assault", "323, 324", "causing grievous hurt", "attacked the victim with a weapon"),
    ("criminal breach of trust", "406", "misappropriation of funds", "failed to account for entrusted property"),
    ("forgery", "467, 468", "forging documents", "created fake documents to obtain illegal benefits"),
    ("criminal intimidation", "506", "threatening with dire consequences", "threatened to harm the complainant"),
    ("robbery", "392", "forcefully taking property", "snatched the victim's belongings"),
    ("house trespass", "448, 451", "unauthorized entry", "entered the property without permission")
]

# Commercial case templates
commercial_templates = [
    "Dispute arose between parties regarding {dispute_type}. The petitioner company claimed {claim}. The agreement dated {date} stipulated {terms}. The respondent breached the contract by {breach}. Seeking {relief}.",
    "Commercial litigation concerning {subject_matter}. The parties entered into an agreement on {date} for {purpose}. The petitioner alleged {allegation}. The respondent contended {defense}. Court examined {examination} and {verdict}.",
    "Contract dispute involving {contract_type}. The petitioner invested Rs. {amount} for {project}. The respondent failed to {failure}. Damages claimed amount to Rs. {damages}. The court {verdict}.",
    "Partnership dispute where {dispute}. The firm was established on {date} with {partners}. Disagreement arose over {issue}. The petitioner sought {remedy}. After reviewing partnership deed and accounts, {verdict}.",
    "Intellectual property matter concerning {ip_type}. The petitioner claimed infringement of {right} registered as {registration}. The respondent was allegedly {infringement}. Evidence showed {evidence}. The court {verdict}."
]

commercial_disputes = [
    ("breach of contract", "supply agreement", "timely delivery of goods", "delaying shipments"),
    ("payment default", "service contract", "payment within 30 days", "non-payment of dues"),
    ("non-performance", "construction contract", "completion within timeline", "abandoning the project"),
    ("trademark infringement", "licensing agreement", "exclusive use of brand", "using similar marks"),
    ("partnership dissolution", "partnership deed", "profit sharing", "misappropriation of funds")
]

# Civil case templates
civil_templates = [
    "Civil suit for {claim_type}. The plaintiff claimed {claim}. The suit property is described as {property}. The defendant contested on grounds that {defense}. Evidence included {evidence}. The court {verdict}.",
    "Dispute regarding {subject}. The plaintiff alleged {allegation} dating back to {date}. The defendant denied the claims stating {denial}. Documentary evidence showed {documents}. After trial, {verdict}.",
    "Matter concerning {issue}. The parties had {relationship}. The plaintiff sought {relief} on the basis that {grounds}. The defendant argued {counter}. The court, after examining {examination}, {verdict}.",
    "Suit for {remedy} filed by plaintiff. The cause of action arose on {date} when {incident}. The plaintiff claimed entitlement based on {basis}. The defendant's reply was {reply}. The court {verdict}.",
    "Litigation over {dispute}. The plaintiff and defendant had {dealings}. The plaintiff asserted {assertion}. The defendant challenged {challenge}. Court considered {considerations} and {verdict}."
]

civil_issues = [
    ("specific performance", "sale agreement", "enforcement of contract to sell property"),
    ("declaration of title", "ancestral property", "rightful ownership"),
    ("permanent injunction", "land dispute", "preventing encroachment"),
    ("recovery of money", "loan transaction", "repayment of borrowed amount"),
    ("partition", "joint family property", "division of assets")
]

# Constitutional case templates
constitutional_templates = [
    "Public Interest Litigation challenging {issue}. The petitioner organization raised concerns about {concern}. Article {article} of the Constitution was invoked. The petition highlighted {violation}. The court {verdict}.",
    "Writ petition under Article {article} questioning {question}. The impugned {impugned} was challenged as {challenge}. The petitioner contended {contention}. The respondent State justified {justification}. The court {verdict}.",
    "Constitutional challenge to {law}. The petitioner argued violation of fundamental rights under Articles {articles}. The impugned provision {provision}. The State defended on grounds of {grounds}. After constitutional scrutiny, {verdict}.",
    "Petition seeking enforcement of {right}. The petitioner alleged {allegation} violating constitutional guarantees. The matter involved {involvement}. Public interest demanded {demand}. The court {verdict}.",
    "Challenge to administrative action on grounds of {grounds}. The decision dated {date} was assailed as {assail}. The petitioner relied on {reliance}. The authority contended {authority_stand}. The court {verdict}."
]

constitutional_issues = [
    ("environmental pollution", "226", "industrial emissions violating right to clean air", "arbitrary and unreasonable"),
    ("arbitrary detention", "32", "illegal arrest without proper warrant", "unconstitutional"),
    ("discriminatory policy", "14, 15", "classification lacking rational nexus", "violative of equality"),
    ("freedom of speech", "19(1)(a)", "censorship of expression", "ultra vires"),
    ("right to education", "21A", "denial of admission to children", "unconstitutional")
]

# Property case templates
property_templates = [
    "Dispute concerning property bearing {description}. The plaintiff claimed title through {source}. The property was {nature}. The defendant contested claiming {defense}. Relevant documents included {documents}. The court {verdict}.",
    "Suit for possession of {property_type}. The plaintiff's case was based on {basis}. The property was allegedly {status}. The defendant claimed {claim}. After examining title deeds and evidence, {verdict}.",
    "Partition suit regarding the property. The suit property measured {measurement} and was {location}. The parties were {relation}. Each party claimed {claim_share}. The court appointed a commissioner and {verdict}.",
    "Property dispute where {dispute}. The property was originally {origin}. The plaintiff acquired rights through {acquisition}. The defendant's possession was {possession}. The court {verdict}.",
    "Matter relating to {issue} of property. The property in question was {description}. The plaintiff sought {remedy}. The defendant's stand was {stand}. Evidence showed {evidence}. The court {verdict}."
]

# Service/Employment templates
service_templates = [
    "Service matter concerning {issue}. The petitioner was employed as {position} since {date}. The dispute arose regarding {dispute}. Service rules provided {rules}. The petitioner claimed {claim}. The court {verdict}.",
    "Employment dispute where {situation}. The petitioner had {tenure} of service. The impugned order dated {date} {order}. The petitioner challenged on grounds of {grounds}. The authority's stand was {stand}. The court {verdict}.",
    "Challenge to {action} by employer. The petitioner worked as {role} in {department}. The action was taken alleging {allegation}. The petitioner denied and claimed {defense}. After examining service records, {verdict}.",
    "Pension/retirement benefits matter. The petitioner retired on {date} after {years} years of service. The dispute concerned {dispute}. The petitioner was entitled to {entitlement}. The respondent denied on grounds {denial}. The court {verdict}.",
    "Promotion/seniority dispute in {organization}. The petitioner claimed {claim} based on {basis}. The seniority list dated {date} {list_issue}. The respondent argued {argument}. After reviewing records, {verdict}."
]

service_issues = [
    ("wrongful termination", "Senior Engineer", "dismissed the petitioner without inquiry"),
    ("non-payment of dues", "Assistant Manager", "withheld salary and allowances"),
    ("denial of promotion", "Deputy Collector", "superseded despite seniority"),
    ("pension calculation", "Professor", "incorrectly computed pensionary benefits"),
    ("disciplinary action", "Inspector", "imposed penalty disproportionate to charges")
]

# Tax case templates
tax_templates = [
    "Tax dispute for assessment year {year}. The assessee challenged {challenge}. The assessed income was Rs. {amount}. The tax authority {authority_action}. The assessee contended {contention}. The tribunal {verdict}.",
    "Appeal against {tax_type} demand. The impugned order dated {date} raised demand of Rs. {amount}. The appellant argued {argument}. The department justified {justification}. After examining records, {verdict}.",
    "Matter concerning {issue} under {act}. The taxpayer declared {declaration}. The department alleged {allegation}. Difference arose due to {difference}. The appellant relied on {reliance}. The court {verdict}.",
    "Challenge to {assessment_type} assessment. The original return showed {return_value}. The reassessment was based on {basis}. The assessee objected to {objection}. The revenue defended {defense}. The court {verdict}.",
    "Dispute regarding {dispute}. The transaction involved {transaction}. The tax liability was {liability}. The assessee claimed {exemption}. The department denied {denial}. After legal scrutiny, {verdict}."
]

# Family law templates
family_templates = [
    "Matrimonial dispute concerning {issue}. The parties were married on {date}. The petitioner alleged {allegation}. The marriage broke down due to {reason}. The respondent contested {contest}. The court {verdict}.",
    "Petition for {remedy} under {act}. The petitioner claimed {claim}. The parties have {children}. The respondent's conduct was {conduct}. Evidence showed {evidence}. The court {verdict}.",
    "Maintenance matter under Section {section}. The petitioner wife sought {amount} per month. She alleged {allegation}. The respondent husband claimed {claim}. Financial status showed {status}. The court {verdict}.",
    "Custody dispute concerning {child}. The minor child aged {age} was {situation}. The petitioner sought {custody_type} custody. The respondent opposed on grounds {grounds}. Considering child's welfare, {verdict}.",
    "Divorce petition on grounds of {grounds}. The marriage was solemnized on {date}. The petitioner alleged {cruelty}. The respondent denied {denial}. After examining evidence and counseling, {verdict}."
]

def generate_criminal_description(pet, res, case_no):
    template = random.choice(criminal_templates)
    offense_data = random.choice(criminal_offenses)
    
    description = template.format(
        sections=offense_data[1],
        offense=offense_data[0],
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2018, 2021)}",
        action=offense_data[3],
        defense=random.choice([
            "false implication", "lack of evidence", "alibi", 
            "misidentification", "procedural irregularities"
        ]),
        verdict=random.choice([
            "convicted the accused and sentenced to {years} years imprisonment".format(years=random.randint(1, 7)),
            "acquitted the accused due to lack of sufficient evidence",
            "found the accused guilty and imposed a fine of Rs. {amount}".format(amount=random.randint(5000, 50000)),
            "partially allowed the appeal and reduced the sentence"
        ]),
        circumstances=offense_data[2].format(amount=f"{random.randint(10, 500)},000"),
        plea=random.choice(["not guilty", "guilty", "conditional plea"]),
        evidence=random.choice([
            "CCTV footage and eyewitness accounts",
            "forensic reports and material evidence",
            "documentary evidence and confessional statements",
            "expert testimony and circumstantial evidence"
        ]),
        allegation=offense_data[3],
        denial=random.choice([
            "wrongful accusation", "mistaken identity", "fabricated charges"
        ]),
        medical=random.choice([
            "injuries consistent with assault", "no evidence of physical harm",
            "forensic findings supporting the case"
        ]),
        incident=offense_data[3],
        lower_verdict=random.choice(["convicted the accused", "acquitted the accused"]),
        grounds=random.choice([
            "new evidence", "procedural errors", "insufficient evidence", "violation of rights"
        ]),
        prosecution_case=offense_data[2].format(amount=f"{random.randint(10, 500)},000"),
        defense_case=random.choice([
            "the accused was not present at the scene",
            "the evidence was fabricated",
            "there was no criminal intent"
        ])
    )
    
    return description, offense_data[0]

def generate_commercial_description(pet, res, case_no):
    template = random.choice(commercial_templates)
    dispute = random.choice(commercial_disputes)
    
    description = template.format(
        dispute_type=dispute[0],
        claim=f"breach of {dispute[1]} terms",
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2015, 2020)}",
        terms=dispute[2],
        breach=dispute[3],
        relief=random.choice([
            "specific performance and damages",
            "compensation of Rs. {amount} lakhs".format(amount=random.randint(10, 500)),
            "permanent injunction and costs"
        ]),
        subject_matter=dispute[1],
        purpose=random.choice([
            "supply of goods", "rendering services", "joint venture", "technology transfer"
        ]),
        allegation=dispute[3],
        defense=random.choice([
            "force majeure circumstances", "prior breach by petitioner", "contract was void"
        ]),
        examination=random.choice([
            "contract terms and correspondence", "expert opinions", "financial records"
        ]),
        verdict=random.choice([
            "directed specific performance within 90 days",
            "awarded damages of Rs. {amount} lakhs".format(amount=random.randint(5, 200)),
            "dismissed the suit for lack of evidence",
            "partly decreed the suit with costs"
        ]),
        contract_type=dispute[1],
        amount=f"{random.randint(10, 500)}",
        project=random.choice([
            "construction of commercial complex", "supply of machinery",
            "software development", "consulting services"
        ]),
        failure=dispute[3],
        damages=f"{random.randint(50, 1000)}",
        dispute=f"disagreement over {dispute[0]}",
        partners=random.choice(["two partners", "three partners", "multiple partners"]),
        issue=dispute[0],
        remedy=random.choice(["dissolution and accounts", "removal of partner", "share of profits"]),
        ip_type=random.choice(["trademark", "copyright", "patent", "design"]),
        right=random.choice(["registered trademark", "copyrighted work", "patented invention"]),
        registration=f"No. {random.randint(100000, 999999)}",
        infringement=random.choice([
            "using identical marks in same trade",
            "copying protected design",
            "unauthorized reproduction"
        ]),
        evidence=random.choice([
            "market survey and consumer confusion",
            "comparative analysis of products",
            "expert technical reports"
        ])
    )
    
    return description, dispute[0]

def generate_civil_description(pet, res, case_no):
    template = random.choice(civil_templates)
    issue = random.choice(civil_issues)
    
    description = template.format(
        claim_type=issue[0],
        claim=issue[2],
        property=f"land measuring {random.randint(100, 5000)} sq.ft in {random.choice(['urban', 'rural'])} area",
        defense=random.choice([
            "title was defective", "suit was barred by limitation", 
            "no cause of action", "plaintiff had unclean hands"
        ]),
        evidence=random.choice([
            "sale deeds and revenue records", "witness testimonies",
            "survey reports and maps", "possession certificates"
        ]),
        verdict=random.choice([
            "decreed the suit in favor of plaintiff",
            "dismissed the suit",
            "partly decreed the suit",
            "directed the defendant to perform the agreement within 60 days"
        ]),
        subject=issue[1],
        allegation=issue[2],
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2010, 2020)}",
        denial=random.choice([
            "the claim was false and fabricated",
            "plaintiff had no legal right",
            "defendant was the rightful owner"
        ]),
        documents=random.choice([
            "registered sale deeds", "mutation entries", "tax receipts", "possession records"
        ]),
        issue=issue[0],
        relationship=random.choice([
            "entered into an agreement", "were co-owners", "had family relations"
        ]),
        relief=issue[0],
        grounds=issue[2],
        counter=random.choice([
            "plaintiff's title was questionable",
            "suit was not maintainable",
            "defendant had better title"
        ]),
        examination=random.choice([
            "title documents", "revenue records", "witness statements", "expert reports"
        ]),
        remedy=issue[0],
        incident=random.choice([
            "the defendant refused to execute sale deed",
            "dispute arose over boundaries",
            "defendant took unauthorized possession"
        ]),
        basis=issue[2],
        reply=random.choice([
            "denying all material allegations",
            "claiming prescriptive title",
            "pleading limitation"
        ]),
        dispute=issue[1],
        dealings=random.choice([
            "business transactions", "family relationship", "contractual relations"
        ]),
        assertion=issue[2],
        challenge=random.choice([
            "jurisdiction of the court",
            "valuation for court fees",
            "plaintiff's locus standi"
        ]),
        considerations=random.choice([
            "preponderance of probabilities",
            "documentary and oral evidence",
            "legal precedents"
        ])
    )
    
    return description, issue[0]

def generate_constitutional_description(pet, res, case_no):
    template = random.choice(constitutional_templates)
    issue = random.choice(constitutional_issues)
    
    description = template.format(
        issue=issue[0],
        concern=issue[2],
        article=issue[1],
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2018, 2021)}",
        violation=random.choice([
            "systematic violations of fundamental rights",
            "arbitrary state action",
            "discriminatory practices"
        ]),
        verdict=random.choice([
            "issued directions to the respondent State to remedy the situation",
            "struck down the impugned provision as unconstitutional",
            "disposed of the petition with guidelines",
            "appointed a monitoring committee"
        ]),
        question=issue[0],
        impugned=random.choice([
            "government order", "notification", "policy decision", "legislative provision"
        ]),
        challenge=issue[3],
        contention=issue[2],
        justification=random.choice([
            "public interest and welfare",
            "constitutional validity",
            "administrative necessity"
        ]),
        law=random.choice([
            "statutory provision", "executive order", "administrative action"
        ]),
        articles=issue[1],
        provision=random.choice([
            "created arbitrary classification",
            "violated procedural fairness",
            "exceeded legislative competence"
        ]),
        grounds=random.choice([
            "reasonable restrictions", "state policy", "national security"
        ]),
        right=random.choice([
            "fundamental rights", "constitutional guarantees", "legal rights"
        ]),
        allegation=issue[2],
        involvement=random.choice([
            "matters of public importance",
            "widespread violations",
            "systemic failures"
        ]),
        demand=random.choice([
            "immediate intervention", "corrective measures", "compensatory relief"
        ]),
        assail=issue[3],
        reliance=random.choice([
            "constitutional provisions and precedents",
            "international conventions",
            "statutory safeguards"
        ]),
        authority_stand=random.choice([
            "action was within powers",
            "procedure was followed",
            "decision was in public interest"
        ])
    )
    
    return description, issue[0]

def generate_service_description(pet, res, case_no):
    template = random.choice(service_templates)
    issue = random.choice(service_issues)
    
    description = template.format(
        issue=issue[0],
        position=issue[1],
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2005, 2015)}",
        dispute=issue[0],
        rules=random.choice([
            "that termination required show cause notice",
            "seniority for promotion",
            "benefits based on service period"
        ]),
        claim=random.choice([
            "reinstatement with back wages",
            "payment of dues",
            "promotion with seniority"
        ]),
        verdict=random.choice([
            "set aside the impugned order and directed reinstatement",
            "upheld the termination as valid",
            "directed payment of all dues within 3 months",
            "restored seniority and granted consequential benefits"
        ]),
        situation=issue[0],
        tenure=f"{random.randint(5, 30)} years",
        order=issue[2],
        grounds=random.choice([
            "violation of natural justice",
            "malafide intent",
            "non-compliance with procedure"
        ]),
        stand=random.choice([
            "action was justified",
            "petitioner's performance was unsatisfactory",
            "procedure was duly followed"
        ]),
        action=issue[0],
        role=issue[1],
        department=random.choice([
            "Public Works Department",
            "Revenue Department",
            "Education Department",
            "Health Department"
        ]),
        allegation=random.choice([
            "misconduct and negligence",
            "financial irregularities",
            "dereliction of duty"
        ]),
        defense=random.choice([
            "false charges leveled to victimize",
            "proper procedure was not followed",
            "no evidence of misconduct"
        ]),
        years=random.randint(10, 35),
        dispute_matter=issue[0],
        entitlement=random.choice([
            "full pension benefits",
            "gratuity and commutation",
            "medical benefits"
        ]),
        denial=random.choice([
            "incomplete service period",
            "pending disciplinary proceedings",
            "incorrect calculations"
        ]),
        organization=random.choice([
            "government department",
            "public sector undertaking",
            "autonomous body"
        ]),
        claim_matter=f"{issue[0]} was due",
        basis=random.choice([
            "years of service and performance",
            "recruitment rules and seniority",
            "court judgments"
        ]),
        list_issue=random.choice([
            "wrongly placed petitioner below juniors",
            "ignored petitioner's service",
            "contained factual errors"
        ]),
        argument=random.choice([
            "petitioner lacked requisite qualifications",
            "disciplinary proceedings were pending",
            "seniority was correctly determined"
        ])
    )
    
    return description, issue[0]

def generate_tax_description(pet, res, case_no):
    template = random.choice(tax_templates)
    
    description = template.format(
        year=f"{random.randint(2015, 2021)}-{random.randint(2016, 2022)}",
        challenge=random.choice([
            "addition of Rs. {amount} lakhs to income".format(amount=random.randint(5, 500)),
            "disallowance of claimed deductions",
            "penalty proceedings"
        ]),
        amount=f"{random.randint(10, 1000)} lakhs",
        authority_action=random.choice([
            "treated certain receipts as taxable income",
            "disallowed claimed expenses",
            "rejected book results"
        ]),
        contention=random.choice([
            "additions were made without proper basis",
            "expenses were legitimate business expenditure",
            "interpretation of law was incorrect"
        ]),
        verdict=random.choice([
            "allowed the appeal and deleted the addition",
            "upheld the assessment order",
            "partly allowed the appeal",
            "remanded the matter for fresh consideration"
        ]),
        tax_type=random.choice(["Income Tax", "GST", "Service Tax", "Customs Duty"]),
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2018, 2021)}",
        argument=random.choice([
            "addition was arbitrary and unsustainable",
            "proper opportunity was not given",
            "evidence was ignored"
        ]),
        justification=random.choice([
            "based on investigation findings",
            "supported by material on record",
            "in accordance with law"
        ]),
        issue=random.choice([
            "capital gains computation",
            "classification of income",
            "allowability of deductions",
            "valuation of assets"
        ]),
        act=random.choice([
            "Income Tax Act, 1961",
            "Customs Act, 1962",
            "GST Act, 2017"
        ]),
        declaration=f"income of Rs. {random.randint(10, 500)} lakhs",
        allegation=random.choice([
            "under-reporting of income",
            "bogus expenses",
            "suppression of turnover"
        ]),
        difference=random.choice([
            "treatment of certain receipts",
            "depreciation calculations",
            "interpretation of exemption provisions"
        ]),
        reliance=random.choice([
            "judicial precedents",
            "departmental circulars",
            "accounting standards"
        ]),
        assessment_type=random.choice(["scrutiny", "reassessment", "best judgment"]),
        return_value=f"income of Rs. {random.randint(5, 200)} lakhs",
        basis=random.choice([
            "information from investigation",
            "audit objections",
            "third party data"
        ]),
        objection=random.choice([
            "reassessment being barred by limitation",
            "lack of proper notice",
            "no new material for reopening"
        ]),
        defense=random.choice([
            "escapement of income was established",
            "proper procedure was followed",
            "reasons were recorded"
        ]),
        dispute=random.choice([
            "applicability of exemption",
            "rate of tax",
            "valuation method"
        ]),
        transaction=f"value of Rs. {random.randint(50, 5000)} lakhs",
        liability=f"Rs. {random.randint(5, 500)} lakhs",
        exemption=random.choice([
            "exemption under relevant provisions",
            "benefit of lower tax rate",
            "credit of taxes paid"
        ]),
        denial=random.choice([
            "on ground of non-fulfillment of conditions",
            "citing lack of proper documentation",
            "as provision was not applicable"
        ])
    )
    
    return description, "taxation"

def generate_family_description(pet, res, case_no):
    template = random.choice(family_templates)
    
    description = template.format(
        issue=random.choice(["divorce", "maintenance", "child custody", "restitution of conjugal rights"]),
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2008, 2018)}",
        allegation=random.choice([
            "cruelty and harassment",
            "desertion without reasonable cause",
            "adultery"
        ]),
        reason=random.choice([
            "irreconcilable differences",
            "continuous conflict and abuse",
            "incompatibility of temperament"
        ]),
        contest=random.choice([
            "denying all allegations",
            "claiming reconciliation attempts",
            "seeking dismissal"
        ]),
        verdict=random.choice([
            "granted divorce decree",
            "dismissed the petition",
            "granted maintenance of Rs. {amount} per month".format(amount=random.randint(10, 50) * 1000),
            "awarded custody to the mother with visitation rights"
        ]),
        remedy=random.choice(["divorce", "judicial separation", "maintenance", "custody"]),
        act=random.choice(["Hindu Marriage Act", "Special Marriage Act", "Muslim Personal Law"]),
        claim=random.choice([
            "divorce on grounds of cruelty",
            "permanent alimony",
            "child custody and support"
        ]),
        children=random.choice([
            "one minor child",
            "two minor children",
            "no children from the marriage"
        ]),
        conduct=random.choice([
            "cruel and abusive",
            "neglectful and indifferent",
            "violent and aggressive"
        ]),
        evidence=random.choice([
            "witness testimonies and medical records",
            "correspondence and photographs",
            "police complaints and FIRs"
        ]),
        section=random.choice(["125 CrPC", "24 of Hindu Marriage Act"]),
        amount=f"Rs. {random.randint(10, 50)},000",
        status=random.choice([
            "earning Rs. {amount} per month".format(amount=random.randint(50, 500) * 1000),
            "without any source of income",
            "running a business"
        ]),
        child=random.choice(["son", "daughter"]),
        age=random.randint(3, 15),
        situation=random.choice([
            "in custody of mother",
            "living with father",
            "with maternal grandparents"
        ]),
        custody_type=random.choice(["sole", "joint"]),
        grounds=random.choice([
            "petitioner was unfit parent",
            "child's welfare required",
            "better financial stability"
        ]),
        cruelty=random.choice([
            "physical and mental torture",
            "desertion for over two years",
            "adultery and infidelity"
        ]),
        denial=random.choice([
            "all allegations of cruelty",
            "charges of desertion",
            "claims of misconduct"
        ])
    )
    
    return description, "family law"

def generate_property_description(pet, res, case_no):
    template = random.choice(property_templates)
    
    description = template.format(
        description=f"Survey No. {random.randint(100, 9999)}, measuring {random.randint(100, 5000)} sq.ft",
        source=random.choice([
            "inheritance from ancestors",
            "registered sale deed dated {date}".format(
                date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(1990, 2015)}"
            ),
            "partition deed",
            "gift deed"
        ]),
        nature=random.choice([
            "agricultural land",
            "residential plot",
            "commercial property",
            "ancestral property"
        ]),
        defense=random.choice([
            "adverse possession for over 12 years",
            "defect in plaintiff's title",
            "prior sale in defendant's favor"
        ]),
        documents=random.choice([
            "sale deeds, revenue records and tax receipts",
            "partition deed and mutation entries",
            "inheritance certificates and wills"
        ]),
        verdict=random.choice([
            "decreed the suit in favor of plaintiff with costs",
            "dismissed the suit for lack of title",
            "partly decreed granting partition",
            "directed defendant to deliver possession within 60 days"
        ]),
        property_type=random.choice(["land", "house property", "shop", "agricultural land"]),
        basis=random.choice([
            "registered sale agreement",
            "inheritance through will",
            "partition of joint family property"
        ]),
        status=random.choice([
            "under unauthorized occupation by defendant",
            "jointly owned with defendant",
            "encroached upon"
        ]),
        claim=random.choice([
            "ownership through adverse possession",
            "better title through prior transaction",
            "rights as co-sharer"
        ]),
        measurement=f"{random.randint(500, 5000)} sq.ft",
        location=random.choice(["urban limits", "rural area", "city outskirts"]),
        relation=random.choice(["co-heirs", "brothers", "former partners"]),
        claim_share=random.choice([
            "equal share", "1/3rd share", "specific portion"
        ]),
        dispute=random.choice([
            "boundaries were disputed",
            "ownership was contested",
            "possession was challenged"
        ]),
        origin=random.choice([
            "purchased by father",
            "ancestral property",
            "acquired through government auction"
        ]),
        acquisition=random.choice([
            "inheritance", "purchase", "partition", "gift"
        ]),
        possession=random.choice([
            "without any legal right",
            "based on fabricated documents",
            "as a trespasser"
        ]),
        issue=random.choice(["partition", "possession", "title", "boundaries"]),
        remedy=random.choice([
            "declaration of title",
            "partition and separate possession",
            "permanent injunction",
            "possession"
        ]),
        stand=random.choice([
            "plaintiff had no valid title",
            "defendant was owner",
            "suit was barred by limitation"
        ]),
        evidence=random.choice([
            "revenue records favoring plaintiff",
            "long possession by defendant",
            "registered documents supporting title"
        ])
    )
    
    return description, "property dispute"

def generate_consumer_description(pet, res, case_no):
    template = "Consumer complaint alleging {issue}. The complainant purchased {product} for Rs. {amount} on {date}. The deficiency manifested as {defect}. Despite complaints, the opposite party {response}. The complainant sought {relief}. After examining evidence, {verdict}."
    
    description = template.format(
        issue=random.choice([
            "deficiency in service",
            "defective product",
            "unfair trade practice",
            "medical negligence"
        ]),
        product=random.choice([
            "automobile", "electronic goods", "real estate property",
            "medical services", "insurance policy"
        ]),
        amount=f"{random.randint(1, 50)} lakhs",
        date=f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(2017, 2021)}",
        defect=random.choice([
            "manufacturing defects and poor quality",
            "non-performance of promised services",
            "delay in delivery beyond reasonable time",
            "wrong medical treatment causing harm"
        ]),
        response=random.choice([
            "failed to redress the grievance",
            "denied any deficiency",
            "offered inadequate compensation"
        ]),
        relief=random.choice([
            "replacement and compensation for mental agony",
            "refund with interest and damages",
            "compensation for deficiency in service"
        ]),
        verdict=random.choice([
            "allowed the complaint and directed payment of Rs. {comp} lakhs".format(comp=random.randint(1, 20)),
            "dismissed the complaint for lack of evidence",
            "directed the opposite party to replace the product and pay compensation"
        ])
    )
    
    return description, "consumer protection"

# Main processing
print("\nGenerating intelligent case descriptions...")
processed = 0
batch_size = 100
batch_data = []

for idx, row in df.iterrows():
    case_no = row['case_no']
    pet = row['pet']
    res = row['res']
    judgment_date = row.get('judgment_dates', '')
    bench = row.get('bench', '')
    
    # Determine party types
    pet_type = analyze_party_type(pet)
    res_type = analyze_party_type(res)
    
    # Determine category
    category = determine_case_category(pet_type, res_type, pet, res)
    
    # Generate description based on category
    if category == 'criminal':
        description, subcategory = generate_criminal_description(pet, res, case_no)
    elif category == 'commercial':
        description, subcategory = generate_commercial_description(pet, res, case_no)
    elif category == 'constitutional':
        description, subcategory = generate_constitutional_description(pet, res, case_no)
    elif category == 'property':
        description, subcategory = generate_property_description(pet, res, case_no)
    elif category == 'service':
        description, subcategory = generate_service_description(pet, res, case_no)
    elif category == 'tax':
        description, subcategory = generate_tax_description(pet, res, case_no)
    elif category == 'family':
        description, subcategory = generate_family_description(pet, res, case_no)
    elif category == 'consumer':
        description, subcategory = generate_consumer_description(pet, res, case_no)
    else:  # civil
        description, subcategory = generate_civil_description(pet, res, case_no)
    
    # Create full case text for embedding
    case_text = f"""Case No: {case_no}
Category: {category}
Petitioner: {pet}
Respondent: {res}

{description}

Parties: {pet} vs {res}
Keywords: {category}, {subcategory}"""
    
    # Generate embedding
    embedding = model.encode(case_text)
    embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
    
    batch_data.append((
        case_no,
        str(pet) if not pd.isna(pet) else 'Unknown',
        str(res) if not pd.isna(res) else 'Unknown',
        description,
        category,
        str(judgment_date) if not pd.isna(judgment_date) else None,
        str(bench) if not pd.isna(bench) else None,
        embedding_str
    ))
    
    processed += 1
    
    # Batch insert
    if len(batch_data) >= batch_size:
        cur.executemany("""
            INSERT INTO cases 
            (case_number, title, parties, description, category, judgment_date, bench, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, batch_data)
        conn.commit()
        batch_data = []
        print(f"Processed {processed}/{len(df)} cases...")

# Insert remaining
if batch_data:
    cur.executemany("""
        INSERT INTO cases 
        (case_number, title, parties, description, category, judgment_date, bench, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, batch_data)
    conn.commit()

print(f"\n✅ Successfully processed all {processed} cases!")
print("\nCategory distribution:")
cur.execute("SELECT category, COUNT(*) FROM cases GROUP BY category ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} cases")

cur.close()
conn.close()
print("\n🎉 Database population complete!")
