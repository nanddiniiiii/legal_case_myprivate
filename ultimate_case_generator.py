"""
ULTIMATE LEGAL CASE GENERATOR V2.0
==================================
Creates MASSIVELY VARIED case descriptions with:
- 500+ unique crime/case scenarios
- Multiple description formats (narrative, legal, evidence-based)
- True story variety - not just number changes
- All case types: murder, theft, rape, kidnapping, missing person, stampede, 
  honor killing, domestic violence, divorce, property, tax, service, etc.
"""

import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import random
from datetime import datetime, timedelta

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="legal_search",
        user="postgres",
        password="12345",
        port="5432"
    )

# =============================================================================
# STATE-SPECIFIC LOCATION MAPPING
# =============================================================================

# Map states to their major cities/locations
STATE_LOCATIONS = {
    'DELHI': ['Connaught Place', 'Karol Bagh', 'Lajpat Nagar', 'Rohini', 'Dwarka', 'Vasant Vihar', 'South Extension', 'Chandni Chowk', 'Paharganj', 'Janakpuri'],
    'MAHARASHTRA': ['Andheri Mumbai', 'Bandra Mumbai', 'Juhu Mumbai', 'Colaba Mumbai', 'Dadar Mumbai', 'Borivali Mumbai', 'Thane', 'Navi Mumbai', 'MG Road Pune', 'Koregaon Park Pune', 'Kothrud Pune', 'Nagpur Sadar', 'Aurangabad', 'Nashik Road'],
    'KARNATAKA': ['Koramangala Bangalore', 'Indiranagar Bangalore', 'Whitefield Bangalore', 'Jayanagar Bangalore', 'HSR Layout Bangalore', 'Malleshwaram Bangalore', 'Yelahanka Bangalore', 'Hebbal Bangalore', 'Marathahalli', 'Mysore Road'],
    'TAMIL NADU': ['T Nagar Chennai', 'Adyar Chennai', 'Velachery Chennai', 'Anna Nagar Chennai', 'Mylapore Chennai', 'Guindy Chennai', 'Nungambakkam Chennai', 'Coimbatore RS Puram', 'Madurai', 'Salem'],
    'WEST BENGAL': ['Park Street Kolkata', 'Salt Lake Kolkata', 'Ballygunge Kolkata', 'Howrah', 'Dum Dum Kolkata', 'Jadavpur Kolkata', 'Behala', 'Barasat', 'New Town', 'Siliguri'],
    'TELANGANA': ['Banjara Hills Hyderabad', 'Hitech City Hyderabad', 'Secunderabad', 'Jubilee Hills Hyderabad', 'Madhapur Hyderabad', 'Kukatpally Hyderabad', 'Ameerpet', 'LB Nagar', 'Uppal', 'Gachibowli'],
    'ANDHRA PRADESH': ['Vijayawada', 'Visakhapatnam', 'Guntur', 'Tirupati', 'Nellore', 'Kakinada', 'Rajahmundry', 'Kurnool'],
    'GUJARAT': ['Vastrapur Ahmedabad', 'Satellite Ahmedabad', 'Maninagar Ahmedabad', 'Navrangpura Ahmedabad', 'Bodakdev Ahmedabad', 'Paldi Ahmedabad', 'Surat', 'Vadodara', 'Rajkot'],
    'RAJASTHAN': ['Civil Lines Jaipur', 'Malviya Nagar Jaipur', 'Vaishali Nagar Jaipur', 'C Scheme Jaipur', 'Raja Park Jaipur', 'MI Road Jaipur', 'Jodhpur', 'Udaipur', 'Kota'],
    'UTTAR PRADESH': ['Gomti Nagar Lucknow', 'Hazratganj Lucknow', 'Alambagh Lucknow', 'Indira Nagar Lucknow', 'Hazratganj Kanpur', 'Civil Lines Kanpur', 'Station Road Varanasi', 'Lanka Varanasi', 'Noida', 'Ghaziabad', 'Meerut', 'Agra'],
    'BIHAR': ['Rajpath Patna', 'Boring Road Patna', 'Kankarbagh Patna', 'Fraser Road Patna', 'Gaya', 'Muzaffarpur', 'Bhagalpur'],
    'JHARKHAND': ['Gandhi Maidan Ranchi', 'Main Road Ranchi', 'Lalpur Ranchi', 'Dhanbad', 'Jamshedpur', 'Bokaro'],
    'MADHYA PRADESH': ['Residency Road Indore', 'MG Road Indore', 'Bhopal New Market', 'Arera Colony Bhopal', 'Gwalior', 'Jabalpur', 'Ujjain'],
    'PUNJAB': ['Model Town Ludhiana', 'Civil Lines Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda'],
    'HARYANA': ['Sector 17 Chandigarh', 'Sector 22 Chandigarh', 'Gurgaon Cyber City', 'DLF Phase Gurgaon', 'Faridabad', 'Panipat', 'Ambala', 'Rohtak', 'Hisar'],
    'KERALA': ['MG Road Kochi', 'Ernakulam', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur', 'Kannur'],
    'ODISHA': ['Bhubaneswar', 'Cuttack', 'Puri', 'Rourkela'],
    'CHHATTISGARH': ['Raipur', 'Bhilai', 'Bilaspur', 'Durg'],
    'ASSAM': ['Guwahati', 'Dibrugarh', 'Jorhat', 'Silchar'],
    'UTTARAKHAND': ['Dehradun', 'Haridwar', 'Roorkee', 'Haldwani'],
    'GOA': ['Panjim', 'Margao', 'Vasco da Gama', 'Mapusa'],
    'HIMACHAL PRADESH': ['Shimla', 'Dharamshala', 'Manali', 'Solan'],
    'JAMMU AND KASHMIR': ['Jammu', 'Srinagar', 'Anantnag'],
    'TRIPURA': ['Agartala'],
    'MEGHALAYA': ['Shillong'],
    'MANIPUR': ['Imphal'],
    'NAGALAND': ['Kohima', 'Dimapur'],
    'MIZORAM': ['Aizawl'],
    'SIKKIM': ['Gangtok']
}

# Festival to month mapping for realistic dates
FESTIVAL_DATES = {
    'New Year celebration': [(31, 12), (1, 1)],
    'New Year Eve party': [(31, 12)],
    'Republic Day': [(26, 1)],
    'Holi': [(3, 1), (3, 31)],  # March
    'Holi festival': [(3, 1), (3, 31)],  # March
    'Ram Navami': [(4, 1), (4, 30)],  # April
    'Mahavir Jayanti': [(4, 1), (4, 30)],
    'Buddha Purnima': [(5, 1), (5, 31)],  # May
    'Eid': [(5, 1), (6, 30)],  # Varies, but typically May-June
    'Eid celebration': [(5, 1), (6, 30)],
    'Eid prayers': [(5, 1), (6, 30)],
    'Muharram procession': [(8, 1), (8, 31)],  # Islamic month, varies
    'Janmashtami': [(8, 1), (9, 30)],  # August-September
    'Ganesh Chaturthi': [(8, 15), (9, 15)],
    'Ganesh Visarjan': [(8, 20), (9, 20)],
    'Onam': [(8, 15), (9, 15)],
    'Independence Day': [(15, 8)],
    'Dussehra': [(9, 15), (10, 31)],  # September-October
    'Durga Puja': [(9, 15), (10, 31)],
    'Durga Puja immersion': [(9, 20), (10, 31)],
    'Diwali': [(10, 1), (11, 30)],  # October-November
    'Diwali celebration': [(10, 1), (11, 30)],
    'Navratri': [(9, 15), (10, 31)],
    'Navratri celebration': [(9, 15), (10, 31)],
    'garba night': [(9, 15), (10, 31)],  # During Navratri
    'dandiya': [(9, 15), (10, 31)],  # During Navratri
    'Guru Nanak Jayanti': [(11, 1), (11, 30)],
    'Christmas': [(24, 12), (25, 12)],
    'Christmas mass': [(24, 12), (25, 12)],
    'Kumbh Mela': [(1, 1), (4, 30)],  # Varies, but typically Jan-April
    'Ardh Kumbh': [(1, 1), (4, 30)],
    'Maha Kumbh': [(1, 1), (4, 30)],
    'Kanwar Yatra': [(7, 1), (8, 15)],  # July-August
    'Rath Yatra': [(6, 15), (7, 15)]  # June-July
}

def extract_state_from_party(party_name):
    """Extract state name from party name like 'STATE OF KARNATAKA' or 'THE STATE OF UTTAR PRADESH'"""
    party_upper = party_name.upper()
    
    if 'STATE OF' in party_upper:
        # Extract text after "STATE OF"
        parts = party_upper.split('STATE OF')
        if len(parts) > 1:
            state_part = parts[1].strip()
            # Get first word or two (state name)
            state_words = state_part.split()
            if len(state_words) >= 2 and state_words[0] in ['UTTAR', 'MADHYA', 'HIMACHAL', 'ANDHRA', 'ARUNACHAL', 'WEST', 'JAMMU']:
                state = f"{state_words[0]} {state_words[1]}"
            elif state_words:
                state = state_words[0]
            else:
                return None
            
            # Map common variations
            state_mapping = {
                'U.P.': 'UTTAR PRADESH',
                'UP': 'UTTAR PRADESH',
                'M.P.': 'MADHYA PRADESH',
                'MP': 'MADHYA PRADESH',
                'HP': 'HIMACHAL PRADESH',
                'AP': 'ANDHRA PRADESH',
                'GNCT': 'DELHI',
                'NCT': 'DELHI'
            }
            
            state = state_mapping.get(state, state)
            
            if state in STATE_LOCATIONS:
                return state
    
    return None

def get_locations_for_state(state):
    """Get location list for a specific state, or return generic India-wide locations"""
    if state and state in STATE_LOCATIONS:
        return STATE_LOCATIONS[state]
    
    # Return mixed locations from all states if state not identified
    all_locations = []
    for locs in STATE_LOCATIONS.values():
        all_locations.extend(locs[:3])  # Take first 3 from each state
    return all_locations

def get_date_for_festival(festival_name, year_range=(2015, 2024)):
    """Get realistic date for a festival/event"""
    festival_lower = festival_name.lower()
    
    # Find matching festival
    for fest_key, date_ranges in FESTIVAL_DATES.items():
        if fest_key.lower() in festival_lower or festival_lower in fest_key.lower():
            # Pick one of the possible date ranges
            day, month = random.choice(date_ranges)
            year = random.randint(*year_range)
            return f"{day}/{month}/{year}"
    
    # Default: random date
    return f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(*year_range)}"

# =============================================================================
# PARTY TYPE ANALYSIS
# =============================================================================

def analyze_party_type(party_name):
    """Determine if party is individual, company, or government"""
    party_lower = party_name.lower()
    
    # Government entities
    gov_keywords = ['state of', 'union of india', 'government', 'commissioner', 'director', 
                    'secretary', 'ministry', 'department', 'authority', 'board', 'corporation',
                    'municipal', 'gram panchayat', 'collector', 'superintendent', 'inspector']
    if any(keyword in party_lower for keyword in gov_keywords):
        return 'government'
    
    # Companies
    company_keywords = ['ltd', 'limited', 'pvt', 'private', 'company', 'corporation', 
                       'inc', 'bank', 'm/s', 'industries', 'enterprises', 'co.']
    if any(keyword in party_lower for keyword in company_keywords):
        return 'company'
    
    return 'individual'

def determine_case_category(pet_type, res_type, petitioner, respondent):
    """Determine case category based on parties"""
    pet_lower = petitioner.lower()
    res_lower = respondent.lower()
    
    # Criminal cases - State vs Individual
    if 'state of' in res_lower or 'state of' in pet_lower:
        return 'criminal'
    
    # Tax/Service cases - Individual vs Government authorities
    if pet_type == 'individual' and res_type == 'government':
        if any(word in res_lower for word in ['commissioner', 'income tax', 'gst', 'customs', 'excise']):
            return 'tax'
        elif any(word in res_lower for word in ['secretary', 'director', 'superintendent', 'authority']):
            return 'service'
        return 'constitutional'
    
    # Commercial - Company vs Company or Company vs Individual
    if pet_type == 'company' or res_type == 'company':
        return 'commercial'
    
    # Family matters - Individual vs Individual with family keywords
    if pet_type == 'individual' and res_type == 'individual':
        family_keywords = ['wife', 'husband', 'divorce', 'maintenance', 'custody', 'matrimonial']
        if any(keyword in pet_lower or keyword in res_lower for keyword in family_keywords):
            return 'family'
        
        # Property disputes
        property_keywords = ['property', 'land', 'plot', 'partition', 'title', 'possession']
        if any(keyword in pet_lower or keyword in res_lower for keyword in property_keywords):
            return 'property'
    
    # Default to civil
    return 'civil'

# =============================================================================
# MEGA CRIMINAL CASE TEMPLATES - TRUE VARIETY
# =============================================================================

# MURDER CASES - Different methods, motives, scenarios
murder_scenarios = [
    # Format 1: Narrative style
    {
        'method': 'poisoning',
        'template': "On {date}, the deceased {victim_name} collapsed after consuming food at {location}. Post-mortem revealed presence of {poison} in fatal quantities. Investigation disclosed that accused {accused_role} had purchased {poison} from {shop} days prior. Motive established was {motive}. {witnesses} witnesses testified seeing accused mixing substance in victim's {food_item}. Forensic report confirmed {poison} in stomach contents. Chemical examiner's report corroborated poisoning. Accused's {behavior} after incident raised suspicion. Defense claimed {defense}. Medical evidence proved {medical_finding}. Court convicted under Section {section} IPC based on {evidence_type}."
    },
    {
        'method': 'stabbing',
        'template': "The incident occurred on {date} at {location} when accused attacked deceased with {weapon}. Victim suffered {injury_count} stab wounds on {body_parts}. Death was instantaneous/occurred after {hours} hours. Eye-witnesses {witness_names} testified that accused and victim had {dispute_type} over {dispute_reason}. Accused was apprehended {capture_time} with blood-stained {weapon} and clothes. Forensic analysis matched blood groups. Post-mortem revealed {medical_details}. Accused confessed to {confession}. Motive was {motive}. Court found accused guilty under Section {section} IPC."
    },
    {
        'method': 'shooting',
        'template': "On {date} at approximately {time}, deceased was shot {bullet_count} times at {location}. Ballistic examination revealed bullets were fired from {weapon_type} recovered from accused's possession. Death occurred due to {injury_type} causing {medical_cause}. Witnesses heard {sound_description} and saw accused fleeing. CCTV footage from {cctv_location} captured the incident. Accused had {motive} as motive. Gun license verification showed {license_status}. Forensic evidence including {forensic_items} conclusively proved guilt. Convicted under Section {section} IPC with {sentence}."
    },
    {
        'method': 'strangulation',
        'template': "Deceased {victim_name} was found dead on {date} with ligature marks on neck. Post-mortem confirmed death by {strangulation_type}. {item_used} was recovered from scene. Accused {accused_name}, {relation} of victim, was last person seen with deceased at {location}. Motive was {motive}. Victim had told {confidant} about {threat} from accused. Struggle marks indicated {struggle_details}. Fingernail scrapings matched accused's DNA. Accused's {behavior} and {lie_details} established guilt. Convicted under Section {section} IPC."
    },
    {
        'method': 'burning',
        'template': "On {date}, victim suffered {burn_percentage}% burns and died on {death_date}. Dying declaration recorded by {authority} stated that {accused_name} poured {substance} and set victim ablaze. Incident occurred at {location} following {dispute}. Motive was {motive}. Forensic analysis detected {accelerant} at scene. Accused had purchased {substance} from {vendor} prior to incident. Neighbors heard {sounds} and victim's screams. Medical evidence confirmed {burn_type}. Accused's {defense} rejected. Convicted under Section {section} IPC."
    },
    {
        'method': 'drowning',
        'template': "Body of {victim_name} recovered from {water_body} on {date}. Post-mortem revealed death by drowning with {injury_details} suggesting foul play. Witnesses saw accused and victim arguing near {location}. Victim's {clothing} had tears and accused's DNA under fingernails. Accused claimed {alibi} but call records placed him at scene. Motive was {motive}. Water in lungs confirmed drowning. Absence of suicide note and {evidence_items} proved homicidal drowning. Convicted under Section {section} IPC."
    },
    {
        'method': 'hit and run',
        'template': "On {date} at {time}, {victim_name} was hit by vehicle driven by accused at {location}. Victim died on spot due to {injury_type}. Accused fled scene but vehicle {vehicle_type} was traced through {tracing_method}. Paint samples from victim's clothes matched accused's vehicle. Accused was in {condition} at time. CCTV footage showed {video_evidence}. Witnesses noted {witness_details}. Motive was {motive}. Accused's {defense} disproved by evidence. Convicted under Sections {section} IPC and {mv_act}."
    },
    {
        'method': 'honor killing',
        'template': "Deceased {victim_name} and {partner_name} were killed on {date} for {reason}. Accused family members, including {accused_names}, opposed the {relationship_type}. Victims were {action} and bodies found at {location}. Post-mortem revealed {murder_method}. Khap panchayat/family had threatened victims on {threat_date}. Witnesses testified to {threats}. Accused claimed {cultural_defense} but court held it unjustifiable. Murder was pre-planned as evidenced by {planning_details}. All accused convicted under Section {section} IPC for {verdict}."
    },
    {
        'method': 'dowry death',
        'template': "Within {timeframe} of marriage, {victim_name} died under suspicious circumstances on {date}. Husband {accused_name} and in-laws caused death due to dowry demands of {dowry_amount} and {dowry_items}. Victim had complained to {authority} about {harassment_details}. Post-mortem revealed {cause}. Dying declaration/suicide note mentioned {dowry_demands}. Witnesses including {witnesses} testified to harassment. Stridhan articles worth Rs. {value} were not returned. Medical evidence showed {injuries}. Convicted under Section {section} IPC and Dowry Prohibition Act."
    },
    {
        'method': 'acid attack',
        'template': "On {date}, accused threw acid on {victim_name} at {location} causing {burn_percentage}% burns. Victim's statement recorded described attack by {accused_name}. Motive was {motive}. Acid purchase traced to {source}. Medical treatment records show {treatment_details}. Victim underwent {surgeries} surgeries. Permanent disfigurement resulted. Witnesses saw {witness_details}. Forensic analysis confirmed {acid_type}. Convicted under Section {section} IPC with enhanced punishment for grievous injuries."
    },
    {
        'method': 'mob lynching',
        'template': "On {date}, {victim_name} was lynched by mob of {mob_size} persons at {location} on suspicion of {accusation}. Victim died due to {injuries}. Accused persons {accused_list} were identified through {identification_method}. Video footage showed {video_details}. Post-mortem revealed {medical_findings}. No evidence of {accusation} found. Mob was incited by {instigator}. Police arrived {delay} later. Witnesses testified to {witness_account}. All accused convicted under Sections {section} IPC for mob violence resulting in death."
    },
    {
        'method': 'infanticide',
        'template': "Newly born {gender} child found dead on {date} at {location}. Post-mortem revealed {cause_of_death}. Investigation traced mother as {accused_name}. Motive was {motive}. Medical examination of mother confirmed recent childbirth. Accused admitted to {confession}. Reasons stated were {reasons}. Baby was born {circumstance}. No registration of birth. Evidence of {evidence_details}. Convicted under Section {section} IPC for infanticide."
    },
    {
        'method': 'gang murder',
        'template': "On {date}, {victim_name} was killed by gang of {gang_size} accused at {location}. Attack was due to {gang_rivalry}. Victim suffered {injury_count} injuries from {weapons}. Eye-witnesses {witnesses} identified accused {accused_names}. Call records showed {communication}. All accused arrested within {timeframe}. Each accused's role: {role_details}. Motive was {motive}. Forensic evidence linked {forensic_link}. Conspiracy established through {conspiracy_evidence}. All convicted under Sections {section} IPC read with {conspiracy_section}."
    }
]

# THEFT/ROBBERY CASES - Different types
theft_scenarios = [
    {
        'type': 'house burglary',
        'template': "On {date}, complainant's house at {location} was burgled. Articles stolen included {items} valued at Rs. {amount}. Entry was through {entry_method}. Neighbors noticed {suspicious_activity}. Accused {accused_name} was caught trying to sell {item} at {shop}. Upon interrogation, recovered {recovery_items}. Accused confessed to {confession}. Fingerprints from {location} matched accused's. Previous burglary record of accused in {area} established modus operandi. Convicted under Section {section} IPC."
    },
    {
        'type': 'vehicle theft',
        'template': "On {date}, {vehicle_type} bearing registration {registration} was stolen from {location}. FIR lodged immediately. Vehicle traced to {destination} after {days} days. Accused {accused_name} was found in possession without documents. Vehicle identification number matched stolen vehicle. Accused had {fake_documents}. Recovery panchnama drawn. Accused is habitual offender with {previous_cases} previous theft cases. Engine and chassis numbers were being tampered. Convicted under Sections {section} IPC and Motor Vehicles Act."
    },
    {
        'type': 'pickpocketing',
        'template': "On {date} at {location}, complainant's {item} containing {contents} and Rs. {amount} was stolen by accused through pickpocketing. Incident occurred in {circumstance}. Accused was caught red-handed by {witness} while attempting to {action}. Stolen articles recovered from accused's possession. CCTV footage showed accused operating near {area}. Accused has {criminal_record} similar offenses. Modus operandi involves {method}. Convicted under Section {section} IPC."
    },
    {
        'type': 'shop theft',
        'template': "CCTV footage from shop at {location} dated {date} showed accused {accused_name} stealing {items} worth Rs. {amount}. Accused entered shop as customer and {method}. Shop owner filed complaint immediately. Accused was arrested from {residence} and stolen goods recovered. Accused admitted to selling some items at {destination}. Similar pattern in {other_shops}. Previous shoplifting convictions. Convicted under Section {section} IPC with compensation ordered."
    },
    {
        'type': 'jewelry theft',
        'template': "On {date}, jewelry worth Rs. {amount} stolen from {location}. Items included {jewelry_items}. Investigation revealed {method}. Accused {accused_name}, {occupation}, had {access_or_opportunity}. Jewelry recovered from {recovery_location}. Pawn shop owner identified accused. Some jewelry had been melted. Accused's {financial_trouble} established motive. Forensic evidence: {forensic}. Previous involvement in {similar_cases}. Convicted under Section {section} IPC."
    },
    {
        'type': 'robbery with violence',
        'template': "On {date} at {time}, accused robbed {victim} of {items} worth Rs. {amount} at {location}. Violence used: {violence_type}. Victim suffered {injuries}. Accused {accused_details} threatened with {weapon}. Witness {witness_name} saw and identified accused. Stolen items recovered from {location}. Medical examination confirmed {medical}. Accused has criminal antecedents in {area}. Identification parade conducted. Convicted under Section {section} IPC with rigorous imprisonment."
    },
    {
        'type': 'bank theft',
        'template': "On {date}, accused {accused_name}, employee of {bank}, committed theft of Rs. {amount} from {vault_or_accounts}. Audit revealed {discrepancy}. Investigation showed {method}. Accused had created {fake_entries}. Money trail led to {destination}. Part amount recovered from {location}. Accused confessed to {confession}. Breach of trust as employee. Convicted under Sections {section} IPC including criminal breach of trust."
    },
    {
        'type': 'cattle theft',
        'template': "On {date}, complainant's {cattle_type} valued at Rs. {amount} was stolen from {location}. Accused {accused_name} was found transporting {cattle_count} cattle towards {destination}. Cattle identified by {identification_marks}. Accused could not produce documents. Previous cases of cattle theft in {area}. Accused part of {gang_details}. Recovery panchnama prepared. Convicted under Section {section} IPC and relevant Cattle Protection Act provisions."
    },
    {
        'type': 'cyber fraud theft',  
        'template': "Complainant received {phishing_method} on {date} asking to {action}. Complainant shared {details} and Rs. {amount} was debited from account. Transaction traced to {account_details}. Accused {accused_name} operated from {location}. Cyber forensics revealed {technical_details}. Multiple victims identified. Accused part of organized cyber crime syndicate. Convicted under Section {section} IPC and IT Act for cyber fraud and cheating."
    }
]

# RAPE/SEXUAL ASSAULT CASES - Sensitive but varied
sexual_assault_scenarios = [
    {
        'template': "On {date}, victim {age} years old was sexually assaulted by accused {accused_name} at {location}. Victim's statement recorded under Section 164 CrPC described {incident_details}. Medical examination confirmed {medical_findings}. DNA analysis matched accused's sample. Accused {relation_to_victim} had {opportunity}. Victim identified accused in {identification}. Defense of {defense} rejected. POCSO Act applicable due to victim's age. Convicted under Section {section} IPC and POCSO Act with {sentence}."
    },
    {
        'template': "Gang rape case dated {date} where victim was assaulted by {accused_count} accused at {location}. Victim was {circumstance} when accused persons {action}. Medical evidence showed {injuries}. All accused identified by victim. DNA evidence matched {accused_names}. Call records established {conspiracy}. Each accused's role: {role_details}. Conviction under Section {section} IPC with death penalty/life imprisonment for all accused."
    },
    {
        'template': "Accused {accused_name}, {occupation}, assaulted minor victim aged {age} on {date} at {location}. Incident came to light when {discovery_method}. Victim's testimony corroborated by {evidence}. Medical examination revealed {findings}. Accused was known to victim as {relation}. Pattern of abuse over {duration}. POCSO Act provisions invoked. Psychological trauma evident. Convicted with enhanced punishment under POCSO Act."
    },
    {
        'template': "On {date}, victim was raped by accused after being administered {substance} at {location}. Victim regained consciousness and reported to {authority}. Medical tests confirmed presence of {drug} and sexual assault. CCTV showed accused {cctv_details}. Accused's {defense} disproved by toxicology report. Accused had similar modus operandi in {previous_cases}. Convicted under Sections {section} IPC with aggravated punishment."
    },
    {
        'template': "Marital rape case where wife filed complaint of forced sexual relations by husband on {date}. Despite refusal, husband {action} causing {injuries}. Medical evidence supported complaint. Husband's abusive behavior established through {witnesses}. Domestic violence history documented. Though not rape under IPC, convicted under Domestic Violence Act and Section {section} for causing hurt and cruelty."
    }
]

# KIDNAPPING CASES
kidnapping_scenarios = [
    {
        'template': "On {date}, {victim_name} aged {age} was kidnapped from {location} by accused {accused_name}. Ransom demand of Rs. {amount} received through {medium}. Victim rescued from {rescue_location} on {rescue_date}. Victim identified accused. Ransom calls traced. Accused's {motive}. Victim was kept {confinement_details}. Medical examination showed {condition}. Convicted under Section {section} IPC for kidnapping and extortion."
    },
    {
        'template': "Minor {victim_name} aged {age} went missing on {date} from {location}. Parents filed missing complaint. Investigation revealed accused {accused_name} had enticed victim with {enticement}. Victim recovered from {destination} on {recovery_date}. Accused had {motive}. Victim's statement recorded. Accused is {accused_background}. Convicted under Section {section} IPC and POCSO Act for kidnapping minor."
    },
    {
        'template': "On {date}, {victim_name} kidnapped for {purpose} by accused persons {accused_names}. Victim taken to {location} and {treatment}. Rescue operation conducted on {date}. Victim identified all accused. Motive: {motive}. Evidence: {evidence_details}. Accused belong to {criminal_gang}. Victim's {ordeal_details}. Convicted under Sections {section} IPC for conspiracy and kidnapping."
    },
    {
        'template': "Bride kidnapping case dated {date} where {victim_name} was forcibly abducted by {accused_name} and relatives. Marriage ceremony performed without consent at {location}. Victim escaped and reported to police. Medical examination confirmed {findings}. Accused claimed {defense} but victim's testimony clear. Conviction under Sections {section} IPC for kidnapping and rape."
    }
]

