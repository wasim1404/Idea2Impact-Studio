import streamlit as st
import spacy
import re
import io
import PyPDF2
import requests
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import google.generativeai as genai
import json
import sqlite3
from datetime import datetime, timedelta
import time
from google.api_core.exceptions import ResourceExhausted
from fpdf import FPDF
import os

# --- Global Variables & Constants ---
DATABASE_FILE = 'proposals.db'
# IMPORTANT: Replace with your actual Google AI API Key. DO NOT share this key publicly.
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
SELECTED_MODEL = "models/learnlm-2.0-flash-experimental"

# --- Initialize Google Generative AI ---
if GOOGLE_AI_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_AI_API_KEY)
    except Exception as e:
        st.error(f'Error configuring Google AI: {e}')

# --- Common Helper Functions ---
def generate_content_with_retry(model_name, prompt, max_retries=10, initial_delay=5):
    model = genai.GenerativeModel(model_name)
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response
        except ResourceExhausted:
            wait_time = initial_delay * (2 ** i)
            st.warning(f"Rate limit exceeded. Retrying in {int(wait_time)} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            st.error(f"An unexpected error occurred during AI generation: {type(e).__name__}: {e}")
            return None
    st.error(f"Failed to generate content after {max_retries} retries due to rate limits.")
    return None

@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load('en_core_web_md')
    except OSError:
        st.error("SpaCy model 'en_core_web_md' not found. Please install it using: python -m spacy download en_core_web_md")
        st.stop()

nlp = load_spacy_model()

def clean_text(text):
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00a0': ' ', '\u2022': '-', '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2015': '-', '\u00b7': '-', '\u2212': '-', '\u00e9': 'e', '\u00e1': 'a', '\u00f1': 'n', '\u00fc': 'u', '\u00e7': 'c', '\u00f6': 'o', '\u00e4': 'a', '\u00df': 'ss', '\u00e0': 'a', '\u00e8': 'e', '\u00f4': 'o', '\u00fb': 'u', '\u00ee': 'i', '\u00e2': 'a', '\u00ea': 'e', '\u00f9': 'u', '\u00e5': 'a', '\u00f8': 'o', '\u00e3': 'a', '\u00e2': 'a', '\u00e7': 'c', '\u00e0': 'a', '\u00e8': 'e', '\u00e9': 'e', '\u00ea': 'e', '\u00eb': 'e', '\u00ef': 'i', '\u00f4': 'o', '\u00f6': 'o', '\u00f9': 'u', '\u00fc': 'u', '\u00fd': 'y', '\u00ff': 'y', '\u015f': 's', '\u015e': 'S', '\u011f': 'g', '\u011e': 'G', '\u0131': 'i', '\u0130': 'I', '\u0159': 'r', '\u0158': 'R', '\u0161': 's', '\u0160': 'S', '\u017e': 'z', '\u017d': 'Z', '\u010d': 'c', '\u010c': 'C', '\u0107': 'c', '\u0106': 'C', '\u0142': 'l', '\u0141': 'L', '\u015b': 's', '\u015a': 'S', '\u017a': 'z', '\u0179': 'Z', '\u017c': 'z', '\u017b': 'Z', '\u0105': 'a', '\u0104': 'A', '\u0119': 'e', '\u0118': 'E', '\u012f': 'i', '\u012e': 'I', '\u016b': 'u', '\u016a': 'U', '\u0173': 'u', '\u0172': 'U', '\u0101': 'a', '\u0100': 'A', '\u0113': 'e', '\u0112': 'E', '\u012b': 'i', '\u012a': 'I', '\u014d': 'o', '\u014c': 'O', '\u016b': 'u', '\u016a': 'U', '\u0103': 'a', '\u0102': 'A', '\u0115': 'e', '\u0114': 'E', '\u012d': 'i', '\u012c': 'I', '\u014f': 'o', '\u014e': 'O', '\u016d': 'u', '\u016c': 'U', '\u0109': 'c', '\u0108': 'C', '\u011d': 'g', '\u011c': 'G', '\u0125': 'h', '\u0124': 'H', '\u0135': 'j', '\u0134': 'J', '\u015d': 's', '\u015c': 'S', '\u0165': 't', '\u0164': 'T', '\u0171': 'u', '\u0170': 'U', '\u0175': 'w', '\u0174': 'W', '\u0177': 'y', '\u0176': 'Y'}
    for uni, ascii_char in replacements.items():
        text = text.replace(uni, ascii_char)
    return text.encode('latin-1', 'replace').decode('latin-1')

def clean_extracted_text(text):
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text) # Ensure consistent newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_section(text, headers):
    for header in headers:
        pattern = rf'{header}:?\s*(.*?)(\n\s*\n|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ''

def truncate(text, length=500):
    if len(text) > length:
        return text[:length] + '...'
    return text

def extract_keywords(text):
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        if len(chunk.text) > 2:
            keywords.add(chunk.text.lower().strip())
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'GPE', 'PERSON', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'NORP', 'FAC', 'LOC', 'DATE', 'TIME', 'MONEY', 'PERCENT']:
            keywords.add(ent.text.lower().strip())
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 2:
            keywords.add(token.lemma_.lower().strip())
    return list(keywords)

