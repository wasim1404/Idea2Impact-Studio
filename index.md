# AI Research Proposal Mentor and Grant Writing Assistant

## Overview

This package contains a comprehensive set of resources for an AI-powered research proposal mentor and grant writing assistant designed to help faculty members craft successful grant proposals. The assistant is configured to interpret funding calls, align research profiles with opportunities, structure proposals according to agency requirements, facilitate brainstorming, and generate polished academic language.

## Core Files

- [**prompt.json**](./prompt.json) - The system prompt that defines the AI assistant's capabilities and behavior
- [**README.md**](./README.md) - Introduction and overview of the assistant's purpose and capabilities
- [**how_to_use_this_assistant.md**](./how_to_use_this_assistant.md) - Detailed guide on effectively interacting with the assistant

## Sample Materials

- [**sample_funding_call.md**](./sample_funding_call.md) - Example of a funding opportunity announcement
- [**sample_researcher_profile.md**](./sample_researcher_profile.md) - Example researcher profile for matching with opportunities
- [**sample_interaction.md**](./sample_interaction.md) - Demonstration of a dialogue with the assistant
- [**sample_questionnaire.md**](./sample_questionnaire.md) - Structured questions for developing proposal components
- [**sample_successful_proposals.md**](./sample_successful_proposals.md) - Annotated excerpts from funded proposals

## Reference Guides

- [**grant_writing_best_practices.md**](./grant_writing_best_practices.md) - Comprehensive guide to effective grant writing
- [**effective_proposal_language.md**](./effective_proposal_language.md) - Examples of strong academic language for proposals
- [**funding_agency_formats.md**](./funding_agency_formats.md) - Requirements for different funding agencies
- [**grant_writing_glossary.md**](./grant_writing_glossary.md) - Definitions of grant-related terminology
- [**grant_submission_checklist.md**](./grant_submission_checklist.md) - Comprehensive pre-submission verification list
- [**responding_to_reviewers.md**](./responding_to_reviewers.md) - Guide for addressing reviewer comments

## Getting Started

To begin using the AI research proposal mentor and grant writing assistant:

1. Review the [README.md](./README.md) for an overview of capabilities
2. Consult [how_to_use_this_assistant.md](./how_to_use_this_assistant.md) for interaction strategies
3. Explore the sample materials to understand how the assistant works
4. Reference the guides as needed during your proposal development process

## Using This Package

This package is designed to support the entire grant development lifecycle:

1. **Initial Planning**: Use the assistant to analyze funding opportunities and align them with research interests
2. **Proposal Development**: Work section by section through your proposal with guided assistance
3. **Review and Refinement**: Get feedback on draft content and suggestions for improvement
4. **Submission Preparation**: Ensure all components are complete using the submission checklist
5. **Revision Process**: Address reviewer comments effectively if resubmission is needed

The assistant is most effective when you provide clear context about your research background, the specific funding opportunity, and your particular needs at each stage of the process.

The error you’re seeing means that the spaCy model en_core_web_md is not installed on your system. This model is required for semantic similarity matching because it provides word vectors.

**To fix this:**

1. Open your terminal in the project directory.
2. Run the following command to download and install the medium English model:
```
python -m spacy download en_core_web_md
```

After the installation completes, restart your Streamlit app.  
You should now be able to use the semantic similarity features without errors!

Let me know if you need help with the installation or if you encounter any other issues.

Great question! The best place to put your API keys depends on the type of project you’re working on. The most secure and common way is to use **environment variables**. Here’s how you can do it for a typical Python project (like yours, since you have an `app.py` file):

---

## 1. Using Environment Variables (Recommended)

### Step 1: Create a `.env` File (Optional but convenient)
- In your project directory, create a file named `.env`.
- Add your API key like this:
  ```
  OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

### Step 2: Load the Environment Variable in Python
- Install the `python-dotenv` package if you haven’t already:
  ```
  pip install python-dotenv
  ```
- In your `app.py`, add:
  ```python
  import os
  from dotenv import load_dotenv

  load_dotenv()  # take environment variables from .env.

  api_key = os.getenv("OPENAI_API_KEY")
  ```

### Step 3: Use the `api_key` Variable in Your Code
- Pass `api_key` to the OpenAI client or wherever it’s needed.

---

## 2. Setting Environment Variables Directly (Alternative)

### On Windows (Command Prompt or PowerShell)
```powershell
$env:OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python app.py
```

### On macOS/Linux (Terminal)
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python app.py
```

---

## 3. **Never** Hardcode API Keys in Your Code