# MISSING PERSON CASES
missing_person_scenarios = [
    {
        'template': "On {date}, {person_name} aged {age} went missing from {location}. Last seen at {last_location} wearing {clothing}. Family filed missing complaint. Investigation revealed {findings}. Person was traced to {found_location} on {found_date} in {condition}. Person had {reason_for_missing}. Case closed as {closure_status}."
    },
    {
        'template': "Missing person report filed on {date} for {person_name}. Extensive search conducted. CCTV footage showed person at {location}. Mobile phone last location: {tower_location}. After {days} days, body found at {discovery_location}. Post-mortem revealed {cause_of_death}. Investigation converted to murder case. Accused {accused_name} arrested. Motive: {motive}."
    },
    {
        'template': "On {date}, {person_name} left home and didn't return. Social media appeals made. Person traced through {tracing_method}. Found living at {location} voluntarily. Person had left due to {reason}. Family counseling provided. No criminal angle found. Case closed."
    }
]

# TRAFFIC/VEHICULAR CASES
traffic_scenarios = [
    {
        'template': "Road accident on {date} at {location} caused by accused's rash and negligent driving. {vehicle_type} driven by accused hit {victim_vehicle_or_person} causing death of {victim_name}. Accused was {condition} at time. Blood alcohol content: {alcohol_level}. Speed estimated at {speed} in {limit} zone. Witnesses testified to {witness_account}. Victim died due to {injuries}. Convicted under Section {section} IPC and Motor Vehicles Act."
    },
    {
        'template': "On {date}, accused driving {vehicle_type} jumped red light at {intersection} and collided with {victim_vehicle_or_person}. {casualty_count} persons died. Traffic CCTV showed accused's violation. Vehicle was overspeeding at {speed}. Brake failure claimed but mechanical inspection showed {findings}. Accused has {previous_violations} traffic violations. Convicted under Section {section} IPC for causing death by negligence."
    }
]

# STAMPEDE CASES
stampede_scenarios = [
    {
        'template': "Stampede occurred on {date} at {location} during {event} resulting in {death_count} deaths. Victims died due to {cause}. Investigation revealed {failure_details}. Organizers {accused_names} failed to {safety_measures}. Crowd size was {crowd_count} against capacity of {capacity}. Police permission had {permission_status}. Emergency exits were {exit_status}. Criminal negligence established. Convicted under Section {section} IPC for causing death by negligence."
    },
    {
        'template': "During {festival_or_event} on {date} at {venue}, stampede killed {victims_count} persons. Accused {organizer_names} despite knowing risk of overcrowding did not {precautions}. Barricading was {barricade_status}. Medical facilities were {medical_status}. Rumor of {rumor} triggered panic. Previous incidents at venue ignored. Convicted under Section {section} IPC for culpable homicide not amounting to murder."
    }
]

# =============================================================================
# FAMILY CASES - MASSIVE VARIETY
# =============================================================================

# DIVORCE CASES - Different grounds
divorce_scenarios = [
    {
        'ground': 'cruelty',
        'template': "Petition under Section 13(1)(ia) Hindu Marriage Act for divorce on ground of cruelty. Petitioner {petitioner} married to respondent {respondent} on {marriage_date}. Allegations: {cruelty_acts}. Respondent subjected petitioner to {physical_or_mental_cruelty}. Incidents dated {incident_dates}. Medical records showed {medical_evidence}. Witnesses {witnesses} corroborated. Respondent's {defense}. Court found {findings}. Cruelty both physical and mental proved. Decree of divorce granted dissolving marriage."
    },
    {
        'ground': 'adultery',
        'template': "Divorce petition filed on ground of adultery under Section 13(1)(i). Petitioner alleged respondent having illicit relationship with {person_name}. Evidence: {evidence_list}. Private investigator's report dated {date} showed {findings}. Hotel records, photographs, witness statements established adultery. Respondent denied but evidence overwhelming. Court held adultery proved. Marriage irretrievably broken. Decree of divorce granted."
    },
    {
        'ground': 'desertion',
        'template': "Petition for divorce on ground of desertion for continuous period of {years} years. Respondent {respondent} left matrimonial home on {date} without reasonable cause. Petitioner made attempts at reconciliation on {dates}. Respondent refused to return. Legal notice sent on {notice_date} unanswered. Desertion both factual and intentional. Animus deserendi proved. Court granted decree of divorce under Section 13(1)(ib)."
    },
    {
        'ground': 'conversion',
        'template': "Divorce sought on ground that respondent ceased to be Hindu by conversion to {religion} on {date}. Certificate of conversion produced. Respondent admitted conversion. Marriage performed under Hindu rites. Petitioner continued to practice Hinduism. Ground under Section 13(1)(ii) satisfied. Decree of divorce granted."
    },
    {
        'ground': 'unsound mind',
        'template': "Divorce petition under Section 13(1)(iii) on ground of unsound mind. Respondent suffering from {mental_illness} since {duration}. Medical reports from {hospital_or_doctor} dated {dates} established mental disorder. Respondent incapable of performing marital duties. Treatment undertaken but incurable. Expert testimony of {expert} confirmed condition. Court granted divorce on ground of incurable mental illness."
    },
    {
        'ground': 'leprosy',
        'template': "Petition for divorce on ground of virulent and incurable leprosy under Section 13(1)(iv). Medical certificate from {authority} dated {date} certified respondent suffering from {type} leprosy. Disease communicable and incurable. Petitioner in danger of infection. Respondent undergoing treatment at {facility} but condition incurable. Court granted decree of divorce."
    },
    {
        'ground': 'venereal disease',
        'template': "Divorce sought under Section 13(1)(v) on ground of venereal disease in communicable form. Respondent suffering from {disease}. Medical reports confirmed {findings}. Disease contracted through {source}. Petitioner at risk. Treatment history showed {treatment_details}. Condition communicable and respondent refusing treatment. Decree of divorce granted protecting petitioner's health."
    },
    {
        'ground': 'renunciation',
        'template': "Petition under Section 13(1)(vi) on ground that respondent renounced the world and entered {religious_order} on {date}. Evidence: {evidence}. Respondent has been living as {ascetic_type} at {location}. Respondent has no intention to return to marital life. Letters from {authority} confirmed renunciation. Decree of divorce granted."
    },
    {
        'ground': 'presumed dead',
        'template': "Divorce petition under Section 13(1)(vii) stating respondent not heard of as alive for {years} years. Respondent went missing on {date} from {location}. Police complaint filed. Extensive searches conducted. Inquiries with {persons_or_places} yielded no information. Presumption of death arises. Court granted decree of divorce dissolving marriage."
    },
    {
        'ground': 'no cohabitation',
        'template': "Divorce sought under Section 13(1A)(ii) on ground of no resumption of cohabitation for {years} years after decree of judicial separation granted on {decree_date}. Despite decree, parties did not resume cohabitation. Efforts at reconciliation failed. Separation continues. Court satisfied that marriage has irretrievably broken down. Decree of divorce granted."
    },
    {
        'ground': 'irretrievable breakdown',
        'template': "Though not statutory ground, court invoked Article 142 powers finding irretrievable breakdown of marriage. Parties separated since {date} living apart for {years} years. Reconciliation attempts failed. Marriage is dead emotionally. Continuing marriage serves no purpose. Both parties moved on. In interest of justice, court dissolved marriage by decree of divorce."
    }
]

# DOMESTIC VIOLENCE CASES
domestic_violence_scenarios = [
    {
        'template': "Protection application under Domestic Violence Act by aggrieved wife {petitioner} against husband {respondent}. Allegations: {violence_acts} on dates {dates}. Medical certificates showed {injuries}. Police complaints filed on {complaint_dates}. Respondent {employment_status} subjected wife to {types_of_abuse}. Children aged {children_ages} also affected. Protection Officer's report supported allegations. Court issued protection order restraining respondent from {restrictions}. Residence order granted allowing wife to stay in shared household. Monetary relief of Rs. {amount} per month ordered."
    },
    {
        'template': "DV case filed by {petitioner} against {respondent} and in-laws. Harassment for dowry of {dowry_amount} and {dowry_items} since marriage on {date}. Physical and mental torture documented. Victim forced to {forced_actions}. Medical evidence: {medical}. Stridhan articles worth Rs. {value} not returned. Police reports dated {dates}. Court found prima facie case. Protection order issued. Residence order in favor of petitioner. Compensation of Rs. {compensation} awarded for mental trauma and litigation costs."
    },
    {
        'template': "Application by elderly mother {petitioner} against son {respondent} for domestic violence. Son and daughter-in-law subjected mother to {abuse_types}. Denied basic necessities. Forced to {actions}. Property dispute was {property_details}. Witnesses {witnesses} testified. Senior citizen provisions invoked. Court ordered {orders}. Maintenance of Rs. {amount} directed. Protection from dispossession granted."
    },
    {
        'template': "Domestic violence petition by live-in partner {petitioner} against {respondent}. Relationship since {date}. Subjected to {violence_type}. Attempted eviction from shared household. Financial abuse: {financial_abuse}. Court held live-in relationship covered under DV Act. Protection order issued. Right to reside in shared household upheld. Maintenance awarded. Police protection directed."
    }
]

# MAINTENANCE CASES
maintenance_scenarios = [
    {
        'template': "Maintenance petition under Section 125 CrPC by wife {petitioner} against husband {respondent}. Married since {date}. Husband earning Rs. {income} per month as {occupation}. Wife has {wife_income_status}. {children_count} children aged {ages}. Husband neglected/refused to maintain wife and children. Wife unable to maintain herself. Reasonable expenses estimated at Rs. {expenses}. Court ordered maintenance of Rs. {amount} per month to wife and Rs. {child_amount} per child."
    },
    {
        'template': "Maintenance application by divorced wife under Section 125 CrPC. Divorce decree passed on {date}. No maintenance awarded in divorce. Wife {age} years unable to maintain herself due to {reasons}. Ex-husband earning Rs. {income}. Wife's expenses Rs. {expenses} per month. Court held divorced wife entitled to maintenance. Ordered Rs. {amount} per month till remarriage or death."
    },
    {
        'template': "Parents aged {father_age} and {mother_age} filed maintenance application under Section 125 CrPC against son {respondent}. Son earning Rs. {income} but refusing to maintain aged parents. Parents unable to maintain themselves due to {reasons}. Medical expenses for {ailments}. Statutory duty of son to maintain parents. Court ordered Rs. {amount} per month maintenance."
    },
    {
        'template': "Interim maintenance application in pending divorce case. Wife seeking maintenance pendente lite. Husband's income Rs. {income} per month. Wife left matrimonial home due to {reasons}. {children_count} children in wife's custody. Husband should support wife during litigation. Court granted interim maintenance of Rs. {amount} per month to wife and Rs. {child_amount} per child."
    }
]

# CUSTODY CASES
custody_scenarios = [
    {
        'template': "Custody petition for {children_count} children aged {ages}. Parents separated or divorced. Mother seeks custody based on {mother_reasons}. Father seeks custody claiming {father_reasons}. Children currently with {current_custody}. Welfare of children paramount. Children of tender age. Mother's {employment_or_financial_status}. Father's {employment_or_financial_status2}. Psychological evaluation showed {evaluation}. Court awarded custody to {parent} with visitation rights to other parent every {visitation_schedule}."
    },
    {
        'template': "Habeas Corpus petition by father for custody of minor children allegedly illegally kept by mother. Mother left matrimonial home with children on {date}. Father wants custody. Mother alleges {allegations}. Children aged {ages}. Court examined children. Children expressed {preference}. Welfare of children considered. Court granted custody to {parent} considering {factors}. Maintenance and visitation arranged."
    },
    {
        'template': "Custody battle between parents and grandparents. Parents {status}. Grandparents caring for child aged {age} since {duration}. Best interest of child. Child's attachment to grandparents. Parents' {fitness_status}. Court held {decision} considering child's welfare, stability, and emotional bonds. Custody granted to {person} with {conditions}."
    }
]

# =============================================================================
# PROPERTY CASES - MASSIVE VARIETY
# =============================================================================

property_scenarios = [
    {
        'type': 'title dispute',
        'template': "Suit for declaration of title and permanent injunction regarding property Survey No. {survey} at {location}. Plaintiff claims title through {title_source} dated {date}. Defendant claims title through {def_title_source}. Revenue records show {revenue_entry}. Possession with {possession_party} since {possession_years} years. Plaintiff produced {plaintiff_docs}. Defendant produced {defendant_docs}. Court examined chain of title. Found plaintiff's title {finding}. Decree {decree} passed."
    },
    {
        'type': 'partition',
        'template': "Partition suit by co-owner {plaintiff} against co-owners {defendants}. Property inherited from {ancestor} who died on {date}. Total extent {total_extent}. Plaintiff's share {plaintiff_share}. Property includes {property_description}. Attempts at amicable partition failed. Commissioner appointed for partition. Property valued at Rs. {value}. Actual partition {partition_status}. Court decreed partition by {partition_method} with {allocations}."
    },
    {
        'type': 'adverse possession',
        'template': "Suit for declaration of title based on adverse possession. Plaintiff in possession of property at {location} since {start_year}. Possession is {possession_nature} for over {years} years. Original owner {owner} has not {owner_action}. Plaintiff paid property tax since {tax_year}. Neighbors testified to plaintiff's {testimony}. Defendant claims {defendant_claim}. Court examined {examination}. Found adverse possession {finding}. Title declared in favor of {party}."
    },
    {
        'type': 'specific performance',
        'template': "Suit for specific performance of agreement to sell dated {date}. Sale agreement for property at {location} for Rs. {amount}. Plaintiff paid earnest money of Rs. {advance}. Defendant to execute sale deed by {deadline}. Defendant refused on grounds that {refusal_reason}. Plaintiff always ready and willing. Time was {time_essence}. Market value now Rs. {current_value}. Defendant's refusal is {refusal_nature}. Court {decree} specific performance with {conditions}."
    },
    {
        'type': 'easement',
        'template': "Suit for declaration of right of way over defendant's property. Plaintiff's property at {location} landlocked. Right of way claimed through {path} since {years} years. Easement by {easement_type}. Defendant obstructed path on {obstruction_date} by {obstruction_method}. Plaintiff's {usage_evidence}. Village map shows {map_evidence}. Defendant claims {defense}. Court held easement {holding}. Permanent injunction {injunction_status}."
    },
    {
        'type': 'boundary dispute',
        'template': "Suit for demarcation of boundary between properties. Plaintiff's Survey No. {pl_survey} and Defendant's Survey No. {def_survey} at {location}. Dispute arose when {dispute_origin}. Boundaries as per revenue records: {revenue_boundary}. Actual occupation: {actual_occupation}. Survey commissioned showed {survey_findings}. Plaintiff claims {plaintiff_claim}. Defendant claims {defendant_claim}. Court ordered demarcation as per {demarcation_basis}."
    },
    {
        'type': 'landlord-tenant',
        'template': "Eviction suit under Rent Control Act. Premises at {location} let out on {tenancy_date} at rent of Rs. {rent} per month. Tenant defaulted in rent since {default_date}. Arrears: Rs. {arrears}. Landlord issued notice on {notice_date}. Tenant's defense: {tenant_defense}. Landlord also seeks eviction for {additional_grounds}. Premises required for {requirement}. Court found {findings}. Eviction {eviction_status} ordered with arrears of Rs. {arrears_amount}."
    },
    {
        'type': 'redemption of mortgage',
        'template': "Suit for redemption of mortgage executed on {mortgage_date} for Rs. {amount}. Property mortgaged: {property_description}. Interest rate {rate}% per annum. Principal and interest Rs. {total}. Plaintiff deposited Rs. {deposit} in court. Mortgagee claims {mortgagee_claim}. Accounts settled. Balance due Rs. {balance}. Plaintiff entitled to redeem. Decree for redemption passed on payment of Rs. {final_amount} within {period}."
    },
    {
        'type': 'cancellation of sale deed',
        'template': "Suit for cancellation of sale deed dated {date} for property at {location}. Consideration stated Rs. {stated_amount}. Plaintiff claims sale deed obtained by {fraud_method}. Allegations: {allegations}. Defendant's defense: {defense}. Plaintiff was {plaintiff_status}. Evidence showed {evidence}. Sale deed is {deed_status}. Court held {holding}. Sale deed {cancellation_status}."
    },
    {
        'type': 'trespass',
        'template': "Suit for permanent injunction restraining trespass. Plaintiff owner of property at {location}. Defendant trespassing since {trespass_date} by {trespass_method}. Despite notice dated {notice_date}, trespass continues. Plaintiff suffering {damages_type}. Defendant claims {defendant_claim}. Title with {title_party}. Possession with {possession_party}. Court found unauthorized trespass. Perpetual injunction granted restraining defendant from {injunction_terms}."
    },
    {
        'type': 'encroachment',
        'template': "Suit for removal of encroachment. Defendant encroached upon plaintiff's property measuring {encroached_area} at {location}. Encroachment consists of {encroachment_description}. Encroachment since {encroachment_date}. Plaintiff's title through {title_source}. Revenue records support plaintiff. Defendant claims {defense}. Local Commissioner's report confirmed {report_findings}. Court ordered removal of encroachment with costs. Defendant to vacate within {period}."
    },
    {
        'type': 'inheritance dispute',
        'template': "Suit for partition and declaration regarding inherited property. Deceased {deceased_name} died intestate on {death_date} leaving property worth Rs. {value}. Legal heirs: {heirs_list}. Plaintiff's claim: {plaintiff_claim}. Defendant's claim: {defendant_claim}. Dispute over {dispute_issue}. Succession certificate {certificate_status}. Hindu Succession Act/Muslim law applicable. Court declared {declaration}. Property to be divided as {division_ratio}."
    }
]

# =============================================================================
# CIVIL CASES - DIVERSE TYPES
# =============================================================================

civil_scenarios = [
    {
        'type': 'breach of contract',
        'template': "Suit for damages for breach of contract dated {contract_date}. Contract between plaintiff and defendant for {contract_purpose}. Terms: {contract_terms}. Consideration Rs. {amount}. Defendant breached by {breach_details} on {breach_date}. Plaintiff performed his part. Plaintiff suffered loss of Rs. {loss_amount}. Defendant's defense: {defense}. Contract was {contract_validity}. Breach proved. Court awarded damages of Rs. {damages} with interest @ {rate}% per annum."
    },
    {
        'type': 'recovery of money',
        'template': "Suit for recovery of Rs. {amount} advanced as {loan_type} on {loan_date}. Defendant acknowledged loan by {acknowledgment_method}. Repayment date {repayment_date}. Defendant failed to repay. Legal notice sent on {notice_date} unanswered. Interest at {interest}% per annum. Defendant claims {defense}. Plaintiff proved {proof_method}. Court decreed suit for Rs. {principal} plus interest Rs. {interest_amount} totaling Rs. {total} with future interest and costs."
    },
    {
        'type': 'defamation',
        'template': "Suit for damages for defamation. Defendant published/spoke defamatory statement on {date} stating that plaintiff {defamatory_statement}. Published in {publication_medium}. Plaintiff's reputation damaged. Plaintiff is {plaintiff_status}. Statement is false and malicious. Defendant's defense of {defense}. Plaintiff suffered {damages_details}. Court held statement defamatory. Damages of Rs. {compensation} awarded. Injunction against further defamation granted."
    },
    {
        'type': 'negligence/tort',
        'template': "Suit for damages arising from negligence. On {date} at {location}, defendant's {negligent_act} caused {damage_description} to plaintiff. Plaintiff suffered {injuries_or_losses}. Medical expenses Rs. {medical_expense}. Loss of income Rs. {income_loss}. Defendant owed duty of care. Breach of duty: {breach_details}. Causation established. Defendant's liability: {liability_nature}. Court awarded compensation of Rs. {compensation} including {breakdown}."
    },
    {
        'type': 'declaration suit',
        'template': "Suit for declaration that {declaration_sought}. Plaintiff's case: {plaintiff_case}. Defendant's case: {defendant_case}. Legal question involved: {legal_issue}. Documents produced: {documents}. Law applicable: {applicable_law}. Court examined {examination_details}. Found {findings}. Declared that {declaration}. {consequential_relief} granted."
    },
    {
        'type': 'permanent injunction',
        'template': "Suit for permanent injunction restraining defendant from {act_to_restrain}. Plaintiff is {plaintiff_right}. Defendant threatening to {threatened_act}. Plaintiff will suffer irreparable injury. Balance of convenience in favor of plaintiff. Plaintiff has prima facie case. Defendant's act is {act_nature}. No adequate remedy at law. Court granted permanent injunction restraining defendant from {injunction_terms} with costs."
    },
    {
        'type': 'specific performance contract',
        'template': "Suit for specific performance of contract dated {date} to {contract_obligation}. Plaintiff performed his part by {plaintiff_performance}. Consideration paid Rs. {amount}. Defendant failed to perform by {failure_details}. Time {time_status}. Contract valid and enforceable. Damages inadequate remedy. Plaintiff always ready and willing. Defendant's defense: {defense}. Court decreed specific performance with {modifications} within {timeframe}."
    },
    {
        'type': 'nuisance',
        'template': "Suit for injunction and damages for nuisance. Defendant causing nuisance by {nuisance_act} at {location} since {date}. Plaintiff owner/resident of adjoining property suffering {suffering_details}. Plaintiff complained on {complaint_dates}. Defendant continued. Nuisance is {nuisance_type}. Affecting plaintiff's {affected_rights}. Court held nuisance proved. Permanent injunction issued. Damages of Rs. {damages} awarded. Defendant to abate nuisance within {period}."
    },
    {
        'type': 'guardianship',
        'template': "Petition under Guardians and Wards Act for guardianship of minor {minor_name} aged {age}. Minor's parents {parents_status}. Petitioner {petitioner_relation} seeks guardianship. Minor's property worth Rs. {property_value}. Welfare of minor requires {welfare_reasons}. Other claimants: {other_claimants}. Court examined {examination}. Found petitioner suitable. Welfare of minor paramount. Guardianship granted to {guardian} with conditions: {conditions}."
    },
    {
        'type': 'probate',
        'template': "Petition for grant of probate of Will dated {will_date} executed by {testator} who died on {death_date}. Estate worth Rs. {estate_value}. Beneficiaries: {beneficiaries}. Will executed with due formalities. Testamentary capacity proved. Will attested by {witnesses}. Objections by {objectors} alleging {objections}. Court examined {examination}. Found Will valid. Probate granted to executor {executor_name} with {conditions}."
    }
]

# =============================================================================
# COMMERCIAL CASES - BUSINESS DISPUTES
# =============================================================================

commercial_scenarios = [
    {
        'type': 'company law',
        'template': "Petition under Companies Act for {relief_sought}. Company {company_name} incorporated on {incorporation_date}. Directors: {directors}. Issue involves {issue_description}. Shareholders/creditors: {stakeholders}. Alleged {allegations}. Company's affairs {company_status}. Financial position: {financial_position}. NCLT examined {examination}. Found {findings}. Ordered {order_passed} in interest of company and stakeholders."
    },
    {
        'type': 'arbitration',
        'template': "Arbitration under Arbitration and Conciliation Act arising from {dispute_subject}. Agreement dated {agreement_date} contained arbitration clause. Disputes arose regarding {dispute_details}. Arbitrator {arbitrator_name} appointed. Award dated {award_date} awarded Rs. {award_amount} to {award_favor}. Challenge to award by {challenging_party} on grounds {challenge_grounds}. Court examined {examination}. Award is {award_status}. Upheld/Set aside with reasoning: {reasoning}."
    },
    {
        'type': 'intellectual property',
        'template': "Suit for infringement of {ip_type}. Plaintiff owner of {ip_details} registered as {registration_no}. Defendant infringing by {infringement_act} since {infringement_date}. Plaintiff's {ip_name} has {reputation_details}. Defendant's use causing {damage_type}. Likelihood of confusion. Plaintiff seeks {reliefs}. Defendant's defense: {defense}. Court held infringement proved. Injunction granted. Damages/account of profits of Rs. {damages} awarded."
    },
    {
        'type': 'banking',
        'template': "Suit for recovery by {bank_name} against borrower {borrower}. Loan of Rs. {loan_amount} sanctioned on {loan_date} for {purpose}. Secured by {security_details}. Borrower defaulted since {default_date}. Outstanding: Rs. {outstanding} including interest. Notice under SARFAESI Act issued on {notice_date}. Borrower's objection: {objection}. Bank seeks {relief}. Court examined {examination}. Decreed recovery with {order_details}."
    },
    {
        'type': 'partnership',
        'template': "Suit for dissolution of partnership and accounts. Partnership firm {firm_name} formed on {formation_date} between partners {partners}. Business: {business}. Disputes arose regarding {disputes}. Partnership deed terms: {terms}. Assets worth Rs. {assets}. Liabilities Rs. {liabilities}. Accounts disputed. Commissioner appointed for accounts. Report filed. Court ordered dissolution from {dissolution_date}. Assets to be distributed as {distribution}. Final accounts: {accounts}."
    },
    {
        'type': 'insurance',
        'template': "Claim repudiation by {insurance_company} for policy {policy_no}. Insured event: {event} occurred on {event_date}. Claim of Rs. {claim_amount} filed. Insurer repudiated citing {repudiation_grounds}. Policyholder's case: {policyholder_case}. Policy terms: {policy_terms}. Insurer's investigation: {investigation}. Court examined {examination}. Found {findings}. Insurer directed to pay Rs. {payment_amount} with interest @ {rate}% from {from_date}."
    },
    {
        'type': 'negotiable instruments',
        'template': "Complaint under Section 138 Negotiable Instruments Act. Cheque No. {cheque_no} dated {cheque_date} for Rs. {amount} issued by accused in discharge of {liability}. Cheque dishonored on {dishonor_date} for {dishonor_reason}. Legal notice sent on {notice_date}. Accused failed to pay within 15 days. Accused's defense: {defense}. Complainant proved {proof}. Accused convicted. Fine of Rs. {fine} and compensation of Rs. {compensation} ordered."
    },
    {
        'type': 'franchise',
        'template': "Dispute between franchisor {franchisor} and franchisee {franchisee}. Franchise agreement dated {date} for {business}. Territory: {territory}. Term: {term} years. Franchise fee: Rs. {fee}. Dispute regarding {dispute}. Franchisee alleged {franchisee_allegation}. Franchisor alleged {franchisor_allegation}. Agreement terms: {terms}. Breach by {party}. Court found {findings}. Ordered {order_details}."
    },
    {
        'type': 'consumer protection',
        'template': "Complaint under Consumer Protection Act against {opposite_party}. Complainant purchased {product_or_service} on {date} for Rs. {price}. Defect or deficiency: {defect_details}. Complainant complained on {complaint_date}. Opposite party's response: {op_response}. Loss suffered: Rs. {loss}. Deficiency in service proved. Medical or expert opinion: {expert_opinion}. Forum ordered {order}: compensation Rs. {compensation}, replacement or refund of Rs. {refund_amount}, costs."
    }
]

