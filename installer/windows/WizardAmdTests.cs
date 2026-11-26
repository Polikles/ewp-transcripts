using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;

namespace EwP.Setup;

sealed partial class Wizard
{
    async Task TestAmdWarning(string? previews)
    {
        var priorFind = FindInstallation;
        try
        {
            foreach (string action in new[] { "install", "update" })
            foreach (int locale in new[] { 0, 1 })
            {
                language.SelectedIndex = locale; amdAcknowledgements.Clear();
                string folder = Path.Combine(temporary, "amd-" + action + "-" + locale); Directory.CreateDirectory(folder);
                if (action == "update")
                {
                    File.WriteAllText(Path.Combine(folder, "owner.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder }));
                    File.WriteAllText(Path.Combine(folder, "installation.json"), JsonSerializer.Serialize(new { kind = "ewp-transcripts-managed-v1", root = folder, version = "0.0.1", active = "versions/test-1", local_models = false }));
                }
                FindInstallation = (_, _) => action == "install" ? null : InstallationDiscovery.Read(folder);
                SelectOperation(action); root.Text = folder; await Task.Delay(250);
                HostCheckRunner = () =>
                {
                    SetFixtureHost(); var report = JsonNode.Parse(host!.Value.GetRawText())!;
                    var gpu = report["checks"]!.AsArray().Single(n => n!["code"]!.GetValue<string>() == "gpu")!;
                    gpu["context"]!["amd_devices"] = JsonNode.Parse("[{\"name\":\"AMD Radeon RX 7900 XTX\",\"driver\":\"test\"}]");
                    host = JsonSerializer.SerializeToElement(report); return Task.FromResult(0);
                };
                int shown = 0;
                AmdWarningTest = dialog => { shown++; dialog.Show(); dialog.Close(); return dialog.Accepted; };
                await Next();
                Assert(shown == 1 && hostReady && !AmdAccepted && !CanAdvance, "AMD warning also blocks mixed NVIDIA/AMD hosts until acknowledged");
                var warning = new AmdWarning(this, Pl); warning.Show();
                await CaptureWindow(warning, previews, (Pl ? "pl" : "en") + "-amd-warning-" + action);
                warning.Continue.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                Assert(warning.Accepted, "AMD acknowledgement uses the actual localized button");
                AmdWarningTest = dialog => { dialog.Show(); dialog.Continue.RaiseEvent(new RoutedEventArgs(Button.ClickEvent)); return dialog.Accepted; };
                ShowAmdWarning(); Assert(AmdAccepted && CanAdvance, "AMD acknowledgement permits the checked location to advance");
                ShowAmdWarning(); Assert(AmdAccepted, "acknowledged hardware is not prompted again on rerender");
            }
        }
        finally { HostCheckRunner = null; AmdWarningTest = null; FindInstallation = priorFind; amdAcknowledgements.Clear(); }
    }
}
