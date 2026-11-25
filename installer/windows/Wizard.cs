using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using Microsoft.Win32;

namespace EwP.Setup;

sealed partial class Wizard : Window
{
    internal static readonly Brush Paper = ColorBrush("#F5F2E9"), Ink = ColorBrush("#273342"),
        Muted = ColorBrush("#586778"), Success = ColorBrush("#256445"), Error = ColorBrush("#A53336");
    static Brush ColorBrush(string color) => (Brush)new BrushConverter().ConvertFromInvariantString(color)!;
    // Keep the running installer bytes stable through any later elevation/copy.
    readonly FileStream executableGuard = new(Environment.ProcessPath!, FileMode.Open, FileAccess.Read, FileShare.Read);
    readonly string temporary = Path.Combine(Path.GetTempPath(), "ewp-setup-" + Guid.NewGuid().ToString("N"));
    readonly string embedded, version = Assembly.GetExecutingAssembly().GetName().Version!.ToString(3);
    readonly StackPanel body = new() { Margin = new Thickness(28, 22, 28, 18), MaxWidth = 760 };
    readonly TextBlock subtitle = new();
    readonly WrapPanel steps = new() { VerticalAlignment = VerticalAlignment.Center };
    readonly ComboBox language = new() { ItemsSource = new[] { "English", "Polski" }, SelectedIndex = 1, Width = 105, Padding = new Thickness(7) };
    readonly TextBox root = new() { Padding = new Thickness(10), MinWidth = 320 };
    readonly TextBox log = new() { IsReadOnly = true, TextWrapping = TextWrapping.Wrap, AcceptsReturn = true, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Height = 170, FontSize = 12 };
    readonly CheckBox local = new(), terms = new(), removeModels = new(), removeKey = new();
    readonly TextBlock diskStatus = new() { TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 10, 0, 4) };
    readonly StackPanel hostRows = new();
    readonly Button back, next, cancel;
    readonly TextBlock license;
    readonly Catalog catalog;
    readonly List<string> operations = ["install", "update", "repair", "models", "rollback", "uninstall"];
    JsonElement? host, installed, removal;
    string operation = "install", hfSecret = "", orSecret = "", notice = "";
    bool busy, finished, successful, hostReady, hfValid, orValid, previewReady, testing, logExpanded;
    int page;
    int ProgressPage => operation == "install" ? 4 : 3;
    bool IsProgressPage => page == ProgressPage;
    readonly HashSet<string> missingRequirements = [];
    CancellationTokenSource? locationChange;
    internal Func<string, (long Free, string Volume)> DiskProbe = ProbeDisk;
    string CancelFile => Path.Combine(temporary, "cancel.requested");
    bool Pl => language.SelectedIndex == 1;
    bool IsInstall => operation is "install" or "update" or "repair" or "models";
    bool LocalSelected => local.IsChecked == true || operation == "models";
    string T(string en, string pl) => Pl ? pl : en;

    public Wizard(string[] args)
    {
        Title = "EwP Transcripts · " + version;
        Width = 820; Height = 860; MinWidth = 680; MinHeight = 620;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Background = Paper; Foreground = Ink; FontFamily = new FontFamily("Segoe UI Variable, Segoe UI"); FontSize = 14;
        Icon = Branding.Svg("favicon.svg");
        Directory.CreateDirectory(temporary); embedded = Path.Combine(temporary, "bundle.zip");
        using (var source = Assembly.GetExecutingAssembly().GetManifestResourceStream("bundle.zip")!)
        using (var target = File.Create(embedded)) source.CopyTo(target);
        VerifyBundle(embedded);
        ZipFile.ExtractToDirectory(embedded, Path.Combine(temporary, "payload"));
        using (var source = Assembly.GetExecutingAssembly().GetManifestResourceStream("models.json")!)
            catalog = JsonSerializer.Deserialize<Catalog>(source, new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;
        var shell = new Grid { Background = Paper }; Content = shell;
        shell.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        shell.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        shell.RowDefinitions.Add(new RowDefinition());
        shell.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        var header = new Grid { Background = Branding.HeaderBackground(), Height = 104 };
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        header.ColumnDefinitions.Add(new ColumnDefinition());
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        header.Children.Add(new Image { Source = Branding.Svg("favicon.svg"), Width = 70, Height = 70, Stretch = Stretch.Uniform, Margin = new Thickness(22, 17, 18, 17), HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center });
        var title = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        title.Children.Add(new TextBlock { Text = "EwP Transcripts", FontSize = 28, FontWeight = FontWeights.SemiBold, Foreground = Brushes.White });
        subtitle.Foreground = ColorBrush("#E4EDF7"); subtitle.FontSize = 14; subtitle.Margin = new Thickness(0, 5, 0, 0); title.Children.Add(subtitle);
        Grid.SetColumn(title, 1); header.Children.Add(title);
        language.Margin = new Thickness(16, 0, 22, 0); language.VerticalAlignment = VerticalAlignment.Center;
        Grid.SetColumn(language, 2); header.Children.Add(language); shell.Children.Add(header);
        var progress = new Border { Child = steps, Background = ColorBrush("#E8ECED"), Padding = new Thickness(28, 12, 28, 12) };
        ModernTheme.TextInput(root); log.FontFamily = new FontFamily("Consolas");
        Grid.SetRow(progress, 1); shell.Children.Add(progress);
        var scroll = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled, Content = body };
        Grid.SetRow(scroll, 2); shell.Children.Add(scroll);
        var footer = new Grid { Margin = new Thickness(24, 14, 24, 16) };
        footer.ColumnDefinitions.Add(new ColumnDefinition()); footer.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        license = Link("", ShowLicenses);
        license.VerticalAlignment = VerticalAlignment.Center; footer.Children.Add(license);
        var navigation = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right };
        back = ActionButton("", Back, secondary: true); next = ActionButton("", async () => await Next()); cancel = ActionButton("", Cancel, secondary: true);
        navigation.Children.Add(back); navigation.Children.Add(next); navigation.Children.Add(cancel);
        Grid.SetColumn(navigation, 1); footer.Children.Add(navigation); Grid.SetRow(footer, 3); shell.Children.Add(footer);
        root.TextChanged += (_, _) => { if (!resettingOperation) ScheduleLocation(); };
        local.Checked += (_, _) => { if (page == 2) Render(); }; local.Unchecked += (_, _) => { if (page == 2) Render(); };
        terms.Checked += (_, _) => { missingRequirements.Remove("terms"); ClearRequirementNotice(); if (terms.Parent is Border frame) { frame.Background = Brushes.Transparent; frame.BorderBrush = Brushes.Transparent; } RefreshNavigation(); }; terms.Unchecked += (_, _) => RefreshNavigation();
        language.SelectionChanged += (_, _) => Render();
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] is "--maintenance" or "--uninstall") { maintenance = true; operation = "uninstall"; }
            if (args[i] == "--local-maintenance") { localMaintenance = true; operation = "uninstall"; }
            if (args[i] == "--root" && i + 1 < args.Length) preferredMaintenanceRoot = args[++i];
            if (args[i] == "--operation" && i + 1 < args.Length && operations.Contains(args[i + 1])) operation = args[++i];
        }
        Closing += (_, e) => { if (busy) { e.Cancel = true; Cancel(); } };
        Closed += (_, _) => { executableGuard.Dispose(); hfSecret = orSecret = ""; locationChange?.Cancel(); try { Directory.Delete(temporary, true); } catch { } };
        PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) { e.Handled = true; Cancel(); } };
        SelectOperation(operation);
    }

    internal static TextBlock Heading(string text) => new() { Text = text, FontSize = 23, FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 0, 0, 16), TextWrapping = TextWrapping.Wrap };
    internal static TextBlock Copy(string text, bool muted = false) => new() { Text = text, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 14), Foreground = muted ? Muted : Ink, FontSize = muted ? 12 : 14 };
    internal static Button ActionButton(string text, Action callback, bool secondary = false)
    {
        var button = new Button { Content = text, Padding = new Thickness(16, 9, 16, 9), Margin = new Thickness(0, 0, 8, 0), MinHeight = 36, Background = ColorBrush(secondary ? "#FFFFFF" : "#355880"), Foreground = secondary ? Ink : Brushes.White, BorderBrush = ColorBrush("#BCCBD6"), BorderThickness = new Thickness(secondary ? 1 : 0), HorizontalAlignment = HorizontalAlignment.Left, Cursor = Cursors.Hand };
        var border = new FrameworkElementFactory(typeof(Border)); border.SetValue(Border.CornerRadiusProperty, new CornerRadius(8)); border.SetValue(Border.BorderBrushProperty, new TemplateBindingExtension(Control.BorderBrushProperty)); border.SetValue(Border.BorderThicknessProperty, new TemplateBindingExtension(Control.BorderThicknessProperty)); border.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Control.BackgroundProperty)); border.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Control.PaddingProperty));
        var presenter = new FrameworkElementFactory(typeof(ContentPresenter)); presenter.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center); presenter.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); border.AppendChild(presenter);
        var template = new ControlTemplate(typeof(Button)) { VisualTree = border };
        var hover = new Trigger { Property = IsMouseOverProperty, Value = true }; hover.Setters.Add(new Setter(Control.BackgroundProperty, ColorBrush(secondary ? "#EEF4F8" : "#294B70"))); template.Triggers.Add(hover);
        var disabled = new Trigger { Property = IsEnabledProperty, Value = false }; disabled.Setters.Add(new Setter(OpacityProperty, .45)); template.Triggers.Add(disabled); button.Template = template;
        button.Click += (_, _) => callback(); return button;
    }
    internal static TextBlock Link(string text, Action callback)
    {
        var line = new TextBlock { FontSize = 12, Margin = new Thickness(0, 6, 0, 6), TextWrapping = TextWrapping.Wrap };
        var link = new Hyperlink(new Run(text)) { Foreground = ColorBrush("#245B80") }; link.Click += (_, _) => callback(); line.Inlines.Add(link); return line;
    }
    internal static Image BusyGear()
    {
        var gear = new Image { Source = Branding.Svg("gear.svg"), Width = 24, Height = 24, HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(10, 2, 10, 2), Visibility = Visibility.Collapsed, RenderTransformOrigin = new Point(.5, .5), RenderTransform = new RotateTransform() };
        if (SystemParameters.ClientAreaAnimation) ((RotateTransform)gear.RenderTransform).BeginAnimation(RotateTransform.AngleProperty, new DoubleAnimation(0, 360, TimeSpan.FromSeconds(3)) { RepeatBehavior = RepeatBehavior.Forever });
        return gear;
    }
    static void LabelCheck(CheckBox box, string text) { box.Content = new TextBlock { Text = text, TextWrapping = TextWrapping.Wrap }; box.Margin = new Thickness(0, 8, 0, 12); box.FontSize = 14; }
    static Border Card(UIElement child) => new() { Background = Brushes.White, BorderBrush = ColorBrush("#CDD7DC"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(8), Padding = new Thickness(16), Margin = new Thickness(0, 0, 0, 16), Child = child };
    string OperationName(string op) => op switch
    {
        "install" => T("Install", "Zainstaluj"),
        "update" => T("Update", "Aktualizuj"),
        "repair" => T("Repair", "Napraw"),
        "models" => T("Add local models", "Doinstaluj modele lokalne"),
        "rollback" => T("Restore previous version", "Przywróć poprzednią wersję"),
        _ => T("Uninstall", "Odinstaluj")
    };
    string OperationHelp => operation switch
    {
        "install" => T("Install the program in a new folder. Choose local models or OpenRouter on the following screens.", "Zainstaluj program w nowym folderze. Na kolejnych ekranach wybierzesz modele lokalne lub OpenRouter."),
        "update" => T("Update an existing managed installation to the version in this installer. Work, models and saved keys remain.", "Zaktualizuj istniejącą instalację zarządzaną do wersji z tego instalatora. Praca, modele i zapisane klucze pozostaną."),
        "repair" => T("Restore program files and dependencies for the same installed version. User work remains.", "Przywróć pliki programu i zależności dla tej samej zainstalowanej wersji. Praca pozostanie."),
        "models" => T("Add local models. If the program version is lower than the installer version, update the program first.", "Doinstaluj modele lokalne. Jeśli wersja programu jest niższa niż wersja instalatora, najpierw zaktualizuj program."),
        "rollback" => T("Activate the retained previous program version. No models or user files are removed.", "Przywróć zachowaną poprzednią wersję programu. Modele i pliki użytkownika nie będą usuwane."),
        _ => T("Preview removal, then choose whether to keep shared models and the saved API key. Recordings and work remain.", "Przejrzyj plan usunięcia i wybierz, czy zachować współdzielone modele i klucz API. Nagrania i praca pozostaną.")
    };

    void Render()
    {
        body.Children.Clear();
        subtitle.Text = T("Local-first transcript workflow", "Lokalne narzędzie do transkrypcji");
        ((Run)((Hyperlink)license.Inlines.FirstInline).Inlines.FirstInline).Text = T("Licenses and artwork", "Licencje i autorstwo");
        RenderSteps();
        if (page == 0) RenderWelcome();
        else if (page == 1) RenderLocation();
        else if (page == 2 && IsInstall) RenderModels();
        else if (page == 2) RenderConfirmation();
        else if (operation == "install" && page == 3) RenderOpenRouter();
        else RenderProgress();
        if (notice.Length > 0) { var text = Copy(NoticeText()); text.Foreground = Error; body.Children.Add(text); }
        RefreshNavigation();
    }

    string NoticeText() => notice switch
    {
        "model_check_failed" => T("Cannot verify model files. See technical details.", "Nie można sprawdzić plików modeli. Sprawdź szczegóły techniczne."),
        "requirements" => T("Complete the highlighted requirements before continuing.", "Uzupełnij zaznaczone wymagania przed przejściem dalej."),
        "check_failed" => T("Resolve the failed checks and retry.", "Usuń przyczyny błędów i ponów test."),
        "check_unavailable" => T("Cannot run the computer check. See technical details.", "Nie można uruchomić testu komputera. Sprawdź szczegóły techniczne."),
        _ => T("Cannot prepare removal preview.", "Nie można przygotować planu usunięcia.")
    };

    void RenderWelcome()
    {
        body.Children.Add(Heading(T("What would you like to do?", "Co chcesz zrobić?")));
        body.Children.Add(Copy(T("Choose your language above and select one action.", "Wybierz język powyżej i jedno działanie poniżej."), muted: true));
        var choices = new StackPanel(); actionChoices.Clear();
        foreach (string op in VisibleOperations)
        {
            var radio = Symbols.ActionChoice(OperationName(op), op, operation == op, () => SelectOperation(op, focusChoice: true));
            actionChoices.Add(radio); choices.Children.Add(radio);
        }
        body.Children.Add(choices); body.Children.Add(Copy(OperationHelp));
        body.Children.Add(Copy(T("Installer version: ", "Wersja instalatora: ") + version, muted: true));
    }

    void RenderLocation()
    {
        body.Children.Add(Heading(T("2. Location and checks", "2. Lokalizacja i test")));
        body.Children.Add(Copy(OperationHelp, muted: true));
        if (operation != "install" && detected != null && !manualLocation) RenderDetectedLocation();
        else
        {
            if (operation != "install" && detected == null)
                body.Children.Add(Copy(T("No managed installation was detected. Choose its folder if you have one.", "Nie wykryto instalacji zarządzanej. Wybierz jej folder, jeśli program był już zainstalowany."), muted: true));
            body.Children.Add(Copy(operation == "install" ? T("Program installation folder", "Folder instalacji programu") : T("Installed program folder", "Folder zainstalowanego programu")));
            body.Children.Add(root);
            var chooseFolder = ActionButton(T("Choose folder…", "Wybierz folder…"), ChooseFolder, secondary: true);
            chooseFolder.Margin = new Thickness(0, 8, 0, 0); body.Children.Add(chooseFolder);
        }
        if (operation == "rollback") RenderRollbackChoices();
        body.Children.Add(diskStatus); RefreshLocation();
        if (IsInstall)
        {
            body.Children.Add(Copy(T("Test utilizes small Python runtime. No data is sent", "Test korzysta z małego środowiska Python. Nie wysyła żadnych danych"), muted: true));
            var row = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 14) };
            var test = ActionButton(T("Check this computer", "Sprawdź komputer"), async () => await CheckHost(), secondary: true); test.IsEnabled = !busy;
            if (missingRequirements.Contains("host")) { test.BorderBrush = Error; test.BorderThickness = new Thickness(2); }
            row.Children.Add(test); var gear = BusyGear(); gear.Visibility = busy ? Visibility.Visible : Visibility.Collapsed; row.Children.Add(gear); body.Children.Add(row);
            body.Children.Add(hostRows); RenderHostRows();
            if (ShowVcHelp) body.Children.Add(Link(T("Download Microsoft Visual C++ libraries", "Pobierz biblioteki Microsoft Visual C++"), () => Open(Pl
                ? "https://learn.microsoft.com/pl-pl/cpp/windows/latest-supported-vc-redist"
                : "https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist")));
            if (busy) body.Children.Add(Copy(T("Preparing/checking the installer runtime…", "Przygotowywanie/sprawdzanie środowiska instalatora…"), muted: true));
            AddLog();
        }
    }

    void RenderConfirmation()
    {
        body.Children.Add(Heading("3. " + OperationName(operation)));
        body.Children.Add(Copy(OperationHelp));
        if (operation == "rollback")
        {
            body.Children.Add(Card(Copy(T("Restore the retained previous installation. User work is not changed.", "Przywróć zachowaną poprzednią instalację. Pliki pracy nie będą zmieniane."))));
            return;
        }
        if (previewReady && removal is JsonElement plan)
        {
            body.Children.Add(Copy(T("The following application files will be removed:", "Zostaną usunięte następujące pliki programu:")));
            body.Children.Add(new TextBox { IsReadOnly = true, Text = string.Join(Environment.NewLine, plan.GetProperty("paths").EnumerateArray().Select(v => v.GetString())), TextWrapping = TextWrapping.Wrap, Height = 130, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, FontSize = 12, Padding = new Thickness(8) });
            LabelCheck(removeModels, T("Also remove the recorded model snapshots (may be shared with other programs)", "Usuń także zapisane wersje modeli (mogą być współdzielone z innymi programami)")); body.Children.Add(removeModels);
            LabelCheck(removeKey, T("Also remove the saved OpenRouter key", "Usuń także zapisany klucz OpenRouter")); body.Children.Add(removeKey);
            body.Children.Add(Copy(T("Recordings, results and saved work remain. Keep the defaults if another checkout uses these models.", "Nagrania, wyniki i zapisy pracy pozostaną. Zachowaj ustawienia domyślne, jeśli inne repozytorium używa tych modeli."), muted: true));
        }
        else
        {
            body.Children.Add(Copy(T("Preparing removal preview…", "Przygotowywanie planu usunięcia…")));
            var gear = BusyGear(); gear.Visibility = Visibility.Visible; body.Children.Add(gear);
        }
        AddLog();
    }

    void RenderProgress()
    {
        body.Children.Add(Heading(finished ? (successful ? T("Operation completed", "Operacja ukończona") : T("Operation stopped", "Operacja zatrzymana")) : (ProgressPage + 1) + ". " + OperationName(operation)));
        if (busy) { var gear = BusyGear(); gear.Width = gear.Height = 48; gear.Margin = new Thickness(0, 0, 0, 14); gear.Visibility = Visibility.Visible; body.Children.Add(gear); }
        RenderOperationProgress();
        body.Children.Add(Copy(ProgressMessage()));
        if (finished && successful && operation == "uninstall") body.Children.Add(Copy(T("Program files and shortcuts have been removed. Closing this window removes the installer itself.", "Pliki programu i skróty zostały usunięte. Zamknięcie tego okna usunie sam deinstalator.")));
        AddLog(expand: finished && !successful);
    }

    string progressStage = "";
    string ProgressMessage() => finished ? (successful
        ? T("Read the report below. User work has been preserved.", "Przeczytaj raport poniżej. Pliki pracy zostały zachowane.")
        : T("Read the details below. You can go back and retry; the previous active program remains.", "Przeczytaj szczegóły poniżej. Możesz wrócić i ponowić próbę; poprzednia aktywna wersja pozostała.")) : progressStage switch
        {
            "shutdown" => T("Closing the running application…", "Zamykanie działającej aplikacji…"),
            "register" => T("Saving installation settings…", "Zapisywanie ustawień instalacji…"),
            "permission" => T("Windows will ask for administrator permission for this folder.", "Windows poprosi o uprawnienia administratora dla tego folderu."),
            "extract" => T("Verifying program files…", "Sprawdzanie plików programu…"),
            "dependencies" => T("Installing program dependencies…", "Instalowanie zależności programu…"),
            "python" => T("Preparing the Python runtime…", "Przygotowywanie środowiska Python…"),
            "media" => T("Downloading and installing FFmpeg…", "Pobieranie i instalowanie FFmpeg…"),
            "models" => T("Preparing local models…", "Przygotowywanie modeli lokalnych…"),
            "verify" => T("Checking installed program…", "Sprawdzanie zainstalowanego programu…"),
            "credentials" => T("Saving the optional key in the OS store…", "Zapisywanie opcjonalnego klucza w magazynie systemowym…"),
            "cancel" => T("Cancelling safely… Downloaded cache files will remain.", "Bezpieczne anulowanie… Pobrane pliki cache pozostaną."),
            _ => T("Preparing the operation…", "Przygotowywanie operacji…")
        };

    void AddLog(bool expand = false)
    {
        // A control can have only one parent across page transitions.
        if (log.Parent is Decorator old) old.Child = null;
        else if (log.Parent is ContentControl oldContent) oldContent.Content = null;
        var box = new StackPanel();
        var expander = new Expander { Header = T("Technical details / log", "Szczegóły techniczne / dziennik"), IsExpanded = logExpanded || expand, Foreground = Muted, FontSize = 12, Margin = new Thickness(0, 14, 0, 4), Content = log };
        expander.Expanded += (_, _) => logExpanded = true;
        expander.Collapsed += (_, _) => logExpanded = false;
        box.Children.Add(expander);
        box.Children.Add(Link(T("Save report…", "Zapisz raport…"), SaveReport)); body.Children.Add(box);
    }

    bool CanAdvance => !busy && (finished ? successful : page switch
    {
        0 => true,
        1 => LocationProblem() == null && (!IsInstall || hostReady),
        2 => IsInstall ? ModelsCanContinue : operation == "rollback" || previewReady,
        3 when operation == "install" => true,
        _ => false
    });

    void ClearRequirementNotice()
    {
        if (notice != "requirements") return;
        string text = NoticeText(); notice = "";
        var displayed = body.Children.OfType<TextBlock>().FirstOrDefault(item => item.Text == text);
        if (displayed != null) body.Children.Remove(displayed);
    }

    void HighlightMissingRequirements()
    {
        if (page == 2 && NeedsHf)
        {
            if (!hfValid) missingRequirements.Add("hf");
            else if (terms.IsChecked != true) missingRequirements.Add("terms");
        }
        if (page == 1 && IsInstall && !hostReady) missingRequirements.Add("host");
        if (page == 2 && PreparingModels && !DownloadModels.Any()) missingRequirements.Add("models");
        notice = "requirements"; Render();
        if (missingRequirements.Contains("terms")) { terms.BringIntoView(); terms.Focus(); }
        else if (page == 1) diskStatus.BringIntoView();
    }

    Border RequiredCheck(CheckBox box, string requirement)
    {
        if (box.Parent is Decorator old) old.Child = null;
        bool missing = missingRequirements.Contains(requirement);
        return new Border { Child = box, BorderBrush = missing ? Error : Brushes.Transparent,
            BorderThickness = new Thickness(2), Background = missing ? ColorBrush("#FFF0E8") : Brushes.Transparent,
            CornerRadius = new CornerRadius(6), Padding = new Thickness(8, 0, 8, 0), Margin = new Thickness(-10, 0, 0, 0) };
    }

    void RefreshNavigation()
    {
        back.Content = T("Back", "Wstecz"); cancel.Content = finished ? T("Close", "Zamknij") : T("Cancel", "Anuluj");
        back.Visibility = page == 0 || (finished && successful) ? Visibility.Collapsed : Visibility.Visible;
        back.IsEnabled = !busy; language.IsEnabled = !busy;
        cancel.IsEnabled = !busy || (!(operation is "uninstall" or "rollback" && IsProgressPage) && !File.Exists(CancelFile));
        next.Visibility = finished && (!successful || operation is "uninstall" or "rollback") ? Visibility.Collapsed : Visibility.Visible;
        next.Content = finished ? T("Launch program", "Uruchom program") : page == ProgressPage - 1 ? (IsInstall ? T("Next — ", "Dalej — ") + OperationName(operation) : OperationName(operation)) : T("Next", "Dalej");
        // Keep blocked navigation clickable so it can explain and highlight requirements.
        next.IsEnabled = !busy && (!finished || successful);
        next.Opacity = CanAdvance ? 1 : .45;
        next.ToolTip = CanAdvance ? null : T("Complete the required fields to continue.", "Uzupełnij wymagane pola, aby przejść dalej.");
    }

    async Task Next()
    {
        if (busy) return;
        if (!CanAdvance) { HighlightMissingRequirements(); return; }
        notice = "";
        if (finished) { Launch(); return; }
        if (page == 0) { page = 1; ReadInstalled(); Render(); await AutoCheckHost(); return; }
        if (page == 1)
        {
            page = 2; if (operation == "models") local.IsChecked = true; Render();
            if (operation == "uninstall") await PreviewRemoval();
            return;
        }
        if (page == 2 && operation == "install") { page = 3; Render(); return; }
        if (page == ProgressPage - 1) await RunOperation();
    }
    async void Back() { if (busy) return; notice = ""; if (finished) { finished = false; page = 1; } else page = Math.Max(0, page - 1); Render(); await AutoCheckHost(); }
    void Cancel()
    {
        if (!busy) { Close(); return; }
        if (IsProgressPage && operation is "uninstall" or "rollback") return;
        File.WriteAllText(CancelFile, "cancel"); progressStage = "cancel"; cancel.IsEnabled = false;
        if (IsProgressPage) Render();
    }
    void ScheduleLocation()
    {
        locationChange?.Cancel(); locationChange = new(); var token = locationChange.Token; int epoch = ++stateEpoch;
        hostReady = false; hostAttempted = host != null; removal = null; previewReady = false; notice = ""; log.Clear();
        ReadInstalled();
        if (checkedLocalModels != null && checkedLocalModels != LocalSelected) { host = null; hostAttempted = false; }
        RefreshNavigation();
        _ = RefreshAfterDelay(token, epoch);
    }
    async Task RefreshAfterDelay(CancellationToken token, int epoch)
    {
        try { await Task.Delay(200, token); if (!token.IsCancellationRequested && stateEpoch == epoch) { RefreshLocation(); RefreshHostDisk(); RenderHostRows(); RefreshNavigation(); await AutoCheckHost(); } }
        catch (OperationCanceledException) { }
    }
    void ReadInstalled()
    {
        var info = InstallationDiscovery.Read(root.Text); installed = info?.State;
        if (operation != "install") { detected = info; if (info != null) local.IsChecked = operation == "models" || info.LocalModels; }

    }
    string? LocationProblem()
    {
        try
        {
            if (string.IsNullOrWhiteSpace(root.Text)) return T("Choose the program installation folder.", "Wybierz folder instalacji programu.");
            string path = Path.GetFullPath(root.Text);
            if (path == Path.GetPathRoot(path) || string.Equals(path.TrimEnd('\\'), Environment.GetFolderPath(Environment.SpecialFolder.UserProfile).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
                return T("Choose a separate program folder.", "Wybierz osobny folder programu.");
            if (operation == "install")
            {
                if (Directory.Exists(path) && Directory.EnumerateFileSystemEntries(path).Any() && InstallationDiscovery.Read(path) is not { State: null }) return T("Choose an empty folder; for an existing installation choose Update or Repair.", "Wybierz pusty folder; dla istniejącej instalacji wybierz Aktualizuj lub Napraw.");
                if (DiskProbe(path).Free < 25_000_000_000) return T("At least 25 GB is required (20 GB installation + 5 GB free margin).", "Potrzeba co najmniej 25 GB (20 GB instalacji + 5 GB wolnego miejsca).");
            }
            else
            {
                if (!File.Exists(Path.Combine(path, "owner.json"))) return T("Select an existing managed installation.", "Wybierz istniejącą instalację zarządzaną.");
                if (operation != "uninstall" && installed == null) return T("This installation is incomplete; use Uninstall before installing again.", "Ta instalacja jest niekompletna; przed ponowną instalacją wybierz Odinstaluj.");
                if (installed is JsonElement state)
                {
                    string current = state.GetProperty("version").GetString()!;
                    if (operation is "repair" or "models" && current != version) return Version.Parse(current) > Version.Parse(version)
                        ? T("Download a newer installer matching the installed program version.", "Pobierz nowszą wersję instalatora zgodną z wersją programu.")
                        : T("Update the program first.", "Najpierw zaktualizuj program.");
                    if (operation == "update" && current == version) return T("This version is already installed. Choose Repair if needed.", "Ta wersja jest już zainstalowana. W razie potrzeby wybierz Napraw.");
                    if (operation == "update" && Version.Parse(current) > Version.Parse(version)) return T("This installer is older; use Restore previous version instead.", "Ten instalator jest starszy; wybierz Przywróć poprzednią wersję.");
                    if (operation == "rollback" && RollbackChoices().Count == 0) return T("No files from an older version were found.", "Nie znaleziono plików starszej wersji.");
                }
            }
        }
        catch { return T("Cannot access this folder or its disk.", "Nie można odczytać folderu lub jego dysku."); }
        return null;
    }
    void RefreshLocation()
    {
        string? problem = LocationProblem(); root.BorderBrush = problem == null ? ColorBrush("#9AAEB9") : Error;
        try
        {
            if (string.IsNullOrWhiteSpace(root.Text)) { diskStatus.Text = ""; return; }
            var disk = DiskProbe(root.Text);
            string text = T("Disk space: ", "Miejsce na dysku: ") + GB(disk.Free) + T(" GB free", " GB wolne");
            if (operation == "install") text += T(" · at least 25 GB (20 + 5 GB margin)", " · co najmniej 25 GB (20 + 5 GB marginesu)");
            if (IsInstall && OperationRunner.IsNormallyProtected(root.Text)) text += "\n" + T("Windows may ask for administrator permission when the operation starts.", "Windows może poprosić o uprawnienia administratora przy rozpoczęciu operacji.");
            if (installed is JsonElement state) text += "\n" + T("Installed version: ", "Zainstalowana wersja: ") + state.GetProperty("version").GetString();
            diskStatus.Text = text + (problem == null ? "" : "\n" + problem); diskStatus.Foreground = problem == null ? Muted : Error;
        }
        catch { diskStatus.Text = problem ?? ""; diskStatus.Foreground = Error; }
    }
    static (long Free, string Volume) ProbeDisk(string value)
    {
        string path = Path.GetFullPath(value);
        while (!Directory.Exists(path)) path = Path.GetDirectoryName(path) ?? throw new IOException();
        var disk = new DriveInfo(Path.GetPathRoot(path)!); return (disk.AvailableFreeSpace, disk.Name);
    }
    string GB(long bytes) => (bytes / 1e9).ToString(bytes is > 0 and < 1_000_000_000 ? "0.###" : "0.#", CultureInfo.GetCultureInfo(Pl ? "pl-PL" : "en-US"));
    string? ModelSpaceProblem()
    {
        if (!GpuReady) return T("A working NVIDIA driver is required for local models. Go back to the computer check, or clear the local-model option.", "Modele lokalne wymagają działającego sterownika NVIDIA. Wróć do testu komputera albo odznacz modele lokalne.");
        try
        {
            string cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache/huggingface/hub");
            long missing = DownloadModels.Sum(m => repairModels || reinstallModels ? m.Bytes : ModelMissingBytes(m));
            var modelDisk = DiskProbe(cache); var appDisk = DiskProbe(root.Text);
            long required = 1_000_000_000 + missing + (string.Equals(modelDisk.Volume, appDisk.Volume, StringComparison.OrdinalIgnoreCase) && operation == "install" ? Math.Max(0, 25_000_000_000 - catalog.Models.Sum(m => m.Bytes)) : 0);
            if (modelDisk.Free < required) return T("Not enough space on the model-cache disk. Required free space: ", "Za mało miejsca na dysku cache modeli. Potrzebne wolne miejsce: ") + GB(required) + " GB";
        }
        catch { return T("Cannot check model-cache disk space.", "Nie można sprawdzić miejsca na dysku cache modeli."); }
        return null;
    }
    bool GpuReady => host is JsonElement value && value.GetProperty("checks").EnumerateArray().Any(c => c.GetProperty("code").GetString() == "gpu" && c.GetProperty("status").GetString() == "pass");
    void EnterCredential(bool hf)
    {
        var dialog = new CredentialDialog(this, hf, Pl);
        if (dialog.ShowDialog() != true) return;
        StoreCheckedCredential(hf, dialog.Value);
    }
    void StoreCheckedCredential(bool hf, string value)
    {
        if (hf) { hfSecret = value; hfValid = true; missingRequirements.Remove("hf"); } else { orSecret = value; orValid = true; }
        Render();
    }
    void ShowHfHelp() => CreateHfHelp().ShowDialog();
    Window CreateHfHelp()
    {
        var help = new Window { Owner = this, Icon = Icon, ShowInTaskbar = false, Title = T("Hugging Face token", "Token Hugging Face"), Width = 540, SizeToContent = SizeToContent.Height, ResizeMode = ResizeMode.NoResize, WindowStartupLocation = WindowStartupLocation.CenterOwner, Background = Paper, FontFamily = FontFamily, FontSize = 14 };
        var panel = new StackPanel(); help.Content = new Border { Background = Paper, Padding = new Thickness(24), Child = panel };
        panel.Children.Add(Heading(T("Before entering your token", "Przed podaniem tokenu")));
        panel.Children.Add(TokenWarning());
        panel.Children.Add(Copy(T("The token is used only during installation to download pyannote. It is not saved.", "Token jest używany tylko podczas instalacji do pobrania pyannote. Nie jest zapisywany.")));
        void Step(string before, string label, string url, string after)
        {
            var text = Copy(""); text.Inlines.Add(new Run(before));
            var link = new Hyperlink(new Run(label)) { NavigateUri = new Uri(url) };
            link.RequestNavigate += (_, e) => { Open(e.Uri.AbsoluteUri); e.Handled = true; };
            text.Inlines.Add(link); text.Inlines.Add(new Run(after)); panel.Children.Add(text);
        }
        Step("1. ", T("Create an account", "Załóż konto"), "https://huggingface.co/join", T(" on Hugging Face and sign in.", " Hugging Face i zaloguj się."));
        Step("2. ", T("Open the model page", "Otwórz stronę modelu"), "https://huggingface.co/pyannote/speaker-diarization-community-1", T(", complete the access form and accept the terms.", ", wypełnij formularz dostępu i zaakceptuj warunki."));
        Step(T("3. In ", "3. W "), "Settings → Access Tokens", "https://huggingface.co/settings/tokens", T(", create a read-only token (Read).", " utwórz token tylko do odczytu (Read)."));
        panel.Children.Add(Copy(T("4. Copy it into the installer and check access.", "4. Wklej go do instalatora i sprawdź dostęp.")));
        panel.Children.Add(Link(T("Detailed instructions for this procedure", "Szczegółowa instrukcja tej procedury"), () => Open("https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/HUGGINGFACE_ACCESS" + (Pl ? "_PL" : "") + ".md")));
        var footer = new Grid { Margin = new Thickness(0, 12, 0, 0) }; footer.ColumnDefinitions.Add(new ColumnDefinition()); footer.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var licenses = Link(T("Licenses and artwork", "Licencje i autorstwo"), ShowLicenses); licenses.VerticalAlignment = VerticalAlignment.Center; footer.Children.Add(licenses);
        var close = ActionButton(T("Close", "Zamknij"), () => help.Close()); Grid.SetColumn(close, 1); footer.Children.Add(close); panel.Children.Add(footer);
        help.PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) help.Close(); }; return help;
    }
    async Task CheckHost()
    {
        if (busy) return;
        int epoch = stateEpoch;
        bool localForCheck = LocalSelected; checkedLocalModels = localForCheck;
        busy = true; hostReady = hostAttempted = false; host = null; notice = ""; File.Delete(CancelFile); Render();
        try { int code = await (HostCheckRunner?.Invoke() ?? Worker("check", false)); hostReady = epoch == stateEpoch && code == 0; if (!hostReady && epoch == stateEpoch) notice = "check_failed"; }
        catch { hostReady = false; notice = "check_unavailable"; }
        finally
        {
            busy = false; hostAttempted = epoch == stateEpoch;
            if (hostAttempted) checkedLocalModels = localForCheck;
            Render();
        }
        if (epoch != stateEpoch) await AutoCheckHost();
    }
    async Task PreviewRemoval()
    {
        busy = true; previewReady = false; File.Delete(CancelFile); RefreshNavigation();
        try { previewReady = await Worker("uninstall", false) == 0; }
        catch { notice = "preview_failed"; }
        finally { busy = false; Render(); }
    }
    async Task RunOperation()
    {
        page = ProgressPage; busy = true; finished = successful = false; progressStage = ""; ResetOperationProgress(); operationClock.Start(); File.Delete(CancelFile); Render();
        try { successful = await Worker(repairModels ? "models" : operation, true) == 0; }
        catch { successful = false; log.AppendText("INSTALLER_OPERATION_FAILED\n"); }
        finally { operationClock.Stop(); busy = false; finished = true; hfSecret = orSecret = ""; hfValid = orValid = false; terms.IsChecked = false; Render(); }
    }
    void RenderHostRows()
    {
        hostRows.Children.Clear();
        if (host is not JsonElement result) return;
        if (operation == "models" && installed is JsonElement installedState)
        {
            string current = installedState.GetProperty("version").GetString()!;
            var check = Copy(T("Program version: ", "Wersja programu: ") + current + T(" · installer: ", " · instalator: ") + version + (current == version ? " · OK" : "\n" + LocationProblem()));
            check.Foreground = current == version ? Success : Error; hostRows.Children.Add(check);
        }
        foreach (var row in result.GetProperty("checks").EnumerateArray())
        {
            string status = row.GetProperty("status").GetString()!;
            string code = row.GetProperty("code").GetString()!;
            var grid = new Grid { Margin = new Thickness(0, 5, 0, 5) }; grid.ColumnDefinitions.Add(new ColumnDefinition()); grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100) });
            var description = new StackPanel { Margin = new Thickness(0, 0, 14, 0) };
            description.Children.Add(new TextBlock { Text = HostText(row), TextWrapping = TextWrapping.Wrap });
            if (code == "platform" && status == "warning")
            {
                var note = Copy(T("Compatibility on older or unrecognized Windows versions is not guaranteed.", "Nie gwarantujemy działania na starszych lub nierozpoznanych wersjach Windows."), muted: true);
                note.Margin = new Thickness(0, 4, 0, 0); description.Children.Add(note);
            }
            grid.Children.Add(description);
            if (status == "warning")
            {
                var icon = Symbols.Warning(); icon.HorizontalAlignment = HorizontalAlignment.Left; icon.VerticalAlignment = VerticalAlignment.Center;
                icon.ToolTip = code == "platform" ? T("Older Windows version — compatibility not guaranteed", "Starsza wersja Windows — działanie niegwarantowane") : T("Check could not confirm readiness", "Test nie potwierdził gotowości");
                Grid.SetColumn(icon, 1); grid.Children.Add(icon);
            }
            else
            {
                var state = new TextBlock { Text = status == "pass" ? "OK" : T("action required", "wymaga działania"), Foreground = status == "pass" ? Success : Error, FontWeight = FontWeights.SemiBold, VerticalAlignment = VerticalAlignment.Center };
                Grid.SetColumn(state, 1); grid.Children.Add(state);
            }
            hostRows.Children.Add(grid);
        }
    }
    string HostText(JsonElement row)
    {
        string code = row.GetProperty("code").GetString()!;
        JsonElement context = row.TryGetProperty("context", out var value) ? value : default;
        string Field(string name) => context.ValueKind == JsonValueKind.Object && context.TryGetProperty(name, out var field) ? field.GetString() ?? "" : "";
        return code switch
        {
            "architecture" => T("64-bit processor: ", "Procesor 64-bit: ") + Field("cpu_model"),
            "platform" => T("System: ", "System: ") + Field("name"),
            "disk" => T("Disk space: ", "Miejsce na dysku: ") + "(" + GB(context.GetProperty("free_bytes").GetInt64()) + T(" GB free; ", " GB wolne; ") + GB(context.GetProperty("installation_bytes").GetInt64()) + T(" GB required", " GB wymagane") + (context.TryGetProperty("additional_bytes", out var additional) && operation != "install" ? T(" for program and basic models; additional free space: ", " na program i podstawowe modele; dodatkowe wolne miejsce: ") + GB(additional.GetInt64()) + " GB" : "") + ")",
            "gpu" => T("GPU driver: ", "Sterownik GPU: ") + (context.TryGetProperty("devices", out var devices) && devices.GetArrayLength() > 0 ? string.Join("; ", devices.EnumerateArray().Select(d => d.GetProperty("name").GetString() + " · " + d.GetProperty("driver").GetString())) : T("not detected", "nie wykryto")),
            "vc_runtime" => T("Visual C++ libraries", "Biblioteki Visual C++"),
            _ => "FFmpeg / ffprobe"
        };
    }
    async Task<int> Worker(string op, bool confirm)
    {
        if (testing) throw new InvalidOperationException("A self-test must never invoke installation or network workers");
        bool prepare = op is "install" or "update" or "repair" or "models";
        int epoch = stateEpoch;
        var request = new OperationRequest(op, root.Text, confirm, prepare && LocalSelected || op == "check" && operation == "models",
            prepare && terms.IsChecked == true, removeModels.IsChecked == true, removeKey.IsChecked == true,
            prepare && LocalSelected && hfValid ? hfSecret : "", op == "install" && orValid ? orSecret : "",
            Environment.ProcessPath!, Environment.ProcessId, CancelFile, op == "models" || op == "install" && LocalSelected ? DownloadModels.Select(m => m.Code).ToArray() : null, repairModels || reinstallModels, operation == "rollback" ? rollbackTarget : null);
        async Task Output(string line)
        {
            string text = line, stage = ""; JsonElement? item = null;
            try { using var json = JsonDocument.Parse(line); item = json.RootElement.Clone(); if (item.Value.TryGetProperty("message", out var m)) text = m.GetString() ?? line; if (item.Value.TryGetProperty("stage", out var st)) stage = st.GetString() ?? ""; }
            catch { }
            await Dispatcher.InvokeAsync(() =>
            {
                if (epoch != stateEpoch) return;
                log.AppendText(DateTimeOffset.Now.ToString("HH:mm:ss.fff zzz") + " · " + text + Environment.NewLine); if (log.Text.Length > 100000) log.Text = log.Text[^80000..]; log.ScrollToEnd();
                if (item is JsonElement data && data.TryGetProperty("checks", out _)) { host = data; RenderHostRows(); }
                if (item is JsonElement plan && stage == "preview") removal = plan;
                if (item is JsonElement verification && stage == "model-verification") modelVerification = verification.GetProperty("models").Clone();
                UpdateOperationProgress(stage, text, item);
                if (stage != "log" && stage != "model-item" && stage != "model-complete" && stage != "download" && stage.Length > 0 && IsProgressPage && progressStage != "cancel") { progressStage = stage; Render(); }
            });
        }
        if (OperationRunner.NeedsElevation(request))
        {
            progressStage = "permission"; Render();
            return await OperationRunner.Elevated(request, Output);
        }
        return await OperationRunner.Run(request, Path.Combine(temporary, "payload"), embedded, Path.Combine(temporary, "runtime"), Output);
    }
    void SaveReport()
    {
        var picker = new SaveFileDialog { InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), Filter = "Text (*.txt)|*.txt", FileName = "EwP-setup-report-" + DateTimeOffset.Now.ToString("yyyyMMdd-HHmmss-fff-zzz").Replace(":", "") + ".txt" };
        if (picker.ShowDialog(this) != true) return;
        try { File.WriteAllText(picker.FileName, "EwP Setup " + version + " · " + DateTimeOffset.Now.ToString("o") + Environment.NewLine + "Operation: " + operation + Environment.NewLine + log.Text); }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException)
        { MessageBox.Show(this, T("Cannot save the report here. Choose a writable folder.", "Nie można zapisać tu raportu. Wybierz folder z prawem zapisu."), Title, MessageBoxButton.OK, MessageBoxImage.Warning); }
    }
    void Launch()
    {
        string path = Path.Combine(root.Text, "launch.ps1");
        if (!File.Exists(path)) return;
        var start = new ProcessStartInfo(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), @"WindowsPowerShell\v1.0\powershell.exe")) { UseShellExecute = true };
        foreach (string argument in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path }) start.ArgumentList.Add(argument);
        Process.Start(start); Close();
    }
    internal void ShowLicenses() => Open(Credits.Prepare(Path.Combine(temporary, "payload/app/src/ewp_transcripts/web_assets/brand/NOTICE.txt"), Path.Combine(temporary, "payload/app/src/ewp_transcripts/web_assets/brand/NOTICE-readable.txt")));
    static void Open(string value) => Process.Start(new ProcessStartInfo(value) { UseShellExecute = true });
    internal static void VerifyBundle(string path)
    {
        using var zip = ZipFile.OpenRead(path); using var document = JsonDocument.Parse(zip.GetEntry("bundle.json")!.Open());
        var entries = document.RootElement.GetProperty("sha256").EnumerateObject().ToList();
        if (entries.Count + 1 != zip.Entries.Count || zip.Entries.Select(e => e.FullName.ToLowerInvariant()).Distinct().Count() != zip.Entries.Count) throw new InvalidDataException();
        foreach (var entry in entries)
        {
            if (entry.Name.Split('/').Contains("..") || entry.Name.Contains('\\') || entry.Name.StartsWith('/') || entry.Name.Contains(':')) throw new InvalidDataException();
            using var stream = zip.GetEntry(entry.Name)!.Open();
            if (Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(stream)).ToLowerInvariant() != entry.Value.GetString()) throw new InvalidDataException();
        }
    }
}

sealed class Catalog { public List<ModelEntry> Models { get; set; } = []; }
sealed class ModelEntry
{
    public string Code { get; set; } = "";
    public string Revision { get; set; } = "";
    public bool Gated { get; set; }
    public bool Optional { get; set; }
    public string Repository { get; set; } = "";
    public string Path { get; set; } = "";
    public long Bytes { get; set; }
    public Dictionary<string, long> Files { get; set; } = [];
    public long MissingBytes()
    {
        string folder = Path.Replace("~", Environment.GetFolderPath(Environment.SpecialFolder.UserProfile));
        if (Files.Count == 0) return Bytes;
        return Files.Sum(file =>
        {
            try { var info = new FileInfo(System.IO.Path.Combine(folder, file.Key.Replace('/', System.IO.Path.DirectorySeparatorChar))); return info.Exists && info.Length == file.Value ? 0L : file.Value; }
            catch { return file.Value; }
        });
    }
}
