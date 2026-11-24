using System.IO;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Windows.Controls;

namespace EwP.Setup;

sealed partial class Wizard
{
    string? rollbackTarget;
    sealed record RollbackChoice(string Release, string Version)
    {
        public override string ToString() => "EwP Transcripts " + Version;
    }
    List<RollbackChoice> RollbackChoices()
    {
        var choices = new List<RollbackChoice>();
        if (installed is not JsonElement state || !Version.TryParse(state.GetProperty("version").GetString(), out var current)) return choices;
        try
        {
            using var owner = JsonDocument.Parse(File.ReadAllText(Path.Combine(root.Text, "owner.json")));
            foreach (var item in owner.RootElement.GetProperty("releases").EnumerateArray())
            {
                string release = item.GetString()!;
                if (!Regex.IsMatch(release, @"^versions[\\/][a-zA-Z0-9.\-]+$")) continue;
                string path = Path.Combine(root.Text, release);
                if (!Directory.Exists(path) || (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) continue;
                if (!File.Exists(Path.Combine(path, "app/.venv/Scripts/python.exe"))) continue;
                using var bundle = JsonDocument.Parse(File.ReadAllText(Path.Combine(path, "bundle.json")));
                string version = bundle.RootElement.GetProperty("version").GetString()!;
                if (Version.TryParse(version, out var candidate) && candidate < current) choices.Add(new(release, version));
            }
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException or KeyNotFoundException) { }
        return choices.OrderByDescending(c => Version.Parse(c.Version)).DistinctBy(c => c.Version).ToList();
    }
    void RenderRollbackChoices()
    {
        var choices = RollbackChoices();
        if (!choices.Any(c => c.Release == rollbackTarget)) rollbackTarget = choices.FirstOrDefault()?.Release;
        if (choices.Count == 0) return;
        body.Children.Add(Copy(T("Restore program version:", "Przywróć wersję programu:")));
        if (choices.Count == 1) body.Children.Add(Copy(choices[0].ToString()));
        else
        {
            var select = new ComboBox { ItemsSource = choices, SelectedItem = choices.First(c => c.Release == rollbackTarget), Padding = new System.Windows.Thickness(8) };
            select.SelectionChanged += (_, _) => { rollbackTarget = (select.SelectedItem as RollbackChoice)?.Release; RefreshNavigation(); };
            body.Children.Add(select);
        }
    }
}
