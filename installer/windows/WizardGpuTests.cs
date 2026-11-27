using System.Text.Json;
using System.Text.Json.Nodes;
using System.Windows;

namespace EwP.Setup;

sealed partial class Wizard
{
    async Task TestNvidiaCompatibility(string? previews)
    {
        var priorFind = FindInstallation;
        var priorMissing = ModelMissingBytes;
        try
        {
            FindInstallation = (_, _) => null; ModelMissingBytes = _ => 0;
            foreach (int locale in new[] { 0, 1 })
            foreach (string state in new[] { "unsupported_architecture", "low_vram", "supported", "unknown", "driver_too_old", "selection_unknown", "memory_unknown" })
            {
                language.SelectedIndex = locale; SelectOperation("install");
                root.Text = System.IO.Path.Combine(temporary, "nvidia-preflight-" + state);
                page = 1; SetFixtureHost();
                var report = JsonNode.Parse(host!.Value.GetRawText())!;
                var gpu = report["checks"]!.AsArray().Single(n => n!["code"]!.GetValue<string>() == "gpu")!;
                bool usable = state is "supported" or "low_vram" or "memory_unknown";
                gpu["status"] = state == "supported" ? "pass" : "warning";
                gpu["context"]!["compatibility"] = state;
                gpu["context"]!["local_supported"] = usable;
                gpu["context"]!["minimum_driver"] = "572.61";
                string gpuName = state == "unsupported_architecture" ? "NVIDIA GeForce GTX 1070" : state == "low_vram" ? "NVIDIA GeForce RTX 3070" : "NVIDIA GeForce RTX 3090";
                long? memory = state == "memory_unknown" ? null : state is "low_vram" or "unsupported_architecture" ? 8589934592L : 25769803776L;
                var device = JsonSerializer.SerializeToNode(new { name = gpuName, driver = state == "driver_too_old" ? "570.65" : "580.00", compute_capability = state == "unsupported_architecture" ? "6.1" : state == "unknown" ? "N/A" : "8.6", vram_bytes = memory });
                gpu["context"]!["selected_device"] = device;
                gpu["context"]!["devices"] = new JsonArray(device!.DeepClone());
                host = JsonSerializer.SerializeToElement(report); hostReady = true;
                Render(); UpdateLayout();
                string text = VisibleText(hostRows);
                Assert(CanAdvance && GpuReady == usable, "GPU notice never blocks cloud installation; low VRAM still permits deliberate local choice");
                if (state == "unsupported_architecture") Assert(text.Contains(Pl ? "Lokalna transkrypcja nie zadziała" : "Local transcription will not work"), "unsupported architecture has an actionable localized warning");
                if (state == "low_vram") Assert(text.Contains("12 GB VRAM") && text.Contains(Pl ? "nie gwarantujemy" : "not guaranteed"), "low VRAM remains explicitly untested/unguaranteed");
                if (state != "supported") Assert(text.Contains(Pl ? "ASR w chmurze" : "Cloud ASR"), "unready/low-memory GPU recommends cloud");
                await Capture(previews, (Pl ? "pl" : "en") + "-nvidia-" + state);
                page = 2; local.IsChecked = true; Render();
                Assert(ModelsCanContinue == usable, "only unsupported hardware blocks new local preparation");
                local.IsChecked = false; Render(); Assert(ModelsCanContinue, "clearing local models preserves cloud flow");
                operation = "update"; page = 2; installed = JsonSerializer.SerializeToElement(new { local_models = false });
                Assert(ModelsCanContinue, "app-only update is permitted regardless of GPU notice");
            }
        }
        finally { FindInstallation = priorFind; ModelMissingBytes = priorMissing; }
    }
}
