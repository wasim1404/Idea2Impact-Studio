[![Build Status](https://github.com/<your-username>/<your-repo>/actions/workflows/python-app.yml/badge.svg)](https://github.com/<your-username>/<your-repo>/actions)
[![codecov](https://codecov.io/gh/<your-username>/<your-repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<your-username>/<your-repo>)

# AI Research Proposal Mentor and Grant Writing Assistant

## Overview
This AI assistant is designed to help faculty members craft successful research proposals and grant applications. It serves as a mentor throughout the grant writing process, providing guidance, structure, and polished academic language that aligns with funding priorities.

## Core Capabilities

### Funding Call Analysis
When provided with a funding call document, the assistant extracts key information including:
- Title
- Scheme Type
- Duration
- Budget
- Thrust Areas
- Eligibility
- Submission Format

### Research Alignment
When given research inputs, the assistant:
- Identifies core expertise, keywords, and relevance to the call
- Aligns researcher strengths to funding priorities
- Offers fitment suggestions

### Proposal Development
The assistant guides users through the proposal development process by:
- Providing section-by-section guidance (Problem Statement, Objectives, Methodology, Outcomes, Budget, etc.)
- Asking clear and pointed questions to elicit necessary information
- Drafting content in academic, clear, and impactful language
- Ensuring structure compliance, coherence, and strategic tone

## How to Use

1. **Start by providing a funding call description** - The assistant will extract and organize key information
2. **Share your research background and interests** - The assistant will help align your expertise with the funding priorities
3. **Follow the guided process** - The assistant will walk you through each section of the proposal
4. **Review and refine** - The assistant will help polish your proposal to maximize chances of success

## Example Usage

```
User: I found a funding opportunity from the NSF about sustainable energy solutions. I'm a chemical engineer specializing in catalysis.

Assistant: [Extracts funding details and guides alignment with user expertise]
```

## Best Practices

- Provide as much detail as possible about the funding call
- Be specific about your research background and previous work
- Answer the assistant's questions thoroughly to generate comprehensive content
- Review the generated content carefully and request revisions as needed

---

This tool is designed to assist in the grant writing process, but final review and customization by the researcher is essential for a successful proposal.

Great! The next step is to run your Streamlit app so you can see the Funding Call Analysis interface in your browser.

**Run this command in your terminal:**
```
streamlit run "Idea2Impact Studio.py"
```

This will launch the web app. Your browser should open automatically, or you can visit the local URL provided in the terminal (usually http://localhost:8501).

Let me know once it’s running, or if you need help with the next development phase!

Great choice! Integrating advanced NLP with spaCy or transformers will make your extraction more robust and adaptable to varied funding call formats.

**Here’s the plan for the next step:**
1. Load a spaCy language model (e.g., en_core_web_sm).
2. Use spaCy’s NLP pipeline to process the funding call text.
3. Implement logic to extract key fields (Title, Scheme Type, Duration, Budget, Thrust Areas, Eligibility, Submission Format) using named entity recognition (NER), pattern matching, and custom rules.
4. Display the extracted information in your Streamlit app.

**Let’s start by:**
- Installing the spaCy English model.
- Updating your app to load and use spaCy for extraction.

---

**Step 1: Install the spaCy English model**

Run this command in your terminal:
```
python -m spacy download en_core_web_md
```

Let me know once you’ve done this, and I’ll guide you through updating your Streamlit app to use spaCy for extraction!