<div align="center">

# SATARK
### Smart AI Threat Analysis & Risk Knowledge

**Understand suspicious content. Recognize digital threats. Build safer online habits.**

SATARK is an AI-assisted security-awareness application for exploring suspicious messages, links, images, QR codes, PDFs, and supported videos. It combines guided analysis with practical learning features.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![AI](https://img.shields.io/badge/AI-Groq-111827)
![Project status](https://img.shields.io/badge/status-prototype-8b5cf6)

</div>

---

> **Important:** SATARK is a learning and triage aid—not an antivirus, forensic tool, or proof that content is safe. AI-generated scores are not calibrated probabilities. A suspicious item may be missed, and a legitimate item may be flagged. Independently verify consequential findings.

## Contents

- [What SATARK does](#what-satark-does)
- [Features](#features)
- [How it works](#how-it-works)
- [Technology](#technology)
- [Run locally](#run-locally)
- [Configure Groq](#configure-groq)
- [Project structure](#project-structure)
- [Tests and checks](#tests-and-checks)
- [Security, privacy, and limitations](#security-privacy-and-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

## What SATARK does

SATARK provides a single workspace to examine potentially risky digital content and learn about common online scams. Depending on the selected workflow and available dependencies, it can analyze text, URLs, images/QR codes, PDFs, and videos. Results may include a threat category, risk score, confidence value, indicators, and suggested next steps.

The app also includes interactive learning experiences such as **Scam Challenge**, **SATARK Academy**, and **Classroom Mode**.

## Features

| Feature | Description |
| --- | --- |
| Text analysis | Review suspicious messages and other text for scam indicators. |
| URL analysis | Validate and retrieve eligible public-page text for analysis. |
| Image and QR analysis | Submit supported images and QR-code content for review. |
| PDF analysis | Extract text from supported PDF documents and analyze it. |
| Video analysis | Extract representative frames; optionally transcribe audio when the workflow and provider support it. |
| AI-assisted results | Present a model-generated assessment, indicators, and suggested actions. |
| PDF export | Download a report of an analysis. |
| Session history | Revisit results held in the current app session. |
| Learning | Practice scam recognition and explore security-awareness content. |

Some workflows depend on external provider access or optional packages. A completed analysis does not mean that a file was executed in a sandbox or exhaustively scanned.

## How it works

1. **Choose a workflow** and provide the content you want to examine.
2. **Prepare the input.** Depending on the workflow, SATARK may extract text, inspect image content, or sample video frames.
3. **Request an AI assessment.** Supported analysis is sent to the configured Groq service.
4. **Review the result.** Treat the output as a clue for further investigation, not a definitive security verdict.
5. **Learn and report.** Use the learning sections or export a PDF when useful.

Do not submit passwords, one-time codes, private keys, or unnecessary personal information.

## Technology

- **Python** — application logic
- **Streamlit** — interactive web interface and session state
- **CSS** — application styling
- **Groq** — AI model API and supported audio transcription
- **pypdf** — PDF text extraction
- **Pillow** — image handling and conversion
- **ReportLab** — PDF report generation
- **OpenCV** — video frame extraction

The repository separates several responsibilities into modules. The main Streamlit entry point still contains substantial analysis and UI orchestration, so the application is not yet fully decoupled.

## Run locally

### Requirements

- Python 3.10 or newer
- A Groq API key for AI-powered workflows
- Dependencies listed in `requirements.txt`

### Install

Clone the repository and enter its directory:

```bash
git clone https://github.com/coolbandariya/Satark.git
cd Satark
python -m venv .venv
```

Activate the environment.

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and start Streamlit:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run satark.py
```

Streamlit will print a local address in the terminal. Open it in your browser.

## Configure Groq

Set `GROQ_API_KEY` in your environment before starting the app.

**Windows PowerShell**
```powershell
$env:GROQ_API_KEY="your-key"
streamlit run satark.py
```

**macOS / Linux**
```bash
export GROQ_API_KEY="your-key"
streamlit run satark.py
```

If the app offers a sidebar key field, it can also be used for local experimentation. Never commit API keys or place them in public source files. For deployments, use the hosting provider's secret manager.

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated validation workflow
├── docs/
│   └── ANALYSIS_LIMITATIONS.md  # Interpretation and safe-use guidance
├── tests/
│   ├── test_satark_utils.py     # Shared helper tests
│   └── test_video_processing.py # Video helper tests
├── satark.py                    # Streamlit entry point and app workflows
├── scam_challenge.py             # Scam Challenge game and rendering
├── video_processing.py           # Video frame and audio helpers
├── reports.py                    # PDF report generation
├── satark_utils.py               # Shared text/result helpers
├── url_security.py               # URL validation and public-page fetching
├── styles.css                    # Application styles
├── requirements.txt              # Python dependencies
├── README.md
└── SECURITY.md                   # Security policy and deployment checklist
```

## Tests and checks

Install the project dependencies, then run:

```bash
python -m pip check
python -m compileall -q satark.py scam_challenge.py video_processing.py reports.py satark_utils.py url_security.py tests
python -m unittest discover -s tests -v
```

These checks cover dependency consistency, Python compilation, and the repository's unit tests. They do **not** replace manual testing of Streamlit interactions, live Groq requests, deployment configuration, or end-to-end file processing.

Check the GitHub Actions workflow for the status of automated validation before relying on a change. A passing unit-test run alone does not establish production readiness.

## Security, privacy, and limitations

- **Treat results as advisory.** AI can make mistakes, and attackers can adapt their content.
- **Do not interact with suspicious content** just to confirm a result. Avoid opening suspicious links or executing attachments.
- **Minimize sensitive input.** Do not submit passwords, OTPs, private keys, or data you do not need analyzed.
- **Understand external processing.** Content submitted for AI analysis may be sent to the configured provider. Review the provider's data-handling terms before using sensitive material.
- **Do not treat session history as evidence storage.** It is not a secure, durable case-management system.
- **Use deployment safeguards.** Restrict access where appropriate, keep secrets out of source control, set upload/request limits, and apply network egress controls.

See [Analysis limitations](docs/ANALYSIS_LIMITATIONS.md) and the [Security policy](SECURITY.md) for additional guidance.

## Roadmap

- [x] Move application styling into a dedicated CSS file.
- [x] Extract shared text/result helpers.
- [x] Isolate URL validation and public-page fetching.
- [x] Extract PDF report generation.
- [x] Extract Scam Challenge into its own module.
- [x] Extract video processing helpers.
- [x] Add unit tests for shared helpers and video processing.
- [ ] Further separate analysis/provider logic from Streamlit UI.
- [ ] Add broader workflow and end-to-end tests.
- [ ] Resolve and verify the current CI failure.
- [ ] Complete a deployment-specific security and runtime review.

## Contributing

Focused improvements and bug fixes are welcome. Please:

1. Keep changes small and explain their purpose.
2. Add or update tests for behavior changes.
3. Run the checks above and report what was actually verified.
4. Never commit credentials, tokens, or real sensitive user content.
5. Report security vulnerabilities privately using the process in [SECURITY.md](SECURITY.md), rather than opening a public issue.
