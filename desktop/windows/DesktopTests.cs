using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Web.WebView2.Core;

namespace EwP.Desktop;

sealed partial class DesktopWindow
{
    readonly List<string> testChecks = new();
    bool isolatedTest;
    int testManagerPid, testServerPid;
    void Check(bool condition, string name) { if (!condition) throw new InvalidOperationException("Desktop self-test: " + name); testChecks.Add(name); }
    void WriteTestResult(string result, string error = "")
    {
        if (testReport == null) return;
        File.WriteAllText(testReport, JsonSerializer.Serialize(new { result, error, version = System.Reflection.Assembly.GetExecutingAssembly().GetName().Version!.ToString(3), pid = Environment.ProcessId, manager_pid = testManagerPid, server_pid = testServerPid, window_handle = new System.Windows.Interop.WindowInteropHelper(this).Handle.ToInt64(), state_directory = config.StateDirectory, window_placement = WindowPlacement.Capture(this), startup_placement = startupPlacement, startup_appearance = startupAppearance, appearance, checks = testChecks }));
    }
    async Task Until(Func<Task<bool>> check, int seconds = 40)
    {
        var deadline = DateTime.UtcNow.AddSeconds(seconds);
        while (DateTime.UtcNow < deadline) { if (await check()) return; await Task.Delay(100); }
        throw new TimeoutException("Desktop self-test condition timed out");
    }
    async Task<bool> ScriptFlag(string code) => await view.ExecuteScriptAsync(code) == "true";
    async Task TestFailure(Exception error)
    {
        string detail = error.Message + "\n" + backend.Diagnostic;
        if (isolatedTest)
        {
            try
            {
                await CaptureUi("failure");
                detail += "\n" + await view.ExecuteScriptAsync("JSON.stringify({ready:automaticRecoveryReady,restoring:workspaceRestoreBusy,autosave:workspaceAutosaveStatus.textContent,workspace:workspaceStatus.textContent,pending:collectPendingGuiMedia().length,options:[...workspaceList.options].map(o=>({available:o.dataset.available,value:o.value}))})");
            }
            catch { }
        }
        WriteTestResult("FAIL", detail);
    }
    static string TestWave()
    {
        using var stream = new MemoryStream(); using var writer = new BinaryWriter(stream);
        writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(356);
        writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16);
        writer.Write((short)1); writer.Write((short)1); writer.Write(16000); writer.Write(32000);
        writer.Write((short)2); writer.Write((short)16); writer.Write(System.Text.Encoding.ASCII.GetBytes("data"));
        writer.Write(320); writer.Write(new byte[320]);
        return Convert.ToBase64String(stream.ToArray());
    }
    async Task CaptureUi(string name)
    {
        if (previews == null) return;
        Directory.CreateDirectory(previews); await Task.Delay(150);
        using var target = File.Create(Path.Combine(previews, name + ".png"));
        await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, target);
    }
    async Task SelfTest()
    {
        // Explicit model-free qualification only: never inject test content into a real installation.
        using var owner = JsonDocument.Parse(File.ReadAllText(Path.Combine(config.Root, "owner.json")));
        Check(owner.RootElement.GetProperty("id").GetString() == "native-desktop-test", "isolated owned test installation");
        isolatedTest = true;
        await Until(async () => Flag(await Ui("status"), "ready"));
        testManagerPid = backend.Process!.Id;
        var runtime = (await backend.Request())!.Value; testServerPid = runtime.GetProperty("pid").GetInt32();
        Check(Flag(runtime, "desktop") && !Flag(runtime, "busy"), "authenticated owned desktop backend ready");
        Check(GetConsoleWindow() == IntPtr.Zero, "native application has no console");
        Check(startupAppearance.Theme == (startupAppearance.ThemePreference == "system" ? TitleBar.SystemDark ? "dark" : "light" : startupAppearance.Theme),
            "first or system-preference startup follows Windows; explicit saved theme remains selected");
        Check(await ScriptFlag($"document.documentElement.dataset.theme==='{startupAppearance.Theme}'"),
            "first displayed document matches the startup surface theme");
        if (Environment.GetEnvironmentVariable("EWP_DESKTOP_EXPECT_AMD") == "1")
            Check(await ScriptFlag("document.documentElement.dataset.localAccelerator==='amd' && document.querySelector('#cloud-asr-provider option[value=local]').textContent.includes('(experimental)')"), "managed AMD profile is visibly experimental in the actual renderer without loading models");
        await CheckPlacement();
        Check(!AppConfig.IsLocal("http://127.0.0.1:8765.evil/") && !AppConfig.IsLocal("http://localhost:8765/") && !AppConfig.IsResource("file:///C:/private") && !AppConfig.IsResource("https://example.com/"), "strict loopback origin and resource rules");
        Check(!AppConfig.IsDocument(AppConfig.Origin + "/help") && !AppConfig.IsDocument(AppConfig.Origin + "/assets/app.js"), "only the root document can answer native lifecycle requests");
        await view.ExecuteScriptAsync("window.nativeBlocked=false;fetch('https://example.com/').then(r=>{window.nativeBlocked=r.status===403}).catch(()=>{window.nativeBlocked=true})");
        await Until(() => ScriptFlag("window.nativeBlocked===true"));
        Check(true, "renderer cannot fetch external resources");
        bool restored = (await Ui("status")).GetProperty("pending_count").GetInt32() > 0;
        if (Environment.GetEnvironmentVariable("EWP_DESKTOP_EXPECT_RECOVERY") == "1") Check(restored, "pending media survived the previous full application shutdown");
        if (!restored)
        {
            await view.ExecuteScriptAsync("(()=>{const d=new DataTransfer();d.items.add(new File([Uint8Array.from(atob('" + TestWave() + "'),c=>c.charCodeAt(0))],'native-test-s00e01.wav',{type:'audio/wav'}));nativeMediaInput.files=d.files;nativeMediaInput.dispatchEvent(new Event('change',{bubbles:true}));})()");
            await Until(async () => (await Ui("status")).GetProperty("pending_count").GetInt32() == 1);
            Check(!await ScriptFlag("guiQueueJobs.some(j=>['queued','running'].includes(j.status))"), "adding media does not plan or start transcription");
        }
        else Check(!await ScriptFlag("guiQueueJobs.some(j=>['queued','running'].includes(j.status))"), "recovery restores pending media without restarting processing");
        poll.Stop(); testBusy = true; testChoice = CloseAction.Stay;
        await CloseApplication(); Check(!closed && !waiting, "Keep working cancels native close");
        testChoice = CloseAction.Wait; await CloseApplication();
        Check(waiting && !closed && !backend.Process.HasExited, "Wait keeps the window and backend alive");
        notice.Children.OfType<Button>().Single().RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        Check(!waiting, "waiting for close can be cancelled"); testBusy = false; testChoice = CloseAction.Stop; poll.Start();
        foreach (var (locale, theme) in new[] { ("pl", "light"), ("en", "dark") })
        {
            await view.ExecuteScriptAsync($"(()=>{{const l=document.querySelector('#gui-locale');l.value='{locale}';l.dispatchEvent(new Event('change'));const t=document.querySelector('#gui-theme');t.value='{theme}';t.dispatchEvent(new Event('change'));}})()");
            await CaptureUi(locale + "-desktop-" + theme);
            await CheckPersonalization(locale, theme);
            Check((await Ui("status")).GetProperty("locale").GetString() == locale, "native lifecycle follows explicit " + locale + " preference");
        }
        await view.ExecuteScriptAsync("workspaceName.value='x'.repeat(101)");
        await Until(async () => !Flag(await Ui("status"), "busy"));
        await CloseApplication();
        Check(!backend.Process.HasExited && !closed && view.IsEnabled && notice.Visibility == Visibility.Visible, "invalid work state refuses close and keeps backend/window alive");
        poll.Stop(); testBusy = true; testChoice = CloseAction.Wait;
        await CloseApplication();
        notice.Children.OfType<Button>().Single(button => Equals(button.Tag, "wait")).RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        Check(!waiting && !closed, "waiting remains cancellable after an earlier save failure");
        testBusy = false; testChoice = CloseAction.Stop; poll.Start();
        await view.ExecuteScriptAsync("workspaceName.value=''");
        await view.ExecuteScriptAsync("workspaceAutosave.checked=false");
        Check(Flag(await Ui("prepare-close"), "ok"), "close flush durably saves pending media without a chosen name");
        Check(await ScriptFlag("!workspaceAutosave.checked"), "close saves explicitly without re-enabling a disabled autosave preference");
        await view.ExecuteScriptAsync("workspaceAutosave.checked=true");
        Check(!Flag(await Ui("status"), "dirty"), "no dirty state remains after close flush");
        Check(!await ScriptFlag("guiQueueJobs.some(j=>['queued','running'].includes(j.status))"), "close flush never starts the queue");
        await view.ExecuteScriptAsync("guiQueueJobs=[{job_id:'native-progress',status:'running',updated_at:'0'}];window.nativeProgressTicks=0;window.nativeProgressTimer=setInterval(()=>{window.nativeProgressTicks++;if(guiQueueJobs[0])guiQueueJobs[0].updated_at=String(Date.now())},5)");
        Check(Flag(await Ui("prepare-close"), "ok") && await ScriptFlag("window.nativeProgressTicks>0"), "changing queue metrics do not block durable close-save");
        await view.ExecuteScriptAsync("clearInterval(window.nativeProgressTimer);guiQueueJobs=[]");
        testDownloadPath = Path.Combine(Path.GetDirectoryName(testReport!)!, "desktop-notice-download.txt");
        await view.ExecuteScriptAsync("(()=>{const a=document.createElement('a');a.href='/assets/brand/NOTICE.txt';a.download='notice.txt';document.body.append(a);a.click();a.remove();})()");
        await Until(() => Task.FromResult(File.Exists(testDownloadPath)));
        Check(File.ReadAllText(testDownloadPath).Contains("Cyryl"), "embedded download writes the selected local file"); testDownloadPath = null;
        if (previews != null) CloseChoice.CaptureAndCheck(this, previews);
        // First restart checks normal bounds; subsequent restarts also check maximization.
        WindowState = restored ? WindowState.Maximized : WindowState.Normal;
        if (Environment.GetEnvironmentVariable("EWP_DESKTOP_SNAP_TEST") == "1") await SnapLeftForTest();
        if (Environment.GetEnvironmentVariable("EWP_DESKTOP_FINAL_LIGHT") == "1")
        {
            await view.ExecuteScriptAsync("(()=>{const t=document.querySelector('#gui-theme');t.value='light';t.dispatchEvent(new Event('change'));})()");
            await Until(() => Task.FromResult(appearance.Theme == "light"));
            CheckSurfaceTheme("final-light-before-restart");
        }
        placement.Save(this);
        WriteTestResult("PASS");
        // A crash qualification caller keeps the host alive until it verifies same-instance activation
        // and kills it externally. Normal qualification executes the real save/stop/close path.
        if (Environment.GetEnvironmentVariable("EWP_DESKTOP_CRASH_TEST") != "1") await CloseApplication();
    }
    [DllImport("kernel32.dll")] static extern IntPtr GetConsoleWindow();
}
