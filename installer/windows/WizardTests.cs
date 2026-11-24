using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace EwP.Setup;

sealed partial class Wizard
{
    internal static readonly string[] TestChecks =
    [
        "embedded bundle integrity", "framed SVG and executable icon", "operation-specific navigation",
        "25 GB folder-volume gate", "structured CPU OS disk GPU-driver VC checks",
        "cached host-result EN/PL rerender", "local-model/HF-terms gates", "masked HF/OR paste validation",
        "stale credential response rejection", "matching-version model addition", "removal preview gate",
        "responsive native page previews", "aligned radio glyph and text centers", "action reset and automatic maintenance discovery",
        "conditional Visual C++ help", "Windows release warning", "accessible vector information icon",
        "readable lossless credits", "authenticated same-user permission broker",
        "app-only update and repair without credentials", "selective gated model recovery",
        "restricted installed maintenance entry points", "measured download progress and report timestamps",
        "visible information hover/focus feedback",
        "no installation/model/provider operation; broker transport probe only"
    ];

    internal async Task SelfTest(string? previewDirectory)
    {
        testing = true;
        var directory = Path.Combine(temporary, "test-target"); Directory.CreateDirectory(directory);
        root.Text = directory; DiskProbe = _ => (100_000_000_000L, "TEST-VOLUME");
        Show(); await Task.Delay(250); // Let location-change debounce settle, without invoking a worker.
        Assert(Icon != null, "framed window icon");
        using (var resource = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream("EwP.ico")!)
            Assert(BitmapDecoder.Create(resource, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad).Frames.Count == 7, "seven ICO sizes");
        language.SelectedIndex = 0; page = 0; Render();
        UpdateLayout();
        foreach (var choice in actionChoices)
        {
            choice.ApplyTemplate();
            var glyph = (FrameworkElement)choice.Template.FindName("RadioGlyph", choice);
            var text = (FrameworkElement)choice.Template.FindName("RadioText", choice);
            double gy = glyph.TransformToAncestor(choice).Transform(new Point(0, glyph.ActualHeight / 2)).Y;
            double ty = text.TransformToAncestor(choice).Transform(new Point(0, text.ActualHeight / 2)).Y;
            Assert(Math.Abs(gy - ty) < .75, "radio glyph and label share one center line");
        }
        Assert(next.IsEnabled && subtitle.Text == "Local-first transcript workflow", "welcome EN");
        await Next(); Assert(page == 1 && !next.IsEnabled, "host test required");
        hostReady = true; SetFixtureHost(); Render();
        Assert(next.IsEnabled, "host result permits next");
        DiskProbe = _ => (24_999_999_999L, "TEST-VOLUME"); Render(); Assert(!next.IsEnabled, "25GB margin gate");
        DiskProbe = _ => (25_000_000_000L, "TEST-VOLUME"); Render(); Assert(next.IsEnabled, "25GB boundary");
        DiskProbe = _ => (100_000_000_000L, "TEST-VOLUME");
        var cpu = HostStrings(); Assert(cpu.Contains("64-bit processor: Test CPU"), "host structured model");
        language.SelectedIndex = 1; Assert(HostStrings().Contains("Procesor 64-bit") && !HostStrings().Contains("GB free"), "cached host PL");
        language.SelectedIndex = 0; Assert(HostStrings().Contains("GB free") && HostStrings().Contains("20 GB required") && !HostStrings().Contains("wolne"), "cached host EN");
        await Next(); Assert(page == 2 && !next.IsEnabled && !terms.IsEnabled, "HF gate initially closed");
        language.SelectedIndex = 1; await Capture(previewDirectory, "pl-models-before-token"); language.SelectedIndex = 0;
        local.IsChecked = false; Assert(next.IsEnabled, "cloud/review install needs no credential");
        local.IsChecked = true; hfSecret = "synthetic-hf-never-sent"; hfValid = true; Render();
        Assert(terms.IsEnabled && !next.IsEnabled, "terms only enabled after verified token");
        terms.IsChecked = true; Assert(next.IsEnabled, "verified token and acknowledgment permit next");
        Assert(!VisibleText((DependencyObject)Content).Contains(hfSecret), "main page never exposes token");
        await TestCredentialModals(previewDirectory);
        orSecret = "synthetic-or-never-sent"; orValid = true; Render();
        Assert(!VisibleText((DependencyObject)Content).Contains(orSecret) && !log.Text.Contains(orSecret), "main page and logs never expose key");
        foreach (int locale in new[] { 0, 1 })
        {
            language.SelectedIndex = locale;
            foreach (int step in new[] { 0, 1, 2 }) { page = step; Render(); await Capture(previewDirectory, $"{(Pl ? "pl" : "en")}-step-{step + 1}"); }
        }
        Width = 700; Height = 760; page = 1; Render(); await Capture(previewDirectory, "pl-location-narrow");
        Width = 820; Height = 860;
        string existing = Path.Combine(temporary, "test-existing"); Directory.CreateDirectory(existing);
        File.WriteAllText(Path.Combine(existing, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = existing }));
        File.WriteAllText(Path.Combine(existing, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = existing, version = "0.0.1", active = "versions/test-1", local_models = false, previous = "versions/prior" }));
        root.Text = existing; await Task.Delay(250); operation = "models"; page = 1; Render();
        Assert(!next.IsEnabled && LocationProblem() != null, "adding models cannot silently upgrade older version");
        operation = "update"; hostReady = true; SetFixtureHost(); Render(); Assert(next.IsEnabled, "explicit update handles older version");
        operation = "uninstall"; page = 2; previewReady = false; Render(); Assert(!next.IsEnabled, "uninstall requires preview");
        using (var plan = JsonDocument.Parse("{\"paths\":[\"C:\\\\Users\\\\Example\\\\EwP\\\\runtime\"],\"models\":[]}")) removal = plan.RootElement.Clone();
        previewReady = true; Render(); Assert(next.IsEnabled && !removeModels.IsChecked!.Value && !removeKey.IsChecked!.Value, "removal preserves shared assets by default");
        await Capture(previewDirectory, "pl-uninstall-preview");
        operation = "install"; page = 3; busy = true; progressStage = "models"; Render();
        await Capture(previewDirectory, "pl-install-progress");
        busy = false; finished = successful = true; Render(); await Capture(previewDirectory, "pl-complete");
        await TestActionResetAndPresentation(previewDirectory);
        await TestModelMaintenance(previewDirectory);
        var infoButton = Symbols.InfoButton("Token do pobrania pyannote. Kliknij, aby uzyskać pomoc.", () => { });
        var infoWindow = new Window { Owner = this, Content = infoButton, Width = 180, Height = 120 };
        infoWindow.Show(); infoWindow.Activate(); infoButton.Focus(); infoWindow.UpdateLayout();
        await Dispatcher.Yield(DispatcherPriority.ApplicationIdle);
        var infoFrame = (Border)infoButton.Template.FindName("InfoFrame", infoButton);
        Assert(infoButton.IsKeyboardFocused && ((SolidColorBrush)infoFrame.Background).Color == ((SolidColorBrush)ColorBrush("#C5DDF0")).Color, "info focus visibly changes the rendered frame despite local control background");
        infoWindow.Close();
        if (previewDirectory != null) SaveExeIcon(Path.Combine(previewDirectory, "exe-icon.png"));
        finished = false; successful = false; hfSecret = orSecret = ""; hfValid = orValid = false;
    }

    async Task TestModelMaintenance(string? previews)
    {
        busy = finished = successful = false; language.SelectedIndex = 1;
        string existing = Path.Combine(temporary, "test-model-maintenance"); Directory.CreateDirectory(existing);
        File.WriteAllText(Path.Combine(existing, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = existing }));
        File.WriteAllText(Path.Combine(existing, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = existing, version, active = "versions/test-1", local_models = true, previous = "versions/prior" }));
        string config = Path.Combine(existing, "versions/test-1/app/src/ewp_transcripts/resources"); Directory.CreateDirectory(config);
        File.WriteAllText(Path.Combine(config, "default-config.toml"), string.Join("\n", catalog.Models.Select(m => m.Revision)));
        FindInstallation = (_, _) => InstallationDiscovery.Read(existing);
        SelectOperation("update"); page = 2; Render(); UpdateLayout();
        Assert(next.IsEnabled && !NeedsHf && !VisibleText((DependencyObject)Content).Contains("Podaj klucz OpenRouter"), "same-model update has no token/key gate");
        await Capture(previews, "pl-update-program-only");
        SelectOperation("repair"); page = 2; SetFixtureHost(); Render(); UpdateLayout();
        Assert(next.IsEnabled && !repairModels && !NeedsHf, "repair defaults to app only");
        await Capture(previews, "pl-repair-program-only");
        repairModels = true; selectedModels.Clear(); selectedModels.Add("diarization"); Render();
        Assert(NeedsHf && !next.IsEnabled, "explicit gated redownload requires token");
        await Capture(previews, "pl-repair-gated-model");
        selectedModels.Clear(); selectedModels.Add("asr"); Render();
        Assert(!NeedsHf && next.IsEnabled, "public model redownload needs no HF");
        await Capture(previews, "pl-repair-public-model");
        SelectOperation("models"); page = 2; SetFixtureHost(); selectedModels.Clear(); selectedModels.Add("asr"); Render(); UpdateLayout();
        Assert(!NeedsHf && !VisibleText((DependencyObject)Content).Contains("OpenRouter API"), "adding public models has no OR or gated prompt");
        await Capture(previews, "pl-add-public-model");
        maintenance = true; page = 0; operation = "uninstall"; Render();
        Assert(actionChoices.Count == 3 && actionChoices.All(c => new[] { "repair", "rollback", "uninstall" }.Contains(c.Tag?.ToString())), "installed-program panel limits maintenance");
        await Capture(previews, "pl-installed-program-maintenance");
        maintenance = false; localMaintenance = true; Render();
        Assert(actionChoices.Count == 2, "uninstall.exe offers repair/uninstall only");
        await Capture(previews, "pl-local-uninstall-entry");
        localMaintenance = false; operation = "install"; page = 1; Render(); UpdateLayout();
        Assert(root.Height == 36 && root.ActualHeight < 45, "location field is compact");
        page = 3; busy = true; progressStage = "models"; Render();
        using (var download = JsonDocument.Parse("{\"bytes\":500000000,\"total\":1000000000,\"unit\":\"B\",\"rate\":2500000,\"eta_seconds\":200}"))
            UpdateOperationProgress("download", "model.bin", download.RootElement);
        Assert(!operationProgress.IsIndeterminate && operationProgress.Value == 50 && downloadProgress.Text.Contains("MB/s"), "measured per-file progress/rate/ETA");
        await Capture(previews, "pl-model-download-progress");
        busy = false; FindInstallation = InstallationDiscovery.Find;
    }

    async Task TestCredentialModals(string? previews)
    {
        static Task<CredentialResult> Good(bool hf, string value, CancellationToken token) => Task.FromResult(new CredentialResult(true, "OK", "OK", "OK"));
        var hfDialog = new CredentialDialog(this, true, true, Good);
        Assert(!hfDialog.CanAccept, "empty token cannot be accepted");
        hfDialog.Show(); await hfDialog.TestPaste("synthetic-read-token");
        Assert(hfDialog.CanAccept && hfDialog.Status == "OK" && hfDialog.TestAcceptedValue() == "synthetic-read-token", "paste automatically validates HF");
        await CaptureWindow(hfDialog, previews, "pl-token-modal"); hfDialog.Close();
        var accepted = new CredentialDialog(this, true, false, Good);
        Exception? modalError = null;
        accepted.Loaded += async (_, _) =>
        {
            try { await accepted.TestPaste("synthetic-read-token"); accepted.TestAccept(); }
            catch (Exception e) { modalError = e; accepted.Close(); }
        };
        bool? result = accepted.ShowDialog();
        Assert(modalError == null && result == true && accepted.Value == "synthetic-read-token", "OK closes valid masked dialog and returns checked token");
        StoreCheckedCredential(true, accepted.Value);
        var orDialog = new CredentialDialog(this, false, false, (_, _, _) => Task.FromResult(new CredentialResult(false, "OR_HTTP_401", "Invalid key", "Nieprawidłowy klucz")));
        orDialog.Show(); await orDialog.TestPaste("synthetic-invalid-key"); Assert(!orDialog.CanAccept && orDialog.Status.Contains("OR_HTTP_401"), "failed OR key remains gated");
        await CaptureWindow(orDialog, previews, "en-key-modal-error"); orDialog.Close();
        int calls = 0;
        var stale = new CredentialDialog(this, true, false, async (_, value, _) =>
        {
            Interlocked.Increment(ref calls); await Task.Delay(value == "old-token" ? 500 : 10);
            return new(value == "old-token", value == "old-token" ? "OK" : "HF_HTTP_401", "Invalid token", "Nieprawidłowy token");
        });
        stale.Show(); await stale.TestPaste("old-token"); await stale.TestPaste("new-invalid-token"); await Task.Delay(250);
        Assert(calls == 2 && !stale.CanAccept && stale.Status.Contains("HF_HTTP_401"), "stale success cannot validate new input"); stale.Close();
    }

    async Task TestActionResetAndPresentation(string? previews)
    {
        busy = finished = successful = false;
        string existing = Path.Combine(temporary, "test-existing");
        var info = InstallationDiscovery.Read(existing)!;
        Assert(info != null && info.Root == existing, "owned installation metadata detection");
        FindInstallation = (_, _) => info;
        foreach (string action in operations.Where(o => o != "install"))
        {
            root.Text = Path.Combine(temporary, "old-install-choice");
            hostReady = hostAttempted = hfValid = orValid = previewReady = true;
            hfSecret = "synthetic-hf"; orSecret = "synthetic-or"; notice = "check_failed"; log.Text = "OLD-OPERATION-MESSAGE";
            terms.IsChecked = removeModels.IsChecked = removeKey.IsChecked = true;
            SelectOperation(action); page = 1; Render();
            Assert(root.Text == existing && !manualLocation, "maintenance location automatically detected");
            Assert(host == null && !hostReady && !hostAttempted && !previewReady && removal == null && log.Text.Length == 0 && notice.Length == 0, "changing action resets all check/removal/log state");
            Assert(!hfValid && !orValid && hfSecret.Length == 0 && orSecret.Length == 0 && terms.IsChecked != true && removeModels.IsChecked != true && removeKey.IsChecked != true, "changing action clears credentials and consent");
        }
        SelectOperation("repair"); page = 1; Render(); await Capture(previews, "pl-maintenance-detected");
        FindInstallation = (_, _) => null;
        foreach (string action in operations.Where(o => o != "install"))
        {
            SelectOperation(action); page = 1; Render();
            Assert(root.Text.Length == 0 && manualLocation && !next.IsEnabled, "missing installation asks for location without reusing prior input");
        }
        await Capture(previews, "pl-maintenance-not-found");
        SelectOperation("install"); Assert(root.Text == InstallationDiscovery.DefaultRoot, "install action restores default location");
        root.Text = Path.Combine(temporary, "test-target"); await Task.Delay(250);
        page = 1; hostAttempted = hostReady = true; SetFixtureHost(); Render(); Assert(!ShowVcHelp, "no VC download link after successful runtime check");
        string old = host!.Value.GetRawText().Replace("Windows 11 26H2", "Windows 11 24H2").Replace("\"code\":\"platform\",\"status\":\"pass\"", "\"code\":\"platform\",\"status\":\"warning\"");
        using (var json = JsonDocument.Parse(old)) host = json.RootElement.Clone();
        Render(); Assert(VisibleText((DependencyObject)Content).Contains("Nie gwarantujemy"), "older Windows has a brief compatibility note");
        await Capture(previews, "pl-windows-older-warning");
        string failed = host.Value.GetRawText().Replace("\"code\":\"vc_runtime\",\"status\":\"pass\"", "\"code\":\"vc_runtime\",\"status\":\"warning\"");
        using (var json = JsonDocument.Parse(failed)) host = json.RootElement.Clone();
        Render(); Assert(ShowVcHelp, "inconclusive VC test exposes download help"); await Capture(previews, "pl-vc-inconclusive");
        string original = File.ReadAllText(Path.Combine(temporary, "payload/app/src/ewp_transcripts/web_assets/brand/NOTICE.txt"));
        string credits = Credits.Format(original);
        string Normalize(string value) => System.Text.RegularExpressions.Regex.Replace(value, @"\s+", " ").Trim();
        Assert(Normalize(original) == Normalize(credits), "credits reflow preserves every attribution word");
        Assert(!credits.Contains("Original bytes\r\nare"), "credits have no hard wrap inside original sentence");
        page = 2; local.IsChecked = true; Render(); UpdateLayout();
        Assert(!VisibleText((DependencyObject)Content).Contains("(i)"), "info is a real vector icon");
        var help = CreateHfHelp(); help.Show(); await CaptureWindow(help, previews, "pl-hf-information"); help.Close();
        Assert(InstallFolderFromPicker(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)).EndsWith("EwPTranscripts"), "Program Files picker selects a dedicated app subfolder");
        var output = new List<string>();
        var request = new OperationRequest("broker-self-test", root.Text, false, false, false, false, false,
            "synthetic-hf-not-logged", "synthetic-or-not-logged", Environment.ProcessPath!, Environment.ProcessId, CancelFile);
        int result = await OperationRunner.Elevated(request, line => { output.Add(line); return Task.CompletedTask; }, test: true);
        Assert(result == 0 && output.Count > 0 && output.All(line => !line.Contains(request.HfToken) && !line.Contains(request.OpenRouterKey)), "authenticated broker never exposes secret frames");
        FindInstallation = InstallationDiscovery.Find;
    }

    void SetFixtureHost()
    {
        using var fixture = JsonDocument.Parse("""
        {"checks":[
          {"code":"architecture","status":"pass","context":{"cpu_model":"Test CPU 64-bit"}},
          {"code":"platform","status":"pass","context":{"name":"Windows 11 26H2","display_version":"26H2"}},
          {"code":"disk","status":"pass","context":{"free_bytes":100000000000,"installation_bytes":20000000000}},
          {"code":"gpu","status":"pass","context":{"devices":[{"name":"NVIDIA test GPU","driver":"000.00"}]}},
          {"code":"vc_runtime","status":"pass","context":{}}
        ]}
        """); host = fixture.RootElement.Clone();
    }
    string HostStrings() => host is JsonElement value ? string.Join("\n", value.GetProperty("checks").EnumerateArray().Select(HostText)) : "";
    static void Assert(bool condition, string name) { if (!condition) throw new InvalidDataException("Self-test failed: " + name); }
    static string VisibleText(DependencyObject parent)
    {
        string text = parent is TextBlock block ? block.Text : "";
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++) text += VisibleText(VisualTreeHelper.GetChild(parent, i));
        return text;
    }
    async Task Capture(string? folder, string name) => await CaptureWindow(this, folder, name);
    static async Task CaptureWindow(Window window, string? folder, string name)
    {
        if (folder == null) return;
        Directory.CreateDirectory(folder); window.UpdateLayout(); await Dispatcher.Yield(DispatcherPriority.ApplicationIdle);
        var target = (FrameworkElement)window.Content;
        var image = new RenderTargetBitmap((int)Math.Ceiling(target.ActualWidth), (int)Math.Ceiling(target.ActualHeight), 96, 96, PixelFormats.Pbgra32);
        image.Render(target);
        var pixel = new byte[4]; image.CopyPixels(new Int32Rect(5, 5, 1, 1), pixel, 4, 0);
        Assert(pixel[3] == 255, "native preview has opaque real window background");
        var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(image));
        using var output = File.Create(Path.Combine(folder, name + ".png")); encoder.Save(output);
    }
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] static extern uint ExtractIconEx(string file, int index, out IntPtr large, out IntPtr small, uint count);
    [DllImport("user32.dll")] static extern bool DestroyIcon(IntPtr icon);
    static void SaveExeIcon(string path)
    {
        if (ExtractIconEx(Environment.ProcessPath!, 0, out var large, out var small, 1) == 0) throw new InvalidDataException("No EXE icon");
        try
        {
            var image = Imaging.CreateBitmapSourceFromHIcon(large, Int32Rect.Empty, BitmapSizeOptions.FromEmptyOptions());
            var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(image)); using var output = File.Create(path); encoder.Save(output);
        }
        finally { if (large != IntPtr.Zero) DestroyIcon(large); if (small != IntPtr.Zero) DestroyIcon(small); }
    }
}