# =============================================================================
# TAX CASES
# =============================================================================

tax_scenarios = [
    {
        'type': 'income tax',
        'template': "Appeal against income tax order for AY {ay}. Assessee {assessee_type} engaged in {business}. Addition of Rs. {addition_amount} made on account of {addition_reason}. Assessee's explanation: {explanation}. AO held {ao_holding}. CIT(A) {cita_decision}. Issue: {legal_issue}. Precedents: {case_law}. Tribunal held {tribunal_holding}. Addition {addition_status}. Appeal {appeal_result}."
    },
    {
        'type': 'GST',
        'template': "GST dispute for period {period}. Assessee: {assessee}. Demand of Rs. {demand_amount} comprising tax Rs. {tax}, interest Rs. {interest}, penalty Rs. {penalty}. Issue: {issue_description}. Assessee's case: {assessee_case}. Department's case: {dept_case}. Input tax credit: {itc_status}. Invoices: {invoice_status}. Tribunal examined {examination}. Held {holding}. Demand {demand_status}."
    },
    {
        'type': 'customs',
        'template': "Customs appeal regarding import of {goods} under Bill of Entry No. {be_no}. Classification issue: {classification_dispute}. Assessee classified under CTH {assessee_cth}. Department classified under CTH {dept_cth}. Duty differential: Rs. {duty_diff}. Technical opinion: {technical_opinion}. Precedents: {precedents}. Tribunal held classification under {correct_cth}. Duty liability: Rs. {final_duty}. Appeal {result}."
    },
    {
        'type': 'transfer pricing',
        'template': "Transfer pricing dispute for AY {ay}. Transaction: {transaction_type}. ALP determined by TPO: Rs. {alp}. Assessee's price: Rs. {assessee_price}. Adjustment: Rs. {adjustment}. Method applied: {method}. Comparables: {comparables}. Assessee's objections: {objections}. DRP directions: {drp_directions}. Tribunal held {holding}. Adjustment {adjustment_status}."
    },
    {
        'type': 'penalty',
        'template': "Penalty proceedings under Section {section}. Quantum assessment: addition of Rs. {addition}. Penalty levied: Rs. {penalty}. Grounds: {penalty_grounds}. Assessee's defense: {defense}. Explanation offered: {explanation}. Concealment/inaccurate particulars: {finding}. Bonafide belief: {bonafide}. Court held {holding}. Penalty {penalty_result}."
    }
]

# =============================================================================
# SERVICE MATTERS (Government Employment)
# =============================================================================

service_scenarios = [
    {
        'type': 'termination',
        'template': "Writ petition challenging termination order dated {order_date}. Petitioner {petitioner}, {designation}, terminated on grounds of {grounds}. Served since {joining_date}. Inquiry {inquiry_status}. Petitioner's defense: {defense}. Charges: {charges}. Inquiry officer's findings: {findings}. Violation of principles: {violation}. Court examined {examination}. Found {court_finding}. Order {order_status}. Petitioner {reinstatement_status} with {relief_details}."
    },
    {
        'type': 'promotion',
        'template': "Seniority/promotion dispute. Petitioner joined on {date1}. Respondent joined on {date2}. Promotion post: {post}. Seniority list dated {list_date} placed respondent senior. Petitioner challenges based on {challenge_grounds}. Eligibility criteria: {criteria}. Petitioner's case: {petitioner_case}. Department's case: {dept_case}. Court examined {examination}. Held {holding}. Seniority {seniority_result}. Promotion {promotion_result}."
    },
    {
        'type': 'pension',
        'template': "Pension dispute. Petitioner retired on {retirement_date} after {service_years} years service. Pension sanctioned: Rs. {sanctioned_pension}. Petitioner claims entitlement to Rs. {claimed_pension}. Issue: {pension_issue}. Relevant rules: {rules}. Qualifying service: {qualifying_service}. Department's objection: {objection}. Court applied {law_applied}. Held {holding}. Directed payment of Rs. {final_pension} with arrears from {arrears_date}."
    },
    {
        'type': 'disciplinary',
        'template': "Disciplinary proceedings against {employee}, {designation}. Charges: {charges}. Charge sheet issued on {cs_date}. Inquiry conducted by {io}. Findings: {inquiry_findings}. Penalty imposed: {penalty}. Employee challenges on grounds: {challenge_grounds}. Natural justice violation: {nj_violation}. Court found {court_finding}. Penalty {penalty_status}. Employee {employee_status}."
    },
    {
        'type': 'pay fixation',
        'template': "Dispute regarding pay fixation. Petitioner claims benefit of {benefit}. Relevant order/rule: {order_details}. Department {dept_action}. Financial implication: Rs. {amount}. Petitioner's entitlement based on {entitlement_basis}. Department's objection: {objection}. Interpretation of rules: {interpretation}. Court held {holding}. Benefit {benefit_status}. Arrears with interest ordered."
    },
    {
        'type': 'compassionate appointment',
        'template': "Application for compassionate appointment. Applicant {applicant}, {relation} of deceased employee {deceased} who died on {death_date} while in service. Applied on {application_date}. Rejection grounds: {rejection_grounds}. Applicant's case: {case_details}. Dependent: {dependent_status}. Policy provisions: {policy}. Vacancies: {vacancy_status}. Court held {holding}. Compassionate appointment {appointment_status}."
    }
]

# =============================================================================
# CONSTITUTIONAL CASES - PIL, Rights, etc.
# =============================================================================

constitutional_scenarios = [
    {
        'type': 'PIL',
        'template': "Public Interest Litigation concerning {pil_issue}. Petitioner {petitioner_type} raised issue of {issue_description} affecting {affected_persons}. Alleged violation of Article {article}. State's response: {state_response}. Ground reality: {ground_facts}. Expert committee report: {expert_report}. Court examined {examination}. Directions issued: {directions}. Monitoring committee constituted. Compliance to be ensured by {compliance_date}."
    },
    {
        'type': 'habeas corpus',
        'template': "Habeas Corpus petition for {detenu} allegedly {detention_circumstances}. Detention under {detention_law} on {detention_date}. Grounds: {detention_grounds}. Detaining authority: {authority}. Representation: {representation_status}. Procedural safeguards: {safeguards_status}. Court examined {examination}. Grounds {grounds_status}. Detention {detention_validity}. Detenu {detenu_status}."
    },
    {
        'type': 'fundamental rights',
        'template': "Challenge to {challenged_action} as violative of Article {article}. Petitioner's case: {petitioner_case}. State's justification: {state_justification}. Reasonable restrictions under {restriction_clause}. Proportionality test: {proportionality}. Public interest: {public_interest}. Precedents: {precedents}. Court balanced {balancing}. Held {holding}. Action {action_status}."
    },
    {
        'type': 'mandamus',
        'template': "Mandamus petition directing {respondent} to {relief_sought}. Statutory provision: {statutory_provision}. Petitioner's legal right: {legal_right}. Respondent's duty: {respondent_duty}. Refusal grounds: {refusal_grounds}. Discretion vs mandate: {discretion_issue}. Court held {holding}. Mandamus {mandamus_status} directing {direction}."
    },
    {
        'type': 'environmental',
        'template': "Environmental PIL regarding {environmental_issue} at {location}. Petitioner alleged {allegations}. Environmental impact: {impact}. Expert committee findings: {expert_findings}. Clearances: {clearance_status}. Precautionary principle applicable. Sustainable development vs {vs_factor}. Court applied {principles_applied}. Directions: {environmental_directions}. Compensation: {compensation_details}."
    }
]

# Labour & Employment scenarios
labour_scenarios = [
    "Labour dispute concerning non-payment of wages to {worker_count} workers at {establishment}. Workers claimed wages of ₹{wage_amount} for {months} months. Management contended {management_defense}. Labour Commissioner's proceedings dated {commissioner_date}. Award: {award_details}. Back wages: {back_wages}. Reinstatement: {reinstatement}.",
    
    "Industrial dispute regarding illegal termination of {employee_name} working as {designation} at {company}. Service period: {service_years} years. Termination dated {termination_date} on grounds of {termination_grounds}. No enquiry conducted violating principles of natural justice. Union raised dispute. Reference under Industrial Disputes Act. Tribunal held: {tribunal_finding}. Relief: {relief_granted}.",
    
    "Illegal retrenchment case. {retrenched_count} workmen retrenched on {retrenchment_date} citing {closure_reason}. Mandatory retrenchment compensation of {compensation} not paid. No prior notice to government. Section 25N violated. Workmen claimed {years_service} years of service. Relief sought: {relief}. Court ordered: {court_order}.",
    
    "Unfair labour practice case under Schedule IV Item {item_no}. Management changed service conditions without consultation. Union alleged {allegations}. Affected workers: {affected_workers}. Previous settlement dated {settlement_date} violated. Labour court proceedings. Finding: {finding}. Status quo ordered with compensation of {compensation}.",
    
    "Bonus dispute for assessment year {ay}. Workers demanded {bonus_percentage}% bonus. Management offered {offered_percentage}% claiming losses. Available surplus: ₹{surplus}. Allocable surplus calculation disputed. Set on/Set off claimed for previous years. Payment of Bonus Act provisions. Award: {award_percentage}% with arrears of ₹{arrears}.",
    
    "Gratuity payment dispute. Employee {employee} retired on {retirement_date} after {years} years service. Gratuity payable: ₹{gratuity_amount}. Management withheld payment alleging {allegation}. Controlling authority proceedings. Section 4 of Payment of Gratuity Act. Order: {order} with interest @ {interest_rate}%.",
    
    "ESI/PF dues recovery case. Employer failed to deposit contributions for {period}. Amount: ₹{amount}. Workers: {worker_count}. Inspection dated {inspection_date}. Section 406/409 IPC violation. Criminal complaint filed. Assessment under {act_section}. Damages: {damages}.",
    
    "Contract labour dispute. Principal employer {principal} and contractor {contractor}. Abolition of contract labour demanded citing perennial nature. Workers: {workers}. Nature of work: {work_nature}. Working since {since_date}. Appropriate government notification absent. Regularization claimed. Award: {award}."
]

# Intellectual Property scenarios  
ip_scenarios = [
    "Trademark infringement suit. Plaintiff's registered trademark '{plaintiff_mark}' ({reg_no}) used since {user_since}. Defendant adopted deceptively similar mark '{defendant_mark}'. Goodwill: ₹{goodwill}. Confusion likelihood demonstrated. Phonetic similarity: {phonetic}. Visual similarity: {visual}. Trade Marks Act Section 29. Injunction granted. Damages: ₹{damages}.",
    
    "Patent infringement case. Patent No. {patent_no} for {invention} granted on {grant_date}. Claims: {claims}. Defendant manufacturing {infringing_product} incorporating patented invention. Independent claims violated. Doctrine of equivalents applicable. Prior art comparison: {prior_art}. Novelty and inventive step established. Permanent injunction with damages ₹{damages}.",
    
    "Copyright infringement regarding {work_type}. Original work created on {creation_date} by {author}. Registration: {registration}. Defendant copied {copied_elements}. Substantial similarity test satisfied. Originality established. Section 51 Copyright Act violated. Defendant's defense: {defense}. Court held: {holding}. Compensation: ₹{compensation}.",
    
    "Design infringement. Registered design No. {design_no} for {article}. Novelty features: {features}. Defendant's design: {defendant_design}. Eye appeal comparison. Visual comparison test. Designs Act Section 22. Piracy established. Anton Piller order executed. Counterfeit goods: {goods_count}. Damages: ₹{damages}.",
    
    "Passing off action. Plaintiff's unregistered mark '{mark}' used since {since}. Reputation in {territory}. Goodwill: ₹{goodwill}. Defendant's mark '{defendant_mark}'. Misrepresentation: {misrepresentation}. Consumer confusion: {confusion_evidence}. Dilution of distinctiveness. Balance of convenience. Interim injunction granted.",
    
    "Trade secret misappropriation. Confidential information: {information_type}. Ex-employee {employee} joined competitor {competitor}. Non-compete clause dated {nca_date}. Confidentiality agreement breached. Customer list/technical data stolen. Springboard doctrine. Anton Piller relief. Damages: ₹{damages}. Perpetual injunction.",
    
    "Domain name dispute under INDRP. Domain '{disputed_domain}' registered on {reg_date}. Complainant's trademark: {trademark}. Bad faith registration: {bad_faith}. Typo-squatting/Cyber-squatting. No legitimate interest. WIPO principles. Panel order: {panel_order}. Transfer ordered."
]

# Banking & Finance scenarios
banking_scenarios = [
    "Loan recovery suit under Order XXXVII CPC. Loan account No. {account_no}. Sanctioned: ₹{sanctioned} on {sanction_date}. Outstanding: ₹{outstanding} with interest @ {interest}%. Default since {default_date}. Demand notice under Section 13(2) SARFAESI Act dated {notice_date}. Symbolic possession taken on {possession_date}. Borrower's reply: {borrower_defense}. Decree for ₹{decree_amount}.",
    
    "SARFAESI Act Section 13(4) challenge. Secured creditor {bank} issued notice on {notice_date} for ₹{dues}. Objections filed: {objections}. DM proceedings under Section 14. Classification as NPA: {npa_date}. Valuation: ₹{valuation}. Sale notice dated {sale_date}. Statutory deposit ₹{deposit}. Court held: {holding}.",
    
    "DRT case under RDDB Act. Financial institution {fi} vs borrower {borrower}. Facility: ₹{facility}. Outstanding: ₹{outstanding} as on {date}. Wilful default alleged. Personal guarantee invoked. Recovery certificate No. {rc_no}. Attachment: {attached_assets}. Recovery: ₹{recovered}. Balance: ₹{balance}.",
    
    "Negotiable Instruments Act Section 138. Cheque No. {cheque_no} for ₹{amount} dated {cheque_date} drawn on {bank}. Return memo: {return_reason} dated {return_date}. Legal notice under Section 138 sent on {notice_date}. Complaint filed within limitation. Liability: {liability}. Presumption under Section 139. Defence: {defense}. Convicted. Fine: ₹{fine}. Compensation: ₹{compensation}.",
    
    "Insolvency petition under IBC. Corporate debtor: {debtor}. Operational/Financial creditor: {creditor}. Default amount: ₹{default_amount}. Demand notice under Section 8/9 dated {demand_date}. Application under Section 7/9. Information memorandum. CIRP costs: ₹{cirp_costs}. Resolution professional: {rp}. CoC approval: {coc_percentage}%. Liquidation/Resolution: {outcome}.",
    
    "Credit card fraud case. Card holder: {holder}. Card No. XXXX-{last_four}. Disputed transactions: ₹{disputed_amount} on {transaction_dates}. Two-factor authentication bypassed. Fraudulent international transactions. Bank's deficiency: {deficiency}. Chargeback denied. Customer protection. Liability: {liability_determination}. Refund: ₹{refund}.",
    
    "Mortgage suit for sale. Mortgage deed dated {mortgage_date}. Property: {property}. Mortgage amount: ₹{amount}. Default in repayment. Principal: ₹{principal}. Interest: ₹{interest}. Costs: ₹{costs}. Preliminary decree passed. Final decree for sale. Upset price: ₹{upset_price}. Right of redemption."
]

# Motor Accident Claims scenarios
mac_scenarios = [
    "Motor accident claim under Motor Vehicles Act. Accident dated {accident_date} at {accident_location}. Vehicle {vehicle_type} No. {vehicle_no} driven by {driver} rashly. Victim {victim} aged {age} suffered {injuries}. Treatment at {hospital}. Medical expenses: ₹{medical_expenses}. {disability}% permanent disability. Earning capacity: ₹{earning} p.m. Multiplier: {multiplier}. Compensation assessed: ₹{compensation}. Insurer: {insurer}. Interest @ {interest}%.",
    
    "Fatal accident compensation claim. Deceased {deceased} aged {age} died in accident on {accident_date}. Vehicle No. {vehicle_no}. Dependents: {dependents}. Monthly income: ₹{income}. Future prospects: {prospects}%. Deductions: {deductions}. Multiplier {multiplier} applied. Loss of dependency: ₹{dependency_loss}. Consortium loss: ₹{consortium}. Funeral: ₹{funeral}. Total: ₹{total_compensation}.",
    
    "Hit and run case. Untraced vehicle accident on {date} at {location}. Victim {victim} sustained {injuries}. Police report: {fir_no}. Treatment: ₹{treatment_cost}. Disability: {disability}%. Solatium Fund application. Ex-gratia: ₹{ex_gratia}. No vehicle identification. Section 161 Motor Vehicles Act applicable.",
    
    "Contributory negligence case. Accident between {vehicle1} and {vehicle2} on {date}. Driver1: {driver1} alleged {allegation1}. Driver2: {driver2} alleged {allegation2}. Eye-witnesses: {witnesses}. Police report findings: {findings}. Contributory negligence: {contribution1}% vs {contribution2}%. Apportionment of liability. Compensation reduced to ₹{final_compensation}.",
    
    "No-fault liability claim under Section 140. Claimant {claimant} suffered {injury} in accident involving vehicle {vehicle_no}. Medical certificate: {medical_certificate}. Simple permanent disablement. Income loss proved. Ceiling limit applicable. No enquiry into fault. Ex-gratia payment: ₹{amount}. Additional evidence: {evidence}."
]

# Land Acquisition scenarios  
land_acquisition_scenarios = [
    "Land acquisition compensation dispute. Land acquired for {project} under LA Act {act}. Survey No. {survey_no}, area {area} acres at {village}. Award dated {award_date}: ₹{award_amount} per acre. Market value on {acquisition_date}: ₹{market_value}. Comparable sales: {comparables}. Reference under Section 18. Solatium @ 30%. Interest @ 9%. Enhanced compensation: ₹{enhanced_amount}.",
    
    "RFCTLARR Act 2013 case. Land acquisition notification dated {notification_date}. Social Impact Assessment: {sia_findings}. Consent: {consent_percentage}%. Rehabilitation package: {package}. Affected families: {families}. Objections: {objections}. Award passed: ₹{award} per acre. Market value determination: {determination_method}. Multiplier: {multiplier}. Interest and solatium.",
    
    "Urgency clause challenge under Section 17. Notification dated {notification_date} for {purpose}. Urgency invoked bypassing SIA. Public purpose: {purpose}. Arbitrary exercise alleged. Hearing opportunity denied. Section 17(4) violated. Land owners: {count}. Alternative land: {alternative}. Court held: {holding}. Quashed/Modified: {outcome}."
]

# Election scenarios
election_scenarios = [
    "Election petition under Section 80 RPA. Parliamentary/Assembly constituency: {constituency}. Election dated {election_date}. Returned candidate: {returned_candidate}. Petitioner: {petitioner}. Grounds: Corrupt practice under Section {corrupt_section} - {corrupt_practice}. Affidavit discrepancies. Booth capturing. Expenditure violation: ₹{excess_expenditure}. Evidence: {evidence}. Tribunal finding: {finding}. Election set aside/dismissed.",
    
    "Disqualification petition under Anti-Defection Law. Member {member} elected from {party} joined {new_party} on {defection_date}. Voluntary giving up membership. Merger rule: {merger}. 2/3rd requirement. Speaker's order dated {order_date}: {decision}. Challenge under Article 226. Para 2(1)(a) vs Para 4. Court held: {holding}.",
    
    "Candidate nomination rejection challenge. Nomination filed on {nomination_date} for {constituency}. Rejected on {rejection_date}. Grounds: {rejection_grounds}. Affidavit defects: {defects}. Criminal cases disclosure: {disclosure_status}. Assets declaration: {asset_issue}. Section 33/36 RPA. Limitation period. Court held: {holding}. Nomination restored/rejected."
]

# Insolvency & Bankruptcy scenarios
ibc_scenarios = [
    "Corporate Insolvency Resolution Process under IBC Section {section}. Corporate Debtor: {corporate_debtor}. Financial Creditor: {creditor}. Default: ₹{default_amount}. Admission on {admission_date}. Resolution Professional: {rp}. CIRP period: {cirp_days} days. Claims received: {claims_count} totaling ₹{claims_amount}. CoC meetings: {coc_meetings}. Resolution Plan by {resolution_applicant}: ₹{plan_amount}. Voting: {voting_percentage}%. Liquidation value: ₹{liquidation_value}. Approved/Liquidation: {outcome}.",
    
    "Fraudulent trading under Section 66. Transactions during {period}. Fund diversion: ₹{diverted_amount} to {related_parties}. Preferential transactions. Undervalued transactions: {count}. Look-back period. Avoidance applications. Directors: {directors}. Personal liability claimed. Fraudulent intent: {intent_evidence}. Recovery: ₹{recovery}.",
    
    "Liquidation proceedings under Section 33. Corporate Debtor: {debtor}. Liquidator: {liquidator}. Assets: ₹{assets}. Liabilities: ₹{liabilities}. Waterfall mechanism. Secured creditors: ₹{secured}. Operational creditors: ₹{operational}. Workmen: ₹{workmen}. Distribution: {distribution}. Dissolution order.",
    
    "Section 7/9 admission challenge. Application filed by {creditor_type}. Default: ₹{default}. Pre-existing dispute claimed. Operational creditor: Demand notice dated {demand_date}. Financial creditor: Financial debt vs operational debt. Records of default. Information utility. Admission criteria. Court held: {holding}."
]

# Arbitration scenarios
arbitration_scenarios = [
    "Arbitration Award challenge under Section 34. Award dated {award_date} in dispute between {party1} and {party2}. Arbitrator: {arbitrator}. Claim: ₹{claim}. Award: ₹{award_amount}. Grounds: Patent illegality/Public policy violation - {grounds}. Time limit for challenge: 3 months + 30 days. Limitation: {limitation_status}. Minimal judicial interference principle. Award set aside/upheld: {outcome}.",
    
    "International Commercial Arbitration under UNCITRAL rules. Parties: {party1} ({country1}) and {party2} ({country2}). Seat: {seat}. Venue: {venue}. Arbitrator: {arbitrator}. Dispute: {dispute_nature}. Governing law: {governing_law}. Award dated {award_date}: ${award_usd}. Enforcement under New York Convention. Exequatur proceedings. Recognition: {recognition}.",
    
    "Section 11 appointment petition. Arbitration clause in agreement dated {agreement_date}. Dispute: {dispute}. Notice under Section 21 dated {notice_date}. Failure to appoint arbitrator. Chief Justice/designate appointment. Qualifications required. Conflict check. Arbitrator appointed: {appointed_arbitrator}. Mandate commenced.",
    
    "Emergency arbitration under Section 9. Urgent relief before constitution of tribunal. Ex-parte order: {interim_relief}. Commercial dispute: {dispute}. Balance of convenience. Irreparable injury. Prima facie case. Emergency arbitrator: {emergency_arbitrator}. Order within {days} days. Subsequently confirmed/varied by tribunal."
]

# =============================================================================
# GENERATOR FUNCTIONS - Create truly varied descriptions
# =============================================================================