def extract_objectives(thrust_text):
    objectives = []
    bullets = re.split(r'\n\s*[-*•]\s*', thrust_text)
    if len(bullets) > 1:
        objectives = [b.strip() for b in bullets if b.strip()]
    else:
        doc = nlp(thrust_text)
        objectives = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    return objectives

def extract_paper_titles(text):
    lines = text.split('\n')
    papers = []
    for line in lines:
        line_clean = line.strip()
        if (
            15 < len(line_clean) < 200 and
            not line_clean.isupper() and
            not re.search(r'journal|conference|proceedings|materials|letters|transactions|series|volume|issue|press|doi|cited by|\d{4}', line_clean, re.IGNORECASE) and
            not re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,3}$', line_clean) and
            not re.match(r'^[A-Z]\. [A-Z][a-z]+\b', line_clean)
        ):
            words = line_clean.split()
            cap_words = [w for w in words if w.istitle()]
            if len(words) > 3 and len(cap_words) > 1:
                papers.append(line_clean)
    return list(dict.fromkeys(papers))

def extract_fields(text):
    doc = nlp(text)
    fields = {
        'Funding Agency': '',
        'Scheme Type': '',
        'Duration': '',
        'Budget': '',
        'Thrust Areas': '',
        'Eligibility': '',
        'Submission Format': ''
    }
    text = clean_extracted_text(text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    agency = ''
    for ent in doc.ents:
        if ent.label_ == 'ORG' and re.search(r'(foundation|council|agency|ministry|department|commission|authority|board|laborator(y|ies)|organisation|organization|institute|academy)', ent.text, re.IGNORECASE):
            agency = ent.text.strip()
            break
    if not agency and lines:
        for line in lines[:10]:
            if re.search(r'(foundation|council|agency|ministry|department|commission|authority|board|laborator(y|ies)|organisation|organization|institute|academy)', line, re.IGNORECASE):
                agency = line.strip()
                break
    fields['Funding Agency'] = agency[:120]
    scheme = ''
    for sent in nlp(text).sents:
        if re.search(r'(request for proposals|call for proposals|grant opportunity|funding program|fellowship program|research scheme)', sent.text, re.IGNORECASE) or \
           (re.search(r'(grant|scheme|program|fellowship|funding)', sent.text, re.IGNORECASE) and re.search(r'(open|available|new|launch|apply)', sent.text, re.IGNORECASE)):
            scheme = sent.text.strip().split('\n')[0][:120]
            break
    fields['Scheme Type'] = scheme
    duration = ''
    match = re.search(r'(maximum period of|duration of|project duration of|funding for up to|support for up to)\s*([\w\s\+]+?)(years?|months?|weeks?|days?)\b', text, re.IGNORECASE)
    if match:
        duration = match.group(0)
    else:
        match2 = re.search(r'for a maximum period of\s*([\w\s\+]+?)(years?|months?|weeks?|days?)\b', text, re.IGNORECASE)
        if match2:
            duration = match2.group(0)
        else:
            for ent in doc.ents:
                if ent.label_ == 'DATE':
                    duration = ent.text
                    break
    fields['Duration'] = duration
    budget_matches = re.findall(r'([₹$€£]|INR|USD|EUR|Rs\.?)[ ]?([\d,.]+)[ ]?(crore|lakhs?|million|thousand|hundred)?\b', text, re.IGNORECASE)
    budgets = []
    for match in budget_matches:
        currency, amount, unit = match
        budget_str = f"{currency.strip()} {amount.strip()} {unit.strip()}".strip()
        budgets.append(budget_str)
    match_budget_line = re.findall(r'Budget[^\n\r:]*[:\-]?\s*([\w\s₹$€£INRUSD,\.]+)', text, re.IGNORECASE)
    for b in match_budget_line:
        if b.strip() and b.strip() not in budgets:
            budgets.append(b.strip())
    if not budgets:
        for ent in doc.ents:
            if ent.label_ == 'MONEY':
                budgets.append(ent.text)
    fields['Budget'] = ", ".join(budgets)[:120]
    thrust_headers = ['Thrust Areas', 'Focus Areas', 'Priority Areas', 'Objectives and Scope', 'Program Verticals', 'Scope of the Program']
    thrust = extract_section(text, thrust_headers)
    if not thrust:
        match = re.search(r'(thrust areas?|focus areas?|priority areas?|objectives and scope|program verticals|scope of the program)[:\-]?\s*(.*)', text, re.IGNORECASE)
        if match:
            thrust = match.group(2)
    fields['Thrust Areas'] = truncate(thrust, 500)
    eligibility_headers = ['Eligibility', 'Eligibility Criteria', 'Who can apply', 'Applicants']
    eligibility = extract_section(text, eligibility_headers)
    if not eligibility:
        match = re.search(r'(eligibility|who can apply|applicants)[:\-]?\s*(.*)', text, re.IGNORECASE)
        if match:
            eligibility = match.group(2)
    fields['Eligibility'] = truncate(eligibility, 500)
    submission_headers = ['Submission Format', 'How to Apply', 'Submission Process', 'Application Process', 'How to Submit']
    submission = extract_section(text, submission_headers)
    if not submission:
        match = re.search(r'(submission format|how to apply|submission process|application process|how to submit)[:\-]?\s*(.*)', text, re.IGNORECASE)
        if match:
            submission = match.group(2)
    if not submission:
        submission = 'Not specified in the call.'
    fields['Submission Format'] = truncate(submission, 300)
    return fields

def extract_template_sections(text):
    lines = text.split('\n')
    sections = []
    for line in lines:
        line_clean = line.strip()
        if (len(line_clean) > 3 and (line_clean.isupper() or re.match(r'^[0-9A-Za-z][\).\-] ', line_clean))):
            sections.append(line_clean)
    return sections

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Full Proposal Draft', ln=True, align='C')
        self.ln(4)

# --- Database Initialization (Unified) ---
def init_dbs():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    # Proposals table (from Grant Proposal Generator)
    c.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            funding_agency TEXT,
            scheme_type TEXT,
            duration TEXT,
            budget TEXT,
            thrust_areas TEXT,
            eligibility TEXT,
            submission_format TEXT,
            user_research_background TEXT,
            template_sections TEXT,
            full_proposal_content TEXT
        )
    ''')
    # Generated opportunities table (from Grant Finder)
    c.execute('''
        CREATE TABLE IF NOT EXISTS generated_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            scheme_name TEXT,
            funding_agency TEXT,
            last_date_submission TEXT,
            description TEXT,
            is_processed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Call unified DB init
