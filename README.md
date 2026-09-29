# SATARK — AI Threat Analyzer

A Streamlit-based security-awareness and threat-analysis application that helps users examine suspicious messages, URLs, images, and documents, understand the evidence behind an analysis, and learn safer online habits.

> **Important:** SATARK is an assistive analysis tool, not a malware scanner, forensic platform, or guarantee that content is safe. Treat results as guidance and verify high-risk cases independently.

## What it includes

- AI-assisted analysis with Groq model discovery and fallback selection.
- Support for text and supported file/image inputs.
- Evidence-oriented results with threat category and confidence presentation.
- Session history and report export.
- Scam Challenge, SATARK Academy, and Classroom Mode for security education.
- Session-oriented handling of analysis data.

## Tech stack

- Python
- Streamlit
- Groq API
- pypdf and Pillow for document/image handling
- ReportLab for PDF report generation

## Quick start

Requires Python 3.10+ (use a compatible version for the installed dependencies).

```bash
git clone https://github.com/coolbandariya/Satark.git
cd Satark
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install and launch:

```bash
pip install -r requirements.txt
streamlit run satark.py
```

## Configuration

Set your Groq API key in the environment before launching:

```bash
# macOS / Linux
export GROQ_API_KEY="your-key"

# Windows PowerShell
$env:GROQ_API_KEY="your-key"
```

Never commit API keys or other secrets. Keep local environment files out of version control.

## Responsible use

- Do not submit passwords, private keys, or sensitive personal information.
- A low or high confidence score is not a calibrated probability of safety unless independently validated.
- Do not open suspicious links or files just to verify an analysis.
- Use trusted security tools and official channels for consequential decisions.
- Review provider terms and data handling before submitting private content to an external AI service.

## Repository

- Application: `satark.py`
- Dependencies: `requirements.txt`

## Current status

This repository contains a single-file Streamlit application. For maintainability, future work can separate UI, model/provider integration, input validation, report generation, and educational content into focused modules, with automated tests for each boundary.