**Bad practice:**
```python
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
This exposes your key if you share your code.

---

## 4. Using the Key with OpenAI’s Python Library

If you use the OpenAI library, you can set the key like this:
```python
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
```

---

## Summary Table

| Method         | Security | Ease of Use | Recommended? |
|----------------|----------|-------------|--------------|
| .env file      | High     | Easy        | Yes          |
| Env variable   | High     | Medium      | Yes          |
| Hardcoded      | Low      | Easy        | No           |

---

If you tell me more about your project (e.g., are you using Streamlit, Flask, Jupyter, etc.?), I can give you even more specific instructions!

Let me know if you need help setting this up.

---

### What should you do?

- **If you meant to run a Python project:**  
  Use Python commands, not npm. For example:
  - Install dependencies:  
    ```
    pip install -r requirements.txt
    ```
  - Run your app:  
    ```
    python app.py
    ```

- **If you actually want a Node.js project:**  
  You need to initialize it first:
  ```
  npm init
  ```
  This will create a `package.json` file. But based on your files, this is probably not what you want.

---

**Summary:**  
Your project is Python-based, so you should use Python tools (`pip`, `python`) instead of npm. If you need help running your Python app or installing dependencies, let me know! If you actually want to add Node.js functionality, I can help you set that up as well.

**To clarify for anyone reading:**

- The error occurs because you tried to run an npm command (`npm run dev`) in a folder that does not have a `package.json` file. This is expected for a Python project.
- Your project is Python-based (it uses `app.py` and `requirements.txt`), so you should use Python commands, not npm.

**Correct workflow for your project:**

1. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```
2. **Run your app:**
   ```
   python app.py
   ```

**You do not need to use npm or Node.js commands unless you are intentionally adding JavaScript/Node.js functionality.**

---

If you want, I can help you:
- Set up a proper Python development workflow
- Add more troubleshooting tips to your documentation
- Guide you on how to run your app or install dependencies

Let me know what you’d like to do next!

---

## Quick Start

1. **Clone the repository** (if you haven’t already):
   ```
   git clone <your-repo-url>
   cd Grant
   ```
2. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **(Optional) Set up environment variables:**
   - Create a `.env` file and add your API keys as needed (see instructions above).
4. **Run the app:**
   ```
   python app.py
   ```

---

## Troubleshooting & FAQ

**Q: I get an npm error about missing package.json.**
A: This is a Python project. Use `pip` and `python` commands, not `npm`.

**Q: How do I install dependencies?**
A: Run `pip install -r requirements.txt` in your project directory.

**Q: How do I set environment variables?**
A: Use a `.env` file or set them in your shell before running the app.

**Q: How do I run the app?**
A: Use `python app.py`.

**Q: I get a spaCy model error (en_core_web_md not found).**
A: Run `python -m spacy download en_core_web_md` to install the required model.

If you have other issues, please check the README or contact the maintainer.

---

## Testing

This project uses [pytest](https://pytest.org/) for automated testing.

1. **Install test dependencies:**
   ```
   pip install -r requirements.txt
   pip install pytest
   ```
2. **Run tests:**
   ```
   pytest
   ```

All tests are located in the `tests/` directory.

---

## Development Setup

- It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html) for development:
  ```
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```
- Install development dependencies:
  ```
  pip install pytest
  ```
- Run the app:
  ```
  python app.py
  ```
- Run tests:
  ```
  pytest
  ```

For contributions, please follow PEP8 style guidelines and ensure all tests pass before submitting changes.

---

## Continuous Integration

This project uses [GitHub Actions](https://github.com/features/actions) for continuous integration. All pushes and pull requests to the `main` branch automatically run the test suite on multiple Python versions (3.8–3.11).

You can view the workflow file at `.github/workflows/python-app.yml`.

---

## How to Write Tests

- Place all test files in the `tests/` directory. Test files should be named `test_*.py`.
- Use [pytest](https://docs.pytest.org/) for writing tests.
- Example test structure:
  ```python
  import pytest
  from app import add  # Example function

  def test_add():
      assert add(2, 3) == 5

  @pytest.mark.parametrize("a,b,expected", [
      (1, 1, 2),
      (0, 0, 0),
      (-1, 1, 0)
  ])
  def test_add_param(a, b, expected):
      assert add(a, b) == expected

  def test_add_type_error():
      with pytest.raises(TypeError):
          add("a", 1)
  ```
- Use fixtures for reusable setup.
- Test for both expected results and error conditions.
- Run `pytest` to execute all tests.

For more, see the [pytest documentation](https://docs.pytest.org/).

### What’s Implemented
- A static left-hand sidebar in your Streamlit app shows the grant generation steps and their statuses.
- The sidebar updates automatically as you move through each stage (upload, alignment, template, draft, review/export).
- Progress is visually indicated with icons and a progress bar.

### How to Use It
1. **Start your app** with:
   ```
   streamlit run app.py
   ```
2. As you complete each section (uploading a funding call, entering research background, etc.), the sidebar will update to show your progress.
3. When you finish drafting and export/review your proposal, you can mark the final step as completed.

---

### Next Steps & Enhancements (Optional)
- **Customize Step Names:** You can rename steps or add more if your workflow changes.
- **Add Navigation Links:** If you want clickable navigation to jump to sections, let me know!
- **Persist Progress:** If you want progress to persist across sessions, consider saving `st.session_state` to disk.
- **Visual Improvements:** Add colors, tooltips, or section highlights for better UX.

If you’d like any of these enhancements or have another feature in mind, just tell me what you want to do next!