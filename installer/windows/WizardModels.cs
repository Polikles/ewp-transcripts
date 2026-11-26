using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;

namespace EwP.Setup;

sealed partial class Wizard
{
    bool maintenance, localMaintenance, repairModels, reinstallModels;
    JsonElement? modelVerification;
    readonly HashSet<string> selectedModels = [];
    internal Func<ModelEntry, long> ModelMissingBytes = model => model.MissingBytes();
    IEnumerable<string> VisibleOperations => localMaintenance ? ["repair", "uninstall"] : maintenance ? ["repair", "rollback", "uninstall"] : operations;
    bool PreparingModels => operation == "install" && LocalSelected || operation == "models" || repairModels || operation == "update" && UpdateChangesModels;
    bool UpdateChangesModels => operation == "update" && LocalSelected && installed is JsonElement state &&
        !catalog.Models.Where(m => !m.Optional).All(m => ReadInstalledModelPins(state).Contains(m.Revision, StringComparison.Ordinal));
    string ReadInstalledModelPins(JsonElement state)
    {
        try { return File.ReadAllText(Path.Combine(root.Text, state.GetProperty("active").GetString()!, "app/src/ewp_transcripts/resources/default-config.toml")); }
        catch { return ""; }
    }
    IEnumerable<ModelEntry> DownloadModels => catalog.Models.Where(m =>
        (operation is "install" or "update" && !m.Optional || selectedModels.Contains(m.Code)) && (repairModels || reinstallModels || ModelMissingBytes(m) > 0));
    bool NeedsHf => PreparingModels && DownloadModels.Any(m => m.Gated);
    bool ModelsCanContinue => !PreparingModels ||
        ((!NeedsHf || hfValid && terms.IsChecked == true) && ModelSpaceProblem() == null &&
         (!(operation == "models" || repairModels) || selectedModels.Count > 0));

    void ResetModelState()
    {
        repairModels = reinstallModels = false; modelVerification = null; selectedModels.Clear();
        foreach (var model in catalog.Models.Where(m => !m.Optional && ModelMissingBytes(m) > 0)) selectedModels.Add(model.Code);
    }

    async void ChooseFolder()
    {
        var picker = new Microsoft.Win32.OpenFolderDialog();
        if (picker.ShowDialog(this) != true) return;
        manualLocation = true;
        root.Text = operation == "install" ? InstallFolderFromPicker(picker.FolderName) : picker.FolderName;
        locationChange?.Cancel(); ReadInstalled(); RefreshHostDisk(); Render();
        await AutoCheckHost();
    }

