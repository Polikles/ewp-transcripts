using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace EwP.Desktop;

sealed partial class DesktopWindow
{
    async Task SnapLeftForTest()
    {
        WindowState = WindowState.Normal; BringToFront();
        var before = WindowPlacement.Capture(this)!;
        TestKey(0x5b, 0, 0, UIntPtr.Zero); TestKey(0x25, 0, 0, UIntPtr.Zero);
        TestKey(0x25, 0, 2, UIntPtr.Zero); TestKey(0x5b, 0, 2, UIntPtr.Zero);
        await Until(() => Task.FromResult(WindowPlacement.Capture(this) is { ScreenCoordinates: true } value
            && value.Right - value.Left < before.Right - before.Left - 100), 10);
        placement.Save(this);
        var snapped = placement.Saved!;
        Check(!snapped.Maximized && snapped.ScreenCoordinates && snapped.Right - snapped.Left < before.Right - before.Left - 100,
            "actual Windows Win+Left Snap persists the visible half-screen rectangle");
        CaptureFrame("windows-snap-left");
    }
    [System.Runtime.InteropServices.DllImport("user32.dll", EntryPoint = "keybd_event")]
    static extern void TestKey(byte key, byte scan, uint flags, UIntPtr extra);
    async Task CheckPlacement()
    {
        var current = WindowPlacement.Capture(this);
        if (startupPlacement != null)
            Check(current == startupPlacement, "restart restores exact normal position, size and maximized state");
        else Check(WindowStartupLocation == WindowStartupLocation.CenterScreen, "no saved placement uses centered default");
        string fixture = Path.Combine(Path.GetDirectoryName(testReport!)!, "invalid-window.json");
        foreach (string invalid in new[] { "broken", "{\"Width\":900,\"Height\":600}", "{\"Left\":5,\"Top\":5,\"Right\":4,\"Bottom\":4}" })
        {
            File.WriteAllText(fixture, invalid);
            Check(new WindowPlacement(fixture).Saved == null, "invalid or legacy window geometry falls back safely");
        }
        File.WriteAllText(fixture, JsonSerializer.Serialize(new SavedPlacement(50000, 50000, 50800, 50600, false)));
        var detached = new Window { Width = 800, Height = 600, ShowInTaskbar = false };
        try
        {
            detached.Show();
            Check(new WindowPlacement(fixture).Restore(detached), "valid off-screen geometry can be restored");
            await Task.Delay(100);
            Check(detached.Left < SystemParameters.WorkArea.Right && detached.Top < SystemParameters.WorkArea.Bottom
                && detached.Left + detached.ActualWidth > SystemParameters.WorkArea.Left
                && detached.Top + detached.ActualHeight > SystemParameters.WorkArea.Top,
                "Windows recovers a saved position from an unavailable monitor");
        }
        finally { detached.Close(); File.Delete(fixture); }
        WindowState = WindowState.Normal;
        Left = SystemParameters.WorkArea.Left + 24; Top = SystemParameters.WorkArea.Top + 28;
        Width = Math.Min(1120, SystemParameters.WorkArea.Width - 64);
        Height = Math.Min(800, SystemParameters.WorkArea.Height - 64);
        await Task.Delay(100); placement.Save(this);
        Check(placement.Saved == WindowPlacement.Capture(this) && placement.Saved?.Valid == true,
            "nondefault window position and size are saved before HWND destruction");
    }
    async Task CheckPersonalization(string locale, string theme)
    {
        await view.ExecuteScriptAsync("showGuiStage('settings');document.querySelector('#gui-personalization').click()");
        Check(await ScriptFlag("document.querySelector('#gui-personalization-dialog').open && !document.querySelector('#gui-personal-native').hidden"), "desktop personalization includes native title-bar settings");
        await view.ExecuteScriptAsync("(()=>{let m=document.querySelector('#gui-titlebar-mode');m.value='custom';m.dispatchEvent(new Event('input'));let c=document.querySelector('#gui-titlebar-color');c.value='#5b193f';c.dispatchEvent(new Event('input'));})()");
        await Until(() => Task.FromResult(appliedAppearance?.Caption == 0x3f195b));
        Check(appliedAppearance!.Succeeded, "DWM accepts custom caption and contrasting text attributes");
        CaptureFrame(locale + "-custom-titlebar-" + theme);
        await CaptureUi(locale + "-personalization-" + theme);
        await view.ExecuteScriptAsync("(()=>{let m=document.querySelector('#gui-titlebar-mode');m.value='system';m.dispatchEvent(new Event('input'));})()");
        await Until(() => Task.FromResult(appliedAppearance?.Caption == uint.MaxValue));
        Check(appliedAppearance!.Succeeded, "DWM accepts resetting caption and text to system defaults");
        await view.ExecuteScriptAsync("(()=>{let m=document.querySelector('#gui-titlebar-mode');m.value='application';m.dispatchEvent(new Event('input'));document.querySelector('#gui-personal-close').click();})()");
        await Until(() => Task.FromResult(appliedAppearance?.Caption == (theme == "dark" ? 0x3f3012u : 0xe9f2f5u)));
        Check(appliedAppearance!.Succeeded, "DWM accepts caption and text matching the resolved app theme");
        CaptureFrame(locale + "-application-titlebar-" + theme);
        using (var saved = JsonDocument.Parse(File.ReadAllText(Path.Combine(config.StateDirectory, "appearance.json"))))
            Check(saved.RootElement.GetProperty("Theme").GetString() == theme, "resolved native appearance is cached for next startup");
        ShowClosingProgress(T("Saving work before closing…", "Zapisywanie pracy przed zamknięciem…"));
        var dialog = closingProgress!; dialog.UpdateLayout();
        Check(Math.Abs(dialog.Left + dialog.ActualWidth / 2 - Left - ActualWidth / 2) < 3
            && Math.Abs(dialog.Top + dialog.ActualHeight / 2 - Top - ActualHeight / 2) < 3,
            "saving and closing progress is centered on its owner");
        Check(((SolidColorBrush)dialog.Background).Color == (Color)ColorConverter.ConvertFromString(theme == "dark" ? "#f5f2e9" : "#12303f"),
            "closing progress uses the opposite app theme for contrast");
        if (previews != null)
        {
            var target = (FrameworkElement)dialog.Content;
            var bitmap = new RenderTargetBitmap((int)target.ActualWidth, (int)target.ActualHeight, 96, 96, PixelFormats.Pbgra32); bitmap.Render(target);
            var pixel = new byte[4]; bitmap.CopyPixels(new Int32Rect(5, 5, 1, 1), pixel, 4, 0);
            Check(pixel[3] == 255, "closing progress preview has an opaque contrasting background");
            var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap));
            using var file = File.Create(Path.Combine(previews, locale + "-saving-" + theme + ".png")); encoder.Save(file);
        }
        HideClosingProgress();
        await view.ExecuteScriptAsync("showGuiStage('review');sourcePlayback.hidden=false");
        Check(await ScriptFlag("sourcePlayback.parentElement.id==='gui-sidebar' && playbackAudio.getBoundingClientRect().width<=224 && document.querySelector('main').getBoundingClientRect().right<=innerWidth"),
            "review player stays bounded in the left sidebar without pushing main content outside the window");
        await CaptureUi(locale + "-sidebar-player-" + theme);
        await view.ExecuteScriptAsync("syncSourcePlayback();showGuiStage('workspace')");
    }
}