init_dbs()

def save_proposal_to_db(proposal_data):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO proposals (
            timestamp, funding_agency, scheme_type, duration, budget,
            thrust_areas, eligibility, submission_format, user_research_background,
            template_sections, full_proposal_content
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''',
    (
        proposal_data['timestamp'],
        proposal_data['funding_agency'],
        proposal_data['scheme_type'],
        proposal_data['duration'],
        proposal_data['budget'],
        proposal_data['thrust_areas'],
        proposal_data['eligibility'],
        proposal_data['submission_format'],
        proposal_data['user_research_background'],
        proposal_data['template_sections'],
        proposal_data['full_proposal_content']
    ))
    conn.commit()
    conn.close()

def save_generated_opportunity_to_db(opportunity_data):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO generated_opportunities (
                timestamp, scheme_name, funding_agency, last_date_submission, description
            )
            VALUES (?, ?, ?, ?, ?)
        ''',
        (
            datetime.now().isoformat(),
            opportunity_data['scheme_name'],
            opportunity_data['funding_agency'],
            opportunity_data['last_date_submission'],
            opportunity_data['description']
        ))
        conn.commit()
        st.success("DEBUG: Data committed to DB successfully!")
    except Exception as e:
        st.error(f"DEBUG: Error saving to DB: {e}")
    finally:
        conn.close()

