using System.IO;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace EwP.Desktop;

sealed record AppConfig(string Root, string Python, string WorkingDirectory, string StateDirectory, string InstanceKey)
{
    public const string Origin = "http://127.0.0.1:8765";
    public static AppConfig Load(string root)
    {
        root = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        using var owner = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "owner.json")));
        using var document = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "installation.json")));
        var state = document.RootElement;
        foreach (var value in new[] { owner.RootElement, state })
            if (value.GetProperty("kind").GetString() != "ewp-transcripts-managed-v1" || !string.Equals(Path.GetFullPath(value.GetProperty("root").GetString()!), root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Invalid installation identity");
        string active = state.GetProperty("active").GetString()!;
        if (!Regex.IsMatch(active, @"^versions[/\\][a-zA-Z0-9.\-]+$")) throw new InvalidDataException("Invalid active version");
        string work = Path.Combine(root, active, "app");
        if (!File.Exists(Path.Combine(root, active, "control", "EwP.Transcripts.exe"))) throw new InvalidDataException("This retained version uses browser mode; use its registered shortcut");
        string python = Path.Combine(work, ".venv", "Scripts", "python.exe");
        if (!File.Exists(python) || !File.Exists(Path.Combine(root, "manager.py"))) throw new FileNotFoundException("Installed runtime is unavailable");
        string key = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(root.ToUpperInvariant() + "|" + WindowsIdentity.GetCurrent().User!.Value)));
        string data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "EwPTranscriptsState", "desktop", key);
        Directory.CreateDirectory(data);
        return new(root, python, work, data, key);
    }
    public static bool IsLocal(string uri) => Uri.TryCreate(uri, UriKind.Absolute, out var value) && value.Scheme == "http" && value.Host == "127.0.0.1" && value.Port == 8765 && value.UserInfo.Length == 0;
    public static bool IsDocument(string uri) => IsLocal(uri) && new Uri(uri).AbsolutePath == "/";
    public static bool IsResource(string uri) => IsLocal(uri) || uri.StartsWith("blob:" + Origin + "/", StringComparison.Ordinal);
}
