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
- rejects URL credentials and local hostnames
- resolves hostnames and requires every answer to be globally routable
- connects to an IP address from that validated resolution rather than letting the HTTP client resolve the hostname again
- preserves the original hostname for HTTPS certificate validation and SNI
- validates every redirect independently, limits redirect count, and blocks HTTPS-to-HTTP downgrade redirects
- limits response bytes and rejects unsupported content types

The DNS-validation-to-connection gap is mitigated by pinning the TCP connection to the selected validated IP. This is not a substitute for infrastructure egress controls: deploy with network-level restrictions that prevent access to cloud metadata services and internal networks, and retest the behavior in the actual hosting environment.

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
