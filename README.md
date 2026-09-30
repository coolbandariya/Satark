<div align="center">

# SATARK
### Smart AI Threat Analysis & Risk Knowledge

**A security-awareness workspace for examining suspicious content, understanding evidence, and learning safer online habits.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq-111827)
![Status](https://img.shields.io/badge/status-prototype-8b5cf6)

</div>

---

> **Safety note:** SATARK is an assistive analysis and education tool. It is not an antivirus, forensic platform, or guarantee that content is safe. Model-generated scores are not calibrated probabilities. Verify consequential findings independently.

## Overview

SATARK helps users inspect suspicious messages, URLs, images, QR codes, PDFs, and supported videos. It presents an AI-assisted assessment alongside indicators and suggested next steps. Learning features include Scam Challenge, SATARK Academy, and Classroom Mode.

## Features

| Area | Capabilities |
| --- | --- |
| Content analysis | Text, URL, image/QR, PDF, and supported video workflows |
| Model handling | Groq model discovery and fallback selection |
| Results | Threat category, risk score, confidence, indicators, and recommended actions |
| Reports | Downloadable PDF report |
| Session history | Temporary in-session results and exports |
| Learning | Scam Challenge, Academy lessons, and classroom summaries |

Feature availability depends on installed optional dependencies and provider access.

## Technology

- **Application logic:** Python
- **Interface:** Streamlit
- **Presentation:** Dedicated CSS in `styles.css`
- **AI provider:** Groq API
- **Documents and images:** pypdf, Pillow
- **PDF reports:** ReportLab
- **Optional video processing:** OpenCV

The presentation layer, PDF report rendering, and shared text-normalization helpers are separated from the Streamlit entry point. Analysis, provider/model integration, and interactive learning workflows remain in `satark.py`; these are coupled to Streamlit session state and are not yet independently packaged.

## Quick start

Requires Python 3.10+ and a compatible dependency set.

```bash
git clone https://github.com/coolbandariya/Satark.git
cd Satark
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
streamlit run satark.py
```

## Configuration

Set your Groq API key in the environment:

```bash
# macOS / Linux
export GROQ_API_KEY="your-key"
```

```powershell
# Windows PowerShell
$env:GROQ_API_KEY="your-key"
```

You can also enter the key in the app's sidebar. Never commit API keys, tokens, or local environment files.

## Repository layout

```text
.
├── .github/
│   └── workflows/ci.yml       # Python syntax and repository checks
├── docs/
│   ├── ANALYSIS_LIMITATIONS.md
│   └── ...                    # Project and safety documentation
├── satark.py                  # Streamlit entry point and UI workflows
├── satark_utils.py            # Side-effect-free text/result helpers
├── reports.py                 # PDF report generation
├── tests/
│   └── test_satark_utils.py   # Unit tests for normalization helpers
├── styles.css                 # Application presentation
├── requirements.txt
├── README.md
└── SECURITY.md
```

## Development checks

Run the checks used by CI:

```bash
python -m py_compile satark.py reports.py satark_utils.py tests/test_satark_utils.py
python -m unittest discover -s tests -v
```

Then launch the app and manually verify the affected workflow. CI does not exercise Streamlit interactions, external API behavior, model quality, or PDF rendering end to end.

## Responsible use and privacy

- Do not submit passwords, OTPs, private keys, or unnecessary personal information.
- Do not open suspicious links or execute attachments merely to validate a result.
- A model can produce false positives and false negatives; treat results as triage guidance.
- Review the provider's data-handling terms before sending private content to an external AI service.
- Session history is intended to be temporary; do not treat it as secure evidence storage.
- See [docs/ANALYSIS_LIMITATIONS.md](docs/ANALYSIS_LIMITATIONS.md) and [SECURITY.md](SECURITY.md).

## Roadmap

- [x] Move the large embedded style block into a dedicated CSS file.
- [x] Extract shared text/result normalization helpers into `satark_utils.py`.
- [x] Isolate public URL validation and fetching in `url_security.py`.
- [x] Extract PDF report generation into `reports.py`.
- [x] Add unit tests for normalization helpers.
- [ ] Separate analysis and provider/model integration from Streamlit UI.
- [ ] Extract Scam Challenge and Academy content into learning modules.
- [ ] Add Streamlit workflow tests and PDF regression checks.

## Contributing

Keep changes focused, avoid committing secrets or real sensitive content, and include the verification steps used. For security issues, follow the private reporting guidance in [SECURITY.md](SECURITY.md).
