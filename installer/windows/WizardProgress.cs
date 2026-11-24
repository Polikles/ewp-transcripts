using System.Diagnostics;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace EwP.Setup;

sealed partial class Wizard
{
    readonly Stopwatch operationClock = new();
    readonly TextBlock elapsedProgress = Copy("", muted: true);
    readonly TextBlock activityProgress = Copy("", muted: true);
    readonly TextBlock downloadProgress = Copy("", muted: true);
    readonly ProgressBar operationProgress = new() { Height = 10, Minimum = 0, Maximum = 100, Margin = new Thickness(0, 0, 0, 12) };
    DispatcherTimer? progressTimer;

    void ResetOperationProgress()
    {
        operationClock.Reset(); activityProgress.Text = downloadProgress.Text = elapsedProgress.Text = "";
        operationProgress.IsIndeterminate = true; operationProgress.Value = 0;
    }
    void RenderOperationProgress()
    {
        if (!busy && !finished) return;
        foreach (var text in new[] { elapsedProgress, activityProgress, downloadProgress }) text.Visibility = text.Text.Length > 0 ? Visibility.Visible : Visibility.Collapsed;
        foreach (FrameworkElement control in new FrameworkElement[] { operationProgress, elapsedProgress, activityProgress, downloadProgress })
        {
            if (control.Parent is Panel parent) parent.Children.Remove(control);
            body.Children.Add(control);
        }
        if (finished) { operationProgress.IsIndeterminate = false; operationProgress.Value = successful ? 100 : 0; }
        if (progressTimer == null)
        {
            progressTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            progressTimer.Tick += (_, _) => { elapsedProgress.Text = T("Elapsed: ", "Czas: ") + operationClock.Elapsed.ToString(@"hh\:mm\:ss"); foreach (var text in new[] { elapsedProgress, activityProgress, downloadProgress }) text.Visibility = text.Text.Length > 0 ? Visibility.Visible : Visibility.Collapsed; };
            progressTimer.Start(); Closed += (_, _) => progressTimer.Stop();
        }
    }
    void UpdateOperationProgress(string stage, string text, JsonElement? item)
    {
        if (page != 3) return;
        if (stage == "download" && item is JsonElement data && data.TryGetProperty("bytes", out var count) &&
            data.TryGetProperty("total", out var total) && total.ValueKind == JsonValueKind.Number && total.GetDouble() > 0)
        {
            bool bytes = data.TryGetProperty("unit", out var unit) && unit.GetString() == "B";
            double downloaded = count.GetDouble(), size = total.GetDouble();
            operationProgress.IsIndeterminate = false; operationProgress.Value = Math.Clamp(downloaded / size * 100, 0, 100);
            string amount = bytes ? GB((long)downloaded) + " / " + GB((long)size) + " GB" : downloaded + " / " + size;
            string eta = data.TryGetProperty("eta_seconds", out var remaining) && remaining.ValueKind == JsonValueKind.Number
                ? " · ~" + TimeSpan.FromSeconds(Math.Clamp(remaining.GetDouble(), 0, 864000)).ToString(@"hh\:mm\:ss") : "";
            string rate = bytes && data.TryGetProperty("rate", out var speed) && speed.ValueKind == JsonValueKind.Number ? " · " + (speed.GetDouble() / 1e6).ToString("0.0") + " MB/s" : "";
            downloadProgress.Text = text + " · " + amount + rate + eta; downloadProgress.Visibility = Visibility.Visible; return;
        }
        if (stage != "log" && stage.Length > 0)
        {
            operationProgress.IsIndeterminate = true; downloadProgress.Text = "";
            activityProgress.Text = "";
        }
        if (stage == "log" && text.Length > 4 && text.Length < 300 && !text.TrimStart().StartsWith('"') && !text.TrimStart().StartsWith('{'))
            activityProgress.Text = text;
    }
}