def generate_criminal_description(pet, res, case_no):
    """Generate criminal case description with MASSIVE variety AND location matching"""
    
    # CRITICAL: Extract state from petitioner/respondent for location matching
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    
    # Determine crime type based on petitioner/respondent names or random
    crime_type = random.choice(['murder', 'theft', 'rape', 'kidnapping', 'missing', 'traffic', 'stampede'])
    
    if crime_type == 'murder':
        scenario = random.choice(murder_scenarios)
        # Fill template with varied data
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2023)}",
            'victim_name': pet if 'state' not in pet.lower() else f"deceased {random.choice(['Kumar', 'Singh', 'Sharma', 'Yadav', 'Gupta', 'Verma'])}",
            'location': random.choice(['residence at ' + random.choice(state_locations), 
                                     'workplace in ' + random.choice(state_locations), 
                                     'public place in ' + random.choice(state_locations), 
                                     'isolated area near ' + random.choice(state_locations),
                                     random.choice(state_locations)]),
            'poison': random.choice(['arsenic', 'cyanide', 'rat poison', 'pesticide', 'sleeping pills overdose']),
            'shop': random.choice(['medical store', 'hardware shop', 'agriculture store', 'online platform']),
            'accused_role': random.choice(['business partner', 'relative', 'friend', 'neighbor', 'acquaintance', 'employee']),
            'motive': random.choice(['property dispute', 'financial gain', 'revenge', 'insurance money', 'family dispute', 'business rivalry', 'love triangle']),
            'witnesses': random.randint(2, 8),
            'food_item': random.choice(['tea', 'meal', 'drink', 'sweets', 'medicine']),
            'behavior': random.choice(['unusual behavior', 'fleeing from scene', 'spreading false information', 'tampering with evidence']),
            'defense': random.choice(['alibi', 'accidental consumption', 'suicide theory', 'third party involvement']),
            'medical_finding': random.choice(['poisoning beyond doubt', 'poison quantity fatal', 'no natural cause of death']),
            'evidence_type': random.choice(['circumstantial evidence', 'direct evidence', 'medical and forensic evidence', 'dying declaration']),
            'section': random.choice(['302', '304', '304B', '306']),
            'weapon': random.choice(['knife', 'dagger', 'sword', 'kitchen knife', 'broken bottle', 'screwdriver']),
            'injury_count': random.randint(3, 15),
            'body_parts': random.choice(['chest and abdomen', 'neck and chest', 'back', 'multiple body parts', 'vital organs']),
            'hours': random.randint(1, 6),
            'dispute_type': random.choice(['heated argument', 'physical altercation', 'long-standing enmity', 'sudden quarrel']),
            'dispute_reason': random.choice(['money', 'property', 'woman', 'insult', 'previous incident', 'business matter']),
            'capture_time': random.choice(['immediately', 'within hours', 'next day', 'after chase']),
            'witness_names': f"{random.randint(2,5)} eye-witnesses",
            'medical_details': random.choice(['death due to hemorrhage', 'vital organs damaged', 'excessive blood loss']),
            'confession': random.choice(['crime in fit of rage', 'premeditated murder', 'initial denial later admitted']),
            'bullet_count': random.randint(2, 5),
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}",
            'weapon_type': random.choice(['country-made pistol', 'licensed revolver', '9mm pistol', 'rifle', 'shotgun']),
            'injury_type': random.choice(['head injury', 'chest injury', 'abdominal injury', 'multiple gunshot wounds']),
            'medical_cause': random.choice(['brain hemorrhage', 'damage to vital organs', 'excessive bleeding', 'shock and trauma']),
            'sound_description': random.choice(['gunshot sounds', 'multiple shots', 'firing']),
            'cctv_location': random.choice(['nearby shop', 'ATM', 'building', 'street']),
            'license_status': random.choice(['licensed firearm', 'illegal weapon', 'expired license']),
            'forensic_items': random.choice(['gunpowder residue, bullet casings', 'ballistic report, blood spatter analysis']),
            'sentence': random.choice(['life imprisonment', 'death penalty', '20 years rigorous imprisonment']),
            'strangulation_type': random.choice(['manual strangulation', 'ligature strangulation']),
            'item_used': random.choice(['rope', 'dupatta', 'wire', 'bare hands']),
            'accused_name': res if 'state' not in res.lower() else random.choice(['accused ' + name for name in ['Ramesh', 'Suresh', 'Mahesh', 'Dinesh']]),
            'relation': random.choice(['husband', 'brother', 'business partner', 'friend', 'neighbor', 'relative']),
            'confidant': random.choice(['friend', 'relative', 'colleague', 'neighbor']),
            'threat': random.choice(['threats to life', 'dire consequences', 'harm']),
            'struggle_details': random.choice(['victim fought back', 'defensive wounds present', 'signs of resistance']),
            'lie_details': random.choice(['false alibi', 'contradictory statements', 'changed story']),
            'burn_percentage': random.randint(40, 95),
            'death_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2023)}",
            'authority': random.choice(['Magistrate', 'Executive Magistrate', 'Judicial Magistrate']),
            'substance': random.choice(['kerosene', 'petrol', 'acid', 'inflammable liquid']),
            'dispute': random.choice(['dowry demand', 'domestic quarrel', 'property dispute', 'financial issue']),
            'accelerant': random.choice(['kerosene', 'petrol traces', 'inflammable substance']),
            'vendor': random.choice(['petrol pump', 'shop', 'supplier']),
            'sounds': random.choice(['screams', 'cries for help', 'commotion']),
            'burn_type': random.choice(['ante-mortem burns', 'burns before death', 'homicidal burns']),
            'water_body': random.choice(['river', 'pond', 'well', 'canal', 'lake']),
            'injury_details': random.choice(['head injury', 'strangulation marks', 'wounds', 'trauma']),
            'clothing': random.choice(['torn clothes', 'dress']),
            'alibi': random.choice(['he was elsewhere', 'working', 'at home']),
            'evidence_items': random.choice(['witness testimonies', 'circumstantial evidence', 'forensic evidence']),
            'vehicle_type': random.choice(['car', 'truck', 'tempo', 'SUV', 'motorcycle']),
            'tracing_method': random.choice(['registration number', 'chassis number', 'CCTV footage', 'informer']),
            'condition': random.choice(['drunk', 'rash driving', 'overspeeding']),
            'video_evidence': random.choice(['vehicle hitting victim', 'accused fleeing', 'rash driving']),
            'witness_details': random.choice(['vehicle number', 'driver appearance', 'accident details']),
            'mv_act': 'Motor Vehicles Act',
            'partner_name': random.choice(['partner name', 'lover name']),
            'reason': random.choice(['inter-caste marriage', 'same-gotra marriage', 'love marriage against family wishes']),
            'accused_names': random.choice(['family members', '5 accused persons', 'relatives']),
            'relationship_type': random.choice(['relationship', 'marriage', 'love affair']),
            'action': random.choice(['killed', 'murdered', 'beaten to death']),
            'cultural_defense': random.choice(['family honor', 'community honor', 'tradition']),
            'planning_details': random.choice(['prior meetings', 'weapon procurement', 'conspiracy calls']),
            'verdict': random.choice(['life imprisonment to all', 'death penalty', 'convicted under Section 302 IPC']),
            'timeframe': random.choice(['7 years', '5 years', '3 years', 'one year']),
            'amount': f"{random.randint(5,50)} lakhs",
            'items': random.choice(['gold jewelry', 'cash', 'vehicle', 'property']),
            'harassment_details': random.choice(['physical torture', 'mental cruelty', 'demands for dowry', 'threats']),
            'cause': random.choice(['hanging', 'burns', 'poisoning', 'injuries due to assault']),
            'dowry_demands': random.choice(['cash and jewelry', 'car', 'flat', 'more money']),
            'injuries': random.choice(['burn injuries', 'blunt force trauma', 'multiple injuries']),
            'value': random.randint(100000, 2000000),
            'treatment_details': random.choice(['multiple surgeries', 'ICU treatment', 'ongoing treatment']),
            'surgeries': random.randint(3, 15),
            'acid_type': random.choice(['sulphuric acid', 'hydrochloric acid', 'chemical acid']),
            'mob_size': random.randint(20, 200),
            'accusation': random.choice(['cattle theft', 'child lifting', 'theft', 'witchcraft']),
            'casualty_count': random.randint(1, 5),
            'injuries': random.choice(['mob beating', 'lynching', 'brutal assault']),
            'accused_list': f"{random.randint(10,30)} persons",
            'identification_method': random.choice(['video footage', 'witnesses', 'police investigation']),
            'video_details': random.choice(['entire incident', 'mob violence', 'accused persons beating victim']),
            'medical_findings': random.choice(['multiple injuries all over body', 'death due to mob violence']),
            'instigator': random.choice(['rumor', 'false accusation', 'provocateur']),
            'delay': random.choice(['30 minutes', '1 hour', 'too late']),
            'witness_account': random.choice(['mob frenzy', 'brutal violence', 'victim pleading']),
            'conspiracy_section': '120B',
            'gender': random.choice(['male', 'female']),
            'cause_of_death': random.choice(['asphyxiation', 'exposure', 'head injury']),
            'circumstance': random.choice(['at home', 'in hospital', 'hidden location']),
            'evidence_details': random.choice(['umbilical cord attached', 'fresh birth', 'medical examination']),
            'reasons': random.choice(['unwanted pregnancy', 'out of wedlock', 'gender preference', 'poverty']),
            'gang_size': random.randint(3, 8),
            'gang_rivalry': random.choice(['territorial dispute', 'previous murder revenge', 'business rivalry']),
            'weapons': random.choice(['swords and knives', 'firearms and knives', 'deadly weapons']),
            'communication': random.choice(['coordination calls', 'planning messages', 'conspiracy evidence']),
            'role_details': random.choice(['each had specific role in attack', 'all participated actively']),
            'conspiracy_evidence': random.choice(['call records', 'witness statements', 'recovery of weapons']),
            'forensic_link': random.choice(['weapons to accused', 'blood evidence', 'DNA evidence']),
            # Missing keys for various scenarios
            'murder_method': random.choice(['multiple stab wounds', 'strangulation', 'gunshot wounds', 'blunt force trauma', 'sharp weapon injuries', 'beating to death']),
            'victim_vehicle_or_person': random.choice(['pedestrian', 'motorcyclist', 'cyclist', 'auto-rickshaw', 'another car', 'school bus']),
            'festival_or_event': random.choice(['Diwali celebration', 'Holi festival', 'religious gathering', 'music concert', 'political rally', 'New Year celebration']),
            'threat_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2022)}",
            'threats': random.choice(['dire consequences', 'social ostracism', 'violence', 'murder threats']),
            'alcohol_level': f"{random.uniform(0.08, 0.25):.2f}%",
            'speed': f"{random.randint(80, 150)} km/h",
            'limit': f"{random.randint(30, 60)} km/h",
            'witness_account': random.choice(['rash driving', 'overspeeding', 'jumping red light', 'driving on wrong side']),
            'venue': random.choice(['temple', 'stadium', 'auditorium', 'pandal', 'grounds', 'plaza']),
            'victims_count': random.randint(5, 50),
            'organizer_names': random.choice(['event organizers', 'management committee', 'temple authorities']),
            'precautions': random.choice(['ensure proper crowd control', 'provide adequate security', 'create emergency exits']),
            'barricade_status': random.choice(['insufficient', 'inadequate', 'poorly maintained']),
            'medical_status': random.choice(['insufficient', 'not readily available', 'inadequately staffed']),
            'rumor': random.choice(['fire', 'collapse', 'gunfire', 'bomb scare']),
            # Additional missing keys for acid attack and other scenarios
            'source': random.choice(['chemical shop', 'online purchase', 'hardware store', 'unauthorized dealer']),
            'witness_details': random.choice(['accused fleeing', 'victim screaming', 'attack witnessed', 'accused at scene']),
            'dowry_amount': f"Rs. {random.randint(5, 50)} lakhs",
            'dowry_items': random.choice(['gold jewelry and car', 'cash and property', 'vehicle and flat', 'gold ornaments'])
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
        
    elif crime_type == 'theft':
        scenario = random.choice(theft_scenarios)
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
            'items': random.choice([
                'gold jewelry, cash, laptop', 'LED TV, jewelry, cash', 'mobile phones, wallet', 'expensive watch, cash',
                'diamond necklace, cash Rs 2 lakhs', 'MacBook Pro, iPhone, designer bag', 'gold bangles, rings, earrings',
                'Sony TV, gaming console, speakers', 'DSLR camera, lenses, laptop', 'branded watches, gold chain',
                'Samsung phone, wallet with cards', 'air conditioner, microwave, utensils', 'bicycle, tools, electronics',
                'important documents, laptop, hard disk', 'ancestral jewelry, cash, bonds', 'office equipment, computers',
                'vehicle spare parts, tools', 'copper wires, electrical items', 'medicines, medical equipment',
                'clothes, accessories, cosmetics', 'artwork, antiques, collectibles', 'musical instruments, speakers',
                '50 tola gold ornaments', 'foreign currency, jewelry', 'branded shoes, bags, perfumes'
            ]),
            'amount': random.randint(25000, 8000000),
            'entry_method': random.choice([
                'breaking rear window', 'breaking door lock', 'climbing wall', 'duplicate key', 'breaking balcony grill',
                'opening latch from outside', 'breaking glass pane', 'master key', 'cutting window grill',
                'jumping from adjacent building', 'breaking terrace door', 'opening bathroom window',
                'drilling through wall', 'using skeleton key', 'breaking ventilator', 'prying open door'
            ]),
            'suspicious_activity': random.choice([
                'unknown person loitering', 'sound of breaking', 'lights off', 'door ajar', 'broken lock noticed',
                'neighbor heard noise', 'CCTV showed movement', 'security guard saw person', 'dog barking continuously',
                'vehicle parked suspiciously', 'ladder found outside', 'tools left at scene'
            ]),
            'accused_name': random.choice([
                'Raju', 'Bablu', 'Pappu', 'Guddu', 'Chhotu', 'Munna', 'Bunty', 'Sonu', 'Monu', 'Deepak',
                'Rahul', 'Amit', 'Sunil', 'Ajay', 'Vijay', 'Ramesh', 'Suresh', 'Dinesh', 'Mahesh', 'Rakesh',
                'Arun', 'Varun', 'Karan', 'Arjun', 'Ravi', 'Sanjay', 'Manoj', 'Anil', 'Pankaj', 'Neeraj'
            ]),
            'item': random.choice([
                'leather wallet', 'handbag', 'office bag', 'briefcase', 'backpack', 'sling bag',
                'purse', 'document folder', 'laptop bag', 'shoulder bag', 'file cover', 'passport holder',
                'waist pouch', 'travel pouch'
            ]),
            'shop': random.choice([
                'pawn shop', 'second-hand dealer', 'mobile shop', 'jewelry shop', 'electronics store',
                'scrap dealer', 'local market', 'online marketplace', 'unauthorized dealer', 'fence'
            ]),
            'recovery_items': random.choice([
                'stolen goods', 'burglary tools', 'more stolen items', 'master keys', 'screwdrivers and pliers',
                'cut locks', 'mobile phones', 'jewelry pieces', 'incriminating evidence', 'stolen documents'
            ]),
            'confession': random.choice([
                'multiple burglaries', 'crime', 'theft', '20+ thefts in locality', 'organized gang operations',
                'series of house burglaries', 'vehicle theft ring', 'breaking into shops'
            ]),
            'area': random.choice([
                'same locality', 'nearby areas', 'city', 'entire district', 'neighboring colonies',
                'posh localities', 'residential areas', 'commercial areas', 'industrial zone'
            ]),
            'section': random.choice(['380', '457', '380/34', '457/34', '379', '381', '382', '411', '414']),
            'vehicle_type': random.choice([
                'Honda Activa', 'Hero Splendor', 'Maruti Swift', 'Hyundai i20', 'Honda City', 'Maruti Alto',
                'TVS Jupiter', 'Bajaj Pulsar', 'Royal Enfield', 'Yamaha FZ', 'Suzuki Access', 'Hero Passion',
                'Maruti WagonR', 'Hyundai Creta', 'Tata Nexon', 'Mahindra Scorpio', 'Toyota Innova',
                'Honda Dio', 'Vespa', 'KTM Duke', 'Maruti Baleno', 'Ford EcoSport'
            ]),
            'registration': f"{random.choice(['DL','MH','KA','TN','UP','HR','RJ','GJ','WB','AP','TS','MP','BR','PB','JH','OR','UK','HP','CG','AS'])}-{random.randint(1,30)}-{random.choice(['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V','W','X','Y','Z'])}{random.choice(['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V','W','X','Y','Z'])}-{random.randint(1000,9999)}",
            'destination': random.choice([
                'Delhi', 'Mumbai', 'Uttar Pradesh', 'Bihar', 'Rajasthan', 'Punjab', 'Haryana', 'Madhya Pradesh',
                'Gujarat', 'West Bengal', 'Odisha', 'Jharkhand', 'Uttarakhand', 'Assam', 'Chhattisgarh',
                'Nepal border', 'Bangladesh border', 'local market', 'scrap yard', 'unauthorized dealer'
            ]),
            'days': random.randint(1, 90),
            'fake_documents': random.choice([
                'forged RC book', 'fake registration', 'no documents', 'tampered chassis number',
                'fake insurance papers', 'stolen RC book', 'duplicate key made', 'cloned documents'
            ]),
            'previous_cases': random.randint(1, 35),
            'contents': random.choice([
                'credit cards, documents', 'cash and cards', 'important papers', 'Aadhaar card, PAN card, cash',
                'office ID, driving license', 'voter ID, bank passbook', 'debit cards, insurance papers',
                'passport, visa documents', 'property papers, checkbook'
            ]),
            'circumstance': random.choice([
                'crowded bus', 'railway station', 'market', 'metro', 'local train', 'shopping mall',
                'festival crowd', 'ATM queue', 'ticket counter', 'platform', 'bus stand', 'airport',
                'temple', 'hospital', 'cinema hall', 'park', 'exhibition', 'fair ground'
            ]),
            'action': random.choice([
                'flee', 'escape', 'run', 'disappear in crowd', 'board another vehicle', 'hide',
                'change clothes', 'blend with people', 'take different route'
            ]),
            'witness': random.choice([
                'co-passenger', 'police constable', 'shopkeeper', 'security guard', 'auto driver',
                'ticket checker', 'fellow commuter', 'vendor', 'passerby', 'CCTV footage',
                'station master', 'taxi driver', 'bystander'
            ]),
            'criminal_record': f"{random.randint(1,45)} previous theft cases",
            'method': random.choice([
                'distraction technique', 'razor blade to cut bag', 'pickpocketing technique', 'bumping into victim',
                'creating commotion', 'working in pairs', 'sleight of hand', 'blade to slit pocket',
                'targeting sleeping passengers', 'crowding technique', 'staged accident'
            ]),
            'occupation': random.choice([
                'employee', 'servant', 'known person', 'stranger', 'security guard', 'delivery boy',
                'plumber', 'electrician', 'carpenter', 'painter', 'domestic help', 'driver',
                'tenant', 'neighbor', 'watchman', 'gardener', 'cook'
            ]),
            'residence': random.choice([
                'hideout', 'rented room', 'home', 'slum area', 'unauthorized colony', 'relative house',
                'abandoned building', 'under flyover', 'railway station', 'construction site'
            ]),
            'other_shops': random.choice([
                '2 other shops', 'multiple shops', 'several places', '5 shops in market',
                '3 jewelry stores', 'electronics shops in area', 'entire mall', '10+ outlets'
            ]),
            'jewelry_items': random.choice([
                'gold necklace, bangles, rings', 'diamond jewelry', 'gold and silver articles',
                'mangalsutra, earrings, chain', 'wedding jewelry set', 'precious gemstones',
                'platinum ring, gold coins', 'antique jewelry', 'designer ornaments',
                '50 tola gold bangles', 'diamond studded necklace'
            ]),
            'access_or_opportunity': random.choice([
                'access to premises', 'opportunity during work', 'knowledge of locker',
                'duplicate keys made', 'knew daily routine', 'trusted by family',
                'access to safe combination', 'information from insider', 'worked in house before'
            ]),
            'recovery_location': random.choice([
                'pawn shop', 'accused residence', 'hideout', 'local market', 'scrap dealer',
                'accomplice house', 'railway station locker', 'forest area', 'abandoned plot',
                'under ground', 'rooftop', 'vehicle dickey'
            ]),
            'financial_trouble': random.choice([
                'debt', 'gambling loss', 'financial crisis', 'medical emergency', 'addiction',
                'lavish lifestyle', 'business loss', 'unemployment', 'family pressure',
                'loan repayment', 'drug habit', 'alcohol addiction'
            ]),
            'forensic': random.choice([
                'fingerprints matched', 'tools matched', 'DNA evidence', 'shoeprint matched',
                'hair sample matched', 'fiber analysis', 'handwriting match', 'CCTV footage'
            ]),
            'similar_cases': random.choice([
                'jewelry thefts', 'house burglaries', 'vehicle thefts', 'shop break-ins',
                'office thefts', 'temple robbery', 'bank locker thefts', 'ATM thefts'
            ]),
            'violence_type': random.choice([
                'knife threat', 'physical assault', 'gun threat', 'iron rod attack', 'baseball bat',
                'stick beating', 'chili powder thrown', 'stranglehold', 'punches and kicks',
                'sharp weapon', 'blunt object', 'threatening with acid'
            ]),
            'injuries': random.choice([
                'minor injuries', 'grievous hurt', 'assault injuries', 'head injury', 'fractures',
                'bleeding wounds', 'bruises all over', 'broken bones', 'internal injuries',
                'lacerations', 'deep cuts', 'unconscious state'
            ]),
            'accused_details': random.choice([
                'masked person', 'known criminal', 'gang member', 'habitual offender', 'juvenile',
                'organized gang', 'interstate gang', 'local goon', 'drug addict', 'desperate person'
            ]),
            'weapon': random.choice([
                'knife', 'gun', 'stick', 'country-made pistol', 'sword', 'iron rod',
                'hockey stick', 'broken bottle', 'sharp-edged weapon', 'screwdriver',
                'hammer', 'axe', 'dagger'
            ]),
            'victim': res,  # Added for robbery scenario
            'witness_name': random.choice([
                'shopkeeper', 'passerby', 'victim\'s friend', 'neighbor', 'auto driver',
                'security guard', 'fellow shopkeeper', 'tea stall owner', 'street vendor',
                'night watchman', 'parking attendant', 'other customer'
            ]),
            'medical': random.choice([
                'injuries documented', 'hurt caused', 'MLC issued', 'X-ray shows fractures',
                'CT scan done', 'stitches required', 'hospitalization needed', 'ICU admission'
            ]),
            'bank': random.choice([
                'SBI', 'HDFC Bank', 'ICICI Bank', 'PNB', 'Bank of Baroda', 'Canara Bank',
                'Union Bank', 'Axis Bank', 'IndusInd Bank', 'Yes Bank', 'IDBI Bank',
                'Kotak Mahindra', 'Bank of India'
            ]),
            'vault_or_accounts': random.choice([
                'bank vault', 'customer accounts', 'treasury', 'cash chest', 'locker room',
                'strong room', 'ATM', 'savings accounts', 'current accounts'
            ]),
            'discrepancy': random.choice([
                'amount mismatch', 'missing cash', 'account irregularities', 'unauthorized debits',
                'forged signatures', 'manipulation of records', 'fake entries', 'embezzlement'
            ]),
            'fake_entries': random.choice([
                'false accounts', 'forged signatures', 'dummy accounts', 'fictitious transactions',
                'backdated entries', 'inflated amounts', 'phantom withdrawals', 'paper trail destroyed'
            ]),
            'cattle_type': random.choice([
                'cow', 'buffalo', 'bull', 'ox', 'calf', 'bullock', 'heifer', 'milch cow',
                'Jersey cow', 'Murrah buffalo', 'indigenous breed'
            ]),
            'cattle_count': random.randint(1, 25),
            'identification_marks': random.choice([
                'ear tags', 'brand marks', 'distinct features', 'horn shape', 'color pattern',
                'microchip', 'tattoo marks', 'owner marking', 'collar number'
            ]),
            'gang_details': random.choice([
                'cattle theft gang', 'organized gang', 'interstate racket', 'smuggling ring',
                'slaughterhouse connection', 'illegal trade network', 'systematic operation'
            ]),
            'phishing_method': random.choice([
                'SMS', 'email', 'phone call', 'WhatsApp message', 'fake website', 'social media',
                'lottery scam', 'OTP fraud', 'vishing call', 'QR code scam', 'app link'
            ]),
            'details': random.choice([
                'OTP', 'card details', 'net banking credentials', 'CVV number', 'PIN',
                'account password', 'UPI PIN', 'personal information', 'Aadhaar details'
            ]),
            'account_details': random.choice([
                'mule account', 'shell company account', 'fake account', 'benami account',
                'multiple layer accounts', 'crypto wallet', 'hawala channel', 'overseas account'
            ]),
            'technical_details': random.choice([
                'IP address traced', 'device fingerprinting', 'transaction analysis', 'server logs',
                'MAC address', 'location tracking', 'SIM card details', 'bank statement forensics',
                'digital footprint', 'cyber trail analysis'
            ]),
            # Additional common keys that might be used across scenarios
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
    
    elif crime_type == 'rape':
        scenario = random.choice(sexual_assault_scenarios)
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'age': random.randint(6, 65),
            'accused_name': res if 'state' not in res.lower() else random.choice(['accused', 'perpetrator']),
            'location': random.choice([
                # Diverse actual locations
                'residence', 'isolated place', 'vehicle', 'workplace', 'school premises', 'office building',
                'abandoned house', 'under construction building', 'park', 'railway station', 'bus stand',
                'hotel room', 'lodging', 'forest area', 'agricultural field', 'factory premises',
                'hospital', 'hostel', 'PG accommodation', 'college campus', 'tuition center',
                'shop', 'godown', 'parking lot', 'terrace', 'staircase', 'elevator',
                'auto-rickshaw', 'taxi', 'private car', 'truck', 'train compartment',
                'temple premises', 'church compound', 'mosque area', 'religious institution',
                'relative house', 'friend house', 'neighbor house', 'servant quarter',
                'cinema hall', 'mall', 'restaurant', 'bar', 'pub', 'resort', 'farmhouse'
            ]),
            'incident_details': random.choice([
                'forceful assault', 'criminal act against will', 'violent attack', 'sexual assault',
                'wrongful restraint and assault', 'abduction and assault', 'assault using force',
                'assault with threats', 'assault at knife-point', 'assault at gunpoint',
                'assault after intoxication', 'assault exploiting vulnerability', 'assault under false pretense',
                'assault after gaining confidence', 'assault during help-seeking', 'assault by authority figure',
                'repeated assaults over period', 'gang assault', 'brutal attack', 'heinous crime'
            ]),
            'medical_findings': random.choice([
                'injuries consistent with assault', 'internal injuries', 'trauma', 'genital injuries',
                'bruises and abrasions', 'bite marks', 'strangulation marks', 'defensive injuries',
                'torn clothes', 'physical trauma', 'psychological trauma', 'vaginal injuries',
                'anal injuries', 'bleeding', 'swelling', 'multiple injuries all over body',
                'head injury', 'fractures', 'internal bleeding', 'hymen tears',
                'forensic evidence collected', 'DNA samples collected', 'medical examination confirms assault'
            ]),
            'relation_to_victim': random.choice([
                'known to victim', 'neighbor', 'relative', 'stranger', 'acquaintance',
                'uncle', 'cousin', 'father', 'stepfather', 'brother', 'brother-in-law',
                'employer', 'supervisor', 'boss', 'colleague', 'co-worker', 'teacher',
                'tuition teacher', 'priest', 'godman', 'tantrik', 'doctor', 'driver',
                'security guard', 'servant', 'electrician', 'plumber', 'vendor',
                'auto driver', 'taxi driver', 'friend', 'boyfriend', 'ex-boyfriend',
                'husband', 'separated husband', 'father-in-law', 'complete stranger',
                'stalker', 'online friend turned predator', 'social media contact'
            ]),
            'opportunity': random.choice([
                'when victim alone at home', 'took victim to isolated place', 'in vehicle',
                'exploited victim being alone', 'victim called for help', 'pretended to help',
                'offered lift', 'asked directions', 'lured with false promise',
                'used position of authority', 'exploited trust', 'gained entry on pretext',
                'during power cut', 'late night hours', 'when family away',
                'victim returning home alone', 'waiting near victim house', 'followed victim',
                'during festival when area deserted', 'victim working late', 'victim traveling alone',
                'victim in need of help', 'victim seeking employment', 'victim seeking admission'
            ]),
            'identification': random.choice([
                'test identification parade', 'court identification', 'photo identification',
                'victim statement', 'CCTV footage', 'witnessed by others', 'caught red-handed',
                'DNA match', 'clothes matched', 'location known', 'accused confessed',
                'mobile tower location', 'call records', 'eyewitness account'
            ]),
            'defense': random.choice([
                'consent', 'false implication', 'alibi', 'consensual relationship', 'frame-up',
                'enmity with victim family', 'mutual affair', 'denied presence', 'mistaken identity',
                'victim lying', 'no evidence', 'contradictions in statement', 'delayed complaint'
            ]),
            'sentence': random.choice([
                'rigorous imprisonment for 10 years', 'life imprisonment', 'death penalty',
                'imprisonment till death', '20 years rigorous imprisonment', '7 years imprisonment',
                'life imprisonment without remission', 'death by hanging', 'imprisonment for 30 years',
                'enhanced punishment under POCSO', 'life imprisonment with fine'
            ]),
            'section': random.choice([
                '376', '376(2)(n)', '376D', '376AB', '376(2)(i)', '376(2)(f)', '376(2)(a)',
                '376A', '376B', '376C', '376E', '377', '354', '354A', '354B', '354C', '354D',
                '375', '506', '509'
            ]),
            'accused_count': random.randint(2, 12),
            'circumstance': random.choice([
                'returning from work', 'traveling alone', 'alone at night', 'going to shop',
                'returning from tuition', 'coming from school', 'going for morning walk',
                'returning from friend house', 'going to fetch water', 'working in field',
                'attending function', 'going to temple', 'shopping', 'waiting for bus',
                'using public toilet', 'collecting firewood', 'tending cattle',
                'visiting doctor', 'going to police station', 'seeking help'
            ]),
            'action': random.choice([
                'forcibly took', 'abducted', 'overpowered', 'dragged', 'pulled into vehicle',
                'caught hold', 'forcibly restrained', 'gagged and tied', 'threatened with weapon',
                'administered sedative', 'mixed intoxicant', 'chloroformed', 'physically overpowered',
                'lured under false pretense', 'kidnapped', 'confined'
            ]),
            'injuries': random.choice([
                'multiple injuries', 'grievous injuries', 'internal and external injuries',
                'life-threatening injuries', 'critical injuries', 'severe trauma',
                'permanent disability', 'disfigurement', 'broken bones', 'severe bleeding',
                'unconscious state', 'coma', 'near-death condition'
            ]),
            'accused_names': f"{random.randint(2,12)} accused persons",
            'conspiracy': random.choice([
                'pre-planned', 'conspiracy', 'coordination', 'well-planned attack',
                'organized crime', 'gang operation', 'systematic targeting'
            ]),
            'role_details': random.choice(['each participated in crime', 'all equally guilty']),
            'occupation': random.choice(['teacher', 'employer', 'coach', 'doctor', 'guardian']),
            'relation': random.choice(['teacher', 'guardian', 'family friend', 'known person']),
            'discovery_method': random.choice(['victim disclosed to mother', 'medical examination', 'victim\'s complaint']),
            'evidence': random.choice(['medical evidence', 'witness testimony', 'circumstantial evidence']),
            'findings': random.choice(['sexual assault confirmed', 'injuries present', 'trauma evident']),
            'duration': random.choice(['6 months', '1 year', '2 years']),
            'substance': random.choice(['sedative', 'drug', 'intoxicant', 'spiked drink']),
            'authority': random.choice(['police', 'hospital', 'women\'s cell']),
            'drug': random.choice(['benzodiazepine', 'sedative substance', 'intoxicant']),
            'cctv_details': random.choice(['administering substance', 'taking victim', 'at scene']),
            'previous_cases': random.choice(['similar modus operandi cases', 'criminal history']),
            'medical_evidence': random.choice(['injuries', 'assault marks', 'trauma']),
            'witnesses': random.choice(['neighbors', 'relatives', 'colleagues']),
            'ordeal': random.choice(['physical and mental trauma', 'ongoing harassment', 'repeated assault']),
            # Additional common keys
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
    
    elif crime_type == 'kidnapping':
        scenario = random.choice(kidnapping_scenarios)
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'victim_name': random.choice([
                'child Ramesh', 'child Priya', 'child Amit', 'child Sneha', 'child Rohan', 'child Neha',
                'minor Aarav', 'minor Diya', 'minor Arjun', 'minor Ananya', 'victim', 'child victim',
                'the girl child', 'the boy child', 'young girl', 'young boy', 'teenage girl', 'teenage boy'
            ]),
            'age': random.randint(3, 30),
            'accused_name': res if 'state' not in res.lower() else random.choice([
                'accused', 'kidnapper', 'abductor', 'perpetrator', 'criminal', 'offender',
                'trafficker', 'gang member', 'habitual offender', 'known criminal'
            ]),
            'location': random.choice([
                'school gate', 'tuition center gate', 'near school', 'bus stop', 'market', 'playground',
                'near home', 'park', 'temple', 'fair ground', 'railway station', 'mall entrance',
                'shopping area', 'cinema hall', 'hospital gate', 'street', 'public place',
                'mela ground', 'exhibition ground', 'sports complex', 'community center',
                'garden', 'near relatives house', 'wedding venue', 'function hall'
            ]),
            'amount': random.randint(100000, 50000000),
            'medium': random.choice([
                'phone call', 'WhatsApp message', 'SMS', 'email', 'recorded video call',
                'voice message', 'Telegram', 'letter', 'intermediary', 'courier',
                'direct contact', 'messenger'
            ]),
            'rescue_location': random.choice([
                'hideout in Delhi', 'abandoned house in UP', 'remote village in Bihar', 'secret location in Haryana',
                'farmhouse in Punjab', 'dhaba on highway', 'rented room in slum area', 'forest in MP',
                'godown in industrial area', 'under-construction building', 'cave in hills',
                'shed in agricultural field', 'warehouse', 'truck container', 'boat',
                'border area hideout', 'safe house', 'accomplice residence', 'hotel room'
            ]),
            'rescue_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'motive': random.choice([
                'ransom', 'revenge', 'human trafficking', 'forced marriage', 'forced labor',
                'organ trade', 'begging racket', 'child trafficking', 'sexual exploitation',
                'adoption racket', 'property dispute', 'business rivalry', 'personal enmity',
                'extortion', 'illegal adoption', 'bonded labor', 'prostitution racket'
            ]),
            'confinement_details': random.choice([
                'in locked room', 'tied up', 'in dark room', 'in basement', 'handcuffed',
                'chained', 'gagged and bound', 'in container', 'in vehicle', 'in shed',
                'in underground chamber', 'in attic', 'in warehouse', 'in godown',
                'in jungle hut', 'in abandoned building'
            ]),
            'condition': random.choice([
                'traumatized but physically fine', 'minor injuries', 'malnourished', 'severely traumatized',
                'injured', 'critical condition', 'weak and dehydrated', 'tortured', 'beaten',
                'psychologically damaged', 'physical and mental trauma', 'unconscious',
                'drugged state', 'severe distress'
            ]),
            'section': random.choice(['363', '364', '364A', '365', '366', '366A', '366B', '367', '368', '369']),
            'enticement': random.choice([
                'chocolates', 'toys', 'job offer', 'help finding lost item', 'ice cream',
                'sweets', 'mobile phone', 'video game', 'puppy', 'kitten', 'money',
                'movie offer', 'gifts', 'modeling opportunity', 'acting opportunity',
                'foreign job promise', 'education opportunity', 'sports coaching',
                'pretense of knowing parents', 'medical emergency of family'
            ]),
            'destination': random.choice([
                'another city', 'another state', 'village', 'hideout', 'border area',
                'Delhi', 'Mumbai', 'Kolkata', 'Bangladesh border', 'Nepal border',
                'remote location', 'international destination', 'unknown location',
                'trafficking den', 'red light area', 'forced labor camp'
            ]),
            'recovery_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'accused_background': random.choice([
                'known criminal', 'trafficking ring member', 'habitual offender', 'previous kidnapping cases',
                'organized crime member', 'serial offender', 'proclaimed offender', 'wanted criminal',
                'similar cases history', 'interstate criminal', 'history sheeter',
                'involved in multiple kidnappings', 'part of gang', 'professional kidnapper'
            ]),
            'accused_names': f"{random.randint(2,8)} accused persons",
            'purpose': random.choice([
                'ransom', 'trafficking', 'forced labor', 'forced marriage', 'sexual exploitation',
                'begging', 'organ trade', 'adoption racket', 'bonded labor', 'prostitution',
                'child pornography', 'illegal adoption', 'revenge', 'extortion'
            ]),
            'treatment': random.choice([
                'confined', 'tortured', 'kept in captivity', 'beaten', 'starved', 'abused',
                'subjected to trauma', 'ill-treated', 'drugged', 'threatened', 'exploited',
                'sold', 'traded', 'kept in inhuman conditions'
            ]),
            'criminal_gang': random.choice([
                'trafficking gang', 'kidnapping gang', 'organized crime gang', 'interstate gang',
                'international trafficking network', 'child trafficking syndicate', 'begging mafia',
                'organ trade network', 'prostitution racket', 'adoption racket gang'
            ]),
            'ordeal_details': random.choice([
                'severe trauma', 'physical and mental torture', 'prolonged captivity', 'repeated abuse',
                'inhuman treatment', 'continuous torture', 'psychological trauma', 'sexual abuse',
                'physical assault', 'life-threatening conditions', 'near-death experience'
            ]),
            'partner_name': random.choice([
                'partner', 'lover', 'boyfriend', 'girlfriend', 'boy', 'girl',
                'friend', 'acquaintance', 'online friend', 'social media contact'
            ]),
            'relatives': random.choice([
                'family members', 'relatives', 'parents', 'guardians', 'father', 'mother',
                'uncle', 'aunt', 'grandparents', 'siblings', 'family'
            ]),
            'reason': random.choice([
                'marriage against wishes', 'forced marriage', 'family pressure', 'caste difference',
                'religious difference', 'family opposition', 'love affair', 'elopement',
                'inter-caste marriage', 'inter-religious marriage', 'parental objection'
            ]),
            'findings': random.choice([
                'forced confinement', 'assault', 'rape', 'torture', 'illegal detention',
                'wrongful restraint', 'sexual abuse', 'physical abuse', 'exploitation'
            ]),
            'testimony': random.choice([
                'clear and consistent', 'credible', 'detailed account', 'reliable',
                'corroborated', 'truthful', 'convincing', 'supported by evidence'
            ]),
            # Additional keys needed by some kidnapping scenarios
            'evidence_details': random.choice([
                'witness statements', 'recovery details', 'forensic evidence', 'CCTV footage',
                'phone records', 'location tracking', 'ransom calls recording', 'medical evidence',
                'confession', 'recovered items', 'identification by victim'
            ]),
            'defense': random.choice([
                'false accusation', 'mistaken identity', 'alibi', 'victim went willingly',
                'consensual', 'no wrongful confinement', 'misunderstanding', 'frame-up',
                'victim lying', 'no evidence', 'fabricated case'
            ]),
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
    
    elif crime_type == 'missing':
        scenario = random.choice(missing_person_scenarios)
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2023)}",
            'person_name': random.choice(['Ramesh Kumar', 'Priya Sharma', 'Minor child', 'Elderly person']),
            'age': random.randint(10, 70),
            'location': random.choice(['home', 'school', 'market', 'workplace']),
            'last_location': random.choice(['bus stop', 'near home', 'market', 'friend\'s place']),
            'clothing': random.choice(['blue shirt and jeans', 'school uniform', 'saree', 'kurta']),
            'findings': random.choice(['person eloped', 'went voluntarily', 'kidnapped']),
            'found_location': random.choice(['another city', 'relative\'s place', 'hiding']),
            'found_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
            'condition': random.choice(['safe', 'traumatized', 'injured']),
            'reason_for_missing': random.choice(['family dispute', 'love affair', 'job', 'study']),
            'closure_status': random.choice(['person found safe', 'reunited with family']),
            'tower_location': random.choice(['Delhi area', 'Mumbai region', 'near highway']),
            'days': random.randint(5, 30),
            'discovery_location': random.choice(['forest', 'canal', 'abandoned building', 'field']),
            'cause_of_death': random.choice(['murder', 'accidental death', 'natural death']),
            'accused_name': res if 'state' not in res.lower() else 'accused person',
            'tracing_method': random.choice(['social media', 'phone tracking', 'informer', 'police investigation']),
            'reason': random.choice(['family problems', 'love affair', 'mental stress', 'job opportunity']),
            # Additional keys for missing person scenarios that lead to murder cases
            'motive': random.choice(['unknown', 'under investigation', 'robbery', 'revenge', 'dispute']),
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
    
    elif crime_type == 'traffic':
        scenario = random.choice(traffic_scenarios)
        data = {
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            'location': random.choice([
                'NH-1', 'NH-2', 'NH-4', 'NH-8', 'NH-24', 'NH-44', 'Ring Road', 'Outer Ring Road',
                'Main Market Road', 'Highway', 'Express Highway', 'Delhi-Jaipur Highway', 'Mumbai-Pune Expressway',
                'Bangalore-Mysore Road', 'Chennai-Bangalore Highway', 'Yamuna Expressway',
                'Eastern Peripheral Expressway', 'Link Road', 'Bypass Road', 'Service Road',
                'Cantonment Road', 'MG Road', 'Park Street', 'Mall Road', 'Station Road',
                'GT Road', 'Ambala-Chandigarh Highway', 'Agra-Lucknow Expressway'
            ]),
            'vehicle_type': random.choice([
                'car', 'Maruti Swift', 'Honda City', 'Hyundai i20', 'truck', 'Tata truck', 'lorry',
                'bus', 'state transport bus', 'private bus', 'motorcycle', 'bike', 'Royal Enfield',
                'SUV', 'Fortuner', 'Scorpio', 'XUV', 'auto-rickshaw', 'tempo', 'tractor'
            ]),
            'victim_vehicle_or_person': random.choice([
                'pedestrian', 'elderly pedestrian', 'child pedestrian', 'motorcyclist', 'cyclist',
                'scooty rider', 'auto-rickshaw passenger', 'another car', 'school bus', 'tempo traveller',
                'rickshaw puller', 'street vendor', 'person on roadside', 'laborer'
            ]),
            'victim_name': random.choice([
                'Ramesh', 'Priya', 'Suresh', 'Anita', 'Rajesh', 'Meena', 'Vijay', 'Sunita', 'victim'
            ]),
            'condition': random.choice([
                'under influence of alcohol', 'overspeeding', 'rash driving', 'using mobile phone',
                'drowsy driving', 'red light jumping', 'wrong side driving', 'racing'
            ]),
            'alcohol_level': f"{random.randint(50, 250)} mg/100ml",
            'speed': random.randint(80, 150),
            'limit': f"{random.randint(40, 80)} km/h",
            'witness_account': random.choice([
                'rash driving', 'jumping signal', 'overspeeding', 'drunk driving', 'zigzag driving',
                'overtaking dangerously', 'racing with another vehicle', 'mobile phone use'
            ]),
            'injuries': random.choice([
                'head injury', 'multiple fractures', 'internal injuries', 'death on spot',
                'critical condition', 'coma', 'spinal injury', 'limb amputation', 'brain damage'
            ]),
            'section': random.choice(['279', '304A', '338', '337', '304', '184 MV Act', '185 MV Act']),
            'intersection': random.choice([
                'Connaught Place', 'Sector 5 crossing', 'Main Square', 'Park Street junction',
                'MG Road crossing', 'Ring Road intersection', 'Highway toll plaza', 'traffic signal'
            ]),
            'casualty_count': random.randint(1, 8),
            'findings': random.choice([
                'vehicle in good condition', 'no mechanical failure', 'driver negligence',
                'brake failure', 'tire burst', 'defective vehicle', 'poor vehicle maintenance'
            ]),
            'previous_violations': random.randint(2, 30),
            # Additional keys needed by traffic scenarios
            'motive': random.choice(['accident', 'negligence', 'recklessness', 'no criminal intent']),
            'defense': random.choice([
                'mechanical failure', 'sudden obstruction', 'victim fault', 'unavoidable accident',
                'another vehicle caused', 'poor road condition', 'animal crossing'
            ]),
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'
    
    else:  # stampede
        scenario = random.choice(stampede_scenarios)
        
        # First select event/festival
        event = random.choice([
            'religious festival', 'Ganesh Chaturthi', 'Durga Puja', 'Dussehra', 'Diwali', 'Holi',
            'Eid celebration', 'Christmas', 'New Year celebration', 'Kumbh Mela', 'Kanwar Yatra',
            'concert', 'music festival', 'DJ night', 'rock concert', 'classical music concert',
            'sports event', 'cricket match', 'football match', 'marathon', 'IPL match',
            'fair', 'mela', 'exhibition', 'book fair', 'trade fair',
            'political rally', 'election campaign', 'PM rally', 'protest',
            'wedding procession', 'religious procession', 'Muharram procession', 'Rath Yatra',
            'college fest', 'cultural program', 'garba night', 'Navratri celebration',
            'movie premiere', 'celebrity event', 'religious discourse', 'temple inauguration'
        ])
        
        festival_or_event = random.choice([
            'Diwali celebration', 'Holi festival', 'Dussehra', 'Ganesh Visarjan', 'Durga Puja immersion',
            'religious gathering', 'Eid prayers', 'Christmas mass', 'Guru Nanak Jayanti',
            'music concert', 'Bollywood concert', 'DJ event', 'EDM festival',
            'political rally', 'PM rally', 'election meeting', 'New Year celebration', 'New Year Eve party',
            'cricket match', 'IPL final', 'India-Pakistan match', 'temple darshan',
            'Kumbh Mela', 'Ardh Kumbh', 'Maha Kumbh', 'Kanwar Yatra',
            'college fest', 'technical fest', 'garba night', 'dandiya', 'Navratri',
            'Janmashtami', 'Ram Navami', 'Buddha Purnima', 'Mahavir Jayanti'
        ])
        
        # CRITICAL FIX: Match date to festival/event
        date = get_date_for_festival(festival_or_event)
        
        data = {
            'date': date,  # USE FESTIVAL-MATCHED DATE
            'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
            'event': event,
            'festival_or_event': festival_or_event,
            'death_count': random.randint(5, 300),
            'cause': random.choice([
                'asphyxiation', 'trampling', 'crush injuries', 'suffocation', 'cardiac arrest',
                'stampede', 'crowd crush', 'panic', 'chaos'
            ]),
            'failure_details': random.choice([
                'inadequate crowd management', 'no safety measures', 'poor planning', 'lack of barricades',
                'insufficient security', 'no crowd control', 'overcrowding', 'narrow exits',
                'single entry/exit', 'no emergency plan', 'no medical facilities',
                'delayed response', 'poor venue selection', 'inadequate lighting'
            ]),
            'accused_names': random.choice([
                'organizers', 'event management company', 'authorities', 'district administration',
                'trust members', 'committee', 'venue owners', 'security agency', 'local authorities'
            ]),
            'safety_measures': random.choice([
                'provide adequate security', 'crowd control', 'emergency exits', 'proper barricading',
                'medical facilities', 'fire safety', 'multiple entry/exit', 'trained staff', 'CCTV monitoring'
            ]),
            'crowd_count': random.randint(10000, 5000000),
            'capacity': random.randint(5000, 500000),
            'permission_status': random.choice([
                'conditions not followed', 'capacity exceeded', 'no proper permission',
                'permission violated', 'unauthorized event', 'safety norms violated'
            ]),
            'exit_status': random.choice([
                'blocked', 'insufficient', 'locked', 'narrow', 'jammed', 'obstructed',
                'only one exit', 'inadequate', 'not marked'
            ]),
            'section': random.choice(['304A', '304', '336', '337', '338', '285', '286', '287']),
            'festival': random.choice([
                'Dussehra', 'Diwali', 'Holi', 'Eid', 'Ganesh Chaturthi', 'Durga Puja',
                'Navratri', 'Christmas', 'New Year', 'Kumbh Mela', 'Ram Navami'
            ]),
            'venue': random.choice([
                'temple', 'ground', 'stadium', 'hall', 'maidan', 'park', 'auditorium',
                'fairground', 'riverbank', 'ghat', 'fort', 'exhibition center'
            ]),
            'victims_count': random.randint(10, 400),
            'organizer_names': random.choice([
                'event company', 'trust', 'committee', 'NGO', 'religious trust',
                'management committee', 'event managers', 'local body', 'society'
            ]),
            'precautions': random.choice([
                'limit crowd', 'provide security', 'create emergency plan', 'install barricades',
                'deploy police', 'medical teams', 'fire safety', 'crowd marshals', 'CCTV cameras'
            ]),
            'barricade_status': random.choice([
                'inadequate', 'broken', 'insufficient', 'weak', 'poorly placed', 'missing',
                'collapsed', 'not strong enough'
            ]),
            'medical_status': random.choice([
                'insufficient', 'delayed', 'inadequate', 'no ambulances', 'late arrival',
                'not prepared', 'understaffed', 'overwhelmed'
            ]),
            'rumor': random.choice([
                'fire', 'bomb', 'bomb scare', 'structure collapse', 'emergency', 'shooting',
                'terrorist attack', 'earthquake', 'cylinder blast', 'short circuit'
            ]),
            'time': f"{random.randint(1,12)}:{random.choice(['00', '15', '30', '45'])} {random.choice(['AM', 'PM'])}"
        }
        
        description = scenario['template'].format(**data)
        return description, 'criminal'

print("GENERATOR FUNCTIONS ADDED!")
print("Criminal case generator with 7 crime types completed!")
print("Next: Adding Family, Civil, Property, Commercial, Tax, Service, Consumer, Constitutional generators...")

# =============================================================================
# FAMILY CASE GENERATOR - Divorce, DV, Maintenance, Custody
# =============================================================================

def generate_family_description(pet, res, case_no):
    """Generate highly varied family law case descriptions WITH state-specific locations"""
    
    # CRITICAL: Extract state from petitioner/respondent for location matching
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    
    # Determine family case type
    family_types = ['divorce', 'domestic_violence', 'maintenance', 'custody']
    case_type = random.choice(family_types)
    
    if case_type == 'divorce':
        scenario = random.choice(divorce_scenarios)
        
        data = {
            'petitioner': pet,
            'respondent': res,
            'marriage_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(1990,2020)}",
            'cruelty_acts': random.choice([
                'physical violence, verbal abuse, dowry harassment',
                'mental torture, threats, confinement',
                'constant beatings, denial of food, locking in room',
                'burning with cigarettes, pouring hot water, hitting with iron rod',
                'forcing to leave job, restricting movement, isolation from family',
                'sexual abuse, marital rape, unnatural sex demands',
                'alcoholism, coming home drunk, creating scenes',
                'extramarital affair, bringing paramour home, adultery',
                'demanding dowry, harassment by in-laws, threats for more money',
                'taunting about complexion, appearance, inability to conceive',
                'not providing maintenance, desertion, throwing out of house',
                'abusing in front of children, public humiliation, character assassination',
                'forcing into prostitution, immoral trafficking, unnatural acts',
                'threatening to kill, attempted murder, acid attack threats',
                'cruelty during pregnancy, abortion pressure, sex determination demands',
                'gambling away money, drug addiction, criminal activities',
                'not taking to hospital, denying medical treatment',
                'filing false cases, mental harassment through litigation'
            ]),
            'physical_or_mental_cruelty': random.choice([
                'physical beatings and mental torture', 'continuous harassment for money',
                'denial of basic needs and emotional abuse', 'violence and degrading treatment',
                'sexual abuse and physical violence', 'constant humiliation and threats',
                'economic abuse and deprivation', 'isolation and control',
                'torture during pregnancy', 'cruelty in presence of children',
                'abuse by in-laws with husband support', 'marital rape and forced acts',
                'threatening with weapon', 'attempting to murder', 'driving to suicide',
                'not providing food or shelter', 'throwing out of house repeatedly'
            ]),
            'incident_dates': ', '.join([f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}" for _ in range(3)]),
            'medical_evidence': random.choice([
                'bruises and injuries documented', 'psychological trauma reports',
                'hospital records of injuries', 'doctor certificates', 'MLC copy',
                'X-ray showing fractures', 'burn injury reports', 'miscarriage medical records',
                'suicide attempt medical records', 'mental health treatment records',
                'forensic medical examination', 'photographs of injuries',
                'prescription for psychiatric medicines', 'hospital admission records'
            ]),
            'witnesses': random.choice([
                'parents', 'neighbors', 'family members', 'friends', 'siblings',
                'colleague', 'domestic help', 'children', 'relatives',
                'society members', 'security guard', 'shopkeeper', 'doctor',
                'police constable', 'auto driver', 'landlord'
            ]),
            'defense': random.choice([
                'denied allegations', 'claimed provocation', 'counter-allegations filed',
                'claimed petitioner at fault', 'said wife is disobedient',
                'claimed dowry demands by wife family', 'alleged false case',
                'said wife left willingly', 'claimed mutual fights',
                'said wife characterless', 'alleged mental instability of wife',
                'claimed self-defense', 'denied physical violence'
            ]),
            'findings': random.choice([
                'cruelty proved beyond doubt', 'pattern of abuse established',
                'respondent behavior unbearable', 'mental cruelty of high degree',
                'physical violence corroborated', 'medical evidence credible',
                'witnesses reliable', 'respondent failed to rebut',
                'matrimonial home became hell', 'continued cohabitation impossible',
                'irretrievable breakdown of marriage', 'no hope of reconciliation'
            ]),
            # Adultery specific
            'person_name': random.choice([
                'Mr. X', 'colleague Mr. Y', 'friend', 'third party', 'neighbor',
                'business partner', 'subordinate at office', 'boss', 'ex-boyfriend',
                'classmate', 'gym instructor', 'driver', 'tenant', 'co-worker'
            ]),
            'evidence_list': random.choice([
                'photographs, hotel bills, witness statements',
                'private investigator report, messages, call records',
                'admission in cross-examination, circumstantial evidence',
                'WhatsApp chats, emails, social media messages',
                'CCTV footage, hotel check-in registers',
                'caught red-handed by petitioner',
                'confession, credit card statements showing gifts',
                'witnesses saw together repeatedly', 'residing together'
            ]),
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}",
            # Desertion specific
            'years': random.choice(['2', '3', '4', '5', '6', '7', '8', '9', '10']),
            'dates': ', '.join([f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2023)}" for _ in range(2)]),
            'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2016,2024)}",
            # Conversion specific
            'religion': random.choice([
                'Islam', 'Christianity', 'Buddhism', 'another religion', 'Jainism',
                'Sikhism', 'atheism', 'foreign religion'
            ]),
            # Mental illness specific
            'mental_illness': random.choice([
                'schizophrenia', 'bipolar disorder', 'severe depression', 'psychosis',
                'paranoid disorder', 'manic depressive disorder', 'acute mania',
                'delusional disorder', 'severe anxiety disorder', 'OCD',
                'personality disorder', 'dementia', 'mental retardation'
            ]),
            'duration': random.choice(['3 years', '5 years', '7 years', '10 years', 'many years', 'over a decade']),
            'hospital_or_doctor': random.choice([
                'NIMHANS', 'Govt. Mental Hospital', 'Institute of Mental Health',
                'psychiatrist Dr. X', 'Dr. Y - Psychiatrist', 'mental asylum',
                'psychiatric ward of Govt. Hospital', 'private psychiatric facility'
            ]),
            'expert': random.choice(['psychiatrist', 'medical expert', 'psychologist', 'medical board']),
            # Leprosy/VD specific
            'authority': random.choice([
                'Medical Board', 'District Medical Officer', 'Specialist Doctor',
                'Dermatologist', 'Venereologist', 'Government Medical Expert',
                'Panel of Doctors', 'Skin Specialist'
            ]),
            'type': random.choice(['virulent', 'severe', 'communicable', 'incurable', 'contagious', 'infectious']),
            'facility': random.choice([
                'Government Hospital', 'Leprosy Treatment Centre', 'Special Hospital',
                'TB and Leprosy Sanatorium', 'District Hospital', 'Medical College Hospital',
                'Specialized Treatment Facility', 'Govt. Medical Institution'
            ]),
            'disease': random.choice([
                'syphilis', 'gonorrhea', 'sexually transmitted disease', 'venereal disease',
                'HIV/AIDS', 'Hepatitis B', 'genital herpes', 'STD'
            ]),
            'source': random.choice([
                'extramarital relations', 'before marriage', 'unknown source',
                'pre-marital affairs', 'commercial sex', 'illicit relationship',
                'concealed before marriage', 'visiting brothels'
            ]),
            'treatment_details': random.choice([
                'undergoing treatment', 'refused treatment', 'partial treatment',
                'discontinued treatment', 'not responding to treatment',
                'long-term treatment required', 'no cure available'
            ]),
            # Renunciation specific
            'religious_order': random.choice([
                'sanyas', 'monastic order', 'religious ashram', 'sanyasi order',
                'Jain muni', 'Buddhist monk order', 'hermit life', 'renunciate order'
            ]),
            'ascetic_type': random.choice([
                'sannyasi', 'monk', 'ascetic', 'sanyasi', 'muni', 'sadhu',
                'hermit', 'renunciate', 'bhikku', 'swami'
            ]),
            'location': random.choice([
                'Himalayan ashram', 'religious institution', 'monastery',
                'Rishikesh ashram', 'Haridwar', 'Varanasi', 'remote forest',
                'Tirupati', 'Buddhist monastery', 'Jain ashram'
            ]),
            'evidence': random.choice([
                'photographs, ashram records', 'witness statements', 'admission',
                'ashram register', 'changed attire and lifestyle',
                'renounced worldly life', 'living in ashram for years',
                'vow of celibacy', 'gave away property'
            ]),
            # Presumed dead specific
            'persons_or_places': random.choice([
                'relatives, friends, last known locations',
                'family members, police, native place',
                'all known contacts, workplaces, hangouts',
                'parents, siblings, colleagues, hometown',
                'extended family, police stations, hospitals',
                'neighbours, employers, usual haunts'
            ]),
            # No cohabitation specific
            'decree_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
            # Common keys added
            'plaintiff': pet,
            'defendant': res,
            'amount': random.randint(5000, 200000)
        }
        
        description = scenario['template'].format(**data)
        return description, 'family'
    
    elif case_type == 'domestic_violence':
        scenario = random.choice(domestic_violence_scenarios)
        
        data = {
            'petitioner': pet,
            'respondent': res,
            'violence_acts': random.choice([
                'physical beatings, verbal abuse, and threatening',
                'slapping, pushing, and mental torture',
                'assault with household items', 'continuous harassment and intimidation',
                'hitting with belt, throwing objects', 'pulling hair, dragging on floor',
                'burning with cigarette, pouring hot water', 'kicking, punching, strangling',
                'beating with stick, iron rod, chappal', 'locking in room, starving',
                'abusing in filthy language', 'threatening to kill, acid attack',
                'forcing out of house in night', 'not allowing to sleep',
                'denying food, water, basic needs', 'economic abuse, taking away salary',
                'marital rape, forced unnatural sex', 'torture in presence of children',
                'inviting outsiders to abuse', 'stripping, parading naked',
                'threatening with false cases', 'snatching children'
            ]),
            'dates': ', '.join([f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}" for _ in range(3)]),
            'injuries': random.choice([
                'bruises on arms and face', 'head injury and fractures',
                'multiple contusions', 'psychological trauma',
                'broken nose, teeth', 'burn injuries on hands and back',
                'internal injuries', 'miscarriage due to beating',
                'permanent scar on face', 'hearing loss in one ear',
                'vision affected', 'spine injury', 'fracture in ribs',
                'strangulation marks on neck', 'knife injury on abdomen',
                'severe depression, PTSD', 'suicidal tendencies'
            ]),
            'complaint_dates': ', '.join([f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}" for _ in range(2)]),
            'employment_status': random.choice([
                'employed as engineer', 'businessman', 'government servant', 'private employee',
                'works in IT company', 'bank employee', 'doctor', 'teacher', 'police officer',
                'lawyer', 'CA', 'shop owner', 'contractor', 'driver', 'unemployed but capable',
                'retired officer', 'army personnel', 'runs own business'
            ]),
            'types_of_abuse': random.choice([
                'physical, mental, and economic abuse', 'verbal and emotional torture',
                'violence and harassment', 'threats and intimidation',
                'sexual, physical and economic abuse', 'dowry harassment and torture',
                'mental cruelty and deprivation', 'isolation and control',
                'public humiliation and character assassination',
                'threats to life and wellbeing', 'abuse by in-laws with husband consent'
            ]),
            'children_ages': random.choice([
                '3 and 7 years', '5 years', '8 and 10 years', '6 years',
                '2, 5 and 8 years', '4 years', '1 and 3 years', '10 and 12 years',
                '6 months', 'pregnant', 'no children', '15 and 17 years'
            ]),
            'restrictions': random.choice([
                'any act of violence or harassment', 'entering shared household',
                'communicating with petitioner', 'threatening or intimidating',
                'coming within 200 meters', 'contacting family members',
                'disposing shared property', 'cutting utilities',
                'interfering with employment', 'filing false cases',
                'taking children without permission', 'stalking or following'
            ]),
            'amount': random.randint(5000, 100000),
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2005,2020)}",
            'dowry_amount': random.choice([
                'Rs. 10 lakhs', 'Rs. 5 lakhs cash', 'Rs. 20 lakhs',
                'Rs. 15 lakhs',
                'Rs. 20 lakhs'
            ]),
            'dowry_items': random.choice([
                'car and jewelry',
                'gold ornaments',
                'flat and vehicle',
                'property and valuables'
            ]),
            'forced_actions': random.choice([
                'bring money from parents',
                'sign property documents',
                'leave matrimonial home',
                'do all household work'
            ]),
            'medical': random.choice([
                'injury marks documented',
                'treatment records available',
                'psychological trauma evident',
                'hospitalization required'
            ]),
            'value': random.randint(200000, 2000000),
            'compensation': random.randint(100000, 500000),
            # Elderly mother specific
            'abuse_types': random.choice([
                'verbal abuse, denial of food, and neglect',
                'physical violence and eviction threats',
                'mental torture and financial exploitation'
            ]),
            'actions': random.choice([
                'live in servant quarters',
                'leave the house',
                'transfer property',
                'stop interfering'
            ]),
            'property_details': random.choice([
                'over ancestral property',
                'regarding will',
                'about ownership',
                'concerning inheritance'
            ]),
            'witnesses': random.choice(['relatives', 'neighbors', 'social workers']),
            'orders': random.choice([
                'protection order, residence order',
                'restraining order against son',
                'right to stay in property'
            ]),
            # Live-in partner specific
            'violence_type': random.choice([
                'physical violence and threats',
                'mental torture and harassment',
                'eviction attempts and abuse'
            ]),
            'financial_abuse': random.choice([
                'denial of financial support',
                'taking away earnings',
                'refusal to maintain',
                'economic exploitation'
            ]),
            # Common keys added
            'plaintiff': pet,
            'defendant': res,
            'amount': random.randint(5000, 50000)
        }
        
        description = scenario['template'].format(**data)
        return description, 'family'
    
    elif case_type == 'maintenance':
        scenario = random.choice(maintenance_scenarios)
        
        data = {
            'petitioner': pet,
            'respondent': res,
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
            'income': random.randint(30000, 200000),
            'occupation': random.choice([
                'engineer', 'businessman', 'government employee',
                'private sector employee', 'professional', 'contractor'
            ]),
            'wife_income_status': random.choice([
                'no independent source of income',
                'minimal income insufficient for needs',
                'unemployed and dependent',
                'earning Rs. 10,000 per month'
            ]),
            'children_count': random.choice(['one', 'two', 'three']),
            'ages': random.choice(['5 years', '3 and 7 years', '8 and 10 years', '4, 6 and 9 years']),
            'expenses': random.randint(20000, 80000),
            'amount': random.randint(10000, 50000),
            'child_amount': random.randint(5000, 20000),
            # Divorced wife specific
            'age': random.randint(30, 55),
            'reasons': random.choice([
                'health issues and no skills',
                'old age and unemployment',
                'taking care of children',
                'medical conditions'
            ]),
            # Parents maintenance specific
            'father_age': random.randint(65, 85),
            'mother_age': random.randint(60, 80),
            'ailments': random.choice([
                'diabetes and heart disease',
                'arthritis and hypertension',
                'multiple health issues',
                'age-related ailments'
            ]),
            # Interim maintenance specific
            # Common keys added
            'plaintiff': pet,
            'defendant': res
        }
        
        description = scenario['template'].format(**data)
        return description, 'family'
    
    elif case_type == 'custody':
        scenario = random.choice(custody_scenarios)
        
        data = {
            'children_count': random.choice(['one child', 'two children', 'three children']),
            'ages': random.choice(['3 years', '5 and 8 years', '4, 7 and 10 years', '6 years']),
            'mother_reasons': random.choice([
                'tender age of children, emotional bond',
                'better care and nurturing capability',
                'stable home environment',
                'children attachment to mother'
            ]),
            'father_reasons': random.choice([
                'better financial capacity',
                'can provide better education',
                'mother neglectful',
                'moral character concerns'
            ]),
            'current_custody': random.choice(['mother', 'father', 'grandparents']),
            'employment_or_financial_status': random.choice([
                'employed with stable income',
                'good financial position',
                'owns business',
                'working professional'
            ]),
            'employment_or_financial_status2': random.choice([
                'employed with stable income',
                'good financial position',
                'owns business',
                'working professional'
            ]),
            'evaluation': random.choice([
                'children comfortable with mother',
                'bonding strong with father',
                'neutral preference',
                'welfare best with mother'
            ]),
            'parent': random.choice(['mother', 'father']),
            'visitation_schedule': random.choice([
                'alternate weekend',
                'first and third Sunday',
                'weekly on Sunday',
                'fortnight'
            ]),
            # Habeas corpus specific
            'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
            'allegations': random.choice([
                'domestic violence by father',
                'neglect by mother',
                'unfit parent',
                'child abuse'
            ]),
            'preference': random.choice([
                'wish to stay with mother',
                'comfortable with father',
                'want to be with grandparents'
            ]),
            'factors': random.choice([
                'welfare and stability',
                'emotional wellbeing',
                'best interests of child',
                'educational needs'
            ]),
            # Grandparents custody specific
            'status': random.choice([
                'separated and in conflict',
                'divorced',
                'deceased',
                'unable to care'
            ]),
            'age': random.randint(4, 12),
            'duration': random.choice(['3 years', '5 years', '2 years', 'since birth']),
            'fitness_status': random.choice([
                'rehabilitation from addiction',
                'unstable employment',
                'new relationships',
                'frequent relocation'
            ]),
            'decision': random.choice([
                'custody to grandparents',
                'custody to parents with conditions',
                'shared arrangement'
            ]),
            'person': random.choice(['grandparents', 'mother', 'father']),
            'conditions': random.choice([
                'regular visitation to parents',
                'financial support from parents',
                'monitoring by welfare officer',
                'periodic review'
            ]),
            # Common keys added
            'plaintiff': pet,
            'defendant': res,
            'amount': random.randint(5000, 50000)
        }
        
        description = scenario['template'].format(**data)
        return description, 'family'
    
    # Default fallback
    return f"Family law matter between {pet} and {res} involving matrimonial dispute and relief sought.", 'family'

print("Family case generator completed with divorce, domestic violence, maintenance, custody!")
print("Next: Adding Civil, Property, Commercial, Tax, Service, Consumer, Constitutional generators...")

# =============================================================================
# CIVIL CASE GENERATOR - Contracts, Recovery, Torts, etc.
# =============================================================================

def generate_civil_description(pet, res, case_no):
    """Generate varied civil case descriptions WITH state-specific locations"""
    
    # CRITICAL: Extract state from petitioner/respondent for location matching
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    
    scenario = random.choice(civil_scenarios)
    
    data = {
        'contract_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'contract_purpose': random.choice(['supply of goods', 'construction work', 'services', 'business transaction']),
        'contract_terms': random.choice(['delivery within 6 months', 'quality specifications', 'payment terms', 'performance obligations']),
        'amount': random.randint(500000, 50000000),
        'breach_details': random.choice(['non-delivery', 'defective performance', 'delay', 'abandoning work']),
        'breach_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'loss_amount': random.randint(1000000, 100000000),
        'defense': random.choice(['force majeure', 'plaintiff breach', 'terms not agreed', 'circumstances beyond control']),
        'contract_validity': random.choice(['valid and binding', 'legally enforceable']),
        'damages': random.randint(2000000, 80000000),
        'rate': random.randint(9, 18),
        'loan_type': random.choice(['business loan', 'personal loan', 'advance', 'financial accommodation']),
        'loan_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2018,2023)}",
        'acknowledgment_method': random.choice(['promissory note', 'written acknowledgment', 'email', 'WhatsApp message']),
        'repayment_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'interest': random.randint(12, 24),
        'proof_method': random.choice(['documentary evidence', 'bank statements', 'witness testimony']),
        'principal': random.randint(1000000, 50000000),
        'interest_amount': random.randint(200000, 10000000),
        'total': random.randint(1500000, 60000000),
        'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'defamatory_statement': random.choice(['involved in fraud', 'of bad character', 'corrupt person', 'criminal', 'cheat']),
        'publication_medium': random.choice(['newspaper', 'social media', 'public meeting', 'WhatsApp groups', 'email']),
        'plaintiff_status': random.choice(['businessman', 'professional', 'public figure', 'respectable person']),
        'damages_details': random.choice(['business loss', 'mental agony', 'reputation damage', 'social boycott']),
        'compensation': random.randint(500000, 10000000),
        'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
        'negligent_act': random.choice(['careless driving', 'faulty construction', 'inadequate safety', 'breach of duty']),
        'damage_description': random.choice(['injuries', 'property damage', 'business loss', 'physical harm']),
        'injuries_or_losses': random.choice(['broken bones', 'head injury', 'permanent disability', 'financial loss']),
        'medical_expense': random.randint(100000, 2000000),
        'income_loss': random.randint(500000, 5000000),
        'breach_details': random.choice(['failed to exercise reasonable care', 'ignored safety norms', 'reckless act']),
        'liability_nature': random.choice(['strict liability', 'negligence established', 'vicarious liability']),
        'breakdown': random.choice(['medical Rs. 5 lakhs, loss of income Rs. 10 lakhs', 'itemized compensation']),
        'declaration_sought': random.choice(['plaintiff is lawful owner', 'document is void', 'plaintiff has right']),
        'plaintiff_case': random.choice(['acquired right through law', 'document forged', 'entitled by statute']),
        'defendant_case': random.choice(['plaintiff has no right', 'document genuine', 'statute not applicable']),
        'legal_issue': random.choice(['interpretation of statute', 'validity of document', 'legal title']),
        'documents': random.choice(['title deeds, agreements', 'official records', 'correspondence']),
        'applicable_law': random.choice(['Transfer of Property Act', 'Contract Act', 'specific statute']),
        'examination_details': random.choice(['evidence and law', 'documents and testimony', 'legal precedents']),
        'findings': random.choice(['plaintiff entitled', 'defendant claim unsustainable', 'law favors plaintiff']),
        'declaration': random.choice(['plaintiff is owner', 'document is void', 'right established']),
        'consequential_relief': random.choice(['Permanent injunction', 'Possession', 'No relief']),
        'act_to_restrain': random.choice(['interfering with plaintiff rights', 'trespassing', 'causing nuisance', 'breaching contract']),
        'plaintiff_right': random.choice(['lawful owner', 'entitled to', 'having legal right']),
        'threatened_act': random.choice(['dispossess plaintiff', 'interfere', 'violate rights', 'breach agreement']),
        'act_nature': random.choice(['illegal', 'wrongful', 'in violation of rights', 'unauthorized']),
        'injunction_terms': random.choice(['trespassing on property', 'interfering with business', 'committing nuisance']),
        'contract_obligation': random.choice(['transfer property', 'deliver goods', 'complete work', 'perform services']),
        'plaintiff_performance': random.choice(['paying consideration', 'completing his part', 'fulfilling obligations']),
        'failure_details': random.choice(['refusing to transfer', 'not delivering', 'abandoning work']),
        'time_status': random.choice(['not essence of contract', 'extended by mutual consent', 'was essence']),
        'modifications': random.choice(['none', 'adjusted consideration', 'extended timeline']),
        'timeframe': random.choice(['3 months', '6 months', '60 days']),
        'nuisance_act': random.choice(['loud noise', 'pollution', 'blocking access', 'dangerous activity']),
        'suffering_details': random.choice(['health problems', 'loss of peace', 'property damage', 'business loss']),
        'complaint_dates': ', '.join([f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}" for _ in range(2)]),
        'nuisance_type': random.choice(['public nuisance', 'private nuisance', 'statutory nuisance']),
        'affected_rights': random.choice(['peaceful enjoyment', 'health and comfort', 'property rights']),
        'period': random.choice(['30 days', '60 days', '3 months']),
        'minor_name': random.choice(['minor child', 'the minor', 'infant']),
        'age': random.randint(5, 17),
        'parents_status': random.choice(['deceased', 'incapacitated', 'unfit', 'absent']),
        'petitioner_relation': random.choice(['uncle', 'grandfather', 'elder brother', 'maternal uncle']),
        'property_value': random.randint(1000000, 50000000),
        'welfare_reasons': random.choice(['proper upbringing', 'education', 'management of property']),
        'other_claimants': random.choice(['none', 'other relatives', 'father side family']),
        'examination': random.choice(['minor welfare', 'petitioner suitability', 'competing claims']),
        'guardian': random.choice(['petitioner', 'maternal uncle', 'grandfather']),
        'conditions': random.choice(['bond for proper care', 'periodic reporting', 'court supervision']),
        'will_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'testator': random.choice(['deceased', 'late Mr. X', 'the testator']),
        'death_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'estate_value': random.randint(10000000, 500000000),
        'beneficiaries': random.choice(['children', 'wife and children', 'named persons', 'charities']),
        'witnesses': random.choice(['two witnesses', 'attesting witnesses']),
        'objectors': random.choice(['legal heirs', 'excluded persons', 'rival claimants']),
        'objections': random.choice(['undue influence', 'lack of testamentary capacity', 'fraud', 'forgery']),
        'executor_name': random.choice(['executor named', 'petitioner', 'family member']),
        'holding': random.choice(['established', 'proven', 'affirmed', 'confirmed', 'upheld']),  # Added for various civil scenarios
        'plaintiff': pet,  # Added for partition and other civil scenarios
        'defendants': res  # Added for partition scenarios
    }
    
    description = scenario['template'].format(**data)
    return description, 'civil'

# =============================================================================
# PROPERTY CASE GENERATOR
# =============================================================================

def generate_property_description(pet, res, case_no):
    """Generate varied property dispute descriptions WITH state-specific locations"""
    
    # CRITICAL: Extract state from petitioner/respondent
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    
    scenario = random.choice(property_scenarios)
    
    data = {
        'survey': f"{random.randint(1,999)}/{random.randint(1,500)}",
        'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
        'title_source': random.choice(['sale deed dated', 'inheritance from', 'adverse possession', 'gift deed']),
        'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(1990,2020)}",
        'def_title_source': random.choice(['prior sale deed', 'family settlement', 'partition deed', 'possession']),
        'revenue_entry': random.choice(['plaintiff as owner', 'disputed', 'defendant shown', 'entries unclear']),
        'possession_party': random.choice(['plaintiff', 'defendant', 'disputed', 'joint']),
        'possession_years': random.randint(10, 40),
        'plaintiff_docs': random.choice(['sale deeds, tax receipts', 'chain of title documents', 'possession evidence']),
        'defendant_docs': random.choice(['alternative title deeds', 'family records', 'revenue documents']),
        'finding': random.choice(['superior and valid', 'defective', 'prior in time']),
        'decree': random.choice(['in favor of plaintiff', 'dismissing suit', 'partial relief']),
        'ancestor': random.choice(['father', 'grandfather', 'late Mr. X']),
        'total_extent': f"{random.randint(5,50)} acres",
        'plaintiff_share': random.choice(['1/3', '1/4', '1/2', 'equal share']),
        'property_description': random.choice(['agricultural land', 'house property', 'commercial building', 'ancestral property']),
        'value': random.randint(5000000, 500000000),
        'partition_status': random.choice(['not possible', 'feasible', 'partially possible']),
        'partition_method': random.choice(['metes and bounds', 'sale and distribution', 'allotment of specific portions']),
        'allocations': random.choice(['specific portions to each', 'by drawing lots', 'by agreement']),
        'start_year': random.randint(1980, 2000),
        'possession_nature': random.choice(['open, continuous, hostile', 'adverse and exclusive', 'uninterrupted']),
        'owner': random.choice(['true owner', 'title holder', 'record owner']),
        'owner_action': random.choice(['visited property', 'objected', 'filed suit', 'demanded possession']),
        'tax_year': random.randint(1985, 2005),
        'testimony': random.choice(['long possession', 'treating as owner', 'cultivation']),
        'defendant_claim': random.choice(['ownership', 'superior title', 'permissive possession']),
        'examination': random.choice(['title documents', 'possession evidence', 'limitation period']),
        'finding': random.choice(['proved', 'not established', 'period completed']),
        'party': random.choice(['plaintiff', 'defendant']),
        'amount': random.randint(1000000, 100000000),
        'advance': random.randint(100000, 10000000),
        'deadline': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'refusal_reason': random.choice(['better offer received', 'changed mind', 'title disputed', 'market value increased']),
        'current_value': random.randint(5000000, 200000000),
        'refusal_nature': random.choice(['unjustified', 'motivated by greed', 'breach of contract']),
        'time_essence': random.choice(['not essence', 'was essence but extended', 'was essence']),
        'conditions': random.choice(['on payment of balance', 'within specified time', 'as per agreement']),
        'path': random.choice(['pathway', 'passage', 'access road', 'lane']),
        'years': random.randint(20, 60),
        'easement_type': random.choice(['prescription', 'necessity', 'grant', 'long user']),
        'obstruction_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'obstruction_method': random.choice(['constructing wall', 'locking gate', 'parking vehicle', 'debris']),
        'usage_evidence': random.choice(['witness testimony', 'photographs', 'usage records']),
        'map_evidence': random.choice(['pathway shown', 'access marked', 'traditional path']),
        'defense': random.choice(['no right of way', 'alternative access', 'recent claim']),
        'holding': random.choice(['established by prescription', 'by necessity', 'not proved']),
        'injunction_status': random.choice(['granted', 'refused', 'granted with conditions']),
        'pl_survey': f"{random.randint(1,500)}/{random.randint(1,300)}",
        'def_survey': f"{random.randint(1,500)}/{random.randint(1,300)}",
        'dispute_origin': random.choice(['new construction', 'cultivation', 'fencing', 'survey discrepancy']),
        'revenue_boundary': random.choice(['clearly defined', 'ambiguous', 'disputed']),
        'actual_occupation': random.choice(['beyond boundaries', 'as per records', 'encroachment']),
        'survey_findings': random.choice(['encroachment by defendant', 'plaintiff beyond limits', 'as per records']),
        'plaintiff_claim': random.choice(['as per revenue records', 'traditional boundaries', 'actual occupation']),
        'defendant_claim': random.choice(['different alignment', 'extended boundaries', 'acquisition by adverse possession']),
        'demarcation_basis': random.choice(['revenue records', 'fresh survey', 'compromise']),
        'tenancy_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2000,2015)}",
        'rent': random.randint(5000, 100000),
        'default_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'arrears': random.randint(50000, 1000000),
        'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'tenant_defense': random.choice(['rent paid', 'rent disputed', 'repair deductions', 'hardship']),
        'additional_grounds': random.choice(['personal use', 'renovation', 'bona fide need', 'subletting']),
        'requirement': random.choice(['own residence', 'family member', 'business', 'reconstruction']),
        'findings': random.choice(['default proved', 'landlord requirement genuine', 'grounds established']),
        'eviction_status': random.choice(['ordered', 'refused', 'on payment of arrears']),
        'arrears_amount': random.randint(100000, 2000000),
        'mortgage_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'property_description': random.choice(['house property', 'agricultural land', 'commercial building']),
        'rate': random.randint(12, 18),
        'total': random.randint(2000000, 50000000),
        'deposit': random.randint(1000000, 30000000),
        'mortgagee_claim': random.choice(['higher amount', 'interest arrears', 'additional charges']),
        'balance': random.randint(500000, 20000000),
        'final_amount': random.randint(1500000, 40000000),
        'period': random.choice(['3 months', '6 months', '90 days']),
        'stated_amount': random.randint(1000000, 50000000),
        'fraud_method': random.choice(['undue influence', 'misrepresentation', 'fraud', 'coercion', 'forgery']),
        'allegations': random.choice(['signature forged', 'no consideration', 'document obtained by fraud', 'mental incapacity']),
        'defense': random.choice(['transaction genuine', 'consideration paid', 'executed voluntarily']),
        'plaintiff_status': random.choice(['illiterate', 'of unsound mind', 'old age', 'under pressure']),
        'evidence': random.choice(['expert opinion', 'witness testimony', 'circumstantial evidence', 'document examination']),
        'deed_status': random.choice(['voidable', 'void', 'valid but disputed']),
        'holding': random.choice(['fraud proved', 'transaction genuine', 'undue influence established']),
        'cancellation_status': random.choice(['ordered', 'refused', 'set aside']),
        'trespass_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'trespass_method': random.choice(['entering property', 'constructing', 'cultivating', 'occupying']),
        'damages_type': random.choice(['loss of use', 'damage to property', 'mental agony', 'business loss']),
        'title_party': random.choice(['plaintiff', 'disputed', 'plaintiff through title deeds']),
        'possession_party': random.choice(['plaintiff', 'defendant illegally', 'plaintiff for years']),
        'injunction_terms': random.choice(['entering property', 'interfering', 'trespassing', 'obstructing']),
        'encroached_area': f"{random.randint(100,1000)} sq. ft.",
        'encroachment_description': random.choice(['construction', 'wall', 'shed', 'temporary structure', 'fence']),
        'encroachment_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2018,2024)}",
        'title_source': random.choice(['sale deed', 'inheritance', 'govt. allotment']),
        'report_findings': random.choice(['encroachment confirmed', 'as per plaintiff claim', 'defendant beyond boundaries']),
        'deceased_name': random.choice(['late Mr. X', 'deceased', 'father']),
        'death_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'heirs_list': random.choice(['widow and three children', 'children', 'legal heirs']),
        'dispute_issue': random.choice(['share of property', 'inclusion as heir', 'quantum of share', 'exclusion claim']),
        'certificate_status': random.choice(['issued', 'pending', 'not required']),
        'declaration': random.choice(['all heirs entitled equally', 'as per law of succession', 'shares defined']),
        'division_ratio': random.choice(['equal shares', 'as per law', '1/3 to widow, rest to children']),
        'plaintiff': pet,  # Added for property scenarios
        'defendant': res,  # Added for property scenarios
        'defendants': res  # Added for property scenarios
    }
    
    description = scenario['template'].format(**data)
    return description, 'property'

# =============================================================================
# ADDITIONAL SPECIALIZED GENERATOR FUNCTIONS
# =============================================================================

def generate_labour_description(pet, res, case_no):
    """Generate labour & employment case descriptions WITH state-specific locations"""
    
    # CRITICAL: Extract state from petitioner/respondent
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    
    scenario = random.choice(labour_scenarios)
    
    data = {
        'worker_count': random.randint(10, 500),
        'establishment': pet if 'ltd' in pet.lower() or 'company' in pet.lower() else 'Industrial Establishment',
        'wage_amount': random.randint(50000, 5000000),
        'months': random.randint(3, 24),
        'management_defense': random.choice(['financial difficulties', 'workers absent', 'work not done', 'closure']),
        'commissioner_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'award_details': random.choice(['wages ordered to be paid', 'partial payment', 'dismissed']),
        'back_wages': f"₹{random.randint(100000, 10000000)}",
        'reinstatement': random.choice(['ordered', 'with back wages', 'in lieu of compensation', 'refused']),
        'employee_name': res if 'union' not in res.lower() else 'Employee',
        'designation': random.choice(['Worker', 'Supervisor', 'Clerk', 'Operator', 'Technician']),
        'company': pet if 'ltd' in pet.lower() else 'Company Ltd.',
        'service_years': random.randint(5, 30),
        'termination_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'termination_grounds': random.choice(['misconduct', 'poor performance', 'absenteeism', 'insubordination']),
        'tribunal_finding': random.choice(['termination illegal', 'no proper enquiry', 'principles violated', 'termination justified']),
        'relief_granted': random.choice(['reinstatement with back wages', 'compensation in lieu', 'dismissed']),
        'retrenched_count': random.randint(10, 200),
        'retrenchment_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'closure_reason': random.choice(['financial losses', 'covid impact', 'closure of unit', 'automation']),
        'compensation': f"₹{random.randint(100000, 5000000)}",
        'years_service': random.randint(5, 25),
        'relief': random.choice(['compensation', 'reinstatement', 'regularization']),
        'court_order': random.choice(['compensation ordered', 'reinstatement directed', 'retrenchment valid']),
        'item_no': random.randint(1, 15),
        'allegations': random.choice(['service conditions changed', 'workload increased', 'wages reduced', 'benefits withdrawn']),
        'affected_workers': random.randint(50, 500),
        'settlement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2020)}",
        'finding': random.choice(['unfair practice established', 'no unfair practice', 'settlement violated']),
        'ay': f"{random.randint(2015,2023)}-{random.randint(16,24)}",
        'bonus_percentage': random.randint(15, 25),
        'offered_percentage': random.randint(8, 12),
        'surplus': random.randint(1000000, 100000000),
        'award_percentage': random.randint(12, 20),
        'arrears': random.randint(500000, 10000000),
        'employee': res,
        'retirement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'years': random.randint(20, 40),
        'gratuity_amount': random.randint(500000, 5000000),
        'allegation': random.choice(['misconduct', 'violation of rules', 'unauthorized absence']),
        'order': random.choice(['payment ordered', 'withheld', 'reduced amount']),
        'interest_rate': random.randint(8, 12),
        'period': f"{random.randint(2018,2022)} to {random.randint(2023,2024)}",
        'amount': random.randint(1000000, 50000000),
        'worker_count': random.randint(50, 1000),
        'inspection_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'act_section': random.choice(['Section 7A ESIC Act', 'Section 7Q PF Act']),
        'damages': random.randint(100000, 10000000),
        'principal': pet,
        'contractor': res if 'contractor' in res.lower() else 'Contractor',
        'workers': random.randint(20, 200),
        'work_nature': random.choice(['loading/unloading', 'cleaning', 'security', 'maintenance', 'canteen']),
        'since_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'award': random.choice(['regularization ordered', 'contract labour abolished', 'dismissed']),
        'plaintiff': pet,  # Added for labour scenarios
        'defendant': res,  # Added for labour scenarios
        'holding': random.choice(['in favor of workers', 'dismissed', 'partly allowed'])  # Added for labour scenarios
    }
    
    description = scenario.format(**data)
    return description, 'labour'

def generate_ip_description(pet, res, case_no):
    """Generate Intellectual Property case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(ip_scenarios)
    
    data = {
        'plaintiff_mark': f"{random.choice(['TECH', 'SMART', 'MEGA', 'SUPER', 'PRIME'])}{random.choice(['PLUS', 'PRO', 'MAX', 'STAR', 'CARE'])}",
        'reg_no': f"{random.randint(100000, 9999999)}",
        'user_since': random.randint(1990, 2015),
        'defendant_mark': f"{random.choice(['TECH', 'SMART', 'MEGA', 'SUPER', 'PRIME'])}{random.choice(['PLUS', 'PRO', 'MAX', 'STAR', 'CARE'])}",
        'goodwill': random.randint(10000000, 500000000),
        'phonetic': random.choice(['high', 'substantial', 'confusing']),
        'visual': random.choice(['deceptively similar', 'identical', 'substantially similar']),
        'damages': random.randint(1000000, 50000000),
        'patent_no': f"{random.randint(100000, 999999)}/{random.randint(2010, 2020)}",
        'invention': random.choice(['pharmaceutical composition', 'mechanical device', 'chemical process', 'electronic circuit']),
        'grant_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'claims': random.randint(5, 30),
        'infringing_product': random.choice(['similar device', 'equivalent product', 'same composition']),
        'prior_art': random.choice(['distinguished', 'not cited', 'overcome']),
        'work_type': random.choice(['literary work', 'artistic work', 'cinematograph film', 'sound recording', 'computer program']),
        'creation_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'author': pet,
        'registration': f"L-{random.randint(10000, 99999)}/{random.randint(2010, 2020)}",
        'copied_elements': random.choice(['substantial portions', 'entire work', 'key elements', 'distinctive features']),
        'defense': random.choice(['independent creation', 'fair dealing', 'license', 'public domain']),
        'holding': random.choice(['infringement established', 'dismissed', 'partial infringement']),
        'compensation': random.randint(500000, 20000000),
        'design_no': f"{random.randint(200000, 299999)}",
        'article': random.choice(['furniture', 'container', 'textile', 'electrical appliance']),
        'features': random.choice(['ornamental features', 'shape and configuration', 'pattern', 'surface ornamentation']),
        'defendant_design': random.choice(['substantial copy', 'fraudulent imitation', 'colorable variation']),
        'goods_count': random.randint(100, 10000),
        'mark': f"{random.choice(['ABC', 'XYZ', 'PQR'])}{random.choice(['TECH', 'PLUS', 'CARE'])}",
        'since': random.randint(1980, 2010),
        'territory': random.choice(['India', 'particular states', 'nationwide']),
        'defendant_mark': f"{random.choice(['ABC', 'XYZ', 'PQR'])}{random.choice(['TECH', 'PLUS', 'CARE'])}",
        'misrepresentation': random.choice(['get-up copied', 'packaging similar', 'trade dress', 'color scheme']),
        'confusion_evidence': random.choice(['customer testimony', 'survey evidence', 'actual confusion cases']),
        'information_type': random.choice(['customer database', 'technical know-how', 'business methods', 'formulations']),
        'employee': res,
        'competitor': res if 'ltd' in res.lower() else 'Competitor Company',
        'nca_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'disputed_domain': f"{random.choice(['tech', 'smart', 'mega'])}{random.choice(['plus', 'pro', 'care'])}.com",
        'reg_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2018,2023)}",
        'trademark': f"{random.choice(['TECH', 'SMART', 'MEGA'])}PLUS",
        'bad_faith': random.choice(['blocking registration', 'selling to trademark owner', 'diverting traffic']),
        'panel_order': random.choice(['transfer', 'cancel', 'dismissed']),
        'plaintiff': pet,  # Added for IP scenarios
        'defendant': res,  # Added for IP scenarios
        'amount': random.randint(100000, 50000000)  # Added for IP scenarios
    }
    
    description = scenario.format(**data)
    return description, 'ip'

def generate_banking_description(pet, res, case_no):
    """Generate Banking & Finance case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(banking_scenarios)
    
    data = {
        'account_no': f"{random.randint(10000000, 99999999)}",
        'sanctioned': random.randint(1000000, 100000000),
        'sanction_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'outstanding': random.randint(2000000, 150000000),
        'interest': random.randint(9, 18),
        'default_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'possession_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2023,2024)}",
        'borrower_defense': random.choice(['financial difficulties', 'dispute in valuation', 'procedure not followed']),
        'decree_amount': random.randint(2500000, 160000000),
        'bank': pet if 'bank' in pet.lower() else 'Bank',
        'dues': random.randint(1000000, 100000000),
        'objections': random.choice(['valuation incorrect', 'NPA classification wrong', 'notice defective']),
        'npa_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2023)}",
        'valuation': random.randint(5000000, 200000000),
        'sale_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2023,2024)}",
        'deposit': random.randint(100000, 10000000),
        'holding': random.choice(['notice valid', 'procedure followed', 'objections dismissed', 'sale set aside']),
        'fi': pet,
        'borrower': res,
        'facility': random.randint(10000000, 500000000),
        'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2023,2024)}",
        'rc_no': f"RC/{random.randint(100, 999)}/{random.randint(2023,2024)}",
        'attached_assets': random.choice(['immovable property', 'bank accounts', 'vehicles', 'machinery']),
        'recovered': random.randint(1000000, 50000000),
        'balance': random.randint(500000, 50000000),
        'cheque_no': random.randint(100000, 999999),
        'amount': random.randint(50000, 10000000),
        'cheque_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'return_reason': random.choice(['Insufficient Funds', 'Account Closed', 'Payment Stopped', 'Exceeds Arrangement']),
        'return_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'liability': random.choice(['loan repayment', 'business transaction', 'purchase consideration', 'debt']),
        'defense': random.choice(['no legally enforceable debt', 'cheque blank', 'amount disputed', 'consideration failed']),
        'fine': random.randint(50000, 10000000),
        'debtor': res,
        'creditor': pet,
        'default_amount': random.randint(1000000, 500000000),
        'demand_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'cirp_costs': random.randint(1000000, 50000000),
        'rp': random.choice(['Mr. A.K. Sharma', 'Ms. R. Verma', 'Mr. S.N. Patel']),
        'coc_percentage': random.randint(66, 100),
        'outcome': random.choice(['Resolution Plan Approved', 'Liquidation Ordered']),
        'holder': res,
        'last_four': random.randint(1000, 9999),
        'disputed_amount': random.randint(50000, 500000),
        'transaction_dates': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2023,2024)}",
        'deficiency': random.choice(['no two-factor authentication', 'inadequate security', 'delay in blocking']),
        'liability_determination': random.choice(['bank liable', 'customer liable', 'shared liability']),
        'refund': random.randint(50000, 500000),
        'mortgage_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2010,2020)}",
        'property': random.choice(['House No. X', 'Plot No. Y', 'Shop No. Z']),
        'principal': random.randint(1000000, 50000000),
        'costs': random.randint(50000, 500000),
        'upset_price': random.randint(1500000, 60000000),
        'plaintiff': pet,  # Added for banking scenarios
        'defendant': res,  # Added for banking scenarios
        'amount': random.randint(100000, 100000000)  # Added for banking scenarios
    }
    
    description = scenario.format(**data)
    return description, 'banking'

