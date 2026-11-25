using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;

namespace EwP.Setup;

sealed partial class Wizard
{
    readonly Stopwatch operationClock = new();
    readonly TextBlock elapsedProgress = Copy("", muted: true), activityProgress = Copy("", muted: true);
    readonly TextBlock overallProgressText = Copy("", muted: true), downloadsSummary = Copy("", muted: true);
    readonly TextBlock downloadProgress = Copy("", muted: true), downloadAmount = Copy("", muted: true), downloadRate = Copy("", muted: true), downloadEta = Copy("", muted: true);
    readonly ProgressBar operationProgress = new() { Height = 10, Minimum = 0, Maximum = 100, Margin = new Thickness(0, 0, 0, 12) };
    readonly ProgressBar overallProgress = new() { Height = 10, Minimum = 0, Maximum = 100, Margin = new Thickness(0, 0, 0, 10) };
    readonly HashSet<string> downloadsStarted = [], downloadsFinished = [];
    readonly Dictionary<string, double> downloadBytes = [];
    string[] operationPhases = [];
    int overallPhase;
    DispatcherTimer? progressTimer;

    void ResetOperationProgress()
    {
        operationClock.Reset(); activityProgress.Text = downloadProgress.Text = elapsedProgress.Text = "";
        downloadAmount.Text = downloadRate.Text = downloadEta.Text = "";
        downloadsStarted.Clear(); downloadsFinished.Clear(); downloadBytes.Clear(); overallPhase = 0;
        operationPhases = operation is "install" or "update" or "repair" && !repairModels
            ? ["extract", "python", "dependencies", "media", ..(LocalSelected ? new[] { "models" } : Array.Empty<string>()), "verify", ..(orValid && operation == "install" ? new[] { "credentials" } : Array.Empty<string>()), "register"]
            : operation == "models" || repairModels ? ["models", "verify", "register"]
            : operation == "uninstall" ? ["preview", "shutdown", "removal"] : ["verify", "register"];
        operationProgress.IsIndeterminate = true; operationProgress.Value = overallProgress.Value = 0;
        RefreshOverallProgress();
    }
    void RefreshOverallProgress()
    {
        int total = Math.Max(1, operationPhases.Length), completed = finished && successful ? total : Math.Min(overallPhase, total);
        overallProgress.Value = completed * 100.0 / total;
        overallProgressText.Text = T("Overall progress · stages completed: ", "Postęp całej operacji · ukończone etapy: ") + completed + " / " + total;
        downloadsSummary.Text = T("Downloads completed: ", "Ukończone pobrania: ") + downloadsFinished.Count + T(" · in progress: ", " · w toku: ") + (downloadsStarted.Count - downloadsFinished.Count);
    }
    void RenderOperationProgress()
    {
        if (!busy && !finished) return;
        RefreshOverallProgress();
        void Add(FrameworkElement control)
        {
            if (control.Parent is Panel parent) parent.Children.Remove(control);
            body.Children.Add(control);
        }
        Add(overallProgressText); Add(overallProgress);
        Add(Copy(T("Current item", "Bieżący element"), muted: true)); Add(operationProgress);
        elapsedProgress.FontFamily = new FontFamily("Consolas"); elapsedProgress.Height = 20; elapsedProgress.Margin = new Thickness(0, 0, 0, 4); Add(elapsedProgress);
        activityProgress.Height = 32; activityProgress.TextTrimming = TextTrimming.CharacterEllipsis; activityProgress.Margin = new Thickness(0, 0, 0, 4); Add(activityProgress);
        var metrics = new Grid { Height = 24, Margin = new Thickness(0, 0, 0, 4), HorizontalAlignment = HorizontalAlignment.Stretch };
        foreach (var width in new[] { new GridLength(1, GridUnitType.Star), new GridLength(145), new GridLength(100), new GridLength(80) }) metrics.ColumnDefinitions.Add(new ColumnDefinition { Width = width });
        int column = 0;
        foreach (var text in new[] { downloadProgress, downloadAmount, downloadRate, downloadEta })
        {
            if (text.Parent is Panel old) old.Children.Remove(text);
            text.TextWrapping = TextWrapping.NoWrap; text.TextTrimming = TextTrimming.CharacterEllipsis;
            text.FontFamily = new FontFamily("Consolas"); text.FontSize = 12; text.Margin = new Thickness(0, 0, 8, 0);
            Grid.SetColumn(text, column++); metrics.Children.Add(text);
        }
        Add(metrics); downloadsSummary.Height = 20; Add(downloadsSummary);
        if (finished) { operationProgress.IsIndeterminate = false; operationProgress.Value = successful ? 100 : 0; }
        if (progressTimer == null)
        {
            progressTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            progressTimer.Tick += (_, _) => elapsedProgress.Text = T("Elapsed: ", "Czas: ") + operationClock.Elapsed.ToString(@"hh\:mm\:ss");
            progressTimer.Start(); Closed += (_, _) => progressTimer.Stop();
        }
    }
    void UpdateOperationProgress(string stage, string text, JsonElement? item)
    {
        if (!IsProgressPage) return;
        int phase = Array.IndexOf(operationPhases, stage);
        if (phase >= 0) overallPhase = Math.Max(overallPhase, phase);
        if (stage == "complete") overallPhase = operationPhases.Length;
        if (stage == "download" && item is JsonElement data && data.TryGetProperty("bytes", out var count) && count.ValueKind == JsonValueKind.Number)
        {
            bool bytes = data.TryGetProperty("unit", out var unit) && unit.GetString() == "B";
            double downloaded = count.GetDouble(), size = data.TryGetProperty("total", out var total) && total.ValueKind == JsonValueKind.Number ? total.GetDouble() : 0;
            string id = data.TryGetProperty("download_id", out var key) ? key.GetString() ?? text : stage + ":" + text;
            downloadsStarted.Add(id); downloadBytes[id] = Math.Max(downloadBytes.GetValueOrDefault(id), downloaded);
            if (size > 0 && downloaded >= size) downloadsFinished.Add(id);
            operationProgress.IsIndeterminate = size <= 0; if (size > 0) operationProgress.Value = Math.Clamp(downloaded / size * 100, 0, 100);
            downloadProgress.Text = text; downloadProgress.ToolTip = text;
            downloadAmount.Text = bytes ? GB((long)downloaded) + (size > 0 ? " / " + GB((long)size) : "") + " GB" : downloaded + (size > 0 ? " / " + size : "");
            downloadRate.Text = bytes && data.TryGetProperty("rate", out var speed) && speed.ValueKind == JsonValueKind.Number ? (speed.GetDouble() / 1e6).ToString("0.0") + " MB/s" : "";
            downloadEta.Text = data.TryGetProperty("eta_seconds", out var remaining) && remaining.ValueKind == JsonValueKind.Number
                ? "~" + TimeSpan.FromSeconds(Math.Clamp(remaining.GetDouble(), 0, 864000)).ToString(@"hh\:mm\:ss") : "";
            RefreshOverallProgress(); return;
        }
        if (stage == "log")
        {
            var download = Regex.Match(text.Trim(), @"^(Downloading|Downloaded)\s+([^\s(]+)");
            if (download.Success)
            {
                string id = "package:" + download.Groups[2].Value;
                downloadsStarted.Add(id); if (download.Groups[1].Value == "Downloaded") downloadsFinished.Add(id);
            }
            if (download.Success) activityProgress.Text = download.Groups[2].Value;
        }
        else if (stage == "model-complete")
        {
            foreach (string id in downloadsStarted.Where(id => id.StartsWith(text + ":", StringComparison.Ordinal))) downloadsFinished.Add(id);
        }
        else if (stage == "model-item")
        {
            activityProgress.Text = text; operationProgress.IsIndeterminate = true;
            downloadProgress.Text = downloadAmount.Text = downloadRate.Text = downloadEta.Text = "";
        }
        else if (stage.Length > 0)
        {
            operationProgress.IsIndeterminate = true;
            downloadProgress.Text = downloadAmount.Text = downloadRate.Text = downloadEta.Text = "";
            activityProgress.Text = "";
        }
        RefreshOverallProgress();
    }
}
