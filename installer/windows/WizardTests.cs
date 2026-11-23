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
        "responsive native page previews", "no install worker or external network invocation"
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
        Assert(next.IsEnabled && subtitle.Text == "Local-first transcript workflow", "welcome EN");
        await Next(); Assert(page == 1 && !next.IsEnabled, "host test required");
        hostReady = true; SetFixtureHost(); Render();
        Assert(next.IsEnabled, "host result permits next");
        DiskProbe = _ => (24_999_999_999L, "TEST-VOLUME"); Render(); Assert(!next.IsEnabled, "25GB margin gate");
        DiskProbe = _ => (25_000_000_000L, "TEST-VOLUME"); Render(); Assert(next.IsEnabled, "25GB boundary");
        DiskProbe = _ => (100_000_000_000L, "TEST-VOLUME");
        var cpu = HostStrings(); Assert(cpu.Contains("64-bit processor: Test CPU"), "host structured model");
        language.SelectedIndex = 1; Assert(HostStrings().Contains("Procesor 64-bit") && !HostStrings().Contains("GB free"), "cached host PL");
        language.SelectedIndex = 0; Assert(HostStrings().Contains("GB free") && !HostStrings().Contains("wolne"), "cached host EN");
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
        File.WriteAllText(Path.Combine(existing, "owner.json"), "{}");
        File.WriteAllText(Path.Combine(existing, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", version = "0.0.1", local_models = false, previous = "versions/prior" }));
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
        if (previewDirectory != null) SaveExeIcon(Path.Combine(previewDirectory, "exe-icon.png"));
        finished = false; successful = false; hfSecret = orSecret = ""; hfValid = orValid = false;
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

    void SetFixtureHost()
    {
        using var fixture = JsonDocument.Parse("""
        {"checks":[
          {"code":"architecture","status":"pass","context":{"cpu_model":"Test CPU 64-bit"}},
          {"code":"platform","status":"pass","context":{"name":"Windows 11 x64"}},
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
