using System.Text.Json;
using System.Text.Json.Nodes;

namespace EwP.Setup;

sealed partial class Wizard
{
    internal Func<Task<int>>? HostCheckRunner;
    bool? checkedLocalModels;

    async Task AutoCheckHost()
    {
        if (page != 1 || !IsInstall || busy || LocationProblem() != null || testing && HostCheckRunner == null) return;
        if (checkedLocalModels != null && checkedLocalModels != LocalSelected) { host = null; hostReady = hostAttempted = false; }
        if (host != null)
        {
            RefreshHostDisk(); RenderHostRows(); RefreshNavigation(); return;
        }
        if (!hostAttempted) await CheckHost();
    }

    void RefreshHostDisk()
    {
        if (host is not JsonElement cached) return;
        var document = JsonNode.Parse(cached.GetRawText())!.AsObject();
        var rows = document["checks"]!.AsArray();
        var row = rows.OfType<JsonObject>().FirstOrDefault(r => r["code"]?.GetValue<string>() == "disk");
        if (row == null) { hostReady = false; return; }
        long required = operation == "install" ? 25_000_000_000L : 8L * 1024 * 1024 * 1024;
        long free = 0; bool available;
        try { free = DiskProbe(root.Text).Free; available = free >= required; }
        catch { available = false; }
        row["status"] = available ? "pass" : "fail";
        row["message"] = available ? "Disk space checked" : "Not enough accessible disk space";
        row["context"] = new JsonObject {
            ["free_bytes"] = free, ["required_bytes"] = required,
            ["installation_bytes"] = 20_000_000_000L, ["additional_bytes"] = required,
            ["reserve_bytes"] = operation == "install" ? 5_000_000_000L : 0L,
        };
        hostReady = rows.OfType<JsonObject>().All(r => r["status"]?.GetValue<string>() != "fail");
        document["ready"] = hostReady;
        host = JsonSerializer.SerializeToElement(document);
        hostAttempted = true;
    }
}
