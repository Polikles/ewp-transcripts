using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;

namespace EwP.Setup;

sealed partial class Wizard
{
    internal Func<string?, bool, InstallationInfo?> FindInstallation = InstallationDiscovery.Find;
    readonly List<RadioButton> actionChoices = [];
    string? preferredMaintenanceRoot;
    InstallationInfo? detected;
    bool manualLocation, resettingOperation, hostAttempted;
    int stateEpoch;

    void SelectOperation(string value, bool focusChoice = false)
    {
        if (busy || !operations.Contains(value)) return;
        resettingOperation = true;
        try
        {
            locationChange?.Cancel(); stateEpoch++;
            operation = value; page = 0; notice = progressStage = "";
            host = installed = removal = null;
            hostReady = hostAttempted = previewReady = finished = successful = false;
            hfSecret = orSecret = ""; hfValid = orValid = false;
            terms.IsChecked = removeModels.IsChecked = removeKey.IsChecked = false;
            log.Clear(); File.Delete(CancelFile);
            detected = value == "install" ? null : FindInstallation(preferredMaintenanceRoot, value == "uninstall");
            manualLocation = detected == null;
            root.Text = value == "install" ? InstallationDiscovery.DefaultRoot : detected?.Root ?? "";
            installed = detected?.State;
            local.IsChecked = value == "models" || (value == "install" || detected?.LocalModels == true);
        }
        finally { resettingOperation = false; }
        Render();
        if (focusChoice) Dispatcher.BeginInvoke(DispatcherPriority.Input, new Action(() => actionChoices.FirstOrDefault(c => c.Tag?.ToString() == value)?.Focus()));
    }

    void RenderSteps()
    {
        steps.Children.Clear();
        string[] names = [T("Action", "Działanie"), T("Location and checks", "Lokalizacja i test"),
            IsInstall ? T("Models and keys", "Modele i klucze") : T("Confirm", "Potwierdzenie"),
            IsInstall && !finished ? T("Installation", "Instalacja") : T("Result", "Wynik")];
        for (int i = 0; i < names.Length; i++)
        {
            bool current = page == i;
            steps.Children.Add(new Border
            {
                Background = current ? ColorBrush("#355880") : Brushes.Transparent,
                CornerRadius = new CornerRadius(14),
                Padding = new Thickness(10, 5, 10, 5),
                Margin = new Thickness(0, 0, 5, 0),
                Child = new TextBlock { Text = $"{i + 1}. {names[i]}", Foreground = current ? Brushes.White : Muted, FontSize = 12, VerticalAlignment = VerticalAlignment.Center }
            });
        }
    }

    static string InstallFolderFromPicker(string folder)
    {
        string path = Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar);
        bool container = path == Path.GetPathRoot(folder)?.TrimEnd(Path.DirectorySeparatorChar) ||
            new[] { Environment.SpecialFolder.ProgramFiles, Environment.SpecialFolder.ProgramFilesX86 }
                .Select(Environment.GetFolderPath).Any(p => p.Length > 0 && string.Equals(p.TrimEnd(Path.DirectorySeparatorChar), path, StringComparison.OrdinalIgnoreCase));
        return container ? Path.Combine(folder, "EwPTranscripts") : folder;
    }

    bool ShowVcHelp => hostAttempted && (host is not JsonElement result ||
        !result.GetProperty("checks").EnumerateArray().Any(c => c.GetProperty("code").GetString() == "vc_runtime" && c.GetProperty("status").GetString() == "pass"));

    void RenderDetectedLocation()
    {
        body.Children.Add(Copy(T("Detected installation", "Wykryta instalacja"), muted: true));
        var info = new StackPanel();
        info.Children.Add(new TextBlock { Text = detected?.Version.Length > 0 ? "EwP Transcripts " + detected.Version : "EwP Transcripts", FontSize = 16, FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 0, 0, 6) });
        info.Children.Add(new TextBlock { Text = root.Text, TextWrapping = TextWrapping.Wrap, Foreground = Muted, FontSize = 13 });
        body.Children.Add(Card(info));
        body.Children.Add(Link(T("Choose another installation…", "Wybierz inną instalację…"), () => { manualLocation = true; Render(); }));
    }
}
