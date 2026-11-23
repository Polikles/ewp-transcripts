using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using Microsoft.Win32.SafeHandles;

namespace EwP.Setup;

sealed record OperationRequest(string Operation, string Root, bool Confirm, bool Local, bool Terms,
    bool RemoveModels, bool RemoveKey, string HfToken, string OpenRouterKey, string WizardSource,
    int WizardPid, string CancelFile);

static class OperationRunner
{
    internal static bool Mutates(OperationRequest request) => request.Operation is "install" or "update" or "repair" or "rollback" || request.Operation == "uninstall" && request.Confirm;

    internal static bool NeedsElevation(OperationRequest request)
    {
        if (!Mutates(request)) return false;
        return !CanWrite(request.Root);
    }

    static bool CanWrite(string root)
    {
        string? probe = null; bool directory = false;
        try
        {
            string path = Path.GetFullPath(root);
            if (Directory.Exists(path))
            {
                probe = Path.Combine(path, ".ewp-write-probe-" + Guid.NewGuid().ToString("N"));
                using var file = new FileStream(probe, FileMode.CreateNew, FileAccess.Write, FileShare.None, 1, FileOptions.DeleteOnClose);
            }
            else
            {
                while (!Directory.Exists(path)) path = Path.GetDirectoryName(path) ?? throw new IOException();
                probe = Path.Combine(path, ".ewp-write-probe-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(probe); directory = true;
                using var file = File.Create(Path.Combine(probe, "write"));
            }
            return true;
        }
        catch (UnauthorizedAccessException) { return false; }
        catch (System.Security.SecurityException) { return false; }
        finally
        {
            if (probe != null) try { if (directory) Directory.Delete(probe, true); else File.Delete(probe); } catch { }
        }
    }

    internal static bool IsNormallyProtected(string root)
    {
        try
        {
            string path = Path.GetFullPath(root).TrimEnd('\\') + "\\";
            return new[] { Environment.SpecialFolder.ProgramFiles, Environment.SpecialFolder.ProgramFilesX86, Environment.SpecialFolder.Windows }
                .Select(Environment.GetFolderPath).Where(p => p.Length > 0).Any(p => path.StartsWith(p.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase));
        }
        catch { return false; }
    }

    internal static async Task<int> Run(OperationRequest request, string payload, string bundle, string runtime,
        Func<string, Task> output)
    {
        var info = new ProcessStartInfo("powershell.exe")
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            RedirectStandardInput = true
        };
        foreach (string argument in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", Path.Combine(payload, "control/Install-EwP.ps1"),
            "-Action", request.Operation, "-Root", request.Root, "-Bundle", bundle, "-SecretsStdin", "-CancelFile", request.CancelFile }) info.ArgumentList.Add(argument);
        if (request.Confirm || request.Operation == "check") info.ArgumentList.Add("-Yes");
        info.ArgumentList.Add(request.Local ? "-Local" : "-CloudOnly");
        if (request.Terms) info.ArgumentList.Add("-AcceptModelTerms");
        if (request.RemoveModels && request.Operation == "uninstall") info.ArgumentList.Add("-RemoveModels");
        if (request.RemoveKey && request.Operation == "uninstall") info.ArgumentList.Add("-RemoveKey");
        foreach (string name in new[] { "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE", "VIRTUAL_ENV", "CONDA_PREFIX", "UV_CONFIG_FILE", "UV_INDEX_URL", "UV_EXTRA_INDEX_URL", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL" }) info.Environment.Remove(name);
        info.Environment["PYTHONNOUSERSITE"] = "1";
        info.Environment["UV_PYTHON_PREFERENCE"] = "only-managed";
        info.Environment["EWP_BOOTSTRAP_RUNTIME"] = runtime;
        using var process = new Process { StartInfo = info }; process.Start();
        try
        {
            await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new
            {
                hf_token = request.HfToken,
                openrouter_key = request.OpenRouterKey,
                wizard_source = request.WizardSource,
                wizard_pid = request.WizardPid
            })); process.StandardInput.Close();
            async Task Read(StreamReader stream)
            {
                while (await stream.ReadLineAsync() is string line) await output(Redact(line, request));
            }
            await Task.WhenAll(Read(process.StandardOutput), Read(process.StandardError));
            await process.WaitForExitAsync(); return process.ExitCode;
        }
        catch
        {
            if (!process.HasExited) { process.Kill(entireProcessTree: true); await process.WaitForExitAsync(); }
            throw;
        }
    }

    static string Redact(string line, OperationRequest request)
    {
        if (request.HfToken.Length > 0) line = line.Replace(request.HfToken, "[redacted]");
        if (request.OpenRouterKey.Length > 0) line = line.Replace(request.OpenRouterKey, "[redacted]");
        return line;
    }

    internal static async Task<int> Elevated(OperationRequest request, Func<string, Task> output, bool test = false)
    {
        string name = "ewp-setup-" + Guid.NewGuid().ToString("N");
        var sid = WindowsIdentity.GetCurrent().User ?? throw new UnauthorizedAccessException();
        var security = new PipeSecurity(); security.SetOwner(sid); security.SetAccessRuleProtection(true, false);
        security.AddAccessRule(new PipeAccessRule(sid, PipeAccessRights.FullControl, AccessControlType.Allow));
        // CurrentUserOnly also compares elevation level and cannot bridge a legitimate UAC change.
        // Use an explicit same-SID ACL and authenticate kernel-reported peer PIDs instead.
        using var pipe = NamedPipeServerStreamAcl.Create(name, PipeDirection.InOut, 1, PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.FirstPipeInstance, 4096, 4096, security);
        var start = new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), @"WindowsPowerShell\v1.0\powershell.exe"))
        { UseShellExecute = !test, Verb = test ? "" : "runas", WindowStyle = ProcessWindowStyle.Hidden, CreateNoWindow = test };
        foreach (string argument in new[] { "-NoProfile", "-NonInteractive", "-EncodedCommand", Convert.ToBase64String(Encoding.Unicode.GetBytes(ElevationBootstrap(name, Environment.ProcessId, test))) }) start.ArgumentList.Add(argument);
        Process? worker;
        try { worker = await Task.Run(() => Process.Start(start)); }
        catch (Win32Exception e) when (e.NativeErrorCode == 1223)
        {
            await output("{\"stage\":\"error\",\"message\":\"INSTALL_ADMIN_CANCELLED: Administrator permission was not granted\"}"); return 2;
        }
        using (worker)
        {
            if (worker == null) throw new IOException("Cannot start elevated operation");
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(45));
            try
            {
                var connection = pipe.WaitForConnectionAsync(timeout.Token);
                var exit = worker.WaitForExitAsync(timeout.Token);
                if (await Task.WhenAny(connection, exit) == exit && !pipe.IsConnected) throw new IOException("Elevated bootstrap exited before authentication");
                await connection;
            }
            catch (OperationCanceledException)
            {
                await output("{\"stage\":\"error\",\"message\":\"INSTALL_ADMIN_ACCOUNT_MISMATCH: Use the same Windows account for elevation or choose a writable folder\"}"); return 2;
            }
            if (!GetNamedPipeClientProcessId(pipe.SafePipeHandle, out uint client) || !TrustedWorker(client, worker.Id)) throw new UnauthorizedAccessException("Unexpected installer worker");
            using var reader = new StreamReader(pipe, new UTF8Encoding(false), false, 4096, true);
            using var writer = new StreamWriter(pipe, new UTF8Encoding(false), 4096, true) { AutoFlush = true };
            string? hello = await reader.ReadLineAsync(timeout.Token);
            if (hello != sid.Value) throw new UnauthorizedAccessException("Installer elevation changed the Windows account");
            await writer.WriteLineAsync(JsonSerializer.Serialize(request));
            while (await reader.ReadLineAsync() is string line)
            {
                if (line.StartsWith("EWP_EXIT:", StringComparison.Ordinal))
                {
                    int code = int.Parse(line[9..]); await worker.WaitForExitAsync(); return code;
                }
                await output(Redact(line, request));
            }
            throw new IOException("Elevated operation ended without a result");
        }
    }

    static string ElevationBootstrap(string pipe, int parent, bool test)
    {
        string exe = "'" + Environment.ProcessPath!.Replace("'", "''") + "'";
        string arguments = "--elevated-operation --pipe " + pipe + " --parent " + parent + (test ? " --broker-self-test" : "");
        // Native single-file DLLs must also extract under an admin-only directory before CLR starts.
        return $$"""
        $ErrorActionPreference='Stop'
        $dir=Join-Path ([Environment]::GetFolderPath('CommonProgramFiles')) ('EwP-elevated-'+[Guid]::NewGuid().ToString('N'))
        $acl=[Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true,$false)
        $admin=[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
        $system=[Security.Principal.SecurityIdentifier]::new('S-1-5-18')
        $acl.SetOwner($admin)
        foreach($sid in @($admin,$system)){
          $rule=[Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
          $acl.AddAccessRule($rule)
        }
        [IO.Directory]::CreateDirectory($dir,$acl)|Out-Null
        try {
          $start=New-Object Diagnostics.ProcessStartInfo
          $start.FileName={{exe}}
          $start.Arguments='{{arguments}}'
          $start.UseShellExecute=$false
          $start.EnvironmentVariables['DOTNET_BUNDLE_EXTRACT_BASE_DIR']=$dir
          $p=[Diagnostics.Process]::Start($start)
          $p.WaitForExit()
          $code=$p.ExitCode
        } finally { [IO.Directory]::Delete($dir,$true) }
        exit $code
        """;
    }

    static bool TrustedWorker(uint pid, int parent)
    {
        using var snapshot = new SafeFileHandle(CreateToolhelp32Snapshot(2, 0), true);
        if (snapshot.IsInvalid) return false;
        var entry = new ProcessEntry { Size = (uint)Marshal.SizeOf<ProcessEntry>(), Executable = "" };
        bool found = false;
        if (Process32First(snapshot, ref entry)) do
        {
            if (entry.Pid == pid) { found = entry.Parent == parent; break; }
        } while (Process32Next(snapshot, ref entry));
        if (!found) return false;
        using var process = new SafeFileHandle(OpenProcess(0x1000, false, pid), true);
        if (process.IsInvalid) return false;
        var path = new StringBuilder(32768); uint size = (uint)path.Capacity;
        return QueryFullProcessImageName(process, 0, path, ref size) &&
            string.Equals(Path.GetFullPath(path.ToString()), Path.GetFullPath(Environment.ProcessPath!), StringComparison.OrdinalIgnoreCase);
    }

    internal static async Task<int> WorkerMain(string pipeName, int parent, bool test)
    {
        string? temporary = null;
        try
        {
            using var pipe = new NamedPipeClientStream(".", pipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(40)); await pipe.ConnectAsync(timeout.Token);
            if (!GetNamedPipeServerProcessId(pipe.SafePipeHandle, out uint server) || server != parent) throw new UnauthorizedAccessException();
            using var reader = new StreamReader(pipe, new UTF8Encoding(false), false, 4096, true);
            using var writer = new StreamWriter(pipe, new UTF8Encoding(false), 4096, true) { AutoFlush = true };
            await writer.WriteLineAsync(WindowsIdentity.GetCurrent().User!.Value);
            string json = await reader.ReadLineAsync(timeout.Token) ?? throw new IOException();
            if (json.Length > 65536) throw new InvalidDataException();
            var request = JsonSerializer.Deserialize<OperationRequest>(json) ?? throw new InvalidDataException();
            if (test)
            {
                if (request.Operation != "broker-self-test") throw new InvalidDataException();
                await writer.WriteLineAsync("{\"stage\":\"test\",\"message\":\"Authenticated same-user worker\"}");
                await writer.WriteLineAsync("EWP_EXIT:0"); return 0;
            }
            if (!new[] { "install", "update", "repair", "rollback", "uninstall" }.Contains(request.Operation) ||
                request.WizardPid != parent || !string.Equals(request.WizardSource, Environment.ProcessPath, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException();
            // Elevated code and dependencies live below a protected OS folder, never a user-writable payload.
            string parentDirectory = Environment.GetFolderPath(Environment.SpecialFolder.CommonProgramFiles);
            temporary = Path.Combine(parentDirectory, "EwP-setup-" + Guid.NewGuid().ToString("N"));
            var admin = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null);
            var system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
            var acl = new DirectorySecurity(); acl.SetOwner(admin); acl.SetAccessRuleProtection(true, false);
            foreach (var identity in new[] { admin, system }) acl.AddAccessRule(new FileSystemAccessRule(identity, FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
            new DirectoryInfo(temporary).Create(acl);
            string bundle = Path.Combine(temporary, "bundle.zip");
            using (var source = typeof(OperationRunner).Assembly.GetManifestResourceStream("bundle.zip")!)
            using (var target = File.Create(bundle)) await source.CopyToAsync(target);
            Wizard.VerifyBundle(bundle);
            string payload = Path.Combine(temporary, "payload"); System.IO.Compression.ZipFile.ExtractToDirectory(bundle, payload);
            using var writing = new SemaphoreSlim(1, 1);
            async Task Send(string line)
            {
                await writing.WaitAsync();
                try { await writer.WriteLineAsync(line); }
                finally { writing.Release(); }
            }
            int result = await Run(request, payload, bundle, Path.Combine(temporary, "runtime"), Send);
            await writer.WriteLineAsync("EWP_EXIT:" + result); return result;
        }
        catch { return 2; }
        finally { if (temporary != null) try { Directory.Delete(temporary, true); } catch { } }
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct ProcessEntry
    {
        public uint Size, Usage, Pid;
        public IntPtr Heap;
        public uint Module, Threads, Parent;
        public int Priority;
        public uint Flags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string Executable;
    }
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
    [DllImport("kernel32.dll", EntryPoint = "Process32FirstW", CharSet = CharSet.Unicode)] static extern bool Process32First(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", EntryPoint = "Process32NextW", CharSet = CharSet.Unicode)] static extern bool Process32Next(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", EntryPoint = "QueryFullProcessImageNameW", CharSet = CharSet.Unicode)] static extern bool QueryFullProcessImageName(SafeFileHandle process, uint flags, StringBuilder name, ref uint size);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetNamedPipeClientProcessId(SafePipeHandle pipe, out uint pid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetNamedPipeServerProcessId(SafePipeHandle pipe, out uint pid);
}
