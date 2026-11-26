using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
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
        "visible information hover/focus feedback", "persistent technical log expansion",
        "disabled installed models and explicit reinstall", "real older-version rollback selection", "required-check click feedback",
        "five-step first install and optional OpenRouter page", "overall progress and stable metrics",
        "same-version update refusal", "automatic required host checks for install/update/repair/models", "disk-only folder refresh without repeated hardware probes", "failed host checks stay blocked after folder changes", "optional local ASR unchecked defaults and selection", "technical-only backend notices", "application-pattern header",
        "reviewed EN/PL copy and localized project notices", "newer-installer release links in every maintenance flow", "separate smaller OpenRouter spending footnote", "application-pattern light body",
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
        Assert(CanAdvance && subtitle.Text == "Local-first transcript workflow", "welcome EN");
        await Next(); Assert(page == 1 && !CanAdvance, "host test required");
        hostReady = true; SetFixtureHost(); Render();
        Assert(CanAdvance, "host result permits next");
        DiskProbe = _ => (24_999_999_999L, "TEST-VOLUME"); Render(); Assert(!CanAdvance, "25GB margin gate");
        DiskProbe = _ => (25_000_000_000L, "TEST-VOLUME"); Render(); Assert(CanAdvance, "25GB boundary");
        DiskProbe = _ => (100_000_000_000L, "TEST-VOLUME");
        var cpu = HostStrings(); Assert(cpu.Contains("64-bit processor: Test CPU"), "host structured model");
        language.SelectedIndex = 1; Assert(HostStrings().Contains("Procesor 64-bit") && !HostStrings().Contains("GB free"), "cached host PL");
        language.SelectedIndex = 0; Assert(HostStrings().Contains("GB free") && HostStrings().Contains("20 GB required") && !HostStrings().Contains("wolne"), "cached host EN");
        await Next(); Assert(page == 2 && !CanAdvance && !terms.IsEnabled, "HF gate initially closed");
        language.SelectedIndex = 1; await Capture(previewDirectory, "pl-models-before-token"); language.SelectedIndex = 0;
        local.IsChecked = false; Assert(CanAdvance, "cloud/review install needs no credential");
        local.IsChecked = true; hfSecret = "synthetic-hf-never-sent"; hfValid = true; Render();
        Assert(terms.IsEnabled && !CanAdvance, "terms only enabled after verified token");
        await Next();
        Assert(page == 2 && next.IsEnabled && !CanAdvance && missingRequirements.Contains("terms") && terms.Parent is Border frame && frame.BorderBrush == Error, "blocked Next highlights missing HF acknowledgment");
        await Capture(previewDirectory, "en-required-hf-terms");
        terms.IsChecked = true; Assert(CanAdvance, "verified token and acknowledgment permit next");
        Assert(!VisibleText((DependencyObject)Content).Contains(hfSecret), "main page never exposes token");
        await Next(); Assert(page == 3 && ProgressPage == 4 && steps.Children.Count == 5 && CanAdvance, "first install has a separate optional OpenRouter step");
        Assert(VisibleText(body).Contains("OpenRouter") && !VisibleText(body).Contains("Hugging Face"), "OpenRouter is separate from models/HF");
        await Capture(previewDirectory, "en-openrouter-step");
        language.SelectedIndex = 1; await Capture(previewDirectory, "pl-openrouter-step"); language.SelectedIndex = 0;
        Back(); Assert(page == 2 && !VisibleText(body).Contains("OpenRouter API"), "models step does not request OpenRouter key");
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
        Assert(!CanAdvance && LocationProblem() != null, "adding models cannot silently upgrade older version");
        operation = "update"; hostReady = true; SetFixtureHost(); Render(); Assert(CanAdvance, "explicit update handles older version");
        operation = "uninstall"; page = 2; previewReady = false; Render(); Assert(!CanAdvance, "uninstall requires preview");
        using (var plan = JsonDocument.Parse("{\"paths\":[\"C:\\\\Users\\\\Example\\\\EwP\\\\runtime\"],\"models\":[]}")) removal = plan.RootElement.Clone();
        previewReady = true; Render(); Assert(CanAdvance && !removeModels.IsChecked!.Value && !removeKey.IsChecked!.Value, "removal preserves shared assets by default");
        await Capture(previewDirectory, "pl-uninstall-preview");
        operation = "install"; page = ProgressPage; busy = true; progressStage = "models"; Render();
        await Capture(previewDirectory, "pl-install-progress");
        busy = false; finished = successful = true; Render(); await Capture(previewDirectory, "pl-complete");
        await TestActionResetAndPresentation(previewDirectory);
        await TestModelMaintenance(previewDirectory);
        await TestAutomaticHostChecks(previewDirectory);
        await TestReviewedCopy(previewDirectory);
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

    async Task TestReviewedCopy(string? previews)
    {
        Assert(((Grid)Content).Background is DrawingBrush { TileMode: TileMode.Tile } light && light.Drawing is DrawingGroup { Children.Count: 2 }, "light body uses opaque tiled application artwork");
        string folder = Path.Combine(temporary, "test-copy-newer"); Directory.CreateDirectory(folder);
        File.WriteAllText(Path.Combine(folder, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder }));
        File.WriteAllText(Path.Combine(folder, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder, version = "99.0.0", active = "versions/newer", local_models = false }));
        foreach (int locale in new[] { 0, 1 })
        {
            language.SelectedIndex = locale;
            foreach (string action in new[] { "update", "repair", "models" })
            {
                SelectOperation(action); root.Text = folder; await Task.Delay(250); ReadInstalled();
                page = 1; SetFixtureHost(); hostReady = true; Render(); UpdateLayout();
                Assert(!CanAdvance && LocationProblem() != null, "newer program blocks " + action);
                Assert(diskStatus.Inlines.OfType<Hyperlink>().Single().NavigateUri.AbsoluteUri == InstallerReleasesUrl, "release hyperlink in " + action + " location / " + locale);
                if (action == "models")
                    Assert(FindVisual<TextBlock>(hostRows).SelectMany(t => t.Inlines.OfType<Hyperlink>()).Any(h => h.NavigateUri.AbsoluteUri == InstallerReleasesUrl), "model version result links releases too");
                if (action is "models" or "update") await Capture(previews, $"{(Pl ? "pl" : "en")}-newer-installer-{action}");
            }
            operation = "install"; page = 3; busy = finished = false; Render(); UpdateLayout();
            var note = body.Children.OfType<TextBlock>().Single(t => t.Text.StartsWith("*"));
            int index = body.Children.IndexOf(note); var instruction = (TextBlock)body.Children[index - 1];
            string instructionText = new TextRange(instruction.ContentStart, instruction.ContentEnd).Text;
            Assert(note.FontSize < instruction.FontSize, $"spending comment is smaller / {locale}: {note.FontSize} < {instruction.FontSize}");
            Assert(instructionText.Contains("*") && !instructionText.Contains("$2") && note.Text.Contains("$2"), "spending comment is separate from linked instruction / " + locale);
            Assert(note.TransformToAncestor(body).Transform(new Point()).Y >= instruction.TransformToAncestor(body).Transform(new Point(0, instruction.ActualHeight)).Y, "footnote below linked instruction");
            Assert(NoticeFile.EndsWith(Pl ? "NOTICE_PL.txt" : "NOTICE.txt"), "notice follows installer language");
            string notices = File.ReadAllText(NoticeFile);
            Assert(notices.Contains("Cyryl") && !notices.Contains("Assets copied") && !notices.Contains("brandbook 0.4.0"), "owner removed internal notice paragraph");
            await Capture(previews, $"{(Pl ? "pl" : "en")}-reviewed-openrouter-footnote");
        }
        Width = 700; Height = 760; await Capture(previews, "pl-reviewed-openrouter-narrow"); Width = 820; Height = 860;
        var reused = Copy("Download a newer installer."); SetCopy(reused, "All ready.");
        Assert(!reused.Inlines.OfType<Hyperlink>().Any() && reused.Text == "All ready.", "replaced dynamic copy drops stale release link");
    }

    async Task TestAutomaticHostChecks(string? previews)
    {
        busy = finished = successful = false;
        int calls = 0; long free = 100_000_000_000L;
        var priorDisk = DiskProbe; var priorFind = FindInstallation;
        DiskProbe = _ => (free, "TEST-AUTO-VOLUME");
        HostCheckRunner = () => { calls++; Assert(page == 1 && busy, "automatic check runs on busy location page"); SetFixtureHost(); return Task.FromResult(0); };
        try
        {
            foreach (string action in new[] { "install", "update", "repair", "models" })
            {
                string folder = Path.Combine(temporary, "test-auto-" + action); Directory.CreateDirectory(folder);
                if (action != "install")
                {
                    File.WriteAllText(Path.Combine(folder, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder }));
                    File.WriteAllText(Path.Combine(folder, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder, version = action == "update" ? "0.0.1" : version, active = "versions/test-1", local_models = false }));
                }
                FindInstallation = (_, _) => action == "install" ? null : InstallationDiscovery.Read(folder);
                SelectOperation(action); root.Text = folder; await Task.Delay(250);
                int previous = calls;
                await Next();
                Assert(page == 1 && calls == previous + 1 && hostReady && hostAttempted && CanAdvance, action + " auto-check completes without manual test click");
                await AutoCheckHost();
                Assert(calls == previous + 1, "cached/debounced check does not repeat hardware probes");
                if (action == "install")
                {
                    string hardware = string.Join("|", host!.Value.GetProperty("checks").EnumerateArray().Where(r => r.GetProperty("code").GetString() != "disk").Select(r => r.GetRawText()));
                    free = 24_000_000_000L; root.Text = folder + "-low-space"; await Task.Delay(300);
                    Assert(calls == previous + 1 && !CanAdvance && !hostReady && hostAttempted, "low-space folder blocks without repeating full check");
                    Assert(host!.Value.GetProperty("checks").EnumerateArray().Single(r => r.GetProperty("code").GetString() == "disk").GetProperty("context").GetProperty("free_bytes").GetInt64() == free, "cached disk table reflects changed volume");
                    Assert(string.Join("|", host.Value.GetProperty("checks").EnumerateArray().Where(r => r.GetProperty("code").GetString() != "disk").Select(r => r.GetRawText())) == hardware, "CPU OS GPU and runtime results remain unchanged");
                    language.SelectedIndex = 1; await Capture(previews, "pl-auto-check-new-disk-full");
                    free = 100_000_000_000L; root.Text = folder + "-enough-space"; await Task.Delay(300);
                    Assert(calls == previous + 1 && hostReady && CanAdvance, "adequate target recovers Next using only a disk check");
                    await Capture(previews, "pl-auto-check-new-disk-ready");
                    using var failed = JsonDocument.Parse(host!.Value.GetRawText().Replace("\"code\":\"architecture\",\"status\":\"pass\"", "\"code\":\"architecture\",\"status\":\"fail\""));
                    host = failed.RootElement.Clone(); root.Text = folder + "-failed-cpu"; await Task.Delay(300);
                    Assert(!hostReady && !CanAdvance && calls == previous + 1, "disk-only refresh cannot clear a failed CPU check");
                }
                if (action == "update") await Capture(previews, "pl-update-automatic-check-ready");
            }
            FindInstallation = (_, _) => null;
            SelectOperation("update"); int atInvalid = calls; await Next();
            Assert(page == 1 && calls == atInvalid && !CanAdvance, "unknown update folder waits without worker");
            SelectOperation("uninstall"); await Next();
            Assert(calls == atInvalid, "uninstall does not launch unneeded host tests");
        }
        finally { HostCheckRunner = null; DiskProbe = priorDisk; FindInstallation = priorFind; busy = finished = successful = false; }
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
        Assert(CanAdvance && !NeedsHf && !VisibleText((DependencyObject)Content).Contains("Podaj klucz OpenRouter"), "same-model update has no token/key gate");
        await Capture(previews, "pl-update-program-only");
        page = 1; Render(); Assert(!CanAdvance && LocationProblem() != null, "same-version update is blocked");
        SelectOperation("repair"); page = 2; SetFixtureHost(); Render(); UpdateLayout();
        Assert(CanAdvance && !repairModels && !NeedsHf, "repair defaults to app only");
        await Capture(previews, "pl-repair-program-only");
        repairModels = true; selectedModels.Clear(); selectedModels.Add("diarization"); Render();
        Assert(NeedsHf && !CanAdvance, "explicit gated redownload requires token");
        await Capture(previews, "pl-repair-gated-model");
        selectedModels.Clear(); selectedModels.Add("asr"); Render();
        Assert(!NeedsHf && CanAdvance, "public model redownload needs no HF");
        await Capture(previews, "pl-repair-public-model");
        SelectOperation("models"); page = 2; SetFixtureHost(); selectedModels.Clear(); selectedModels.Add("asr"); Render(); UpdateLayout();
        Assert(!NeedsHf && !VisibleText((DependencyObject)Content).Contains("OpenRouter API"), "adding public models has no OR or gated prompt");
        await Capture(previews, "pl-add-public-model");
        ModelMissingBytes = _ => 0; ResetModelState(); Render(); UpdateLayout();
        Assert(!NeedsHf && !CanAdvance && selectedModels.Count == 0 && !DownloadModels.Any(), "installed models have no implicit selection/download/token");
        Assert(FindVisual<CheckBox>(body).Count(c => !c.IsEnabled) == catalog.Models.Count, "installed model boxes are disabled");
        await Capture(previews, "pl-models-already-installed");
        reinstallModels = true; selectedModels.Add("diarization"); Render(); UpdateLayout();
        Assert(NeedsHf && DownloadModels.Single().Code == "diarization", "explicit reinstall unlocks selected gated download");
        await Capture(previews, "pl-models-explicit-reinstall");
        ModelMissingBytes = model => model.MissingBytes();
        SelectOperation("repair"); page = ProgressPage; busy = true; Render(); UpdateLayout();
        var details = FindVisual<Expander>(body).Single(); details.IsExpanded = true;
        progressStage = "dependencies"; Render(); UpdateLayout();
        Assert(FindVisual<Expander>(body).Single().IsExpanded, "log stays open across progress rerender");
        FindVisual<Expander>(body).Single().IsExpanded = false;
        progressStage = "verify"; Render(); UpdateLayout();
        Assert(!FindVisual<Expander>(body).Single().IsExpanded, "user can collapse log and keep it collapsed");
        busy = false;
        operation = "install"; ResetModelState(); page = 2; Render();
        Assert(catalog.Models.Count(m => m.Optional) == 2 && !DownloadModels.Any(m => m.Optional), "optional models never download by default");
        selectedModels.Add("asr_v3_turbo"); Render();
        Assert(DownloadModels.Any(m => m.Code == "asr_v3_turbo"), "explicit optional model selection reaches download request");
        await Capture(previews, "pl-optional-local-asr");
        operation = "update"; ResetModelState();
        TestRollbackChoices(existing);

        maintenance = true; page = 0; operation = "uninstall"; Render();
        Assert(actionChoices.Count == 3 && actionChoices.All(c => new[] { "repair", "rollback", "uninstall" }.Contains(c.Tag?.ToString())), "installed-program panel limits maintenance");
        await Capture(previews, "pl-installed-program-maintenance");
        maintenance = false; localMaintenance = true; Render();
        Assert(actionChoices.Count == 2, "uninstall.exe offers repair/uninstall only");
        await Capture(previews, "pl-local-uninstall-entry");
        localMaintenance = false; operation = "install"; page = 1; Render(); UpdateLayout();
        Assert(root.Height == 36 && root.ActualHeight < 45, "location field is compact");
        var textViewport = (ScrollViewer)root.Template.FindName("PART_ContentHost", root);
        Assert(textViewport.ActualHeight >= root.ActualHeight - 4, "compact input does not apply padding twice or clip path text");
        page = ProgressPage; busy = true; progressStage = "models"; ResetOperationProgress(); Render();
        using (var download = JsonDocument.Parse("{\"bytes\":500000000,\"total\":1000000000,\"unit\":\"B\",\"rate\":2500000,\"eta_seconds\":200}"))
            UpdateOperationProgress("download", "model.bin", download.RootElement);
        Assert(!operationProgress.IsIndeterminate && operationProgress.Value == 50 && downloadRate.Text.Contains("MB/s"), "measured per-file progress/rate/ETA");
        UpdateOperationProgress("verify", "Checking installed program", null);
        double completed = overallProgress.Value;
        UpdateOperationProgress("python", "Repeated child runtime check", null);
        Assert(completed > 0 && overallProgress.Value == completed && activityProgress.Height == 32, "overall phase progress does not regress and activity reserves height");
        UpdateOperationProgress("log", "Downloading test-wheel (1MiB)", null);
        UpdateOperationProgress("log", "Downloaded test-wheel", null);
        string previousActivity = activityProgress.Text;
        UpdateOperationProgress("log", "Xet Storage is enabled for this repo, but the hf_xet package is not installed", null);
        Assert(activityProgress.Text == previousActivity, "backend warnings never replace activity/package name");
        UpdateOperationProgress("model-item", "Systran/faster-whisper-large-v3", null);
        Assert(activityProgress.Text == "Systran/faster-whisper-large-v3", "structured model activity shows only repository");
        Assert(downloadsFinished.Contains("package:test-wheel"), "download counter includes completed dependencies");
        using (var finalDownload = JsonDocument.Parse("{\"bytes\":1000000000,\"total\":1000000000,\"unit\":\"B\",\"download_id\":\"fixture:model.bin\"}")) UpdateOperationProgress("download", "model.bin", finalDownload.RootElement);
        Assert(downloadsFinished.Contains("fixture:model.bin"), "download counter includes model byte transfers");
        using (var unknown = JsonDocument.Parse("{\"bytes\":1000,\"total\":null,\"unit\":\"B\",\"download_id\":\"fixture:unknown.bin\"}")) UpdateOperationProgress("download", "unknown.bin", unknown.RootElement);
        Assert(operationProgress.IsIndeterminate && downloadsStarted.Contains("fixture:unknown.bin"), "unknown byte total is honest and counted");
        UpdateOperationProgress("model-complete", "fixture", null);
        Assert(downloadsFinished.Contains("fixture:unknown.bin"), "repository completion closes unknown-total downloads");
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
            Assert(root.Text.Length == 0 && manualLocation && !CanAdvance, "missing installation asks for location without reusing prior input");
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
    static IEnumerable<T> FindVisual<T>(DependencyObject parent) where T : DependencyObject
    {
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
        {
            var child = VisualTreeHelper.GetChild(parent, i);
            if (child is T match) yield return match;
            foreach (var nested in FindVisual<T>(child)) yield return nested;
        }
    }
    void TestRollbackChoices(string existing)
    {
        string[] releases = ["versions/old-1", "versions/old-2", "versions/same", "versions/missing"];
        File.WriteAllText(Path.Combine(existing, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = existing, releases }));
        foreach (var (release, oldVersion) in new[] { (releases[0], "0.1.0"), (releases[1], "0.2.0"), (releases[2], version) })
        {
            string path = Path.Combine(existing, release); Directory.CreateDirectory(Path.Combine(path, "app/.venv/Scripts"));
            File.WriteAllText(Path.Combine(path, "app/.venv/Scripts/python.exe"), "fixture only");
            File.WriteAllText(Path.Combine(path, "bundle.json"), JsonSerializer.Serialize(new { version = oldVersion }));
        }
        SelectOperation("rollback"); page = 1; Render(); UpdateLayout();
        Assert(RollbackChoices().Count == 2 && rollbackTarget == releases[1] && CanAdvance, "rollback lists only existing older runtimes and defaults newest");
        var choice = FindVisual<ComboBox>(body).Single(); choice.SelectedIndex = 1;
        Assert(rollbackTarget == releases[0], "rollback user selects exact version");
        Directory.Delete(Path.Combine(existing, releases[0]), true); Directory.Delete(Path.Combine(existing, releases[1]), true);
        Render(); Assert(!CanAdvance && LocationProblem() != null, "rollback blocked without older files");
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
