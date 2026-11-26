using System.Globalization;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Interop;
using Microsoft.Win32;

namespace EwP.Desktop;

sealed record Appearance(string Theme = "light", string TitleBarMode = "system", string TitleBarColor = "#24485c");
sealed record AppliedAppearance(uint Caption, uint Text, int ImmersiveResult, int CaptionResult, int TextResult)
{
    public bool Succeeded => ImmersiveResult == 0 && CaptionResult == 0 && TextResult == 0;
}
static class TitleBar
{
    public static bool SystemDark
    {
        get { try { return Convert.ToInt32(Registry.GetValue(@"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 1)) == 0; } catch { return false; } }
    }
    public static bool Valid(Appearance value) => value.Theme is "light" or "dark" && value.TitleBarMode is "system" or "application" or "custom" && Regex.IsMatch(value.TitleBarColor, "^#[a-fA-F0-9]{6}$");
    static uint ColorRef(string color) { uint rgb = uint.Parse(color.AsSpan(1), NumberStyles.HexNumber); return (rgb >> 16) | (rgb & 0xff00) | ((rgb & 0xff) << 16); }
    public static AppliedAppearance? Apply(Window window, Appearance value)
    {
        if (!Valid(value)) return null;
        var handle = new WindowInteropHelper(window).Handle; if (handle == IntPtr.Zero) return null;
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
        int modeResult = DwmSetWindowAttribute(handle, 20, ref immersive, 4);
        int captionResult = DwmSetWindowAttribute(handle, 35, ref caption, 4);
        int textResult = DwmSetWindowAttribute(handle, 36, ref text, 4);
        return new(caption, text, modeResult, captionResult, textResult);
    }
    [DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr window, int attribute, ref uint value, int size);
}