@st.cache_resource
def load_taxonomy():
    try:
        with open("taxonomy.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("taxonomy.json not found. Please ensure it's in the project root.")
        return {}

taxonomy = load_taxonomy()

# --- Page Config ---
st.set_page_config(page_title="Idea2Impact Studio", layout="wide")

# --- Custom CSS for Cursor-style look ---
st.markdown("""
    <style>
    /* General Streamlit overrides for dark theme */
    .stApp {
        background-color: #1a1a1a;
        color: #f0f0f0; /* Changed for better readability */
    }
    .css-1d391kg, .stButton>button {
        background-color: #2b2b2b;
        color: #e0e0e0;
        border-radius: 4px;
        border: 1px solid #3c3c3c;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div>div,
    .stMultiSelect>div>div>div>div {
        background-color: #3c3c3c;
        color: #e0e0e0;
        border: 1px solid #555;
        border-radius: 4px;
    }
    .stCodeBlock {
        background-color: #2d2d2d;
        color: #cccccc;
        border-radius: 5px;
        padding: 1em;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f0f0f0;
    }
    .stMarkdown {
        font-family: 'Fira Code', monospace; /* Changed for Cursor-style aesthetic */
    }

    /* Custom sidebar navigation styling */
    .sidebar .sidebar-content {
        background-color: #1e1e1e;
        padding-top: 2rem;
    }
    .css-1lcbmhc, .css-zbnxdr {
        background-color: #1e1e1e;
    }
    .css-1oe5zfg {
        padding-top: 2rem;
    }
    .css-1ymn5ad {
        padding-bottom: 2rem;
    }
    .css-1v3fvcr {
        font-weight: bold;
        color: #f0f0f0;
    }
    .css-pkbujm {
        color: #e0e0e0; /* Sidebar link color */
        font-size: 1.1em;
    }
    .css-pkbujm:hover {
        color: #61afef; /* Hover color */
    }
    /* Sidebar item active state */
    .css-1y4fgqg.eqr7sfu4 {
        background-color: #2b2b2b;
        color: #61afef;
        border-left: 3px solid #61afef;
    }

    /* Card-like button styling for the main dashboard */
    .card-container {
        display: flex;
        flex-wrap: wrap; /* Allow cards to wrap */
        gap: 20px; /* Space between cards */
        justify-content: space-between; /* Distribute cards and fill space */
        padding: 20px 0;
    }
    .stCard { /* Streamlit's internal card class for the dashboard cards */
        background-color: #252526; /* Darker background for cards */
        border: 1px solid #333;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        min-height: 150px; /* Ensure cards have some height */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        cursor: pointer;
        flex-grow: 1; /* Allow cards to grow and fill available space */
        flex-basis: 48%; /* Roughly two cards per row with gap */
        max-width: 48%; /* Max width to ensure two per row */
    }
    .stCard:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
    }
    .card-title {
        color: #f0f0f0; /* Use brighter white for titles */
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .card-description {
        color: #a0a0a0; /* Slightly lighter grey for description */
        font-size: 0.9em;
        flex-grow: 1; /* Allow description to take up available space */
    }
    .card-button {
        background-color: #007acc; /* VS Code blue for button */
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        align-self: flex-start; /* Align button to start of flex item */
        margin-top: 15px; /* Space above the button */
    }
    .card-button:hover {
        background-color: #005f99;
    }

    /* General Streamlit button styling (for main content area) */
    .stButton>button {
        background-color: #007acc; /* VS Code blue */
        color: white;
        border-radius: 4px;
        border: none;
        padding: 10px 20px;
        font-size: 1em;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #005f99;
    }
    .stButton>button:focus {
        box-shadow: none;
    }

    /* Text input and text area styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #333;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 8px 12px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #007acc;
        box-shadow: 0 0 0 1px #007acc;
    }

    /* Selectbox styling */
    .stSelectbox>div>div>div {
        background-color: #333;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 4px;
    }
    .stSelectbox>div>div>div>div>span {
        color: #d4d4d4;
    }

    /* Multiselect styling */
    .stMultiSelect>div>div>div {
        background-color: #333;
        color: #d4d4d4;
        border: 1px solid #555;
        border-radius: 4px;
    }
    .stMultiSelect span {
        color: #d4d4d4;
    }
    .stMultiSelect .st-emotion-cache-1bzx45r { /* Chips */
        background-color: #007acc;
        color: white;
    }
    
    /* Expander styling */
    .st-emotion-cache-lq6x5h { /* Target the expander header */
        background-color: #252526;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 10px;
        color: #d4d4d4;
    }
    .st-emotion-cache-lq6x5h .st-emotion-cache-pkj102 { /* Expander icon */
        color: #d4d4d4;
    }
    /* Custom Card Styles for Dashboard */
    .card-container {
        display: flex;
        flex-wrap: wrap; /* Allow cards to wrap */
        gap: 20px; /* Space between cards */
        justify-content: space-around; /* Distribute cards and fill space */
        padding: 20px 0;
    }
    .stCard { /* Streamlit's internal card class */
        background-color: #252526; /* Darker background for cards */
        border: 1px solid #333;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        min-height: 150px; /* Ensure cards have some height */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        cursor: pointer;
        width: calc(50% - 10px); /* Two cards per row, accounting for gap */
        /* Removed max-width to allow expansion */
    }
    .stCard:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
    }
    .card-title {
        color: #d4d4d4;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .card-description {
        color: #888;
        font-size: 0.9em;
    }
    .card-button {
        background-color: #007acc; /* VS Code blue for button */
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        align-self: flex-start; /* Align button to start of flex item */
    }
    .card-style {
        background-color: #34285b;
        color: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
        cursor: pointer;
        /* text-align: center; will be inline */
    }
    .card-style:hover {
        transform: scale(1.02);
    }
    .card-style .card-title-text {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .card-style .card-description-text {
        font-size: 0.875rem;
        color: #a0a0a0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'current_main_view' not in st.session_state:
    st.session_state['current_main_view'] = 'dashboard' # Default to Dashboard as active
if 'proposal_inputs' not in st.session_state:
    st.session_state['proposal_inputs'] = {}
if 'generated_opportunities' not in st.session_state:
    st.session_state['generated_opportunities'] = []
if 'last_loaded_opportunity' not in st.session_state:
    st.session_state['last_loaded_opportunity'] = None

# Initialize databases on startup
init_dbs()

# --- Navigation Functions ---
def nav_to(view_name):
    st.session_state['current_main_view'] = view_name
    st.rerun()

# --- Sidebar Navigation ---
st.sidebar.markdown('<p style="font-size: 1.5em; font-weight: bold; color: #f0f0f0;"> Idea2Impact Studio</p>', unsafe_allow_html=True)
sidebar_items = [
    {"label": "Idea2Impact Studio", "icon": "🏠", "view": "dashboard"},
    {"label": "Grant Finder", "icon": "🔍", "view": "grant_finder"},
    {"label": "Align with My Research", "icon": "🎯", "view": "align_research"},
    {"label": "Grant Proposal Drafter", "icon": "📄", "view": "proposal_generator"},  
    {"label": "Brainstorm Room", "icon": "🧠", "view": "brainstorm_room"},
    {"label": "My Drafts & Submissions", "icon": "📂", "view": "my_drafts"},
    {"label": "Export & Share Center", "icon": "📤", "view": "export_share"}
]

for item in sidebar_items:
    # Use st.sidebar.button and apply custom CSS via markdown for styling
    if st.sidebar.button(
        f"{item['icon']} {item['label']}",
        key=f"sidebar_nav_{item['view']}",
        help=f"Go to {item['label']}"
    ):
        nav_to(item['view'])
    
    # Apply active style using markdown for the button's parent div
    if st.session_state['current_main_view'] == item['view']:
        st.sidebar.markdown(f"""
            <style>
                div[data-testid="stSidebarNav"] button[key="sidebar_nav_{item['view']}"] {{
                    background-color: #2b2b2b;
                    color: #61afef;
                    border-left: 3px solid #61afef;
                    font-weight: bold;
                }}
            </style>
        """, unsafe_allow_html=True)

# --- Main Content Area ---
st.header("Idea2Impact Studio")

if st.session_state['current_main_view'] == 'dashboard':
    st.markdown("<h3>Welcome to your AI-powered Grant Writing Assistant!</h3>", unsafe_allow_html=True)

    # Define dashboard cards with titles, icons, and descriptions
    dashboard_cards = [
        {"title": "Start New Proposal", "desc": "Launch the Grant Proposal Generator", "emoji": "📝", "view": "proposal_generator"},
        {"title": "Explore Opportunities", "desc": "Browse active funding calls", "emoji": "🔍", "view": "grant_finder"},
        {"title": "Align With Expertise", "desc": "Match calls to your research profile", "emoji": "🎯", "view": "align_research"},
        {"title": "View My Drafts", "desc": "Review or edit your saved drafts", "emoji": "📁", "view": "my_drafts"},
    ]

    # Apply global CSS for overall app styling and custom button styling
    st.markdown('''
    <style>
    .stApp {
        background-color: #121212; /* Apply to the main Streamlit app container */
    }

    /* Container for the card and hidden button */
    .card-wrapper {
        position: relative;
        width: 100%;
        height: 14rem; /* Fixed height for consistency */
        margin-bottom: 1rem; /* Space between cards when they stack */
    }

    /* Styling for Streamlit buttons to make them look like cards, but with transparent background */
    .stButton>button {
        background-color: transparent; /* Make the actual button transparent */
        color: transparent; /* Make button text transparent */
        border: none;
        border-radius: 0.75rem;
        padding: 0;
        box-shadow: none;
        transition: none;
        cursor: pointer;
        width: 100%;
        height: 100%;
        position: absolute; /* Position over the entire wrapper */
        top: 0;
        left: 0;
        z-index: 2; /* Ensure it's above the styled div */
    }
    /* Hide the default hover effect of the Streamlit button */
    .stButton>button:hover {
        transform: none;
        background-color: transparent; 
        color: transparent;
        box-shadow: none;
    }

    /* Styling for the visible card background and content */
    .visible-card {
        background-color: #34285b;
        color: white;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
        cursor: pointer;
        text-align: center;
        height: 100%; /* Fill the wrapper height */
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative; /* For z-index to work */
        z-index: 1; /* Ensure it's below the transparent button */
    }
    .visible-card:hover {
        transform: scale(1.02);
    }

    .card-title-text {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .card-description-text {
        font-size: 0.875rem;
        color: #a0a0a0;
    }
    </style>
    ''', unsafe_allow_html=True)

    # Render cards using Streamlit's column system with styled buttons
    cols = st.columns(len(dashboard_cards)) # Create columns based on the number of cards

    for i, card in enumerate(dashboard_cards):
        with cols[i]: # Place each card in its corresponding column
            st.markdown(f"""
                <div class="card-wrapper">
                    <div class="visible-card">
                        <h3 class="card-title-text">{card['emoji']} {card['title']}</h3>
                        <p class="card-description-text">{card['desc']}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Create a transparent Streamlit button on top of the visible card
            st.button("", key=f"dashboard_card_{card['view']}", on_click=nav_to, args=(card['view'],))

    st.markdown("---")
    st.markdown("### Getting Started Guide")
    st.code("""
# Welcome to Idea2Impact Studio!

# Use this space to:
# 1. Discover funding opportunities tailored to your research.
# 2. Analyze your Research Profile alignment with funding calls.
# 3. Generate new grant proposals with AI assistance.
# 4. Export professional PDF reports.

# To begin, select an option from the sidebar or click a card above.
# Happy Grant Writing!
    """, language='python')

elif st.session_state['current_main_view'] == 'proposal_generator':
    st.header("📄 Grant Proposal Generator")

    # --- Section 1: Funding Call Analysis ---
    st.subheader("1. Funding Call Analysis")

    funding_call_option = st.radio(
        "How would you like to provide the funding call details?",
        ("Upload PDF", "Paste Text", "Enter URL")
    )

    funding_call_text = ""
    if funding_call_option == "Upload PDF":
        uploaded_file = st.file_uploader("Upload PDF of Funding Call", type=["pdf"])
        if uploaded_file:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            funding_call_text = text
            st.success("PDF uploaded and extracted successfully!")
    elif funding_call_option == "Paste Text":
        funding_call_text = st.text_area("Paste Funding Call Text Here", height=300)
    elif funding_call_option == "Enter URL":
        url = st.text_input("Enter URL of Funding Call")
        if url:
            try:
                # Use trafilatura for better text extraction
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded, favor_recall=True)
                    funding_call_text = text if text else "Could not extract sufficient text from the URL."
                else:
                    st.warning("Could not fetch content from the provided URL.")

            except Exception as e:
                st.error(f"Error fetching or parsing URL: {e}")
                funding_call_text = ""
            if funding_call_text:
                st.success("Content extracted from URL!")

    if funding_call_text:
        st.subheader("Extracted Funding Call Details:")
        extracted_fields = extract_fields(funding_call_text)
        
        # Initialize session state for input fields if not already present
        if 'funding_agency' not in st.session_state:
            st.session_state['funding_agency'] = extracted_fields['Funding Agency']
        if 'scheme_type' not in st.session_state:
            st.session_state['scheme_type'] = extracted_fields['Scheme Type']
        if 'duration' not in st.session_state:
            st.session_state['duration'] = extracted_fields['Duration']
        if 'budget' not in st.session_state:
            st.session_state['budget'] = extracted_fields['Budget']
        if 'thrust_areas' not in st.session_state:
            st.session_state['thrust_areas'] = extracted_fields['Thrust Areas']
        if 'eligibility' not in st.session_state:
            st.session_state['eligibility'] = extracted_fields['Eligibility']
        if 'submission_format' not in st.session_state:
            st.session_state['submission_format'] = extracted_fields['Submission Format']

        st.session_state['funding_agency'] = st.text_input("Funding Agency", value=st.session_state['funding_agency'])
        st.session_state['scheme_type'] = st.text_input("Scheme Type", value=st.session_state['scheme_type'])
        st.session_state['duration'] = st.text_input("Duration", value=st.session_state['duration'])
        st.session_state['budget'] = st.text_input("Budget", value=st.session_state['budget'])
        st.session_state['thrust_areas'] = st.text_area("Thrust Areas", value=st.session_state['thrust_areas'], height=150)
        st.session_state['eligibility'] = st.text_area("Eligibility Criteria", value=st.session_state['eligibility'], height=150)
        st.session_state['submission_format'] = st.text_area("Submission Format", value=st.session_state['submission_format'], height=100)

        if st.button('Load Last Generated Opportunity from Research Opportunities Generator'):
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("SELECT id, scheme_name, funding_agency, last_date_submission, description FROM generated_opportunities WHERE is_processed = 0 ORDER BY timestamp DESC LIMIT 1")
            last_opportunity = c.fetchone()
            conn.close()

            if last_opportunity:
                opp_id, scheme_name, funding_agency_opp, last_date_submission, description = last_opportunity
                st.session_state['funding_agency'] = funding_agency_opp
                st.session_state['scheme_type'] = scheme_name
                st.session_state['duration'] = f"Deadline: {last_date_submission}"
                st.session_state['thrust_areas'] = description
                st.session_state['submission_format'] = f"Refer to funding agency website by {last_date_submission}"
                st.success(f"Loaded opportunity: '{scheme_name}' from Research Opportunities Generator. Remember to review details for accuracy!")
                
                conn = sqlite3.connect(DATABASE_FILE)
                c = conn.cursor()
                c.execute("UPDATE generated_opportunities SET is_processed = 1 WHERE id = ?", (opp_id,))
                conn.commit()
                conn.close()
                st.rerun() # Rerun to update the input fields with loaded data
            else:
                st.info("No new generated opportunities to load.")

    # --- Section 2: Proposal Alignment & Ideation ---
    st.subheader("2. Proposal Alignment & Ideation")
    user_research_background = st.text_area("Describe your research background and interests (max 500 words)", height=200, max_chars=500)

    if st.button("Generate Alignment & Key Themes"):
        if funding_call_text and user_research_background:
            alignment_prompt = f"""
            Given the Funding Call details and the User's Research Background, identify key areas of alignment, suggest potential research questions, and brainstorm innovative project ideas.

            Funding Call Details:
            Funding Agency: {st.session_state.get('funding_agency', 'N/A')}
            Scheme Type: {st.session_state.get('scheme_type', 'N/A')}
            Thrust Areas: {st.session_state.get('thrust_areas', 'N/A')}
            Eligibility: {st.session_state.get('eligibility', 'N/A')}

            User Research Background:
            {user_research_background}

            Provide:
            1.  **Alignment Areas**: How does the user's background directly match the funding call's thrust areas/objectives?
            2.  **Proposed Research Questions**: 3-5 specific, impactful, and relevant research questions.
            3.  **Innovative Project Ideas**: 2-3 distinct project ideas, each with a brief (1-2 sentences) description, highlighting novelty and potential impact.
            """
            with st.spinner("Generating alignment report..."):
                alignment_response = generate_content_with_retry(SELECTED_MODEL, alignment_prompt)
                if alignment_response:
                    st.session_state['alignment_report'] = alignment_response.text
                    st.success("Alignment report generated!")
                else:
                    st.error("Failed to generate alignment report. Please try again.")
        else:
            st.warning("Please provide both Funding Call details and your Research Background.")

    if 'alignment_report' in st.session_state:
        st.markdown("### Alignment Report:")
        st.write(st.session_state['alignment_report'])

    # --- Section 3: Proposal Template & Drafting ---
    st.subheader("3. Proposal Template & Drafting")

    template_option = st.radio(
        "How would you like to define your proposal template?",
        ("Generate from Funding Call", "Provide Custom Template Sections")
    )

    template_sections_input = ""
    if template_option == "Generate from Funding Call":
        if funding_call_text:
            if st.button("Generate Template Sections from Call"):
                template_prompt = f"""
                Analyze the following funding call text and extract the typical sections required for a research proposal submission. List them in a clear, numbered or bulleted format. Focus on major sections like 'Introduction', 'Objectives', 'Methodology', 'Budget', 'Timeline', 'Expected Outcomes', 'Bibliography', etc.

                Funding Call Text:
                {funding_call_text}
                """
                with st.spinner("Generating template sections..."):
                    template_response = generate_content_with_retry(SELECTED_MODEL, template_prompt)
                    if template_response:
                        st.session_state['template_sections_generated'] = template_response.text
                        st.success("Template sections generated!")
                    else:
                        st.error("Failed to generate template sections. Please try again.")
            if 'template_sections_generated' in st.session_state:
                st.write(st.session_state['template_sections_generated'])
                template_sections_input = st.session_state['template_sections_generated']
        else:
            st.info("Please provide funding call details first to generate a template.")
    elif template_option == "Provide Custom Template Sections":
        template_sections_input = st.text_area(
            "Enter your custom proposal sections (one per line)",
            height=200,
            value=st.session_state.get('template_sections_generated', '')
        )

    st.session_state['final_template_sections'] = template_sections_input

    if st.button("Generate Full Proposal Draft"):
        if st.session_state.get('final_template_sections') and st.session_state.get('alignment_report') and user_research_background:
            proposal_draft_prompt = f"""
            Generate a comprehensive research proposal draft based on the following information. Structure the proposal according to the provided template sections. Incorporate insights from the alignment report and the user's research background.

            ---
            Funding Call Details:
            Funding Agency: {st.session_state.get('funding_agency', 'N/A')}
            Scheme Type: {st.session_state.get('scheme_type', 'N/A')}
            Duration: {st.session_state.get('duration', 'N/A')}
            Budget (suggested if available): {st.session_state.get('budget', 'N/A')}
            Thrust Areas: {st.session_state.get('thrust_areas', 'N/A')}
            Eligibility: {st.session_state.get('eligibility', 'N/A')}
            Submission Format: {st.session_state.get('submission_format', 'N/A')}

            ---
            User Research Background:
            {user_research_background}

            ---
            Alignment Report & Ideas:
            {st.session_state['alignment_report']}

            ---
            Proposal Template Sections (write content for each):
            {st.session_state['final_template_sections']}

            ---
            Instructions for AI:
            - Write a detailed and persuasive proposal.
            - Ensure logical flow and coherence between sections.
            - Use academic and professional language.
            - Highlight novelty, feasibility, and potential impact.
            - For sections like 'Budget' or 'Timeline', provide realistic placeholders or general statements if specific figures are not derivable from the input, or suggest what should be included.
            - If a section like 'Bibliography' is listed, just put a placeholder like "[References/Bibliography to be added]"
            - Ensure the content directly addresses the funding call's requirements and aligns with the user's background.
            - The full proposal should be at least 1500 words, but ideally around 2000-3000 words for a substantial draft.
            """
            with st.spinner("Generating full proposal draft (this may take a few minutes for a comprehensive draft)..."):
                full_proposal_response = generate_content_with_retry(SELECTED_MODEL, proposal_draft_prompt)
                if full_proposal_response:
                    st.session_state['full_proposal_draft'] = full_proposal_response.text
                    st.success("Full proposal draft generated!")
                else:
                    st.error("Failed to generate full proposal draft. Please try again.")
        else:
            st.warning("Please ensure funding call details, research background, and template sections are provided.")

    if 'full_proposal_draft' in st.session_state:
        st.markdown("### Full Proposal Draft:")
        st.write(st.session_state['full_proposal_draft'])

        # --- Section 4: Export & Save ---
        st.subheader("4. Export & Save")

        if st.button("Save Proposal to Database"):
            proposal_data = {
                'timestamp': datetime.now().isoformat(),
                'funding_agency': st.session_state.get('funding_agency', ''),
                'scheme_type': st.session_state.get('scheme_type', ''),
                'duration': st.session_state.get('duration', ''),
                'budget': st.session_state.get('budget', ''),
                'thrust_areas': st.session_state.get('thrust_areas', ''),
                'eligibility': st.session_state.get('eligibility', ''),
                'submission_format': st.session_state.get('submission_format', ''),
                'user_research_background': user_research_background,
                'template_sections': st.session_state.get('final_template_sections', ''),
                'full_proposal_content': st.session_state.get('full_proposal_draft', '')
            }
            save_proposal_to_db(proposal_data)
            st.success("Proposal saved to database!")

        # Export as PDF
        if st.button("Export Proposal as PDF"):
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, st.session_state['full_proposal_draft'])
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="Download Proposal PDF",
                data=pdf_output,
                file_name="generated_proposal.pdf",
                mime="application/pdf"
            )

        # Export Alignment Report as PDF
        if 'alignment_report' in st.session_state and st.button("Export Alignment Report as PDF"):
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, st.session_state['alignment_report'])
            pdf_output_alignment = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="Download Alignment Report PDF",
                data=pdf_output_alignment,
                file_name="alignment_report.pdf",
                mime="application/pdf"
            )