def generate_mac_description(pet, res, case_no):
    """Generate Motor Accident Claims descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(mac_scenarios)
    
    data = {
        'accident_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'accident_location': random.choice(['NH-8', 'Main Road', 'City Center', 'Highway', 'Junction']),
        'vehicle_type': random.choice(['Car', 'Truck', 'Bus', 'Motorcycle', 'Auto']),
        'vehicle_no': f"{random.choice(['DL', 'MH', 'KA', 'TN', 'UP'])}-{random.randint(1,20)}-{random.choice(['A','B','C','D'])}-{random.randint(1000,9999)}",
        'driver': random.choice(['driver', 'owner', 'unknown driver']),
        'victim': res,
        'age': random.randint(18, 70),
        'injuries': random.choice(['multiple fractures', 'head injury', 'spinal injury', 'leg amputation', 'permanent disability']),
        'hospital': random.choice(['City Hospital', 'Medical College', 'Private Hospital', 'Trauma Center']),
        'medical_expenses': random.randint(50000, 1000000),
        'disability': random.randint(20, 100),
        'earning': random.randint(15000, 100000),
        'multiplier': random.randint(10, 18),
        'compensation': random.randint(500000, 20000000),
        'insurer': random.choice(['National Insurance', 'New India Assurance', 'Oriental Insurance', 'United India Insurance']),
        'deceased': res,
        'dependents': random.choice(['wife and 2 children', 'parents', 'widow', 'family of 4']),
        'income': random.randint(20000, 100000),
        'prospects': random.randint(30, 50),
        'deductions': f"1/{random.randint(3,5)}",
        'dependency_loss': random.randint(1000000, 10000000),
        'consortium': random.randint(40000, 100000),
        'funeral': random.randint(15000, 50000),
        'total_compensation': random.randint(1500000, 12000000),
        'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
        'fir_no': f"{random.randint(100,999)}/{random.randint(2020,2024)}",
        'treatment_cost': random.randint(100000, 500000),
        'ex_gratia': random.choice([25000, 50000, 200000]),
        'vehicle1': f"Car {random.randint(1000,9999)}",
        'vehicle2': f"Truck {random.randint(1000,9999)}",
        'driver1': random.choice(['Mr. X', 'Mr. Y']),
        'driver2': random.choice(['Mr. A', 'Mr. B']),
        'allegation1': random.choice(['rashness', 'high speed', 'wrong side', 'signal jump']),
        'allegation2': random.choice(['sudden braking', 'no lights', 'overloading', 'mechanical failure']),
        'witnesses': random.randint(2, 5),
        'findings': random.choice(['both drivers negligent', 'driver1 more at fault', 'driver2 fully responsible']),
        'contribution1': random.randint(30, 70),
        'contribution2': random.randint(30, 70),
        'final_compensation': random.randint(300000, 5000000),
        'claimant': res,
        'injury': random.choice(['simple injury', 'minor fracture', 'soft tissue injury']),
        'medical_certificate': random.choice(['provided', 'on record']),
        'evidence': random.choice(['medical bills', 'disability certificate']),
        'plaintiff': pet,  # Added for MAC scenarios
        'defendant': res,  # Added for MAC scenarios
        'amount': random.randint(100000, 20000000)  # Added for MAC scenarios
    }
    
    description = scenario.format(**data)
    return description, 'mac'

def generate_land_acquisition_description(pet, res, case_no):
    """Generate Land Acquisition case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(land_acquisition_scenarios)
    
    data = {
        'project': random.choice(['highway construction', 'metro rail', 'industrial corridor', 'airport expansion', 'power project']),
        'act': random.choice(['1894', '2013']),
        'survey_no': f"{random.randint(1,999)}/{random.randint(1,100)}",
        'area': f"{random.randint(1,50)}.{random.randint(10,99)}",
        'village': random.choice(['Village A', 'Village B', 'Town C']),
        'award_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'award_amount': random.randint(100000, 5000000),
        'acquisition_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'market_value': random.randint(500000, 20000000),
        'comparables': random.choice(['sale instances provided', 'registered sale deeds', 'market evidence']),
        'enhanced_amount': random.randint(1000000, 30000000),
        'notification_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'sia_findings': random.choice(['impact assessed', 'moderate impact', 'significant impact']),
        'consent_percentage': random.randint(70, 90),
        'package': random.choice(['R&R package provided', 'housing allotted', 'employment given']),
        'families': random.randint(50, 500),
        'objections': random.choice(['public purpose challenged', 'compensation inadequate', 'procedure violated']),
        'award': random.randint(500000, 10000000),
        'determination_method': random.choice(['comparable sales', 'capitalization method', 'expert valuation']),
        'multiplier': random.randint(1, 3),
        'purpose': random.choice(['highway', 'railway', 'public utility']),
        'alternative': random.choice(['available', 'not explored', 'rejected']),
        'holding': random.choice(['urgency justified', 'not justified', 'procedure followed']),
        'outcome': random.choice(['upheld', 'quashed', 'modified']),
        'plaintiff': pet,  # Added for land acquisition scenarios
        'defendant': res,  # Added for land acquisition scenarios
        'amount': random.randint(100000, 50000000)  # Added for land acquisition scenarios
    }
    
    description = scenario.format(**data)
    return description, 'land_acquisition'

