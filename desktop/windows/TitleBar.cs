using System.Globalization;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Interop;
using Microsoft.Win32;

namespace EwP.Desktop;

sealed record Appearance(string Theme = "light", string TitleBarMode = "system", string TitleBarColor = "#24485c");
static class TitleBar
{
    public static bool SystemDark
    {
        get { try { return Convert.ToInt32(Registry.GetValue(@"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 1)) == 0; } catch { return false; } }
    }
    public static bool Valid(Appearance value) => value.Theme is "light" or "dark" && value.TitleBarMode is "system" or "application" or "custom" && Regex.IsMatch(value.TitleBarColor, "^#[a-fA-F0-9]{6}$");
    static uint ColorRef(string color) { uint rgb = uint.Parse(color.AsSpan(1), NumberStyles.HexNumber); return (rgb >> 16) | (rgb & 0xff00) | ((rgb & 0xff) << 16); }
    public static void Apply(Window window, Appearance value)
    {
        if (!Valid(value)) return;
        var handle = new WindowInteropHelper(window).Handle; if (handle == IntPtr.Zero) return;
        bool dark = value.TitleBarMode == "system" ? SystemDark : value.Theme == "dark";
        uint caption = value.TitleBarMode == "system" ? uint.MaxValue : ColorRef(value.TitleBarMode == "custom" ? value.TitleBarColor : dark ? "#12303f" : "#f5f2e9");
        uint text = uint.MaxValue;
        if (caption != uint.MaxValue)
        {
            static double Linear(double channel) => channel <= .04045 ? channel / 12.92 : Math.Pow((channel + .055) / 1.055, 2.4);
            double luminance = .2126 * Linear((caption & 255) / 255d) + .7152 * Linear(((caption >> 8) & 255) / 255d) + .0722 * Linear(((caption >> 16) & 255) / 255d);
            text = luminance > .179 ? 0u : 0xffffffu; dark = text != 0;
        }
        uint immersive = dark ? 1u : 0u;
        DwmSetWindowAttribute(handle, 20, ref immersive, 4); DwmSetWindowAttribute(handle, 35, ref caption, 4); DwmSetWindowAttribute(handle, 36, ref text, 4);
    }
    internal static uint ReadCaption(Window window) { uint value = 0; if (DwmGetWindowAttribute(new WindowInteropHelper(window).Handle, 35, out value, 4) != 0) throw new InvalidOperationException("Title bar color could not be read"); return value; }
    [DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr window, int attribute, ref uint value, int size);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr window, int attribute, out uint value, int size);
}
