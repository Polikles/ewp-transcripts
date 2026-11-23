# Hugging Face access for local models

The installer needs a **read token**, not your account password, to download the pinned
`pyannote/speaker-diarization-community-1` model. A token does not replace model access approval.
If you choose OpenRouter/review without local models, skip this step.

1. [Create a Hugging Face account](https://huggingface.co/join), confirm your email and sign in.
2. Open the [pyannote model page](https://huggingface.co/pyannote/speaker-diarization-community-1).
   Complete its access form and accept the conditions. Wait for access if the page requires approval.
3. In your account, open **Settings → Access Tokens** or the [token settings page](https://huggingface.co/settings/tokens).
4. Choose **Create new token**, select **Read** access, give it a recognizable name and create it.
   Copy the token privately. Write access is unnecessary. For a fine-grained token, explicitly
   allow reading this gated repository; the ordinary Read token is the simpler option.
5. In the installer, choose **Enter Hugging Face token**, paste it into the masked field and wait
   for its automatic check. **Check token** repeats the check. **OK** accepts only a valid result.
6. The dialog closes and the main page shows **Token valid**. Then acknowledge **I accepted
   pyannote terms on Hugging Face**. This acknowledgment does not submit the upstream access form.

The check reads the model-access endpoint; it sends no recordings/transcript. The token is kept
only in the installer's transient memory and supplied to the explicit model-download child.
It is not saved in a profile, JSON report, command argument or plaintext config. Closing/cancelling
clears the installer fields; the installer does not log into your HF account persistently.

- `HF_HTTP_401`: check that you copied the token itself and that it has not expired or been revoked.
- `HF_HTTP_403`: sign into the same account, accept model conditions and verify token read access.
- `HF_CONNECTION_FAILED`: check the network/proxy and retry; do not disable certificate checks.

Do not paste tokens into support messages, screenshots or reports. You can revoke a temporary token
in HF settings after the model download. Existing complete pinned files are reused; the graphical
installer still verifies access before enabling its terms acknowledgment. Terminal maintenance can
reuse complete caches without a fresh token, as described in [installation](../docs/gui/installation.md).

Official references: [HF tokens](https://huggingface.co/docs/hub/security-tokens),
[gated-model access](https://huggingface.co/docs/hub/models-gated).
