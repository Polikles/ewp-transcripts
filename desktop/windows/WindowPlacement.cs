using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;

namespace EwP.Desktop;

sealed record SavedPlacement(int Left, int Top, int Right, int Bottom, bool Maximized, bool ScreenCoordinates = false)
{
    public bool Valid => Right - (long)Left is >= 200 and <= 30000 && Bottom - (long)Top is >= 150 and <= 30000
        && Math.Abs((long)Left) <= 100000 && Math.Abs((long)Top) <= 100000;
}

sealed class WindowPlacement(string path)
{
    public SavedPlacement? Saved { get; private set; } = Read(path);
    SavedPlacement? observed;
    static SavedPlacement? Read(string path)
    {
        try { var value = JsonSerializer.Deserialize<SavedPlacement>(File.ReadAllText(path)); return value?.Valid == true ? value : null; } catch { return null; }
    }
    public static SavedPlacement? Capture(Window window)
    {
        var value = new Placement { Length = Marshal.SizeOf<Placement>() };
        if (!GetWindowPlacement(new WindowInteropHelper(window).Handle, ref value)) return null;
        bool max = value.Show == 3 || value.Show == 2 && (value.Flags & 2) != 0;
        var bounds = value.Normal;
        // Windows Snap can leave rcNormalPosition at the pre-Snap size. Save the actual HWND
        // rectangle in screen coordinates for ordinary/snapped windows, including resize borders.
        bool actual = false;
        if (value.Show == 1 && ReadWindowRect(new WindowInteropHelper(window).Handle, out var rectangle)) { bounds = rectangle; actual = true; }
        return new(bounds.Left, bounds.Top, bounds.Right, bounds.Bottom, max, actual);
    }
    public bool Restore(Window window)
    {
        if (Saved?.Valid != true) return false;
        if (Saved.ScreenCoordinates && !Saved.Maximized)
        {
            var rect = new Bounds { Left = Saved.Left, Top = Saved.Top, Right = Saved.Right, Bottom = Saved.Bottom };
            var monitor = new MonitorInfo { Size = Marshal.SizeOf<MonitorInfo>() };
            if (GetMonitorInfo(MonitorFromRect(ref rect, 2), ref monitor))
            {
                var work = monitor.Work;
                if (rect.Right <= work.Left || rect.Left >= work.Right || rect.Bottom <= work.Top || rect.Top >= work.Bottom)
                {
                    int width = Math.Min(rect.Right - rect.Left, work.Right - work.Left);
                    int height = Math.Min(rect.Bottom - rect.Top, work.Bottom - work.Top);
                    rect = new Bounds { Left = work.Left, Top = work.Top, Right = work.Left + width, Bottom = work.Top + height };
                }
            }
            return SetWindowPos(new WindowInteropHelper(window).Handle, IntPtr.Zero, rect.Left, rect.Top,
                rect.Right - rect.Left, rect.Bottom - rect.Top, 0x14);
        }
        var value = new Placement { Length = Marshal.SizeOf<Placement>(), Show = Saved.Maximized ? 3 : 1,
            Normal = new Bounds { Left = Saved.Left, Top = Saved.Top, Right = Saved.Right, Bottom = Saved.Bottom } };
        return SetWindowPlacement(new WindowInteropHelper(window).Handle, ref value);
    }
    public void Save(Window window)
    {
        try
        {
            Observe(window);
            var value = observed ?? Capture(window); if (value?.Valid != true) return;
            File.WriteAllText(path + ".tmp", JsonSerializer.Serialize(value)); File.Move(path + ".tmp", path, true); Saved = value;
        }
        catch { }
    }
    public void Observe(Window window)
    {
        // Keep the last actual normal/maximized geometry while minimized; its HWND rectangle
        // otherwise represents the minimized icon or the pre-Snap restore rectangle.
        if (window.WindowState != WindowState.Minimized && Capture(window) is { Valid: true } value) observed = value;
    }
    public static void Reveal(Window window) { if (window.WindowState == WindowState.Minimized) ShowWindow(new WindowInteropHelper(window).Handle, 9); }
    [StructLayout(LayoutKind.Sequential)] struct Point { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] struct Bounds { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] struct Placement { public int Length, Flags, Show; public Point Minimum, Maximum; public Bounds Normal; }
    [StructLayout(LayoutKind.Sequential)] struct MonitorInfo { public int Size; public Bounds Monitor, Work; public int Flags; }
    [DllImport("user32.dll", EntryPoint = "GetWindowRect")] static extern bool ReadWindowRect(IntPtr window, out Bounds rect);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr window, IntPtr after, int x, int y, int width, int height, uint flags);
    [DllImport("user32.dll")] static extern IntPtr MonitorFromRect(ref Bounds rect, uint flags);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] static extern bool GetMonitorInfo(IntPtr monitor, ref MonitorInfo info);
    [DllImport("user32.dll")] static extern bool GetWindowPlacement(IntPtr window, ref Placement placement);
    [DllImport("user32.dll")] static extern bool SetWindowPlacement(IntPtr window, ref Placement placement);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr window, int command);
}
