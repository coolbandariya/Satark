# SATARK architecture and threat model

## Runtime boundaries

SATARK has four important trust boundaries:

1. Browser → Streamlit: UI state and browser-side visual components are untrusted presentation state.
2. User input → preprocessing: uploaded and pasted content is bounded before parsing or encoding.
3. SATARK → external URL: URL fetching is treated as an SSRF-sensitive operation and fails closed on unsafe targets.
4. SATARK → Groq: submitted analysis evidence leaves the application only when the user starts an AI analysis.

## Data flow

User input
  |
  +--> bounded preprocessing
  |       +--> text normalization
  |       +--> PDF extraction
  |       +--> image conversion
  |       +--> video frame/audio extraction
  |       +--> public URL fetch
  |
  +--> analysis orchestration
          |
          +--> Groq provider/model selection
          |
          +--> JSON result
                  |
                  +--> consistency normalization
                  +--> confidence calibration
                  +--> stable findings
                  +--> UI + PDF report

## URL threat model

The URL scanner can cause the application server to make outbound requests, so it is treated as an SSRF boundary. The application:

- permits only HTTP(S)
- rejects URL credentials
- rejects localhost names
- resolves hostnames and requires every resolved address to be globally routable
- validates redirects individually
- limits redirect count
- limits response bytes
- validates the final URL again

This does not eliminate DNS-rebinding or infrastructure-level egress risk. A production deployment should use network-level controls and, for high-assurance environments, an HTTP client that connects to a validated destination address.

## AI threat model

The model is an untrusted analyzer, not an authority. The prompt explicitly separates evidence from inference, but the application still normalizes and constrains the returned result. Confidence is allowed to be low. The UI presents official verification channels for consequential claims.

## Privacy model

SATARK stores history in Streamlit session state only. It does not intentionally persist submitted source files/content to disk. The configured provider may receive the prepared evidence during analysis. Users should avoid secrets and regulated data unless their deployment and provider agreements explicitly allow it.

## Production checklist

- Run all CI workflows successfully on the exact deployment commit.
- Review outbound egress controls.
- Use a secret manager for the Groq API key.
- Restrict access/authentication when the application is not intended to be public.
- Monitor provider errors, latency, rate limits, and resource consumption.
- Verify the deployed browser smoke suite and manually inspect representative devices.
- Maintain dependency updates, review provider advisories, and keep rollback procedures.
