using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace EwP.Setup;

sealed class AmdWarning : Window
{
    public bool Accepted { get; private set; }
    internal readonly Button Continue;
    public AmdWarning(Window owner, bool pl)
    {
        Owner = owner; Title = "AMD (experimental)"; Width = 540;
        SizeToContent = SizeToContent.Height; ResizeMode = ResizeMode.NoResize;
        WindowStartupLocation = WindowStartupLocation.CenterOwner; ShowInTaskbar = false;
        Background = owner.Background; Foreground = owner.Foreground;
        var panel = new StackPanel();
        panel.Children.Add(new TextBlock { Text = pl ? "obsługa kart AMD jest eksperymentalna i nie została przetestowana" : "AMD GPU support is experimental and has not been tested.", TextWrapping = TextWrapping.Wrap, FontSize = 18, Margin = new Thickness(0, 0, 0, 18) });
        Continue = new Button { Content = pl ? "Rozumiem, kontynuuj" : "I understand, continue", Padding = new Thickness(16, 8, 16, 8), HorizontalAlignment = HorizontalAlignment.Right, IsDefault = true };
        Continue.Click += (_, _) => { Accepted = true; Close(); };
        panel.Children.Add(Continue); Content = new Border { Padding = new Thickness(24), Background = Background, Child = panel };
    }
}

sealed partial class Wizard
{
    readonly HashSet<string> amdAcknowledgements = [];
    internal Func<AmdWarning, bool>? AmdWarningTest;
    string AmdKey
    {
        get
        {
            if (operation is not ("install" or "update") || host is not JsonElement report) return "";
            foreach (var row in report.GetProperty("checks").EnumerateArray())
                if (row.GetProperty("code").GetString() == "gpu" && row.TryGetProperty("context", out var context)
                    && context.TryGetProperty("amd_devices", out var devices) && devices.GetArrayLength() > 0)
                    return operation + "|" + devices.GetRawText();
            return "";
        }
    }
    bool AmdAccepted => AmdKey.Length == 0 || amdAcknowledgements.Contains(AmdKey);
    void ShowAmdWarning()
    {
        if (AmdAccepted) return;
        string key = AmdKey;
        var dialog = new AmdWarning(this, Pl);
        bool accepted;
        if (AmdWarningTest != null) accepted = AmdWarningTest(dialog);
        else { dialog.ShowDialog(); accepted = dialog.Accepted; }
        if (accepted) amdAcknowledgements.Add(key);
        Render();
    }
}
