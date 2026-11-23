using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace EwP.Setup;

record InstallationInfo(string Root, JsonElement? State)
{
    public string Version => State?.GetProperty("version").GetString() ?? "";
    public bool LocalModels => State is JsonElement s && s.TryGetProperty("local_models", out var local) && local.ValueKind == JsonValueKind.True;
}

static class InstallationDiscovery
{
    internal static string DefaultRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "EwPTranscripts");

    internal static InstallationInfo? Find(string? preferred = null, bool includePartial = false)
    {
        var candidates = new List<string>();
        if (!string.IsNullOrWhiteSpace(preferred)) candidates.Add(preferred);
        foreach (var hive in new[] { RegistryHive.CurrentUser, RegistryHive.LocalMachine })
            foreach (var view in new[] { RegistryView.Registry64, RegistryView.Registry32 })
                try
                {
                    using var registry = RegistryKey.OpenBaseKey(hive, view);
                    using var key = registry.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts");
                    if (key?.GetValue("InstallLocation") is string root) candidates.Add(root);
                }
                catch (Exception e) when (e is IOException or System.Security.SecurityException or UnauthorizedAccessException) { }
        candidates.Add(DefaultRoot);
        foreach (var programs in new[] { Environment.SpecialFolder.ProgramFiles, Environment.SpecialFolder.ProgramFilesX86 })
        {
            string parent = Environment.GetFolderPath(programs);
            if (parent.Length > 0) candidates.Add(Path.Combine(parent, "EwPTranscripts"));
        }
        return FindIn(candidates, includePartial);
    }

    internal static InstallationInfo? FindIn(IEnumerable<string> candidates, bool includePartial)
    {
        foreach (string root in candidates.Distinct(StringComparer.OrdinalIgnoreCase))
        {
            var info = Read(root);
            if (info != null && (includePartial || info.State != null)) return info;
        }
        return null;
    }

    internal static InstallationInfo? Read(string root)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(root)) return null;
            root = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
            using var owner = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "owner.json")));
            if (owner.RootElement.GetProperty("kind").GetString() != "ewp-transcripts-managed-v1" ||
                !SameRoot(owner.RootElement.GetProperty("root").GetString(), root)) return null;
            JsonElement? state = null;
            string file = Path.Combine(root, "installation.json");
            if (File.Exists(file))
            {
                using var document = JsonDocument.Parse(File.ReadAllText(file)); var value = document.RootElement;
                if (value.GetProperty("kind").GetString() != "ewp-transcripts-managed-v1" ||
                    !SameRoot(value.GetProperty("root").GetString(), root) ||
                    !System.Version.TryParse(value.GetProperty("version").GetString(), out _) ||
                    !Regex.IsMatch(value.GetProperty("active").GetString() ?? "", @"^versions[/\\][a-zA-Z0-9.\-]+$")) return null;
                state = value.Clone();
            }
            return new(root, state);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException or JsonException or KeyNotFoundException or InvalidOperationException or System.Security.SecurityException) { return null; }
    }

    static bool SameRoot(string? left, string right) => left != null && string.Equals(Path.GetFullPath(left).TrimEnd(Path.DirectorySeparatorChar), right, StringComparison.OrdinalIgnoreCase);
}