elif st.session_state['current_main_view'] == 'grant_finder':
    st.header("🔍 Grant Finder (AI-Powered Research Opportunity Generator)")
    
    st.markdown("### Discover New Funding Opportunities with AI")
    st.write("Select research areas and let AI find relevant opportunities for you.")

    # Use st.columns to place broad and specific domain selection side-by-side
    col_broad, col_specific = st.columns(2)

    with col_broad:
        selected_broad_domain = st.selectbox("Select Broad Domain", list(taxonomy.keys()))

    selected_specific_areas = []
    if selected_broad_domain:
        with col_specific:
            selected_specific_areas = st.multiselect(
                "Select Specific Research Areas",
                taxonomy[selected_broad_domain]
            )
    else:
        st.info("Please select a broad domain first.")

    if st.button("Generate Research Opportunities"):
        if selected_specific_areas:
            combined_areas = ", ".join(selected_specific_areas)
            
            # Calculate minimum submission date (today + 15 days)
            min_submission_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

            prompt = f"""Generate a list of 5-7 innovative and actionable research opportunities or project ideas based on the following research areas: {combined_areas}. For each opportunity, provide:
            - Programme/Scheme Name
            - Funding Agency (propose a realistic, but fictional, agency if not explicitly stated by combining keywords)
            - Last Date of Submission (propose a realistic date format like YYYY-MM-DD, ensuring it is at least {min_submission_date} or later)
            - A 2-3 sentence description outlining its scope and potential impact.

            Research Areas: {combined_areas}

            Format your response as a numbered list, with each item clearly labeled for 'Programme/Scheme Name', 'Funding Agency', 'Last Date of Submission', and 'Description'. Example:
            1. Programme/Scheme Name: [Name]
               Funding Agency: [Agency]
               Last Date of Submission: YYYY-MM-DD
               Description: [2-3 sentences description]
            """
            st.info("Generating opportunities... This may take a moment.")
            with st.spinner("AI is brainstorming opportunities..."):
                response = generate_content_with_retry(SELECTED_MODEL, prompt)

            if response and response.text:
                st.session_state['generated_opportunities'] = response.text
                st.success("Opportunities generated!")
            else:
                st.error("Failed to generate research opportunities. Please try again.")
        else:
            st.warning("Please select at least one specific research area.")

    if 'generated_opportunities' in st.session_state and st.session_state['generated_opportunities']:
        st.subheader("Generated Research Opportunities:")
        opportunities_text = st.session_state['generated_opportunities']
        opportunities_list = opportunities_text.strip().split('\n\n') # Split by double newline for separate opportunities

        # Process and display each opportunity
        for i, opp_raw in enumerate(opportunities_list):
            if opp_raw.strip(): # Ensure it's not an empty string
                st.markdown(f"**Opportunity {i+1}**")
                
                scheme_name_match = re.search(r'Programme/Scheme Name: (.*)', opp_raw)
                funding_agency_match = re.search(r'Funding Agency: (.*)', opp_raw)
                last_date_match = re.search(r'Last Date of Submission: (.*)', opp_raw)
                description_match = re.search(r'Description: (.*)', opp_raw, re.DOTALL)

                opportunity_data = {
                    "scheme_name": scheme_name_match.group(1).strip() if scheme_name_match else "N/A",
                    "funding_agency": funding_agency_match.group(1).strip() if funding_agency_match else "N/A",
                    "last_date_submission": last_date_match.group(1).strip() if last_date_match else "N/A",
                    "description": description_match.group(1).strip() if description_match else "N/A"
                }

                st.write(f"**Programme/Scheme Name:** {opportunity_data['scheme_name']}")
                st.write(f"**Funding Agency:** {opportunity_data['funding_agency']}")
                st.write(f"**Last Date of Submission:** {opportunity_data['last_date_submission']}")
                st.write(f"**Description:** {opportunity_data['description']}")

                if st.button(f"Submit this Opportunity ({i+1}) to Grant Proposal Generator", key=f"submit_opp_{i}"):
                    st.info(f"Attempting to submit opportunity: {opportunity_data['scheme_name']}")
                    save_generated_opportunity_to_db(opportunity_data)
                    st.success(f"Opportunity '{opportunity_data['scheme_name']}' submitted! Go to 'Grant Proposal Generator' and click 'Load Last Generated Opportunity'.")
                    st.rerun()
                st.markdown("---") # Separator
