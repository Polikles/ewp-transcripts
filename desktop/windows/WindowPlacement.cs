using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;

namespace EwP.Desktop;

sealed record SavedPlacement(int Left, int Top, int Right, int Bottom, bool Maximized)
{
    public bool Valid => Right - (long)Left is >= 200 and <= 30000 && Bottom - (long)Top is >= 150 and <= 30000
        && Math.Abs((long)Left) <= 100000 && Math.Abs((long)Top) <= 100000;
}

sealed class WindowPlacement(string path)
{
    public SavedPlacement? Saved { get; private set; } = Read(path);
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
        return new(bounds.Left, bounds.Top, bounds.Right, bounds.Bottom, max);
    }
    public bool Restore(Window window)
    {
        if (Saved?.Valid != true) return false;
        var value = new Placement { Length = Marshal.SizeOf<Placement>(), Show = Saved.Maximized ? 3 : 1,
            Normal = new Bounds { Left = Saved.Left, Top = Saved.Top, Right = Saved.Right, Bottom = Saved.Bottom } };
        return SetWindowPlacement(new WindowInteropHelper(window).Handle, ref value);
    }
    public void Save(Window window)
    {
        try
        {
            var value = Capture(window); if (value?.Valid != true) return;
            File.WriteAllText(path + ".tmp", JsonSerializer.Serialize(value)); File.Move(path + ".tmp", path, true); Saved = value;
        }
        catch { }
    }
    public static void Reveal(Window window) { if (window.WindowState == WindowState.Minimized) ShowWindow(new WindowInteropHelper(window).Handle, 9); }
    [StructLayout(LayoutKind.Sequential)] struct Point { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] struct Bounds { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] struct Placement { public int Length, Flags, Show; public Point Minimum, Maximum; public Bounds Normal; }
    [DllImport("user32.dll")] static extern bool GetWindowPlacement(IntPtr window, ref Placement placement);
    [DllImport("user32.dll")] static extern bool SetWindowPlacement(IntPtr window, ref Placement placement);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr window, int command);
}
