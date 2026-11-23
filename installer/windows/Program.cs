using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using System.Reflection;
using System.Diagnostics;
using System.Globalization;
using System.Xml.Linq;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Data;
using Microsoft.Win32;

namespace EwP.Setup;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        var application = new Application();
        bool selfTest = args.Contains("--self-test");
        string? report = null; for (int i = 0; i + 1 < args.Length; i++) if (args[i] == "--self-test-report") report = args[i + 1];
        try { var wizard = new Wizard(args); if (selfTest) { wizard.SelfTest(); wizard.Close(); application.Shutdown(); if (report != null) File.WriteAllText(report, JsonSerializer.Serialize(new { result = "PASS", platform = Environment.OSVersion.ToString(), version = Assembly.GetExecutingAssembly().GetName().Version?.ToString(3), checks = new[] { "embedded bundle integrity", "WPF SVG geometry", "EN/PL labels", "install/update/uninstall controls", "model field scoping", "no worker/network/model invocation" } })); } else application.Run(wizard); } catch (Exception error) { if (selfTest) { Environment.ExitCode = 2; if (report != null) File.WriteAllText(report, JsonSerializer.Serialize(new { result = "FAIL", type = error.GetType().FullName, message = error.Message })); return; } MessageBox.Show("Cannot prepare EwP Setup. Check free temporary disk space and download the complete installer again. / Nie można przygotować instalatora. Sprawdź miejsce na dysku i pobierz go ponownie.", "EwP Setup"); }
    }
}

