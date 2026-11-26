using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Microsoft.Web.WebView2.Core;
using System.Windows.Interop;
using Microsoft.Web.WebView2.Wpf;
using Microsoft.Win32;

namespace EwP.Desktop;

sealed partial class DesktopWindow : Window
{
    readonly AppConfig config;
    readonly OwnedBackend backend = new();
    readonly WebView2 view = new();
    readonly Grid shell = new();
    readonly StackPanel notice = new() { Margin = new Thickness(16, 10, 16, 10) };
    readonly TextBlock message = new() { TextWrapping = TextWrapping.Wrap, FontSize = 14 };
    readonly ProgressBar progress = new() { IsIndeterminate = true, Height = 3, Margin = new Thickness(0, 8, 0, 0) };
    readonly WindowPlacement placement;
    readonly SavedPlacement? startupPlacement;
    readonly DispatcherTimer geometryTimer = new() { Interval = TimeSpan.FromMilliseconds(300) };
    Appearance appearance = new();
    ClosingProgress? closingProgress;
    readonly DispatcherTimer poll = new() { Interval = TimeSpan.FromMilliseconds(500) };
    readonly Dictionary<string, TaskCompletionSource<JsonElement>> replies = new();
    bool pl = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName == "pl";
    bool ready, closed, closing, allowClose, waiting, ticking;
    readonly string? testReport, previews;
    string? testDownloadPath;
    bool testBusy;
    CloseAction testChoice = CloseAction.Stop;
    string T(string en, string polish) => pl ? polish : en;
    static Brush Color(string color) => (Brush)new BrushConverter().ConvertFromInvariantString(color)!;
    public DesktopWindow(AppConfig config, string? testReport = null, string? previews = null)
    {
        this.config = config; this.testReport = testReport; this.previews = previews;
        Title = "EwP Transcripts · " + Assembly.GetExecutingAssembly().GetName().Version!.ToString(3);
        MinWidth = Math.Min(760, SystemParameters.WorkArea.Width); MinHeight = Math.Min(560, SystemParameters.WorkArea.Height);
        Width = Math.Min(1360, SystemParameters.WorkArea.Width); Height = Math.Min(940, SystemParameters.WorkArea.Height);
        placement = new WindowPlacement(Path.Combine(config.StateDirectory, "window.json"));
        startupPlacement = placement.Saved;
        WindowStartupLocation = placement.Saved == null ? WindowStartupLocation.CenterScreen : WindowStartupLocation.Manual; Background = Color("#F5F2E9"); Foreground = Color("#273342"); FontFamily = new FontFamily("Segoe UI");
        using (var icon = Assembly.GetExecutingAssembly().GetManifestResourceStream("EwP.ico")!) Icon = BitmapFrame.Create(icon, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
        try { var saved = JsonSerializer.Deserialize<Appearance>(File.ReadAllText(Path.Combine(config.StateDirectory, "appearance.json"))); if (saved != null && TitleBar.Valid(saved)) appearance = saved; } catch { }
        SourceInitialized += (_, _) => TitleBar.Apply(this, appearance);
        geometryTimer.Tick += (_, _) => { geometryTimer.Stop(); placement.Save(this); };
        void SaveGeometry(object? sender, EventArgs args) { if (!IsLoaded || closed) return; geometryTimer.Stop(); geometryTimer.Start(); }
        LocationChanged += SaveGeometry; SizeChanged += (_, _) => SaveGeometry(this, EventArgs.Empty); StateChanged += SaveGeometry;
        Microsoft.Win32.SystemEvents.UserPreferenceChanged += SystemPreferenceChanged;
        shell.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); shell.RowDefinitions.Add(new RowDefinition());
        notice.Children.Add(message); notice.Children.Add(progress); shell.Children.Add(notice); Grid.SetRow(view, 1); shell.Children.Add(view); Content = shell;
        Loaded += async (_, _) => { placement.Restore(this); await Initialize(); };
        Closing += OnClosing; Closed += OnClosed;
        poll.Tick += async (_, _) => await Poll();
    }
    internal void BringToFront() { if (closed) return; WindowPlacement.Reveal(this); Show(); Activate(); Topmost = true; Topmost = false; Focus(); }
    void ShowNotice(string text, bool busy = false)
    {
        message.Text = text; notice.Visibility = Visibility.Visible; progress.Visibility = busy ? Visibility.Visible : Visibility.Collapsed;
    }
    void OfferDiscard()
    {
        if (notice.Children.OfType<Button>().Any(button => Equals(button.Tag, "discard"))) return;
        var discard = new Button { Tag = "discard", Content = T("Close without saving…", "Zamknij bez zapisu…"), HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 8, 0, 0), Padding = new Thickness(12, 4, 12, 4) };
        discard.Click += (_, _) =>
        {
            if (MessageBox.Show(this,
                T("Discard changes since the last successful save and stop all active work?", "Odrzucić zmiany od ostatniego poprawnego zapisu i zatrzymać wszystkie aktywne zadania?"),
                "EwP Transcripts", MessageBoxButton.YesNo, MessageBoxImage.Warning, MessageBoxResult.No) == MessageBoxResult.Yes) FinishClose();
        };
        notice.Children.Add(discard);
    }
    async Task Initialize()
    {
        try
        {
            ShowNotice(T("Starting EwP Transcripts…", "Uruchamianie EwP Transcripts…"), true);
            // Check before starting Python, so a missing browser runtime leaves no server behind.
            CoreWebView2Environment.GetAvailableBrowserVersionString();
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(config.StateDirectory, "WebView2"));
            if (closed) return;
            await view.EnsureCoreWebView2Async(environment);
            if (closed) return;
            ConfigureWebView(environment);
            backend.Start(config);
            var deadline = DateTime.UtcNow.AddSeconds(60);
            JsonElement? status = null;
            while (!closed && DateTime.UtcNow < deadline)
            {
                if (backend.Process!.HasExited) throw new IOException("Application runtime exited during startup");
                status = await backend.Request();
                if (status != null) break;
                await Task.Delay(150);
            }
            if (closed) return;
            if (status == null) throw new TimeoutException("Application startup timed out");
            var loaded = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
            view.NavigationCompleted += (_, e) => loaded.TrySetResult(e.IsSuccess);
            view.Source = new Uri(AppConfig.Origin + "/");
            if (!await loaded.Task.WaitAsync(TimeSpan.FromSeconds(30))) throw new IOException("Application page could not load");
            ready = true; notice.Visibility = Visibility.Collapsed; poll.Start();
            if (testReport != null) await SelfTest();
        }
        catch (Exception error)
        {
            if (closed) return;
            if (testReport != null) { await TestFailure(error); FinishClose(); return; }
            view.Visibility = Visibility.Collapsed;
            ShowNotice(T("EwP Transcripts could not start. Repair the installation or check Microsoft WebView2 Runtime. Details: ", "Nie udało się uruchomić EwP Transcripts. Napraw instalację lub sprawdź składnik Microsoft WebView2 Runtime. Szczegóły: ") + Path.Combine(config.StateDirectory, "desktop.log"));
            var link = new TextBlock { Margin = new Thickness(0, 14, 0, 0) };
            var hyperlink = new Hyperlink(new Run(T("Get Microsoft WebView2 Runtime", "Pobierz składnik Microsoft WebView2 Runtime")));
            hyperlink.Click += (_, _) => OpenExternal("https://developer.microsoft.com/microsoft-edge/webview2/"); link.Inlines.Add(hyperlink); notice.Children.Add(link);
            SaveDiagnostic(error.GetType().Name + ": " + error.Message);
        }
    }
    void ConfigureWebView(CoreWebView2Environment environment)
    {
        var core = view.CoreWebView2;
        core.Settings.AreHostObjectsAllowed = false; core.Settings.IsWebMessageEnabled = true;
        core.Settings.AreDevToolsEnabled = false; core.Settings.AreBrowserAcceleratorKeysEnabled = false;
        core.Settings.IsPasswordAutosaveEnabled = false; core.Settings.IsGeneralAutofillEnabled = false;
        core.NavigationStarting += (_, e) => { if (!AppConfig.IsDocument(e.Uri)) { e.Cancel = true; if (e.IsUserInitiated) OpenExternal(e.Uri); } };
        core.FrameNavigationStarting += (_, e) => { if (!AppConfig.IsLocal(e.Uri)) e.Cancel = true; };
        core.NewWindowRequested += (_, e) => { e.Handled = true; if (e.IsUserInitiated) OpenExternal(e.Uri); };
        core.AddWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All);
        core.WebResourceRequested += (_, e) => { if (!AppConfig.IsResource(e.Request.Uri)) e.Response = environment.CreateWebResourceResponse(Stream.Null, 403, "Blocked", "Content-Type: text/plain"); };
        core.PermissionRequested += (_, e) => e.State = e.IsUserInitiated && AppConfig.IsDocument(e.Uri) && e.PermissionKind == CoreWebView2PermissionKind.ClipboardRead
            ? CoreWebView2PermissionState.Allow : CoreWebView2PermissionState.Deny;
        core.WebMessageReceived += (_, e) =>
        {
            if (!AppConfig.IsDocument(e.Source)) return;
            try
            {
                using var data = JsonDocument.Parse(e.WebMessageAsJson);
                var value = data.RootElement;
                if (value.GetProperty("type").GetString() == "appearance") { ApplyAppearance(value); return; }
                if (value.GetProperty("type").GetString() != "lifecycle-result") return;
                string id = value.GetProperty("id").GetString()!;
                if (replies.TryGetValue(id, out var reply)) reply.TrySetResult(value.Clone());
            }
            catch (Exception error) when (error is JsonException or KeyNotFoundException or InvalidOperationException) { }
        };
        core.DownloadStarting += async (_, e) =>
        {
            var deferral = e.GetDeferral();
            try
            {
                if (!AppConfig.IsResource(e.DownloadOperation.Uri)) { e.Cancel = true; return; }
                if (testReport != null && testDownloadPath != null) { e.ResultFilePath = testDownloadPath; e.Handled = true; return; }
                await Dispatcher.InvokeAsync(() =>
                {
                    var picker = new SaveFileDialog { FileName = Path.GetFileName(e.ResultFilePath), OverwritePrompt = true, InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments) };
                    if (picker.ShowDialog(this) != true) e.Cancel = true;
                    else { e.ResultFilePath = picker.FileName; e.Handled = true; }
                });
            }
            finally { deferral.Complete(); }
        };
        core.ProcessFailed += (_, _) => { if (!closing && !closed) { ShowNotice(T("The interface stopped responding. Restart the program to restore saved work.", "Interfejs przestał odpowiadać. Uruchom program ponownie, aby przywrócić zapisaną pracę.")); OfferDiscard(); } };
    }
    void SystemPreferenceChanged(object sender, Microsoft.Win32.UserPreferenceChangedEventArgs args) => Dispatcher.BeginInvoke(new Action(() => { if (!closed) TitleBar.Apply(this, appearance); }));
    void ApplyAppearance(JsonElement value)
    {
        var next = new Appearance(value.GetProperty("theme").GetString() ?? "light", value.GetProperty("titleBarMode").GetString() ?? "system", value.GetProperty("titleBarColor").GetString() ?? "#24485c");
        if (!TitleBar.Valid(next)) return;
        appearance = next; TitleBar.Apply(this, next);
        if (value.TryGetProperty("locale", out var locale)) pl = locale.GetString() == "pl";
        try { File.WriteAllText(Path.Combine(config.StateDirectory, "appearance.json"), JsonSerializer.Serialize(next)); } catch { }
    }
    void ShowClosingProgress(string text)
    {
        notice.Visibility = Visibility.Collapsed;
        if (closingProgress == null) { closingProgress = new ClosingProgress(this, appearance.Theme == "dark"); closingProgress.SetMessage(text); closingProgress.Show(); }
        else closingProgress.SetMessage(text);
    }
    void HideClosingProgress() { closingProgress?.Complete(); closingProgress = null; }
    static void OpenExternal(string address)
    {
        if (!Uri.TryCreate(address, UriKind.Absolute, out var uri) || !(uri.Scheme == "https" || AppConfig.IsLocal(address))) return;
        try { Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true }); } catch { }
    }
    async Task<JsonElement> Ui(string kind)
    {
        if (!ready || !AppConfig.IsDocument(view.Source?.AbsoluteUri ?? "")) throw new IOException("The application interface is not ready");
        string id = Guid.NewGuid().ToString("N"); var reply = new TaskCompletionSource<JsonElement>(TaskCreationOptions.RunContinuationsAsynchronously); replies.Add(id, reply);
        try { view.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(new { type = kind, id })); return await reply.Task.WaitAsync(TimeSpan.FromSeconds(kind == "prepare-close" ? 45 : 5)); }
        finally { replies.Remove(id); }
    }
    static bool Flag(JsonElement value, string name) => value.TryGetProperty(name, out var field) && field.ValueKind == JsonValueKind.True;
    async Task Poll()
    {
        if (ticking || closed || closing) return; ticking = true;
        try
        {
            if (backend.Process?.HasExited == true)
            {
                poll.Stop();
                ShowNotice(T("The application runtime stopped. Saved work will be restored after restart. Close this window to restart the program.", "Proces programu został zatrzymany. Zapisana praca zostanie przywrócona po restarcie. Zamknij to okno, aby ponownie uruchomić program."));
                return;
            }
            var status = await backend.Request();
            if (status is JsonElement state && Flag(state, "close_requested")) { await CloseApplication(maintenance: true); return; }
            if (waiting && status is JsonElement latest && !Flag(latest, "busy"))
            {
                var ui = await Ui("status");
                if (!Flag(ui, "busy") && Flag(ui, "ready")) { waiting = false; await CloseApplication(); }
            }
        }
        catch (Exception e) when (e is IOException or TimeoutException or InvalidOperationException) { }
        finally { ticking = false; }
    }
    async void OnClosing(object? sender, CancelEventArgs args)
    {
        if (allowClose) return; args.Cancel = true;
        if (!closing) await CloseApplication();
    }
    async Task CloseApplication(bool maintenance = false)
    {
        if (closed || closing) return;
        closing = true;
        try
        {
            if (!ready) { FinishClose(); return; }
            if (backend.Process?.HasExited == true)
            {
                if (testReport == null && MessageBox.Show(this,
                    T("The application runtime is unavailable. Close the window? Changes made since the last successful save may be lost.", "Proces programu jest niedostępny. Zamknąć okno? Zmiany od ostatniego poprawnego zapisu mogą zostać utracone."),
                    "EwP Transcripts", MessageBoxButton.YesNo, MessageBoxImage.Warning, MessageBoxResult.No) != MessageBoxResult.Yes) return;
                FinishClose(); return;
            }
            var ui = await Ui("status"); pl = ui.GetProperty("locale").GetString() == "pl"; ApplyAppearance(ui);
            var runtime = await backend.Request();
            bool busy = Flag(ui, "busy") || runtime is JsonElement state && Flag(state, "busy") || testReport != null && testBusy;
            if (busy && !maintenance)
            {
                var choice = testReport != null ? testChoice : CloseChoice.Show(this, pl);
                if (choice == CloseAction.Stay) return;
                if (choice == CloseAction.Wait)
                {
                    waiting = true; ShowNotice(T("The program will close after active work finishes.", "Program zamknie się po zakończeniu aktywnych zadań."));
                    if (!notice.Children.OfType<Button>().Any(button => Equals(button.Tag, "wait")))
                    {
                        var cancel = new Button { Tag = "wait", Content = T("Keep working", "Kontynuuj pracę"), HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 8, 0, 0), Padding = new Thickness(12, 4, 12, 4) };
                        cancel.Click += (_, _) => { waiting = false; notice.Children.Remove(cancel); notice.Visibility = Visibility.Collapsed; }; notice.Children.Add(cancel);
                    }
                    return;
                }
            }
            waiting = false;
            foreach (var button in notice.Children.OfType<Button>().Where(button => Equals(button.Tag, "wait")).ToArray()) notice.Children.Remove(button);
            view.IsEnabled = false;
            ShowClosingProgress(T("Saving work before closing…", "Zapisywanie pracy przed zamknięciem…"));
            var saved = await Ui("prepare-close");
            if (!Flag(saved, "ok"))
            {
                if (maintenance) await backend.Request("refuse");
                ShowNotice(T("Work could not be saved. The program remains open. Check Saved work and try again.", "Nie udało się zapisać pracy. Program pozostaje otwarty. Sprawdź Zapisaną pracę i spróbuj ponownie."));
                OfferDiscard();
                return;
            }
            ShowClosingProgress(T("Stopping active work and closing…", "Zatrzymywanie zadań i zamykanie…"));
            await backend.Request("commit");
            if (backend.Process != null)
            {
                try { await backend.Process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(30)); }
                catch (TimeoutException) { SaveDiagnostic("Graceful close timed out after durable workspace save; owned process job is being stopped."); }
            }
            FinishClose();
        }
        catch (Exception error)
        {
            if (maintenance) await backend.Request("refuse");
            ShowNotice(T("Closing was stopped to protect unsaved work. Try again after the current operation.", "Zamykanie zostało wstrzymane, aby chronić niezapisaną pracę. Spróbuj ponownie po bieżącej operacji.")); SaveDiagnostic(error.GetType().Name);
            OfferDiscard();
        }
        finally { HideClosingProgress(); closing = false; if (!closed) view.IsEnabled = true; }
    }
    void FinishClose() { if (closed) return; placement.Save(this); HideClosingProgress(); allowClose = true; Close(); }
    void SaveDiagnostic(string error)
    {
        try { File.WriteAllText(Path.Combine(config.StateDirectory, "desktop.log"), DateTimeOffset.Now.ToString("o") + "\n" + error + "\n" + backend.Diagnostic); } catch { }
    }
    void OnClosed(object? sender, EventArgs args)
    {
        closed = true; poll.Stop();
        foreach (var item in replies.Values) item.TrySetCanceled();
        geometryTimer.Stop(); Microsoft.Win32.SystemEvents.UserPreferenceChanged -= SystemPreferenceChanged;
        HideClosingProgress();
        view.Dispose(); backend.Dispose();
    }
}
