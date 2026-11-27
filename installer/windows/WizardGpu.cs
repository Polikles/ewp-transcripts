using System.Text.Json;

namespace EwP.Setup;

sealed partial class Wizard
{
    string LocalGpuProblem
    {
        get
        {
            if (host is JsonElement report)
                foreach (var row in report.GetProperty("checks").EnumerateArray())
                    if (row.GetProperty("code").GetString() == "gpu" && row.TryGetProperty("context", out var context) && context.TryGetProperty("compatibility", out _))
                        return NvidiaCompatibilityText(context) + " " + T("Clear the local-model option to continue with cloud ASR.", "Odznacz modele lokalne, aby kontynuować z ASR w chmurze.");
            return T("A compatible GPU and driver are required for local ASR. Clear local models to use cloud ASR.", "Lokalne ASR wymaga zgodnej karty i sterownika. Odznacz modele lokalne, aby używać ASR w chmurze.");
        }
    }

    string NvidiaCompatibilityText(JsonElement context)
    {
        string code = context.GetProperty("compatibility").GetString() ?? "unknown";
        string cloud = T("Cloud ASR is recommended.", "Zalecamy ASR w chmurze.");
        string text = code switch
        {
            "unsupported_architecture" => T("This GPU architecture is unsupported by the locked libraries. Local transcription will not work. CUDA Compute Capability 7.0 or newer supported architecture is required (Volta; GeForce Turing or later).", "Architektura tej karty nie jest obsługiwana przez przypięte biblioteki. Lokalna transkrypcja nie zadziała. Wymagana jest obsługiwana architektura z CUDA Compute Capability co najmniej 7.0 (Volta; GeForce Turing lub nowsze)."),
            "driver_too_old" => T("The driver does not meet this application's CUDA 12.8 Update 1 compatibility baseline. Update it before using local ASR. Required version: ", "Sterownik nie spełnia przyjętych wymagań zgodności programu z CUDA 12.8 Update 1. Zaktualizuj go przed użyciem lokalnego ASR. Wymagana wersja: ") + context.GetProperty("minimum_driver").GetString() + ".",
            "low_vram" => T("The GPU architecture is compatible, but it has less than the recommended 12 GB VRAM. Local transcription will probably not work with this amount of memory. This configuration has not been tested; operation is not guaranteed. It may work in some cases.", "Architektura GPU jest zgodna, ale karta ma mniej niż zalecane 12 GB VRAM. Lokalna transkrypcja prawdopodobnie nie zadziała przy tej ilości pamięci. Taka konfiguracja nie była testowana; nie gwarantujemy działania. W niektórych przypadkach może działać."),
            "supported" => T("GPU architecture and driver meet the CUDA 12.8 baseline; at least 12 GB VRAM is detected. This does not guarantee performance or qualify every card. Local diagnostics still apply.", "Architektura GPU i sterownik spełniają wymagania CUDA 12.8; wykryto co najmniej 12 GB VRAM. Nie gwarantuje to wydajności ani działania każdej karty. Nadal obowiązuje diagnostyka lokalna."),
            "memory_unknown" => T("GPU architecture and driver are compatible, but VRAM could not be verified. Fully local ASR is recommended with 12 GB VRAM or more. Smaller configurations are untested and not guaranteed.", "Architektura GPU i sterownik są zgodne, ale nie udało się sprawdzić VRAM. Do pełnego lokalnego ASR zalecamy co najmniej 12 GB VRAM. Mniejsze konfiguracje nie były testowane i nie gwarantujemy działania."),
            "selection_unknown" => T("The GPU used by CUDA could not be identified unambiguously. Memory from separate cards is not combined. Verify CUDA device selection before local ASR.", "Nie udało się jednoznacznie wskazać karty używanej przez CUDA. Pamięć osobnych kart nie jest sumowana. Przed lokalnym ASR sprawdź wybór urządzenia CUDA."),
            "cuda_disabled" => T("CUDA devices are disabled in the current environment. Local NVIDIA ASR is unavailable.", "Urządzenia CUDA są wyłączone w bieżącym środowisku. Lokalne ASR NVIDIA jest niedostępne."),
            "no_nvidia" => T("No usable NVIDIA or AMD GPU was detected for local ASR.", "Nie wykryto dostępnej karty NVIDIA ani AMD do lokalnego ASR."),
            _ => T("GPU architecture or driver compatibility could not be confirmed. Local ASR readiness is not established; update the driver and repeat the check.", "Nie udało się potwierdzić zgodności architektury GPU lub sterownika. Gotowość lokalnego ASR nie została potwierdzona; zaktualizuj sterownik i ponów test.")
        };
        if (context.TryGetProperty("selected_device", out var device))
        {
            string facts = "";
            if (device.TryGetProperty("compute_capability", out var capability)) facts += "CC " + capability.GetString();
            if (device.TryGetProperty("vram_bytes", out var memory) && memory.ValueKind == JsonValueKind.Number && memory.TryGetInt64(out long bytes))
                facts += (facts.Length > 0 ? " · " : "") + (bytes / (double)(1024L * 1024 * 1024)).ToString("0.#", Pl ? System.Globalization.CultureInfo.GetCultureInfo("pl-PL") : System.Globalization.CultureInfo.InvariantCulture) + " GiB VRAM";
            if (facts.Length > 0) text = facts + ". " + text;
        }
        return code == "supported" ? text : text + " " + cloud;
    }
}