sealed class Wizard : Window
{
    readonly StackPanel form = new() { Margin = new Thickness(24) };
    readonly TextBox root = new() { MinWidth = 460 };
    readonly TextBox bundle = new() { IsReadOnly = true };
    readonly PasswordBox hf = new(), orKey = new();
    readonly CheckBox local = new(), terms = new(), removeModels = new(), removeKey = new();
    readonly TextBox log = new() { IsReadOnly = true, TextWrapping = TextWrapping.Wrap, AcceptsReturn = true, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Height = 180 };
    readonly TextBlock summary = new() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 8) };
    readonly ComboBox language = new() { ItemsSource = new[] { "English", "Polski" }, SelectedIndex = 1, Width = 100 };
    readonly ComboBox action = new() { Width = 210 };
    string Operation => (action.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "install";
    void SetOperation(string code) { action.SelectedItem = action.Items.Cast<ComboBoxItem>().First(i => i.Tag?.ToString() == code); }
    readonly TextBlock hostResults = new() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 8) };
    readonly Expander details = new() { Margin = new Thickness(0, 8, 0, 8) };
    readonly StackPanel actions = new() { Orientation = Orientation.Horizontal };
    readonly System.Collections.Generic.List<(TextBlock, string, string)> labels = new();
    readonly System.Collections.Generic.List<(Button, string, string)> buttons = new();
    readonly System.Collections.Generic.List<(CheckBox, string, string)> checks = new();
    readonly string temporary = Path.Combine(Path.GetTempPath(), "ewp-setup-" + Guid.NewGuid().ToString("N"));
    readonly string embedded;
    readonly Image gear;
    bool busy = false;
    bool Pl => language.SelectedIndex == 1;
    string T(string en, string pl) => Pl ? pl : en;

    public Wizard(string[] args)
    {
        Title = "EwP Transcripts — Setup " + Assembly.GetExecutingAssembly().GetName().Version?.ToString(3); Width = 820; Height = 970; MinWidth = 640; MinHeight = 720;
        Background = new SolidColorBrush(Color.FromRgb(245, 243, 238)); Foreground = new SolidColorBrush(Color.FromRgb(36, 61, 76));
        FontFamily = new FontFamily("Montserrat, Segoe UI"); FontSize = 14;
        Directory.CreateDirectory(temporary);
        embedded = Path.Combine(temporary, "bundle.zip");
        using (var resource = Assembly.GetExecutingAssembly().GetManifestResourceStream("bundle.zip"))
        {
            if (resource == null) throw new InvalidOperationException("Build contains no application bundle");
            using var target = File.Create(embedded); resource.CopyTo(target);
        }
        // The bundle is embedded in the delivered executable; verify its internal manifest before execution.
        VerifyBundle(embedded);
        ZipFile.ExtractToDirectory(embedded, Path.Combine(temporary, "payload"));
        var shell = new DockPanel(); Content = shell;
        var header = new DockPanel() { Background = new SolidColorBrush(Color.FromRgb(53, 88, 128)), Height = 100 };
        DockPanel.SetDock(header, Dock.Top); shell.Children.Add(header);
        var logo = new Image() { Source = Svg("logo.svg"), Width = 84, Height = 84, Margin = new Thickness(14, 6, 14, 6) }; Icon = Svg("favicon.svg"); header.Children.Add(new Border() { Background = Brushes.White, CornerRadius = new CornerRadius(14), Child = logo, Margin = new Thickness(8) });
        header.Children.Add(new TextBlock() { Text = "EwP Transcripts", FontSize = 29, FontWeight = FontWeights.Bold, Foreground = Brushes.White, VerticalAlignment = VerticalAlignment.Center });
        var scroll = new ScrollViewer() { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Content = form }; shell.Children.Add(scroll);
        using (var existing = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts")) { if (existing?.GetValue("InstallLocation") is string location && File.Exists(Path.Combine(location, "installation.json"))) { root.Text = location; try { using var state = JsonDocument.Parse(File.ReadAllText(Path.Combine(location, "installation.json"))); local.IsChecked = state.RootElement.GetProperty("local_models").GetBoolean(); } catch { } } }
        foreach (var code in new[] { "install", "update", "repair", "rollback", "uninstall" }) action.Items.Add(new ComboBoxItem() { Tag = code }); action.SelectedIndex = 0;
        var choices = new StackPanel() { Orientation = Orientation.Horizontal }; choices.Children.Add(language); choices.Children.Add(action); form.Children.Add(choices);
        Heading("1. Check this computer", "1. Sprawdź komputer");
        Label("Host checks prepare a small private Python installer runtime. No models or audio are sent.", "Testy przygotowują małe prywatne środowisko Python instalatora. Nie wysyłają modeli ani audio.");
        var host = Button("Check host", "Sprawdź komputer", async () => await Work("check")); form.Children.Add(host); form.Children.Add(hostResults);
        form.Children.Add(Button("Microsoft Visual C++ x64 prerequisite", "Wymagany Microsoft Visual C++ x64", () => Open("https://aka.ms/vc14/vc_redist.x64.exe")));
        Heading("2. Installation and version", "2. Instalacja i wersja");
        Label("Installation folder (separate from your recordings)", "Katalog instalacji (osobny od nagrań)");
        if (root.Text.Length == 0) root.Text = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "EwPTranscripts"); form.Children.Add(root);
        form.Children.Add(Button("Choose installation folder…", "Wybierz katalog instalacji…", () => { var d = new OpenFolderDialog(); if (d.ShowDialog() == true) root.Text = d.FolderName; }));
        Label("Selected version bundle", "Wybrana paczka wersji"); bundle.Text = embedded; form.Children.Add(bundle);
        form.Children.Add(Button("Choose another version bundle…", "Wybierz inną paczkę wersji…", () => { var d = new OpenFileDialog() { Filter = "EwP bundle (*.zip)|*.zip" }; if (d.ShowDialog() == true) { bundle.Text = d.FileName; terms.IsChecked = false; } }));
        Heading("3. Models and optional credentials", "3. Modele i opcjonalne klucze");
        Check(local, "Prepare local GPU models (otherwise cloud/review usage)", "Przygotuj modele lokalnego GPU (bez tego: chmura lub weryfikacja)");
        Label("For cloud-only transcription choose OpenRouter as the recording engine in the app.", "Przy transkrypcji bez modeli lokalnych wybierz OpenRouter jako silnik nagrania w programie.");
        Check(terms, "Download selected models; I accepted pyannote model terms on Hugging Face", "Pobierz wybrane modele; zaakceptowałem warunki pyannote w Hugging Face");
        form.Children.Add(Button("Open gated-model terms", "Otwórz warunki modelu", () => Open("https://huggingface.co/pyannote/speaker-diarization-community-1")));
        Label("Hugging Face read token — used only for this model download", "Token odczytu Hugging Face — tylko do tego pobrania modeli"); form.Children.Add(hf);
        Label("Optional OpenRouter key — deliberately saved in the OS credential store", "Opcjonalny klucz OpenRouter — jawnie zapisany w magazynie systemowym"); form.Children.Add(orKey);
        Label("A saved key does not authorize paid calls or audio upload. The app asks for that separately.", "Zapis klucza nie wyraża zgody na płatne wywołania ani wysłanie audio. Program pyta o to osobno.");
        form.Children.Add(Button("Check entered OpenRouter key", "Sprawdź wpisany klucz OpenRouter", async () => await CheckKey()));
        Check(removeModels, "Uninstall: also remove the exact selected model snapshots (shared use!)", "Deinstalacja: usuń też dokładne snapshoty modeli (mogą być współdzielone!)");
        Check(removeKey, "Uninstall: also remove the saved OpenRouter key", "Deinstalacja: usuń też zapisany klucz OpenRouter");
        Heading("4. Run selected operation", "4. Wykonaj wybraną operację");
        gear = new Image() { Source = Svg("gear.svg"), Width = 24, Height = 24, Visibility = Visibility.Collapsed, Margin = new Thickness(0, 0, 12, 0) };
        gear.RenderTransformOrigin = new Point(.5, .5); gear.RenderTransform = new RotateTransform();
        if (SystemParameters.ClientAreaAnimation) ((RotateTransform)gear.RenderTransform).BeginAnimation(RotateTransform.AngleProperty, new DoubleAnimation(0, 360, TimeSpan.FromSeconds(3)) { RepeatBehavior = RepeatBehavior.Forever });
        var gearFrame = new Border() { Background = Brushes.White, CornerRadius = new CornerRadius(20), Padding = new Thickness(6), Margin = new Thickness(8), VerticalAlignment = VerticalAlignment.Center, Child = gear }; gearFrame.SetBinding(UIElement.VisibilityProperty, new Binding("Visibility") { Source = gear }); DockPanel.SetDock(gearFrame, Dock.Right); header.Children.Insert(1, gearFrame);
        actions.Children.Add(Button("Continue", "Kontynuuj", async () => await Work(Operation)));
        actions.Children.Add(Button("Launch installed app", "Uruchom zainstalowany program", () => Launch()));
        form.Children.Add(actions); form.Children.Add(summary); var detailTitle = new TextBlock(); labels.Add((detailTitle, "Technical details / log", "Szczegóły techniczne / dziennik")); details.Header = detailTitle; details.Content = log; form.Children.Add(details);
        var footer = new StackPanel() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        footer.Children.Add(Button("Licenses and artwork", "Licencje i autorstwo", () => Open(Path.Combine(temporary, "payload/app/src/ewp_transcripts/web_assets/brand/NOTICE.txt"))));
        footer.Children.Add(Button("Save report…", "Zapisz raport…", () => { var d = new SaveFileDialog() { Filter = "Text (*.txt)|*.txt", FileName = "EwP-setup-report.txt" }; if (d.ShowDialog() == true) File.WriteAllText(d.FileName, log.Text); }));
        footer.Children.Add(Button("Close", "Zamknij", () => Close())); form.Children.Add(footer);
        language.SelectionChanged += (_, _) => Translate();
        local.Checked += (_, _) => UpdateOptions(); local.Unchecked += (_, _) => UpdateOptions();
        action.SelectionChanged += (_, _) => UpdateOptions();
        for (int i = 0; i < args.Length; i++) { if (args[i] == "--uninstall") SetOperation("uninstall"); if (args[i] == "--root" && i + 1 < args.Length) root.Text = args[++i]; }
        Closing += (_, e) => { if (busy) { e.Cancel = true; MessageBox.Show(T("Wait until this operation finishes.", "Poczekaj na zakończenie operacji.")); } };
        Closed += (_, _) => { try { Directory.Delete(temporary, true); } catch { } };
        Translate(); UpdateOptions();
    }

    public void SelfTest()
    {
        if (gear.Source == null || Icon == null || !Title.Contains(Assembly.GetExecutingAssembly().GetName().Version!.ToString(3))) throw new InvalidDataException();
        language.SelectedIndex = 0; Translate(); if (buttons.Any(b => b.Item1.Content?.ToString() != b.Item2)) throw new InvalidDataException();
        language.SelectedIndex = 1; Translate(); if (buttons.Any(b => b.Item1.Content?.ToString() != b.Item3)) throw new InvalidDataException();
        SetOperation("uninstall"); UpdateOptions(); if (removeModels.Visibility != Visibility.Visible || hf.IsEnabled) throw new InvalidDataException();
        SetOperation("install"); local.IsChecked = true; UpdateOptions(); if (!hf.IsEnabled || removeModels.Visibility != Visibility.Collapsed) throw new InvalidDataException();
        if (hf.Password.Length > 0 || orKey.Password.Length > 0 || busy) throw new InvalidDataException();
    }
    void Heading(string en, string pl) { var text = new TextBlock() { FontSize = 19, FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 20, 0, 8) }; labels.Add((text, en, pl)); form.Children.Add(text); }
    void Label(string en, string pl) { var text = new TextBlock() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 5) }; labels.Add((text, en, pl)); form.Children.Add(text); }
    void Check(CheckBox box, string en, string pl) { box.Content = new TextBlock() { TextWrapping = TextWrapping.Wrap }; box.Margin = new Thickness(0, 8, 0, 5); checks.Add((box, en, pl)); form.Children.Add(box); }
    Button Button(string en, string pl, Action callback) { var b = new Button() { Padding = new Thickness(13, 7, 13, 7), Margin = new Thickness(0, 6, 9, 3), Background = new SolidColorBrush(Color.FromRgb(53, 106, 128)), Foreground = Brushes.White }; b.Click += (_, _) => callback(); buttons.Add((b, en, pl)); return b; }
    void Translate() { foreach (ComboBoxItem item in action.Items) item.Content = item.Tag?.ToString() switch { "install" => T("Install", "Zainstaluj"), "update" => T("Update", "Aktualizuj"), "repair" => T("Repair", "Napraw"), "rollback" => T("Restore previous version", "Przywróć poprzednią wersję"), _ => T("Uninstall", "Odinstaluj") }; foreach (var (text, en, pl) in labels) text.Text = T(en, pl); foreach (var (b, en, pl) in buttons) b.Content = T(en, pl); foreach (var (box, en, pl) in checks) ((TextBlock)box.Content).Text = T(en, pl); }
    void UpdateOptions() { bool deleting = Operation == "uninstall"; removeModels.Visibility = removeKey.Visibility = deleting ? Visibility.Visible : Visibility.Collapsed; terms.IsEnabled = hf.IsEnabled = local.IsChecked == true && !deleting; orKey.IsEnabled = !deleting; }
    void Open(string url) { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
    void Launch() { var path = Path.Combine(root.Text, "EwP.cmd"); if (File.Exists(path)) Process.Start(new ProcessStartInfo(path) { UseShellExecute = true }); else summary.Text = T("Install the application first.", "Najpierw zainstaluj program."); }
    async System.Threading.Tasks.Task CheckKey()
    {
        string key = orKey.Password;
        if (string.IsNullOrWhiteSpace(key)) { summary.Text = T("Enter the optional key first.", "Najpierw wpisz opcjonalny klucz."); return; }
        try { using var client = new System.Net.Http.HttpClient() { Timeout = TimeSpan.FromSeconds(20) }; client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", key); using var response = await client.GetAsync("https://openrouter.ai/api/v1/key"); summary.Text = response.IsSuccessStatusCode ? T("Key and connection work. No audio sent. The key will be saved only when you install.", "Klucz i połączenie działają. Nie wysłano audio. Klucz zostanie zapisany dopiero podczas instalacji.") : T("Key check failed. Check key and network.", "Test klucza nie powiódł się. Sprawdź klucz i sieć."); } catch { summary.Text = T("Cannot check the key; check the connection.", "Nie można sprawdzić klucza; sprawdź połączenie."); }
    }
    async System.Threading.Tasks.Task Work(string operation)
    {
        if (busy) return;
        if (operation == "install" && local.IsChecked == true && terms.IsChecked != true) { summary.Text = T("Confirm model download/terms first.", "Najpierw potwierdź pobranie modeli i ich warunki."); return; }
        bool deleting = operation == "uninstall", closeAfter = false;
        if (deleting && MessageBox.Show(T("Preview the removal plan first? Nothing will be deleted until you confirm the displayed plan.", "Przygotować plan usunięcia? Nic nie zostanie usunięte bez potwierdzenia wyświetlonego planu."), Title, MessageBoxButton.OKCancel) != MessageBoxResult.OK) return;
        summary.Text = T("Preparing installer runtime…", "Przygotowywanie środowiska instalatora…");
        foreach (var control in form.Children.OfType<Control>()) if (control != log) control.IsEnabled = false; action.IsEnabled = language.IsEnabled = false;
        summary.BringIntoView();
        busy = true; gear.Visibility = Visibility.Visible; actions.IsEnabled = false;
        string token = "", key = ""; if (operation is "install" or "update" or "repair") { token = hf.Password; key = orKey.Password; hf.Clear(); orKey.Clear(); }
        try
        {
            VerifyBundle(bundle.Text);
            var result = await Worker(operation, false, token, key);
            if (deleting && result == 0 && MessageBox.Show(T("Remove the listed application files? User recordings/publications remain. Selected model/key removal cannot be undone.", "Usunąć wymienione pliki programu? Nagrania i publikacje pozostaną. Wybrane usunięcie modeli i klucza jest nieodwracalne."), Title, MessageBoxButton.YesNo) == MessageBoxResult.Yes) { result = await Worker(operation, true, "", ""); closeAfter = result == 0; }
            summary.Text = result == 0 ? T("Operation completed. Read the report below.", "Operacja ukończona. Przeczytaj raport poniżej.") : T("Operation needs attention. Read host/dependency details below; the previous active app is preserved on update failure.", "Operacja wymaga uwagi. Przeczytaj szczegóły komputera i zależności poniżej; nieudana aktualizacja zachowuje poprzednią aktywną wersję.");
        }
        catch { summary.Text = T("Cannot complete this operation. Check the selected bundle, location and connection.", "Nie można ukończyć operacji. Sprawdź paczkę, katalog i połączenie."); }
        finally { busy = false; foreach (var control in form.Children.OfType<Control>()) control.IsEnabled = true; action.IsEnabled = language.IsEnabled = true; UpdateOptions(); actions.IsEnabled = true; gear.Visibility = Visibility.Collapsed; if (closeAfter) Close(); }
    }
    async System.Threading.Tasks.Task<int> Worker(string operation, bool confirm, string token, string key)
    {
        string script = Path.Combine(temporary, "payload/control/Install-EwP.ps1");
        var info = new ProcessStartInfo("powershell.exe") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, RedirectStandardInput = true };
        foreach (string a in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Action", operation, "-Root", root.Text, "-Bundle", bundle.Text, "-SecretsStdin" }) info.ArgumentList.Add(a);
        if (operation != "uninstall" || confirm) info.ArgumentList.Add("-Yes");
        if (local.IsChecked == true) info.ArgumentList.Add("-Local"); else info.ArgumentList.Add("-CloudOnly"); if (terms.IsChecked == true) info.ArgumentList.Add("-AcceptModelTerms"); if (removeModels.IsChecked == true) info.ArgumentList.Add("-RemoveModels"); if (removeKey.IsChecked == true) info.ArgumentList.Add("-RemoveKey");
        info.Environment["EWP_BOOTSTRAP_RUNTIME"] = Path.Combine(temporary, "runtime");
        using var process = new Process() { StartInfo = info }; process.Start();
        await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new { hf_token = token, openrouter_key = key, wizard_source = Environment.ProcessPath, wizard_pid = Environment.ProcessId })); process.StandardInput.Close();
        async System.Threading.Tasks.Task Read(StreamReader reader)
        {
            while (await reader.ReadLineAsync() is string line)
            {
                if (token.Length > 0) line = line.Replace(token, "[redacted]"); if (key.Length > 0) line = line.Replace(key, "[redacted]");
                string text = line, stage = "", hostText = "";
                try
                {
                    using var document = JsonDocument.Parse(line); var item = document.RootElement;
                    if (item.TryGetProperty("message", out var message)) text = message.GetString() ?? line;
                    if (item.TryGetProperty("stage", out var phase)) stage = phase.GetString() ?? "";
                    if (item.TryGetProperty("checks", out var rows)) foreach (var row in rows.EnumerateArray()) hostText += HostRow(row) + Environment.NewLine;
                    if (item.TryGetProperty("paths", out var paths)) text += "\n" + paths.ToString();
                    if (item.TryGetProperty("models", out var models)) text += "\n" + models.ToString();
                    if (item.TryGetProperty("preserved_unknown", out var unknown)) text += "\n" + unknown.ToString();
                }
                catch { }
                await Dispatcher.InvokeAsync(() =>
                {
                    log.AppendText(text + Environment.NewLine); if (log.Text.Length > 100000) log.Text = log.Text[^80000..]; log.ScrollToEnd();
                    if (hostText.Length > 0) hostResults.Text = hostText;
                    if (stage.Length > 0 && stage != "log") summary.Text = StageLabel(stage);
                    if (stage == "error" || stage == "preview") details.IsExpanded = true;
                });
            }
        }
        await System.Threading.Tasks.Task.WhenAll(Read(process.StandardOutput), Read(process.StandardError)); await process.WaitForExitAsync(); return process.ExitCode;
    }
    string HostRow(JsonElement row)
    {
        string code = row.GetProperty("code").GetString() ?? "", status = row.GetProperty("status").GetString() ?? "";
        bool ready = status == "pass"; string label = code switch
        {
            "architecture" => T("64-bit architecture", "Architektura 64-bitowa"),
            "platform" => T("Supported Windows/Ubuntu", "Obsługiwany Windows/Ubuntu"),
            "disk" => T("Free disk space", "Wolne miejsce na dysku"),
            "gpu" => T("NVIDIA driver for local ASR", "Sterownik NVIDIA do lokalnego ASR"),
            "media" => T("FFmpeg and ffprobe", "FFmpeg i ffprobe"),
            _ => T("Microsoft Visual C++ x64 runtime", "Biblioteki Microsoft Visual C++ x64")
        };
        string result = status == "pass" ? T("ready", "gotowe") : status == "warning" ? T("check if needed", "sprawdź w razie potrzeby") : T("action required", "wymaga działania");
        if (code == "disk") label += " · " + row.GetProperty("message").GetString();
        if (code == "platform" || code == "architecture") label += " · " + row.GetProperty("message").GetString();
        if (code == "vc_runtime" && !ready) label += " · " + T("use the prerequisite button", "użyj przycisku wymaganego składnika");
        return label + ": " + result;
    }
    string StageLabel(string stage) => stage switch
    {
        "host" => T("Host check completed; read the results above.", "Test komputera zakończony; przeczytaj wyniki powyżej."),
        "extract" => T("Verifying version bundle…", "Sprawdzanie paczki wersji…"),
        "dependencies" => T("Installing application dependencies…", "Instalowanie zależności programu…"),
        "models" => T("Checking/preparing selected model snapshots…", "Sprawdzanie/przygotowywanie wybranych modeli…"),
        "verify" => T("Checking installed application…", "Sprawdzanie zainstalowanego programu…"),
        "credentials" => T("Saving the optional key in the OS store…", "Zapisywanie opcjonalnego klucza w magazynie systemowym…"),
        "preview" => T("Read the removal plan in technical details before confirming.", "Przeczytaj plan usunięcia w szczegółach przed potwierdzeniem."),
        "error" => T("Check failed prerequisites, model access and the technical report.", "Sprawdź brakujące składniki, dostęp do modeli i raport techniczny."),
        _ => T("Finishing selected operation…", "Kończenie wybranej operacji…")
    };
    static void VerifyBundle(string file) { using var zip = ZipFile.OpenRead(file); var entry = zip.GetEntry("bundle.json") ?? throw new InvalidDataException(); using var doc = JsonDocument.Parse(entry.Open()); foreach (var item in doc.RootElement.GetProperty("sha256").EnumerateObject()) { if (item.Name.Contains("..") || item.Name.Contains('\\') || item.Name.StartsWith('/') || item.Name.Contains(':')) throw new InvalidDataException(); var asset = zip.GetEntry(item.Name) ?? throw new InvalidDataException(); using var source = asset.Open(); string actual = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(source)).ToLowerInvariant(); if (actual != item.Value.GetString()) throw new InvalidDataException(); } }
    static ImageSource Svg(string name)
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name)!; var xml = XDocument.Load(stream); var svg = xml.Root!; var values = svg.Attribute("viewBox")!.Value.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray(); var bounds = new Rect(values[0], values[1], values[2], values[3]);
        var styles = new System.Collections.Generic.Dictionary<string, string>(); foreach (var element in svg.Descendants().Where(e => e.Name.LocalName == "style")) foreach (Match m in Regex.Matches(element.Value, @"\.(cls-\d+)\s*\{([^}]+)\}")) styles[m.Groups[1].Value] = m.Groups[2].Value;
        var group = new DrawingGroup() { ClipGeometry = new RectangleGeometry(bounds) }; group.Children.Add(new GeometryDrawing(Brushes.Transparent, null, new RectangleGeometry(bounds)));
        foreach (var element in svg.Descendants().Where(e => e.Name.LocalName is "path" or "circle" or "rect"))
        {
            if (element.Ancestors().Any(e => e.Name.LocalName == "defs")) continue;
            string css = element.Attribute("class") is XAttribute c && styles.TryGetValue(c.Value, out string? v) ? v : "";
            string Value(string key, string fallback) { var attr = element.Attribute(key); if (attr != null) return attr.Value; string found = Regex.Match(css, Regex.Escape(key) + @"\s*:\s*([^;]+)").Groups[1].Value.Trim(); return found.Length > 0 ? found : fallback; }
            double Number(string key) => double.Parse(element.Attribute(key)?.Value ?? "0", CultureInfo.InvariantCulture);
            Geometry? geometry = element.Name.LocalName switch { "path" => Geometry.Parse(element.Attribute("d")!.Value), "circle" => new EllipseGeometry(new Point(Number("cx"), Number("cy")), Number("r"), Number("r")), "rect" => new RectangleGeometry(new Rect(Number("x"), Number("y"), Number("width"), Number("height")), Number("rx"), Number("ry") == 0 ? Number("rx") : Number("ry")), _ => null };
            if (geometry == null) continue; if (geometry is StreamGeometry shape) shape.FillRule = FillRule.Nonzero; string fill = Value("fill", "#356A80"), stroke = Value("stroke", "none"); Brush? BrushFor(string x) => x == "none" ? null : (Brush)new BrushConverter().ConvertFromInvariantString(x)!;
            var pen = stroke == "none" ? null : new Pen(BrushFor(stroke), double.Parse(Value("stroke-width", "1").Replace("px", ""), CultureInfo.InvariantCulture)); var drawing = new DrawingGroup(); drawing.Children.Add(new GeometryDrawing(BrushFor(fill), pen, geometry));
            // The framed favicon nests the original vector in a centered SVG viewport.
            foreach (var viewport in element.Ancestors().Where(e => e != svg && e.Name.LocalName == "svg"))
            {
                var box = viewport.Attribute("viewBox")!.Value.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray();
                double N(string key) => double.Parse(viewport.Attribute(key)?.Value ?? "0", CultureInfo.InvariantCulture);
                double scale = Math.Min(N("width") / box[2], N("height") / box[3]);
                var wrapper = new DrawingGroup(); wrapper.Children.Add(drawing);
                wrapper.Transform = new MatrixTransform(scale, 0, 0, scale, N("x") + (N("width") - box[2] * scale) / 2 - box[0] * scale, N("y") + (N("height") - box[3] * scale) / 2 - box[1] * scale);
                drawing = wrapper;
            }
            group.Children.Add(drawing);
        }
        return new DrawingImage(group);
    }
}