    void RenderModels()
    {
        body.Children.Add(Heading("3. " + (operation == "install" ? T("Local models and HF token", "Lokalne modele i token HF") : OperationName(operation))));
        if (operation == "update" && !UpdateChangesModels)
        {
            body.Children.Add(Copy(T("Only the program will be updated. Model versions are unchanged.", "Zaktualizowany zostanie tylko program. Wersje modeli pozostają bez zmian.")));
            return;
        }
        if (operation == "repair")
        {
            body.Children.Add(Copy(T("Default: repair program files and dependencies. Local models remain unchanged.", "Domyślnie: napraw pliki programu i zależności. Lokalne modele pozostaną bez zmian.")));
            var check = ActionButton(T("Check models", "Sprawdź modele"), async () => await VerifyModels(), secondary: true); check.IsEnabled = !busy; body.Children.Add(check);
            if (modelVerification is JsonElement models)
            {
                foreach (var result in models.EnumerateArray())
                    body.Children.Add(Copy(result.GetProperty("repository").GetString() + " · " + (result.GetProperty("status").GetString() == "pass" ? "SHA OK" : result.GetProperty("status").GetString() == "not-installed" ? T("optional · not installed", "opcjonalny · niezainstalowany") : T("missing or damaged files", "brakujące lub uszkodzone pliki")) + "\n" + result.GetProperty("path").GetString() + "\n" + result.GetProperty("revision").GetString(), muted: true));
                body.Children.Add(ActionButton(T("Download models again…", "Pobierz ponownie modele…"), () => { repairModels = true; Render(); }, secondary: true));
            }
            if (busy) body.Children.Add(Copy(T("Checking model locations, pinned versions and file hashes…", "Sprawdzanie lokalizacji, wersji i sum kontrolnych modeli…")));
            if (!repairModels) { AddLog(); return; }
            body.Children.Add(Link(T("Return to program-only repair", "Wróć do naprawy programu"), () => { repairModels = false; Render(); }));
        }
        if (operation == "install")
        {
            LabelCheck(local, T("Use local models on my GPU (without them you can only work using OpenRouter API and verify earlier transcripts)", "Użyj lokalnych modeli na moim GPU (bez nich możliwa jest tylko praca przez API OpenRouter i weryfikacja wcześniejszych transkrypcji)"));
            local.IsEnabled = true; body.Children.Add(local);
        }
        if (PreparingModels)
        {
            if (operation == "models")
            {
                var reinstall = new CheckBox { Content = T("Reinstall selected models", "Zainstaluj ponownie wybrane modele"), IsChecked = reinstallModels, Margin = new Thickness(0, 6, 0, 10) };
                reinstall.Checked += (_, _) => { reinstallModels = true; Render(); };
                reinstall.Unchecked += (_, _) => { reinstallModels = false; foreach (var model in catalog.Models.Where(m => ModelMissingBytes(m) == 0)) selectedModels.Remove(model.Code); Render(); };
                body.Children.Add(reinstall);
            }
            var list = new StackPanel();
            foreach (var model in catalog.Models)
            {
                bool selectable = operation == "models" || repairModels || operation == "install" && model.Optional;
                var box = new CheckBox { IsChecked = model.Optional || selectable ? selectedModels.Contains(model.Code) : true, IsEnabled = selectable && (operation != "models" || reinstallModels || ModelMissingBytes(model) > 0),
                    Content = new TextBlock { Text = model.Repository + (model.Optional ? T(" · optional", " · opcjonalny") : "") + (ModelMissingBytes(model) == 0 ? T(" · installed", " · zainstalowany") : ""), TextWrapping = TextWrapping.Wrap }, Margin = new Thickness(0, 3, 0, 3) };
                box.Checked += (_, _) => { selectedModels.Add(model.Code); missingRequirements.Remove("models"); ClearRequirementNotice(); Render(); };
                box.Unchecked += (_, _) => { selectedModels.Remove(model.Code); Render(); };
                list.Children.Add(box);
            }
            var modelCard = Card(list); if (missingRequirements.Contains("models")) { modelCard.BorderBrush = Error; modelCard.BorderThickness = new Thickness(2); } body.Children.Add(modelCard);
            body.Children.Add(Copy(T("Required space for selected downloads: ", "Potrzebne miejsce na wybrane modele: ") + GB(DownloadModels.Sum(m => repairModels || reinstallModels ? m.Bytes : ModelMissingBytes(m))) + " GB", muted: true));
            if (NeedsHf)
            {
                var row = new StackPanel { Orientation = Orientation.Horizontal };
                var enter = ActionButton(T("Enter Hugging Face token", "Podaj token Hugging Face"), () => EnterCredential(true), secondary: true); enter.IsEnabled = !hfValid; if (missingRequirements.Contains("hf")) { enter.BorderBrush = Error; enter.BorderThickness = new Thickness(2); } row.Children.Add(enter);
                row.Children.Add(Symbols.InfoButton(T("Token for downloading pyannote. Click for help.", "Token do pobrania pyannote. Kliknij, aby uzyskać pomoc."), ShowHfHelp));
                if (hfValid) row.Children.Add(new TextBlock { Text = T("Token valid", "Token prawidłowy"), Foreground = Success, VerticalAlignment = VerticalAlignment.Center });
                body.Children.Add(row);
                LabelCheck(terms, T("I accepted pyannote terms on Hugging Face", "Zaakceptowałem warunki pyannote w Hugging Face")); terms.IsEnabled = hfValid; body.Children.Add(RequiredCheck(terms, "terms"));
            }
            string? problem = ModelSpaceProblem();
            if (problem != null) { var warning = Copy(problem); warning.Foreground = Error; body.Children.Add(warning); }
        }

    }

    async Task VerifyModels()
    {
        if (busy) return;
        busy = true; modelVerification = null; File.Delete(CancelFile); Render();
        try
        {
            if (await Worker("verify-models", false) != 0) throw new IOException();
            selectedModels.Clear();
            if (modelVerification is JsonElement models)
                foreach (var model in models.EnumerateArray().Where(m => m.GetProperty("status").GetString() == "fail")) selectedModels.Add(model.GetProperty("code").GetString()!);
        }
        catch { notice = "model_check_failed"; }
        finally { busy = false; Render(); }
    }
}
