using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media.Imaging;

namespace EwP.Desktop;

sealed partial class DesktopWindow
{
    // Test-only whole-window capture: renderer previews omit the native caption/frame.
    void CaptureFrame(string name)
    {
        if (previews == null) return;
        Directory.CreateDirectory(previews);
        var handle = new WindowInteropHelper(this).Handle;
        GetWindowRect(handle, out var rect); int width = rect.Right - rect.Left, height = rect.Bottom - rect.Top;
        var source = GetWindowDC(handle); var memory = CreateCompatibleDC(source);
        var bitmap = CreateCompatibleBitmap(source, width, height); var previous = SelectObject(memory, bitmap);
        try
        {
            DwmFlush();
            Check(PrintWindow(handle, memory, 2), "whole native window including caption can be captured");
            var image = Imaging.CreateBitmapSourceFromHBitmap(bitmap, IntPtr.Zero, Int32Rect.Empty, BitmapSizeOptions.FromEmptyOptions());
            var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(image));
            using var file = File.Create(Path.Combine(previews, name + ".png")); encoder.Save(file);
        }
        finally { SelectObject(memory, previous); DeleteObject(bitmap); DeleteDC(memory); ReleaseDC(handle, source); }
    }
    [StructLayout(LayoutKind.Sequential)] struct FrameRect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr window, out FrameRect rect);
    [DllImport("user32.dll")] static extern IntPtr GetWindowDC(IntPtr window);
    [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr window, IntPtr dc);
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr window, IntPtr dc, uint flags);
    [DllImport("gdi32.dll")] static extern IntPtr CreateCompatibleDC(IntPtr dc);
    [DllImport("gdi32.dll")] static extern IntPtr CreateCompatibleBitmap(IntPtr dc, int width, int height);
    [DllImport("gdi32.dll")] static extern IntPtr SelectObject(IntPtr dc, IntPtr bitmap);
    [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr value);
    [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr dc);
    [DllImport("dwmapi.dll")] static extern int DwmFlush();
}
