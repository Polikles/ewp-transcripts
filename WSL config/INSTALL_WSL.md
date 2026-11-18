# Install WSL2 and Ubuntu 24.04 / 26.04

Skip installation when an existing environment passes [`VERIFY_ENVIRONMENT.md`](VERIFY_ENVIRONMENT.md).

## 1. Inspect the host

Run in PowerShell:

```powershell
wsl --status
wsl --version
wsl --list --verbose
wsl --list --online
```

The EWP-transcripts distribution must show version `2`. Record the exact distribution name printed by `wsl --list --verbose`.

## 2. Install or update WSL

Run PowerShell as Administrator:

```powershell
wsl --install
wsl --update
```

Restart Windows if requested. Microsoft documents `wsl --install` as the standard command for supported Windows versions.

## 3. Install Ubuntu 24.04 or 26.04

Use the exact Ubuntu 24.04 or 26.04 distribution identifier shown by `wsl --list --online`:

```powershell
wsl --install --distribution <Ubuntu-24.04-identifier>
```

The example above uses 24.04; choose the listed 26.04 identifier when installing that accepted baseline. Keep an existing working distribution when updating the GUI.

The identifier is intentionally not hardcoded because Microsoft Store distribution names can vary. On first launch, create the normal non-root Linux user requested by Ubuntu.

## 4. Confirm WSL2

```powershell
wsl --list --verbose
```

If the distribution is version 1:

```powershell
wsl --set-version <distribution-name> 2
```

## 5. Verify Ubuntu

Run inside the Ubuntu terminal:

```bash
cat /etc/os-release
uname -r
```

Expected: Ubuntu 24.04 LTS or 26.04 LTS and a WSL2 kernel. Continue with [`INSTALL_TOOLS.md`](INSTALL_TOOLS.md).

Source: [Microsoft — Install WSL](https://learn.microsoft.com/windows/wsl/install).