def generate_election_description(pet, res, case_no):
    """Generate Election case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(election_scenarios)
    
    data = {
        'constituency': random.choice(['Constituency A', 'Constituency B', 'Parliamentary Seat']),
        'election_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2024)}",
        'returned_candidate': res,
        'petitioner': pet,
        'corrupt_section': random.choice(['123', '123(4)', '123(7)', '123A']),
        'corrupt_practice': random.choice(['bribery', 'undue influence', 'appeal to religion', 'hiring vehicles']),
        'excess_expenditure': random.randint(1000000, 10000000),
        'evidence': random.choice(['cash distribution', 'video evidence', 'witness testimony', 'documents']),
        'finding': random.choice(['corrupt practice proved', 'not established', 'benefit of doubt']),
        'member': res,
        'party': random.choice(['Party A', 'Party B']),
        'new_party': random.choice(['Party X', 'Party Y', 'Opposition']),
        'defection_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'merger': random.choice(['applicable', 'not applicable']),
        'order_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'decision': random.choice(['disqualified', 'not disqualified']),
        'holding': random.choice(['disqualification upheld', 'set aside', 'remanded']),
        'nomination_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2024)}",
        'rejection_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2024)}",
        'rejection_grounds': random.choice(['affidavit defects', 'non-disclosure', 'false information']),
        'defects': random.choice(['criminal cases not disclosed', 'assets incorrect', 'form not complete']),
        'disclosure_status': random.choice(['not disclosed', 'incorrectly disclosed', 'suppressed']),
        'asset_issue': random.choice(['undervalued', 'not mentioned', 'benami assets']),
        'plaintiff': pet,  # Added for election scenarios
        'defendant': res,  # Added for election scenarios
        'amount': random.randint(100000, 10000000)  # Added for election scenarios
    }
    
    description = scenario.format(**data)
    return description, 'election'

def generate_ibc_description(pet, res, case_no):
    """Generate Insolvency & Bankruptcy case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(ibc_scenarios)
    
    data = {
        'section': random.choice(['7', '9', '10']),
        'corporate_debtor': res if 'ltd' in res.lower() else 'Corporate Debtor Ltd.',
        'creditor': pet,
        'default_amount': random.randint(10000000, 1000000000),
        'admission_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'rp': random.choice(['Mr. Rajesh Kumar', 'Ms. Priya Sharma', 'Mr. Anil Verma']),
        'cirp_days': random.randint(180, 330),
        'claims_count': random.randint(10, 100),
        'claims_amount': random.randint(50000000, 5000000000),
        'coc_meetings': random.randint(3, 10),
        'resolution_applicant': random.choice(['ABC Consortium', 'XYZ Ltd.', 'Strategic Investor']),
        'plan_amount': random.randint(30000000, 500000000),
        'voting_percentage': random.randint(66, 100),
        'liquidation_value': random.randint(20000000, 300000000),
        'outcome': random.choice(['Resolution Plan Approved', 'Liquidation Ordered']),
        'period': f"{random.randint(2018,2022)} to {random.randint(2023,2024)}",
        'diverted_amount': random.randint(10000000, 500000000),
        'related_parties': random.choice(['director-controlled entities', 'related parties', 'shell companies']),
        'count': random.randint(5, 20),
        'directors': random.choice(['Mr. X, Mr. Y', 'Board of Directors']),
        'intent_evidence': random.choice(['fund diversion', 'asset stripping', 'siphoning']),
        'recovery': random.randint(5000000, 200000000),
        'debtor': res,
        'liquidator': random.choice(['Mr. A. Mehta', 'Ms. S. Verma']),
        'assets': random.randint(50000000, 1000000000),
        'liabilities': random.randint(100000000, 2000000000),
        'secured': random.randint(50000000, 800000000),
        'operational': random.randint(10000000, 300000000),
        'workmen': random.randint(5000000, 50000000),
        'distribution': random.choice(['as per waterfall', 'secured creditors paid', 'partial recovery']),
        'creditor_type': random.choice(['Financial Creditor', 'Operational Creditor']),
        'default': random.randint(1000000, 500000000),
        'demand_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'holding': random.choice(['admitted', 'dismissed', 'pre-existing dispute']),
        'plaintiff': pet,  # Added for IBC scenarios
        'defendant': res,  # Added for IBC scenarios
        'amount': random.randint(1000000, 500000000)  # Added for IBC scenarios
    }
    
    description = scenario.format(**data)
    return description, 'ibc'