elif st.session_state['current_main_view'] == 'align_research':
    st.header("🎯 Align with My Research (Coming Soon!)")
    st.info("This section will help you align funding calls with your research profile.")
elif st.session_state['current_main_view'] == 'brainstorm_room':
    st.header("🧠 Brainstorm Room (Coming Soon!)")
    st.info("A space for collaborative brainstorming on proposal ideas.")
elif st.session_state['current_main_view'] == 'my_drafts':
    st.header("📂 My Drafts & Submissions")
    st.write("Here you can view your saved proposals and opportunities.")

    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    st.subheader("Saved Proposals:")
    c.execute("SELECT timestamp, funding_agency, scheme_type, full_proposal_content FROM proposals ORDER BY timestamp DESC")
    proposals = c.fetchall()
    if proposals:
        for idx, prop in enumerate(proposals):
            with st.expander(f"Proposal for {prop[1]} - {prop[2]} ({prop[0]})"):
                st.write(prop[3])
    else:
        st.info("No proposals saved yet.")

    st.subheader("Saved Grant Finder Opportunities:")
    c.execute("SELECT timestamp, scheme_name, funding_agency, last_date_submission FROM generated_opportunities ORDER BY timestamp DESC")
    opportunities = c.fetchall()
    if opportunities:
        for idx, opp in enumerate(opportunities):
            st.write(f"- **{opp[1]}** from {opp[2]} (Deadline: {opp[3]}) - Saved on: {opp[0]}")
    else:
        st.info("No generated opportunities saved yet.")

    conn.close()

elif st.session_state['current_main_view'] == 'export_share':
    st.header("📤 Export & Share Center (Coming Soon!)")
    st.info("This section will allow you to export and share your proposals in various formats.")