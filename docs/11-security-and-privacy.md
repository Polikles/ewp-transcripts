# Security and Privacy

This is a technical contract, not a complete user-facing privacy policy or a completed security
assessment. The owner-requested [review plan](SECURITY_REVIEW_PLAN.md) requires a general local
English report first, owner approval before publication, then framework applicability/mapping.
PRIV-01 tracks the missing consolidated policy. Requirements below must be checked against code;
they are not blanket assurance that every control works in all environments.

## 1. Threat model

The application may process unpublished podcasts, training recordings, and personal data. Primary risks include:

- accidental upload to an external service;
- exposure of Hugging Face/OpenRouter/API credentials in memory, environment, IPC or OS stores;
- leaving audio in temporary directories;
- overwriting results;
- writing full transcript text to logs;
- following symbolic links outside the intended input directory;
- concurrent writes to the same result.

## 2. Requirements

- the MVP pipeline runs locally;
- transcription performs no network requests in offline mode;
- no telemetry;
- HF model setup accepts a deliberately supplied transient token through the installer/setup
  environment; normal complete offline snapshots require no token. Review all transport/error paths;
- GUI OpenRouter session keys may be deliberately saved/read/deleted in the OS credential store
  (Windows Credential Manager/Linux Secret Service), with no plaintext fallback; inherited
  environment keys remain a separate source. See [current key behavior](gui/settings.md);
- secrets MUST NOT be serialized into workspaces/profiles/results/logs/reports. Transport to the
  intended provider is a separate authorized boundary, not permission to persist the key elsewhere;
- default logs do not contain transcript content;
- the work directory is private to the current user;
- symbolic links are not followed by default;
- final files are never overwritten;
- temporary files preserved after failure are reported to the user and can be removed explicitly.

## 3. Network use

Explicit network operations and modes must be distinguished:

- explicit model downloads;
- installation/runtime dependency downloads and user-triggered connection/provider checks;
- explicitly selected cloud ASR audio transfer, or correction/translation text transfer, with
  separate scoped consent and offline enforcement. A key check is not upload consent;
- future update checks only with consent and outside the MVP.

`transcribe` in offline mode should configure libraries so that missing models cannot be downloaded implicitly.

### Implemented provider boundaries

Cloud LLM/API use is never an offline operation. It must be explicitly selected and must
show a clear data-transfer warning before transcript content leaves the machine. In an
interactive session the choices are: reject and continue without the cloud operation,
accept once, or accept persistently. Persistent consent is scoped to the exact provider,
endpoint, operation class, and warning-policy version; changing any of them prompts
again. Non-interactive correction/translation uses the documented explicit consent mechanism.
GUI audio/text confirmations and restored workspace/profile state have their own scoped behavior;
never infer consent merely from loading work, finding a key or an earlier CLI consent record.

A loopback/local LLM API is preferable for privacy but is still a separate process and
API boundary. The application cannot guarantee what that server logs, retains, or
forwards. Local API use therefore displays a distinct warning with the same reject,
accept-once, and scoped persistent-consent choices. Documentation must not call a local
API bulletproof or equate it with an in-process offline model.

LM Studio's developer log may display complete request and response bodies, including
full transcript chunks. Those logs are private transcript artifacts: do not expose them
on shared infrastructure, do not include them in ordinary benchmark evidence, and apply
an explicit local retention/deletion policy. Hosting the API on the same private machine
reduces exposure but does not change this logging behavior.

Loopback is the default LM Studio boundary. A non-loopback LAN/VPN/Tailscale-like server
requires a dedicated configuration or CLI opt-in and an additional network-transfer
warning. Plain HTTP may rely on protection supplied by the underlying private overlay;
the application does not verify that protection. Persistent consent remains scoped to
the exact endpoint identity, and a changed address prompts again.

Strict offline mode blocks cloud endpoints. Secrets and consent records must never be
written to canonical results, logs, audits, or revision content. Revision provenance may
record provider/model/endpoint kind and a non-secret endpoint identity.

## 4. Paths in JSON

`results.json` stores source paths for reproducibility. Paths may themselves be sensitive, and user documentation must state this clearly.

A future publication/redaction mode may remove or pseudonymize paths from shared copies, but the canonical local MVP result retains them.

## 5. Supply chain

- installation from a lockfile;
- preference for official sources;
- no automatic prerelease use;
- local vulnerability scanning as part of the release gate;
- dependency upgrades in dedicated pull requests with audio-quality regression tests;
- backend versions recorded in every result.

Early public releases may be unsigned under [release policy](RELEASE_POLICY.md). Production build
attestations are prioritized but not implemented by this documentation task; they establish
verifiable provenance, not a Windows trusted signature or an absence of vulnerabilities.

## 6. Policy and review gaps

The consolidated user policy must explain actual data locations/content, retention/deletion after
success/failure/crash/uninstall, local plaintext files and OS protections, source-path metadata,
optional external transfers/provider responsibility, installation traffic, consent/credential
controls and project contact. Do not invent encryption, deletion guarantees or third-party retention.
SEC-01 verifies these mechanisms at code/process/OS/network/supply-chain levels and records threats,
tradeoffs and residual risk. Reports remain LOCAL/EN until the owner approves publication.