def generate_arbitration_description(pet, res, case_no):
    """Generate Arbitration case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(arbitration_scenarios)
    
    data = {
        'award_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'party1': pet,
        'party2': res,
        'arbitrator': random.choice(['Justice (Retd.) A.K. Sharma', 'Mr. R.K. Verma', 'Ms. S. Mehta']),
        'claim': random.randint(10000000, 500000000),
        'award_amount': random.randint(5000000, 300000000),
        'grounds': random.choice(['patent illegality', 'violation of public policy', 'bias', 'procedure not followed']),
        'limitation_status': random.choice(['within time', 'delayed', 'condonable delay']),
        'outcome': random.choice(['upheld', 'set aside', 'remanded', 'modified']),
        'country1': random.choice(['India', 'Singapore', 'UK', 'USA']),
        'country2': random.choice(['India', 'Singapore', 'UK', 'UAE']),
        'seat': random.choice(['Singapore', 'London', 'Paris', 'New Delhi']),
        'venue': random.choice(['Singapore', 'London', 'Paris', 'Mumbai']),
        'dispute_nature': random.choice(['construction contract', 'supply agreement', 'JV dispute', 'shareholder dispute']),
        'governing_law': random.choice(['Indian law', 'English law', 'Singapore law', 'Swiss law']),
        'award_usd': random.randint(100000, 10000000),
        'recognition': random.choice(['granted', 'refused', 'conditions imposed']),
        'agreement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'dispute': random.choice(['payment dispute', 'breach of contract', 'quality issue', 'termination']),
        'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'appointed_arbitrator': random.choice(['Justice X', 'Mr. Y', 'Ms. Z']),
        'interim_relief': random.choice(['injunction', 'attachment', 'status quo', 'security']),
        'emergency_arbitrator': random.choice(['Mr. A', 'Ms. B']),
        'days': random.randint(7, 15),
        'plaintiff': pet,  # Added for arbitration scenarios
        'defendant': res,  # Added for arbitration scenarios
        'amount': random.randint(100000, 100000000),  # Added for arbitration scenarios
        'holding': random.choice(['award upheld', 'set aside', 'remanded'])  # Added for arbitration scenarios
    }
    
    description = scenario.format(**data)
    return description, 'arbitration'

# =============================================================================
# CATEGORY DETERMINATION & MAIN PROCESSING
# =============================================================================

def determine_case_category(petitioner, respondent):
    """Determine case category based on party analysis - Enhanced with 17 categories"""
    pet_type = analyze_party_type(petitioner)
    res_type = analyze_party_type(respondent)
    
    # Labour & Employment cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['labour', 'worker', 'union', 'workmen', 'employee']):
        return 'labour'
    
    # Intellectual Property cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['trademark', 'patent', 'copyright', 'design', 'ip']):
        return 'ip'
    
    # Banking & Finance cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['bank', 'drt', 'sarfaesi', 'loan', 'debt recovery']):
        if 'accident' not in petitioner.lower() and 'accident' not in respondent.lower():
            return 'banking'
    
    # Motor Accident Claims
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['motor accident', 'mact', 'accident claim', 'claimant']):
        return 'mac'
    
    # Land Acquisition cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['land acquisition', 'lac', 'compensation', 'acquisition']):
        return 'land_acquisition'
    
    # Election cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['election', 'candidate', 'returning officer', 'election commission']):
        return 'election'
    
    # Insolvency & Bankruptcy cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['insolvency', 'nclt', 'nclat', 'ibc', 'resolution professional', 'liquidator']):
        return 'ibc'
    
    # Arbitration cases
    if any(word in petitioner.lower() or word in respondent.lower() for word in ['arbitration', 'arbitral', 'arbitrator']):
        return 'arbitration'
    
    # Criminal cases
    if 'state' in pet_type or 'state' in res_type:
        if any(word in petitioner.lower() or word in respondent.lower() for word in ['commissioner', 'central', 'income tax', 'gst', 'customs']):
            return 'tax'
        return random.choice(['criminal'] * 7 + ['constitutional'])  # More criminal cases
    
    # Government service matters
    if 'government' in pet_type and 'individual' in res_type:
        return 'service'
    if 'individual' in pet_type and 'government' in res_type:
        return 'service'
    
    # Family matters
    if 'individual' in pet_type and 'individual' in res_type:
        # Family keywords
        if any(word in petitioner.lower() or word in respondent.lower() for word in ['wife', 'husband', 'matrimonial']):
            return 'family'
        # Consumer keywords
        if any(word in respondent.lower() for word in ['hospital', 'telecom', 'builders', 'insurance company']):
            return 'consumer'
        # Random mix for individual vs individual - include new categories
        return random.choice(['criminal'] * 3 + ['family'] * 2 + ['civil'] * 2 + ['property'] + ['labour'] + ['mac'])
    
    # Commercial/Corporate
    if 'company' in pet_type or 'company' in res_type:
        if any(word in petitioner.lower() or word in respondent.lower() for word in ['securities', 'sebi']):
            return 'commercial'
        # Include banking, ibc, arbitration for corporate entities
        return random.choice(['commercial'] * 3 + ['tax'] + ['civil'] + ['banking'] + ['ibc'] + ['arbitration'])
    
    # Default distribution - include all categories
    return random.choice(['civil'] * 3 + ['property'] * 2 + ['criminal'] * 2 + ['family'] + ['commercial'] + ['labour'])

# =============================================================================
# REMAINING GENERATORS - Commercial, Tax, Service, Constitutional, Consumer
# =============================================================================

def generate_commercial_description(pet, res, case_no):
    """Generate commercial case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(commercial_scenarios)
    data = {
        'company_name': pet if any(x in pet.lower() for x in ['ltd', 'pvt', 'company']) else 'Company',
        'incorporation_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2000,2020)}",
        'directors': 'directors of company',
        'issue_description': random.choice(['oppression of minority', 'mismanagement', 'fraud', 'deadlock']),
        'relief_sought': random.choice(['removal of directors', 'winding up', 'investigation', 'interim relief']),
        'stakeholders': random.choice(['minority shareholders', 'creditors', 'debenture holders']),
        'allegations': random.choice(['siphoning of funds', 'self-dealing', 'breach of trust', 'ultra vires acts']),
        'company_status': random.choice(['unable to pay debts', 'affairs prejudicial', 'deadlocked']),
        'financial_position': f"liabilities Rs. {random.randint(10,500)} crores",
        'examination': random.choice(['company records', 'financial statements', 'allegations']),
        'findings': random.choice(['oppression established', 'no mismanagement', 'grounds made out']),
        'order_passed': random.choice(['directors removed', 'winding up ordered', 'status quo maintained']),
        'dispute_subject': random.choice(['construction contract', 'supply agreement', 'service contract', 'partnership']),
        'agreement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'dispute_details': random.choice(['payment', 'quality', 'delays', 'breach of terms']),
        'arbitrator_name': 'Justice (Retd.) X',
        'award_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'award_amount': random.randint(1000000, 500000000),
        'award_favor': random.choice(['claimant', 'respondent', 'partly to both']),
        'challenging_party': random.choice(['respondent', 'claimant']),
        'challenge_grounds': random.choice(['patent illegality', 'violation of natural justice', 'beyond scope']),
        'award_status': random.choice(['valid and enforceable', 'set aside', 'remanded']),
        'reasoning': random.choice(['no ground to interfere', 'jurisdictional error', 'procedure violated']),
        'ip_type': random.choice(['trademark', 'copyright', 'patent', 'design']),
        'ip_details': random.choice(['trademark "X"', 'copyrighted work', 'patented invention']),
        'registration_no': f"TM/{random.randint(100000,999999)}",
        'infringement_act': random.choice(['using identical mark', 'copying work', 'manufacturing patented product']),
        'infringement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'ip_name': random.choice(['mark', 'work', 'invention']),
        'reputation_details': random.choice(['goodwill and reputation', 'well-known mark', 'established brand']),
        'damage_type': random.choice(['confusion', 'dilution', 'loss of sales', 'reputation harm']),
        'reliefs': random.choice(['injunction and damages', 'account of profits', 'delivery up']),
        'defense': random.choice(['no infringement', 'prior user', 'generic term', 'honest concurrent use']),
        'damages': random.randint(1000000, 100000000),
        'bank_name': random.choice(['State Bank', 'HDFC Bank', 'ICICI Bank', 'Bank of India']),
        'borrower': res if any(x in res.lower() for x in ['pvt', 'ltd']) else pet,
        'loan_amount': random.randint(5000000, 1000000000),
        'loan_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2020)}",
        'purpose': random.choice(['business expansion', 'working capital', 'project', 'term loan']),
        'security_details': random.choice(['mortgage of property', 'hypothecation of assets', 'personal guarantee', 'pledge of shares']),
        'default_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'outstanding': random.randint(10000000, 1500000000),
        'notice_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'objection': random.choice(['notice defective', 'no default', 'OTS pending', 'moratorium']),
        'relief': random.choice(['recovery of dues', 'possession of secured assets', 'sale of secured assets']),
        'order_details': random.choice(['decree for recovery', 'symbolic possession', 'sale authorized']),
        'firm_name': pet if 'firm' in pet.lower() else 'Partnership Firm',
        'formation_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2000,2018)}",
        'partners': 'partners',
        'business': random.choice(['trading', 'manufacturing', 'services', 'exports']),
        'disputes': random.choice(['accounts', 'profit sharing', 'management', 'admission of partner']),
        'terms': random.choice(['equal sharing', 'specific ratios', 'defined roles']),
        'assets': random.randint(5000000, 500000000),
        'liabilities': random.randint(1000000, 100000000),
        'dissolution_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'distribution': random.choice(['as per partnership deed', 'equally', 'after settling liabilities']),
        'accounts': 'finalized',
        'insurance_company': random.choice(['LIC', 'HDFC Life', 'ICICI Prudential', 'General Insurance Co.']),
        'policy_no': f"POL/{random.randint(100000,999999)}",
        'event': random.choice(['death', 'accident', 'fire', 'hospitalization', 'vehicle damage']),
        'event_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'claim_amount': random.randint(500000, 50000000),
        'repudiation_grounds': random.choice(['non-disclosure', 'exclusion clause', 'breach of warranty', 'pre-existing disease']),
        'policyholder_case': random.choice(['full disclosure made', 'exclusion not applicable', 'warranty complied']),
        'policy_terms': random.choice(['coverage clear', 'no exclusion', 'terms satisfied']),
        'investigation': random.choice(['found material non-disclosure', 'no basis for repudiation', 'claim genuine']),
        'payment_amount': random.randint(1000000, 60000000),
        'rate': random.randint(9, 15),
        'from_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'cheque_no': random.randint(100000, 999999),
        'cheque_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'amount': random.randint(50000, 10000000),
        'liability': random.choice(['loan repayment', 'business dues', 'purchase consideration', 'debt']),
        'dishonor_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2023,2024)}",
        'dishonor_reason': random.choice(['insufficient funds', 'account closed', 'payment stopped', 'exceeds arrangement']),
        'proof': random.choice(['cheque and return memo', 'legal notice and acknowledgment', 'liability documents']),
        'fine': random.randint(100000, 10000000),
        'compensation': random.randint(100000, 20000000),
        'franchisor': pet if 'company' in pet.lower() else 'Franchisor Company',
        'franchisee': res if 'pvt' in res.lower() else 'Franchisee',
        'date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2022)}",
        'territory': random.choice(['Bangalore city', 'Delhi NCR', 'Mumbai', 'Chennai', 'specified territory']),
        'term': random.choice(['5', '7', '10']),
        'fee': random.randint(500000, 50000000),
        'dispute': random.choice(['royalty payments', 'quality standards', 'territory violation', 'termination']),
        'franchisee_allegation': random.choice(['inadequate support', 'quality supplies not provided', 'wrongful termination']),
        'franchisor_allegation': random.choice(['royalty default', 'breach of standards', 'unauthorized expansion']),
        'party': random.choice(['franchisee', 'franchisor', 'both parties']),
        'opposite_party': random.choice(['seller', 'service provider', 'manufacturer', 'dealer']),
        'product_or_service': random.choice(['car', 'appliance', 'services', 'product']),
        'price': random.randint(100000, 5000000),
        'defect_details': random.choice(['manufacturing defect', 'deficiency in service', 'not as per specification']),
        'complaint_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2021,2024)}",
        'op_response': random.choice(['denied liability', 'inadequate response', 'no response']),
        'loss': random.randint(50000, 5000000),
        'expert_opinion': random.choice(['defect confirmed', 'deficiency established', 'complainant case proved']),
        'order': random.choice(['replacement', 'refund', 'compensation']),
        'refund_amount': random.randint(100000, 6000000),
        'plaintiff': pet,  # Added for commercial scenarios
        'defendant': res  # Added for commercial scenarios
    }
    description = scenario['template'].format(**data)
    return description, 'commercial'

def generate_tax_description(pet, res, case_no):
    """Generate tax case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(tax_scenarios)
    ay = f"{random.randint(2015,2023)}-{random.randint(16,24)}"
    data = {
        'ay': ay,
        'assessee_type': random.choice(['company', 'individual', 'partnership firm', 'HUF']),
        'business': random.choice(['manufacturing', 'trading', 'professional services', 'real estate', 'IT services']),
        'addition_amount': random.randint(1000000, 500000000),
        'addition_reason': random.choice(['unexplained cash credits', 'disallowance of expenses', 'transfer pricing', 'undisclosed income']),
        'explanation': random.choice(['documentary evidence provided', 'business necessity explained', 'arm length price']),
        'ao_holding': random.choice(['explanation not satisfactory', 'addition justified', 'revenue leakage']),
        'cita_decision': random.choice(['upheld addition', 'deleted addition', 'reduced addition']),
        'legal_issue': random.choice(['allowability of expenses', 'taxability of income', 'transfer pricing methodology']),
        'case_law': random.choice(['CIT v. XYZ (2015)', 'ABC v. ACIT (2018)', 'Supreme Court precedent']),
        'tribunal_holding': random.choice(['in favor of assessee', 'confirmed addition', 'partly in favor']),
        'addition_status': random.choice(['deleted', 'confirmed', 'reduced']),
        'appeal_result': random.choice(['allowed', 'dismissed', 'partly allowed']),
        'period': f"{random.randint(2018,2021)} to {random.randint(2022,2024)}",
        'assessee': pet,
        'demand_amount': random.randint(5000000, 1000000000),
        'tax': random.randint(2000000, 500000000),
        'interest': random.randint(500000, 100000000),
        'penalty': random.randint(1000000, 300000000),
        'issue_description': random.choice(['ITC availability', 'classification', 'valuation', 'place of supply']),
        'assessee_case': random.choice(['entitled to ITC', 'correct classification', 'proper valuation']),
        'dept_case': random.choice(['ITC not admissible', 'wrong classification', 'undervaluation']),
        'itc_status': random.choice(['allowed', 'denied', 'partially allowed']),
        'invoice_status': random.choice(['proper', 'defective', 'compliant']),
        'examination': random.choice(['invoices and accounts', 'legal provisions', 'precedents']),
        'holding': random.choice(['in favor of assessee', 'upholding department', 'partial relief']),
        'demand_status': random.choice(['set aside', 'confirmed', 'reduced']),
        'goods': random.choice(['machinery', 'electronics', 'raw materials', 'finished goods']),
        'be_no': f"BE/{random.randint(100000,999999)}",
        'classification_dispute': random.choice(['CTH applicable', 'rate of duty', 'exemption eligibility']),
        'assessee_cth': random.randint(1000, 9999),
        'dept_cth': random.randint(1000, 9999),
        'duty_diff': random.randint(500000, 50000000),
        'technical_opinion': random.choice(['supports assessee', 'supports department', 'inconclusive']),
        'precedents': random.choice(['similar classification upheld', 'case law supports assessee']),
        'correct_cth': random.randint(1000, 9999),
        'final_duty': random.randint(1000000, 60000000),
        'result': random.choice(['allowed', 'dismissed', 'remanded']),
        'transaction_type': random.choice(['provision of services', 'royalty payments', 'management fees', 'purchase of goods']),
        'alp': random.randint(10000000, 1000000000),
        'assessee_price': random.randint(5000000, 800000000),
        'adjustment': random.randint(1000000, 500000000),
        'method': random.choice(['TNMM', 'CUP', 'Resale Price Method', 'Cost Plus']),
        'comparables': random.choice(['Company A, B, C', 'selected comparables', 'industry players']),
        'objections': random.choice(['comparables functionally different', 'working capital adjustment', 'risk profile different']),
        'drp_directions': random.choice(['upheld TPO order', 'directed fresh selection', 'reduced adjustment']),
        'adjustment_status': random.choice(['deleted', 'reduced', 'confirmed']),
        'section': random.choice(['271(1)(c)', '271B', '270A', '271AAA']),
        'addition': random.randint(5000000, 500000000),
        'penalty_grounds': random.choice(['concealment of income', 'furnishing inaccurate particulars', 'under-reporting']),
        'defense': random.choice(['bonafide belief', 'no concealment', 'disclosure made', 'legal interpretation']),
        'explanation': random.choice(['explained basis of return', 'relied on advice', 'difference of opinion']),
        'finding': random.choice(['established', 'not proved', 'explained satisfactorily']),
        'bonafide': random.choice(['found', 'not found', 'explained']),
        'penalty_result': random.choice(['deleted', 'confirmed', 'reduced']),
        'plaintiff': pet,  # Added for tax scenarios
        'defendant': res,  # Added for tax scenarios
        'amount': random.randint(100000, 100000000)  # Added for tax scenarios
    }
    description = scenario['template'].format(**data)
    return description, 'tax'

def generate_service_description(pet, res, case_no):
    """Generate government service matter descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(service_scenarios)
    data = {
        'petitioner': pet,
        'designation': random.choice(['Clerk', 'Assistant', 'Officer', 'Inspector', 'Teacher', 'Engineer']),
        'order_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'grounds': random.choice(['misconduct', 'inefficiency', 'corruption', 'absence without leave', 'insubordination']),
        'joining_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(1990,2015)}",
        'inquiry_status': random.choice(['held', 'not held', 'vitiated by procedural lapses']),
        'defense': random.choice(['charges false', 'no evidence', 'procedural violations', 'discrimination']),
        'charges': random.choice(['financial irregularities', 'negligence', 'corruption', 'misconduct']),
        'findings': random.choice(['charges proved', 'not proved', 'some charges proved']),
        'violation': random.choice(['natural justice', 'fair hearing', 'bias of inquiry officer', 'no opportunity']),
        'examination': random.choice(['inquiry proceedings', 'principles of natural justice', 'evidence']),
        'court_finding': random.choice(['violation of natural justice', 'inquiry fair', 'order arbitrary']),
        'order_status': random.choice(['set aside', 'upheld', 'modified']),
        'reinstatement_status': random.choice(['reinstated with back wages', 'reinstated without back wages', 'not reinstated']),
        'relief_details': random.choice(['50% back wages', 'all consequential benefits', 'costs awarded']),
        'date1': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2000,2015)}",
        'date2': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2020)}",
        'post': random.choice(['Deputy Manager', 'Section Officer', 'Superintendent', 'Senior Engineer']),
        'list_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'list_action': random.choice(['placed respondent senior', 'placed petitioner junior', 'revised']),
        'challenge_grounds': random.choice(['wrong fixation of seniority', 'inter se seniority', 'eligibility ignored']),
        'criteria': random.choice(['length of service', 'confirmation date', 'qualifications', 'recruitment rules']),
        'petitioner_case': random.choice(['senior by service', 'eligible for promotion', 'wrongly superseded']),
        'dept_case': random.choice(['respondent senior', 'based on merit', 'as per rules']),
        'seniority_result': random.choice(['refixed in favor of petitioner', 'list upheld', 'directed fresh consideration']),
        'promotion_result': random.choice(['ordered', 'withheld', 'from due date']),
        'retirement_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2018,2023)}",
        'service_years': random.randint(20, 40),
        'sanctioned_pension': random.randint(10000, 50000),
        'claimed_pension': random.randint(15000, 80000),
        'pension_issue': random.choice(['calculation', 'qualifying service', 'pay fixation', 'benefits inclusion']),
        'rules': random.choice(['Pension Rules', 'CCS Pension Rules', 'State Pension Rules']),
        'qualifying_service': f"{random.randint(20,40)} years",
        'objection': random.choice(['break in service', 'unauthorized absence', 'different interpretation']),
        'law_applied': random.choice(['beneficial construction', 'pension rules', 'precedents']),
        'final_pension': random.randint(20000, 90000),
        'arrears_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'employee': pet,
        'cs_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2020,2024)}",
        'io': 'Inquiry Officer',
        'inquiry_findings': random.choice(['charges proved', 'not proved', 'partially proved']),
        'penalty': random.choice(['dismissal', 'removal', 'compulsory retirement', 'reduction in rank', 'stoppage of increments']),
        'nj_violation': random.choice(['found', 'not found', 'substantial violation']),
        'penalty_status': random.choice(['set aside', 'modified', 'confirmed']),
        'employee_status': random.choice(['reinstated', 'retired on normal date', 'penalty reduced']),
        'benefit': random.choice(['ACP', 'pay scale revision', 'MACP', 'allowances']),
        'order_details': random.choice(['notification', 'office order', 'government order', 'circular']),
        'dept_action': random.choice(['denied benefit', 'granted partially', 'sought clarification']),
        'entitlement_basis': random.choice(['length of service', 'court orders', 'pay commission', 'rules']),
        'interpretation': random.choice(['in favor of employee', 'restrictive interpretation rejected', 'plain reading']),
        'benefit_status': random.choice(['granted', 'denied', 'granted from specific date']),
        'applicant': pet,
        'relation': random.choice(['son', 'daughter', 'dependent']),
        'deceased': random.choice(['father', 'mother', 'parent']),
        'death_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2018,2024)}",
        'application_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2019,2024)}",
        'rejection_grounds': random.choice(['no vacancy', 'delay in application', 'not dependent', 'other eligible person']),
        'case_details': random.choice(['sole breadwinner', 'dependent family', 'financial hardship']),
        'dependent_status': random.choice(['fully dependent', 'no other source', 'sole dependent']),
        'policy': random.choice(['Compassionate Appointment Rules', 'Government guidelines', 'DOP&T instructions']),
        'vacancy_status': random.choice(['available', 'not available', 'being created']),
        'appointment_status': random.choice(['directed', 'refused', 'on availability of vacancy']),
        'holding': random.choice(['in favor of petitioner', 'dismissed', 'allowed with directions', 'set aside']),  # Added for service scenarios
        'amount': random.randint(100000, 5000000)  # Added for pay fixation scenarios
    }
    description = scenario['template'].format(**data)
    return description, 'service'

def generate_constitutional_description(pet, res, case_no):
    """Generate constitutional case descriptions WITH state extraction"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    scenario = random.choice(constitutional_scenarios)
    data = {
        'pil_issue': random.choice(['environmental pollution', 'right to education', 'police excess', 'public health', 'corruption']),
        'petitioner_type': random.choice(['NGO', 'social activist', 'advocate', 'concerned citizen']),
        'issue_description': random.choice(['violation of fundamental rights', 'environmental degradation', 'public welfare']),
        'affected_persons': random.choice(['large section of society', 'poor and marginalized', 'citizens', 'public at large']),
        'article': random.choice(['14', '19', '21', '32', '226']),
        'state_response': random.choice(['denied allegations', 'steps being taken', 'policy decision', 'lack of resources']),
        'ground_facts': random.choice(['serious violations', 'established facts', 'undisputed']),
        'expert_report': random.choice(['confirmed violations', 'suggested measures', 'highlighted issues']),
        'examination': random.choice(['facts and law', 'expert reports', 'ground realities']),
        'directions': random.choice(['implement measures within timeframe', 'constitute committee', 'take remedial action']),
        'compliance_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2024,2025)}",
        'detenu': random.choice(['detenu', 'person', 'individual']),
        'detention_circumstances': random.choice(['illegally detained', 'in custody', 'whereabouts unknown']),
        'detention_law': random.choice(['preventive detention law', 'UAPA', 'NSA', 'under executive order']),
        'detention_date': f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2022,2024)}",
        'detention_grounds': random.choice(['security threat', 'public order', 'law and order']),
        'authority': random.choice(['District Magistrate', 'State Government', 'Commissioner']),
        'representation_status': random.choice(['not decided', 'rejected', 'pending']),
        'safeguards_status': random.choice(['complied', 'violated', 'not followed']),
        'grounds_status': random.choice(['vague', 'specific and clear', 'not communicated']),
        'detention_validity': random.choice(['illegal', 'legal', 'procedurally defective']),
        'detenu_status': random.choice(['ordered to be released', 'detention upheld', 'fresh order directed']),
        'challenged_action': random.choice(['statute', 'government order', 'executive action', 'rule']),
        'petitioner_case': random.choice(['violates fundamental rights', 'arbitrary and unreasonable', 'discriminatory']),
        'state_justification': random.choice(['public interest', 'reasonable restrictions', 'policy decision', 'police powers']),
        'restriction_clause': random.choice(['Article 19(2)', 'Article 19(6)', 'reasonable restrictions']),
        'proportionality': random.choice(['disproportionate', 'proportionate', 'excessive']),
        'public_interest': random.choice(['outweighs individual rights', 'not established', 'balanced']),
        'precedents': random.choice(['Maneka Gandhi case', 'Shreya Singhal case', 'relevant precedents']),
        'balancing': random.choice(['individual rights and public interest', 'competing interests']),
        'action_status': random.choice(['struck down', 'upheld', 'read down']),
        'respondent': res,
        'relief_sought': random.choice(['perform statutory duty', 'grant license', 'take action', 'implement scheme']),
        'statutory_provision': random.choice(['Section X of Act', 'statutory rule', 'government scheme']),
        'legal_right': random.choice(['statutory entitlement', 'legitimate expectation', 'constitutional right']),
        'respondent_duty': random.choice(['mandatory duty', 'statutory obligation', 'public duty']),
        'refusal_grounds': random.choice(['no legal right', 'policy matter', 'discretionary']),
        'discretion_issue': random.choice(['pure discretion', 'no discretion', 'guided discretion']),
        'mandamus_status': random.choice(['issued', 'refused', 'conditional mandamus']),
        'direction': random.choice(['performance of duty within timeframe', 'reconsider application', 'comply with law']),
        'environmental_issue': random.choice(['illegal mining', 'deforestation', 'industrial pollution', 'waste disposal']),
        'location': random.choice(state_locations),  # USE STATE-SPECIFIC LOCATIONS
        'allegations': random.choice(['environmental violations', 'illegal activities', 'damage to ecology']),
        'impact': random.choice(['severe damage', 'irreversible harm', 'affecting health']),
        'expert_findings': random.choice(['violations confirmed', 'remedial measures suggested', 'damage assessed']),
        'clearance_status': random.choice(['not obtained', 'expired', 'conditions violated']),
        'principles_applied': random.choice(['polluter pays principle', 'precautionary principle', 'sustainable development']),
        'environmental_directions': random.choice(['stop activities', 'restore ecology', 'pay compensation', 'remedial measures']),
        'compensation_details': f"Rs. {random.randint(10,500)} crores to be paid",
        'holding': random.choice(['in favor of petitioner', 'dismissed', 'allowed with conditions', 'partly allowed']),  # Added for constitutional scenarios
        'plaintiff': pet,  # Added for constitutional scenarios
        'defendant': res,  # Added for constitutional scenarios
        'amount': random.randint(100000, 100000000)  # Added for constitutional scenarios
    }
    description = scenario['template'].format(**data)
    return description, 'constitutional'

def generate_consumer_description(pet, res, case_no):
    """Generate consumer case descriptions WITH state extraction - minimal as we already have from original"""
    state = extract_state_from_party(pet) or extract_state_from_party(res)
    state_locations = get_locations_for_state(state)
    return f"Consumer complaint by {pet} against {res} for deficiency in service/defective goods. Compensation and relief sought under Consumer Protection Act.", 'consumer'

print("ALL GENERATORS COMPLETED!")
print("Now adding main processing loop to generate 47,400 cases...")

# =============================================================================
# MAIN PROCESSING LOOP
# =============================================================================

def determine_case_category(pet, res, case_no):
    """Determine case category from party names and patterns"""
    pet_lower = pet.lower()
    res_lower = res.lower()
    combined = pet_lower + " " + res_lower
    
    # Check for criminal cases (State vs Individual, Commissioner vs X)
    if any(x in combined for x in ['state', 'commissioner of police', 'union of india', 'customs', 'enforcement directorate']):
        if any(x in combined for x in ['customs', 'excise', 'gst', 'income tax', 'sales tax']):
            return 'tax'
        return 'criminal'
    
    # Check for family cases
    if any(x in combined for x in ['wife', 'husband', 'matrimonial', 'divorce', 'custody', 'maintenance', 'domestic violence']):
        return 'family'
    
    # Check for service matters
    if any(x in combined for x in ['government', 'secretary', 'ministry', 'department', 'university', 'public sector']):
        if any(x in combined for x in ['employee', 'service', 'pension', 'promotion', 'termination']):
            return 'service'
    
    # Check for commercial/company matters
    if any(x in combined for x in ['ltd', 'pvt', 'limited', 'company', 'corporation', 'bank', 'insurance']):
        return 'commercial'
    
    # Check for constitutional matters
    if any(x in combined for x in ['union of india', 'state of', 'secretary', 'ministry']) and len(pet_lower) < 30:
        if any(x in combined for x in ['public interest', 'fundamental right', 'habeas corpus']):
            return 'constitutional'
    
    # Check for property matters
    if any(x in combined for x in ['property', 'land', 'estate', 'landlord', 'tenant', 'builder']):
        return 'property'
    
    # Default to civil
    return 'civil'

def process_all_cases():
    """Main function to process all 47,400 cases and populate database"""
    print("\n" + "="*80, flush=True)
    print("ULTIMATE CASE GENERATOR - Processing 47,400 Supreme Court Judgments", flush=True)
    print("="*80 + "\n", flush=True)
    
    # Load CSV data
    print("Loading judgments.csv...", flush=True)
    df = pd.read_csv('archive (2)/judgments.csv')
    print(f"[OK] Loaded {len(df)} cases from CSV\n", flush=True)
    
    # Load sentence transformer model for embeddings
    print("Loading sentence transformer model for embeddings...", flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("[OK] Model loaded successfully\n", flush=True)
    
    # Connect to database
    print("Connecting to database...", flush=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    print("[OK] Connected to PostgreSQL\n", flush=True)
    
    # Clear existing cases
    print("Clearing existing cases from database...", flush=True)
    cursor.execute("DELETE FROM cases")
    conn.commit()
    print("[OK] Database cleared\n", flush=True)
    
    # Process each case
    print("Starting case generation and database insertion...\n", flush=True)
    print("Progress: [Category distribution will be shown every 1000 cases]", flush=True)
    print("-" * 80, flush=True)
    
    category_counts = {}
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Extract data from CSV
            case_no = str(row.get('case_no', f'CASE-{idx+1}'))
            pet = str(row.get('pet', 'Petitioner'))
            res = str(row.get('res', 'Respondent'))
            judgment_date_raw = row.get('judgment_dates', '')
            bench = str(row.get('bench', '')).strip()
            
            # Clean and format judgment date
            if pd.notna(judgment_date_raw) and judgment_date_raw != '':
                judgment_date = str(judgment_date_raw)
            else:
                judgment_date = f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(2015,2024)}"
            
            # Clean party names
            pet = pet.strip() if pet and pet != 'nan' else 'Petitioner'
            res = res.strip() if res and res != 'nan' else 'Respondent'
            bench = bench if bench and bench != 'nan' and bench != '' else 'Hon\'ble Supreme Court'
            
            # Determine category
            category = determine_case_category(pet, res, case_no)
            
            # Generate description based on category
            if category == 'criminal':
                description, category = generate_criminal_description(pet, res, case_no)
            elif category == 'family':
                description, category = generate_family_description(pet, res, case_no)
            elif category == 'civil':
                description, category = generate_civil_description(pet, res, case_no)
            elif category == 'property':
                description, category = generate_property_description(pet, res, case_no)
            elif category == 'commercial':
                description, category = generate_commercial_description(pet, res, case_no)
            elif category == 'tax':
                description, category = generate_tax_description(pet, res, case_no)
            elif category == 'service':
                description, category = generate_service_description(pet, res, case_no)
            elif category == 'constitutional':
                description, category = generate_constitutional_description(pet, res, case_no)
            else:  # consumer or default
                description, category = generate_consumer_description(pet, res, case_no)
            
            # Create title
            title = f"{pet} vs {res}"
            
            # Create parties string
            parties = f"Petitioner: {pet}, Respondent: {res}"
            
            # Generate embedding
            embedding = model.encode(description)
            embedding_list = embedding.tolist()
            
            # Insert into database
            cursor.execute("""
                INSERT INTO cases (case_number, title, parties, description, category, judgment_date, bench, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (case_no, title, parties, description, category, judgment_date, bench, embedding_list))
            
            # Track category counts
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Commit and print progress every 1000 cases
            if (idx + 1) % 1000 == 0:
                conn.commit()
                print(f"\n[OK] Processed {idx + 1} cases", flush=True)
                print(f"  Category distribution so far:", flush=True)
                for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / (idx + 1)) * 100
                    print(f"    {cat.capitalize()}: {count} ({percentage:.1f}%)", flush=True)
                print("-" * 80, flush=True)
        
        except Exception as e:
            error_msg = f"Error processing case {idx + 1} ({case_no}): {str(e)}"
            errors.append(error_msg)
            if len(errors) <= 10:  # Only print first 10 errors
                print(f"WARNING: {error_msg}")
            continue
    
    # Final commit
    conn.commit()
    
    # Print final statistics
    print("\n" + "="*80)
    print("GENERATION COMPLETE!")
    print("="*80)
    print(f"\nTotal cases processed: {len(df)}")
    print(f"Successful insertions: {len(df) - len(errors)}")
    if errors:
        print(f"Errors encountered: {len(errors)}")
    
    print(f"\nFINAL CATEGORY DISTRIBUTION:")
    print("-" * 80)
    total = sum(category_counts.values())
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"{cat.capitalize():15} : {count:5} ({percentage:5.1f}%) {bar}")
    
    print("\n" + "="*80)
    print("Database populated with truly varied case descriptions!")
    print("Each murder case now has unique method: poisoning, stabbing, shooting, etc.")
    print("Each theft case has unique type: burglary, vehicle theft, pickpocketing, etc.")
    print("Each family case has unique grounds: cruelty, desertion, adultery, etc.")
    print("="*80 + "\n")
    
    cursor.close()
    conn.close()

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys
    print("\n[START] Starting Ultimate Case Generator...", flush=True)
    print("This will generate truly varied descriptions for 47,400 cases", flush=True)
    print("Estimated time: 10-15 minutes\n", flush=True)
    
    # Force unbuffered output
    sys.stdout.reconfigure(line_buffering=True)
    
    try:
        process_all_cases()
        print("\n[SUCCESS] Database ready with massively varied case descriptions", flush=True)
        print("You can now:", flush=True)
        print("1. Start the API: python api.py", flush=True)
        print("2. Test search: Search 'murder' will show poisoning, stabbing, shooting, etc.")
        print("3. Browse cases: Each case type will have completely different narratives")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("Check the error message above and try again")

