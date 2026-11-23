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
    readonly string temporary = Path.Combine(Path.GetTempPath(), "ewp-setup-" + Guid.NewGuid().ToString("N"));
    readonly string embedded, version = Assembly.GetExecutingAssembly().GetName().Version!.ToString(3);
    readonly StackPanel body = new() { Margin = new Thickness(28, 22, 28, 18), MaxWidth = 760 };
    readonly TextBlock subtitle = new(), steps = new() { TextWrapping = TextWrapping.Wrap };
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
    bool busy, finished, successful, hostReady, hfValid, orValid, previewReady, testing;
    int page;
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
        Background = Paper; Foreground = Ink; FontFamily = new FontFamily("Segoe UI"); FontSize = 14;
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
        var header = new Grid { Background = ColorBrush("#355880"), Height = 118 };
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        header.ColumnDefinitions.Add(new ColumnDefinition());
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        header.Children.Add(new Image { Source = Branding.Svg("favicon.svg"), Width = 82, Height = 82, Stretch = Stretch.Uniform, Margin = new Thickness(22, 18, 18, 18), HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center });
        var title = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
        title.Children.Add(new TextBlock { Text = "EwP Transcripts", FontSize = 28, FontWeight = FontWeights.SemiBold, Foreground = Brushes.White });
        subtitle.Foreground = ColorBrush("#E4EDF7"); subtitle.FontSize = 14; subtitle.Margin = new Thickness(0, 5, 0, 0); title.Children.Add(subtitle);
        Grid.SetColumn(title, 1); header.Children.Add(title);
        language.Margin = new Thickness(16, 0, 22, 0); language.VerticalAlignment = VerticalAlignment.Center;
        Grid.SetColumn(language, 2); header.Children.Add(language); shell.Children.Add(header);
        var progress = new Border { Child = steps, Background = ColorBrush("#E8ECED"), Padding = new Thickness(28, 12, 28, 12) };
        steps.Foreground = Muted; steps.FontSize = 12;
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
        root.Text = RegisteredRoot() ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "EwPTranscripts");
        ReadInstalled(); local.IsChecked = installed?.TryGetProperty("local_models", out var lm) == true ? lm.GetBoolean() : true;
        root.TextChanged += (_, _) => ScheduleLocation();
        local.Checked += (_, _) => { if (page == 2) Render(); }; local.Unchecked += (_, _) => { if (page == 2) Render(); };
        terms.Checked += (_, _) => RefreshNavigation(); terms.Unchecked += (_, _) => RefreshNavigation();
        language.SelectionChanged += (_, _) => Render();
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--uninstall") operation = "uninstall";
            if (args[i] == "--root" && i + 1 < args.Length) root.Text = args[++i];
        }
        Closing += (_, e) => { if (busy) { e.Cancel = true; Cancel(); } };
        Closed += (_, _) => { hfSecret = orSecret = ""; locationChange?.Cancel(); try { Directory.Delete(temporary, true); } catch { } };
        PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) { e.Handled = true; Cancel(); } };
        Render();
    }

    internal static TextBlock Heading(string text) => new() { Text = text, FontSize = 23, FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 0, 0, 16), TextWrapping = TextWrapping.Wrap };
    internal static TextBlock Copy(string text, bool muted = false) => new() { Text = text, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 14), Foreground = muted ? Muted : Ink, FontSize = muted ? 12 : 14 };
    internal static Button ActionButton(string text, Action callback, bool secondary = false)
    {
        var button = new Button { Content = text, Padding = new Thickness(16, 9, 16, 9), Margin = new Thickness(0, 0, 8, 0), MinHeight = 36, Background = ColorBrush(secondary ? "#E2E8EB" : "#355880"), Foreground = secondary ? Ink : Brushes.White, BorderThickness = new Thickness(0), HorizontalAlignment = HorizontalAlignment.Left, Cursor = Cursors.Hand };
        var border = new FrameworkElementFactory(typeof(Border)); border.SetValue(Border.CornerRadiusProperty, new CornerRadius(6)); border.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Control.BackgroundProperty)); border.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Control.PaddingProperty));
        var presenter = new FrameworkElementFactory(typeof(ContentPresenter)); presenter.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center); presenter.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); border.AppendChild(presenter);
        var template = new ControlTemplate(typeof(Button)) { VisualTree = border };
        var hover = new Trigger { Property = IsMouseOverProperty, Value = true }; hover.Setters.Add(new Setter(Control.BackgroundProperty, ColorBrush(secondary ? "#CFDDE4" : "#294B70"))); template.Triggers.Add(hover);
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
        var gear = new Image { Source = Branding.Svg("gear.svg"), Width = 24, Height = 24, Margin = new Thickness(10, 2, 10, 2), Visibility = Visibility.Collapsed, RenderTransformOrigin = new Point(.5, .5), RenderTransform = new RotateTransform() };
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
        "models" => T("Add the pinned local models to an installed program. Use an installer matching its version.", "Doinstaluj przypięte modele lokalne do istniejącego programu. Użyj instalatora zgodnego z jego wersją."),
        "rollback" => T("Activate the retained previous program version. No models or user files are removed.", "Przywróć zachowaną poprzednią wersję programu. Modele i pliki użytkownika nie będą usuwane."),
        _ => T("Preview removal, then choose whether to keep shared models and the saved API key. Recordings and work remain.", "Przejrzyj plan usunięcia i wybierz, czy zachować współdzielone modele i klucz API. Nagrania i praca pozostaną.")
    };

    void Render()
    {
        body.Children.Clear();
        subtitle.Text = T("Local-first transcript workflow", "Lokalne narzędzie do transkrypcji");
        ((Run)((Hyperlink)license.Inlines.FirstInline).Inlines.FirstInline).Text = T("Licenses and artwork", "Licencje i autorstwo");
        steps.Text = IsInstall
            ? T("1. Action   ›   2. Folder and computer   ›   3. Models and keys   ›   4. Installation", "1. Działanie   ›   2. Folder i komputer   ›   3. Modele i klucze   ›   4. Instalacja")
            : T("1. Action   ›   2. Installed program   ›   3. Confirm   ›   4. Result", "1. Działanie   ›   2. Zainstalowany program   ›   3. Potwierdzenie   ›   4. Wynik");
        if (page == 0) RenderWelcome();
        else if (page == 1) RenderLocation();
        else if (page == 2 && IsInstall) RenderModels();
        else if (page == 2) RenderConfirmation();
        else RenderProgress();
        if (notice.Length > 0) { var text = Copy(NoticeText()); text.Foreground = Error; body.Children.Add(text); }
        RefreshNavigation();
    }

    string NoticeText() => notice switch
    {
        "check_failed" => T("Resolve the failed checks and retry.", "Usuń przyczyny błędów i ponów test."),
        "check_unavailable" => T("Cannot run the computer check. See technical details.", "Nie można uruchomić testu komputera. Sprawdź szczegóły techniczne."),
        _ => T("Cannot prepare removal preview.", "Nie można przygotować planu usunięcia.")
    };

    void RenderWelcome()
    {
        body.Children.Add(Heading(T("What would you like to do?", "Co chcesz zrobić?")));
        body.Children.Add(Copy(T("Choose your language above and select one action.", "Wybierz język powyżej i jedno działanie poniżej."), muted: true));
        var choices = new StackPanel();
        foreach (string op in operations)
        {
            var radio = new RadioButton { Content = OperationName(op), GroupName = "Operation", IsChecked = operation == op, FontSize = 15, Padding = new Thickness(4), Margin = new Thickness(0, 6, 0, 6) };
            radio.Checked += (_, _) => { operation = op; previewReady = false; notice = ""; if (op == "models") local.IsChecked = true; Render(); };
            choices.Children.Add(radio);
        }
        body.Children.Add(Card(choices)); body.Children.Add(Copy(OperationHelp));
        body.Children.Add(Copy(T("Installer version: ", "Wersja instalatora: ") + version, muted: true));
    }

    void RenderLocation()
    {
        body.Children.Add(Heading(IsInstall ? T("2. Folder and computer", "2. Folder i komputer") : T("2. Installed program", "2. Zainstalowany program")));
        body.Children.Add(Copy(OperationHelp, muted: true));
        body.Children.Add(Copy(operation == "install" ? T("Program installation folder", "Folder instalacji programu") : T("Installed program folder", "Folder zainstalowanego programu")));
        body.Children.Add(root);
        var chooseFolder = ActionButton(T("Choose folder…", "Wybierz folder…"), () => { var picker = new OpenFolderDialog(); if (picker.ShowDialog(this) == true) root.Text = picker.FolderName; }, secondary: true);
        chooseFolder.Margin = new Thickness(0, 8, 0, 0); body.Children.Add(chooseFolder);
        body.Children.Add(diskStatus); RefreshLocation();
        if (IsInstall)
        {
            body.Children.Add(Copy(T("Check this computer", "Sprawdź komputer")));
            body.Children.Add(Copy(T("Test utilizes small Python runtime. No data is sent", "Test korzysta z małego środowiska Python. Nie wysyła żadnych danych"), muted: true));
            var row = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 14) };
            var test = ActionButton(T("Check this computer", "Sprawdź komputer"), async () => await CheckHost(), secondary: true); test.IsEnabled = !busy;
            row.Children.Add(test); var gear = BusyGear(); gear.Visibility = busy ? Visibility.Visible : Visibility.Collapsed; row.Children.Add(gear); body.Children.Add(row);
            body.Children.Add(hostRows); RenderHostRows();
            body.Children.Add(Link(T("Download Microsoft Visual C++ libraries", "Pobierz biblioteki Microsoft Visual C++"), () => Open(Pl
                ? "https://learn.microsoft.com/pl-pl/cpp/windows/latest-supported-vc-redist"
                : "https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist")));
            if (busy) body.Children.Add(Copy(T("Preparing/checking the installer runtime…", "Przygotowywanie/sprawdzanie środowiska instalatora…"), muted: true));
            AddLog();
        }
    }

    void RenderModels()
    {
        body.Children.Add(Heading(T("3. Local models and keys", "3. Lokalne modele i klucze")));
        LabelCheck(local, T("Use local models on my GPU (without them you can only work using OpenRouter API and verify earlier transcripts)", "Użyj lokalnych modeli na moim GPU (bez nich możliwa jest tylko praca przez API OpenRouter i weryfikacja wcześniejszych transkrypcji)"));
        local.IsEnabled = operation != "models"; body.Children.Add(local);
        if (LocalSelected)
        {
            var list = new StackPanel();
            foreach (var model in catalog.Models)
            {
                var box = new CheckBox { IsChecked = true, IsEnabled = false, Content = new TextBlock { Text = model.Repository, TextWrapping = TextWrapping.Wrap }, Margin = new Thickness(0, 2, 0, 2) };
                list.Children.Add(box);
            }
            var modelCard = Card(list); modelCard.Padding = new Thickness(10); modelCard.Margin = new Thickness(0, 0, 0, 8); body.Children.Add(modelCard);
            var spaceRow = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 8) };
            var space = Copy(T("Required space: ", "Potrzebne miejsce: ") + GB(catalog.Models.Sum(m => m.Bytes)) + " GB", muted: true); space.Margin = new Thickness(0, 6, 20, 6); spaceRow.Children.Add(space);
            spaceRow.Children.Add(Link(T("Read the model terms", "Przeczytaj warunki modelu"), () => Open("https://huggingface.co/pyannote/speaker-diarization-community-1"))); body.Children.Add(spaceRow);
            var hfRow = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 4) };
            var enter = ActionButton(T("Enter Hugging Face token", "Podaj token Hugging Face"), () => EnterCredential(true), secondary: true); enter.IsEnabled = !hfValid; hfRow.Children.Add(enter);
            hfRow.Children.Add(ActionButton("(i)", ShowHfHelp, secondary: true));
            if (hfValid) hfRow.Children.Add(new TextBlock { Text = T("Token valid", "Token prawidłowy"), Foreground = Success, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(8, 0, 0, 0) });
            body.Children.Add(hfRow);
            LabelCheck(terms, T("I accepted pyannote terms on Hugging Face", "Zaakceptowałem warunki pyannote w Hugging Face")); terms.IsEnabled = hfValid; body.Children.Add(terms);
            string? modelProblem = ModelSpaceProblem();
            if (modelProblem != null) { var warning = Copy(modelProblem); warning.Foreground = Error; body.Children.Add(warning); }
        }
        var optional = new StackPanel();
        optional.Children.Add(Copy(T("(optional) save OpenRouter API key. You can also do it after program installation", "(opcjonalnie) zapisz klucz API OpenRouter. Możesz to zrobić także po instalacji programu")));
        var keyRow = new StackPanel { Orientation = Orientation.Horizontal };
        var key = ActionButton(T("Enter OpenRouter key", "Podaj klucz OpenRouter"), () => EnterCredential(false), secondary: true); key.IsEnabled = !orValid; keyRow.Children.Add(key);
        if (orValid) keyRow.Children.Add(new TextBlock { Text = T("Key valid", "Klucz prawidłowy"), Foreground = Success, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(8, 0, 0, 0) });
        optional.Children.Add(keyRow); var optionalCard = Card(optional); optionalCard.Padding = new Thickness(10); optionalCard.Margin = new Thickness(0, 8, 0, 0); body.Children.Add(optionalCard);

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
        body.Children.Add(Heading(finished ? (successful ? T("Operation completed", "Operacja ukończona") : T("Operation stopped", "Operacja zatrzymana")) : "4. " + OperationName(operation)));
        if (busy) { var gear = BusyGear(); gear.Visibility = Visibility.Visible; body.Children.Add(gear); }
        body.Children.Add(Copy(ProgressMessage()));
        if (finished && successful && operation == "uninstall") body.Children.Add(Copy(T("Close this window to finish removing locked files.", "Zamknij to okno, aby zakończyć usuwanie zablokowanych plików.")));
        AddLog(expand: finished && !successful);
    }

    string progressStage = "";
    string ProgressMessage() => finished ? (successful
        ? T("Read the report below. User work has been preserved.", "Przeczytaj raport poniżej. Pliki pracy zostały zachowane.")
        : T("Read the details below. You can go back and retry; the previous active program remains.", "Przeczytaj szczegóły poniżej. Możesz wrócić i ponowić próbę; poprzednia aktywna wersja pozostała.")) : progressStage switch
        {
            "extract" => T("Verifying program files…", "Sprawdzanie plików programu…"),
            "dependencies" => T("Installing program dependencies…", "Instalowanie zależności programu…"),
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
        var expander = new Expander { Header = T("Technical details / log", "Szczegóły techniczne / dziennik"), IsExpanded = expand, Foreground = Muted, FontSize = 12, Margin = new Thickness(0, 14, 0, 4), Content = log };
        box.Children.Add(expander);
        box.Children.Add(Link(T("Save report…", "Zapisz raport…"), SaveReport)); body.Children.Add(box);
    }

    void RefreshNavigation()
    {
        back.Content = T("Back", "Wstecz"); cancel.Content = finished ? T("Close", "Zamknij") : T("Cancel", "Anuluj");
        back.Visibility = page == 0 || (finished && successful) ? Visibility.Collapsed : Visibility.Visible;
        back.IsEnabled = !busy; language.IsEnabled = !busy;
        cancel.IsEnabled = !busy || (!(operation is "uninstall" or "rollback" && page == 3) && !File.Exists(CancelFile));
        next.Visibility = finished && (!successful || operation is "uninstall" or "rollback") ? Visibility.Collapsed : Visibility.Visible;
        next.Content = finished ? T("Launch program", "Uruchom program") : page == 2 ? (IsInstall ? T("Next — ", "Dalej — ") + OperationName(operation) : OperationName(operation)) : T("Next", "Dalej");
        next.IsEnabled = !busy && (finished ? successful : page switch
        {
            0 => true,
            1 => LocationProblem() == null && (!IsInstall || hostReady),
            2 => IsInstall ? (!LocalSelected || (hfValid && terms.IsChecked == true && ModelSpaceProblem() == null)) : operation == "rollback" || previewReady,
            _ => false
        });
    }

    async Task Next()
    {
        if (!next.IsEnabled) return;
        notice = "";
        if (finished) { Launch(); return; }
        if (page == 0) { page = 1; ReadInstalled(); Render(); return; }
        if (page == 1)
        {
            page = 2; if (operation == "models") local.IsChecked = true; Render();
            if (operation == "uninstall") await PreviewRemoval();
            return;
        }
        if (page == 2) await RunOperation();
    }
    void Back() { if (busy) return; notice = ""; if (finished) { finished = false; page = 1; } else page = Math.Max(0, page - 1); Render(); }
    void Cancel()
    {
        if (!busy) { Close(); return; }
        if (page == 3 && operation is "uninstall" or "rollback") return;
        File.WriteAllText(CancelFile, "cancel"); progressStage = "cancel"; cancel.IsEnabled = false;
        if (page == 3) Render();
    }
    void ScheduleLocation()
    {
        locationChange?.Cancel(); locationChange = new(); var token = locationChange.Token;
        hostReady = false; host = null; previewReady = false; ReadInstalled(); RefreshNavigation();
        _ = RefreshAfterDelay(token);
    }
    async Task RefreshAfterDelay(CancellationToken token)
    {
        try { await Task.Delay(200, token); if (!token.IsCancellationRequested) { RefreshLocation(); RenderHostRows(); RefreshNavigation(); } }
        catch (OperationCanceledException) { }
    }
    void ReadInstalled()
    {
        installed = null;
        try { using var data = JsonDocument.Parse(File.ReadAllText(Path.Combine(root.Text, "installation.json"))); if (data.RootElement.GetProperty("kind").GetString() == "ewp-transcripts-managed-v1") installed = data.RootElement.Clone(); }
        catch { }
    }
    string? LocationProblem()
    {
        try
        {
            string path = Path.GetFullPath(root.Text);
            if (string.IsNullOrWhiteSpace(root.Text) || path == Path.GetPathRoot(path) || string.Equals(path.TrimEnd('\\'), Environment.GetFolderPath(Environment.SpecialFolder.UserProfile).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
                return T("Choose a separate program folder.", "Wybierz osobny folder programu.");
            if (operation == "install")
            {
                if (Directory.Exists(path) && Directory.EnumerateFileSystemEntries(path).Any()) return T("Choose an empty folder; for an existing installation choose Update or Repair.", "Wybierz pusty folder; dla istniejącej instalacji wybierz Aktualizuj lub Napraw.");
                if (DiskProbe(path).Free < 25_000_000_000) return T("At least 25 GB is required (20 GB installation + 5 GB free margin).", "Potrzeba co najmniej 25 GB (20 GB instalacji + 5 GB wolnego miejsca).");
            }
            else
            {
                if (!File.Exists(Path.Combine(path, "owner.json"))) return T("Select an existing managed installation.", "Wybierz istniejącą instalację zarządzaną.");
                if (operation != "uninstall" && installed == null) return T("This installation is incomplete; use Uninstall before installing again.", "Ta instalacja jest niekompletna; przed ponowną instalacją wybierz Odinstaluj.");
                if (installed is JsonElement state)
                {
                    string current = state.GetProperty("version").GetString()!;
                    if (operation is "repair" or "models" && current != version) return T("Use an installer matching the installed version, or choose Update first.", "Użyj instalatora zgodnego z zainstalowaną wersją albo najpierw wybierz Aktualizuj.");
                    if (operation == "update" && Version.Parse(current) > Version.Parse(version)) return T("This installer is older; use Restore previous version instead.", "Ten instalator jest starszy; wybierz Przywróć poprzednią wersję.");
                    if (operation == "rollback" && (!state.TryGetProperty("previous", out var previous) || previous.ValueKind != JsonValueKind.String)) return T("No previous verified version is available.", "Brak poprzedniej zweryfikowanej wersji.");
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
            var disk = DiskProbe(root.Text);
            string text = T("Disk space: ", "Miejsce na dysku: ") + GB(disk.Free) + T(" GB free", " GB wolne");
            if (operation == "install") text += T(" · at least 25 GB (20 + 5 GB margin)", " · co najmniej 25 GB (20 + 5 GB marginesu)");
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
    string GB(long bytes) => (bytes / 1e9).ToString("0.#", CultureInfo.GetCultureInfo(Pl ? "pl-PL" : "en-US"));
    string? ModelSpaceProblem()
    {
        if (!GpuReady) return T("A working NVIDIA driver is required for local models. Go back to the computer check, or clear the local-model option.", "Modele lokalne wymagają działającego sterownika NVIDIA. Wróć do testu komputera albo odznacz modele lokalne.");
        try
        {
            string cache = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cache/huggingface/hub");
            long missing = catalog.Models.Sum(m => m.MissingBytes());
            var modelDisk = DiskProbe(cache); var appDisk = DiskProbe(root.Text);
            long required = 1_000_000_000 + missing + (string.Equals(modelDisk.Volume, appDisk.Volume, StringComparison.OrdinalIgnoreCase) && operation == "install" ? 25_000_000_000 : 0);
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
        if (hf) { hfSecret = value; hfValid = true; } else { orSecret = value; orValid = true; }
        Render();
    }
    void ShowHfHelp()
    {
        var help = new Window { Owner = this, Icon = Icon, ShowInTaskbar = false, Title = T("Hugging Face token", "Token Hugging Face"), Width = 540, SizeToContent = SizeToContent.Height, ResizeMode = ResizeMode.NoResize, WindowStartupLocation = WindowStartupLocation.CenterOwner, Background = Paper, FontFamily = FontFamily, FontSize = 14 };
        var panel = new StackPanel(); help.Content = new Border { Background = Paper, Padding = new Thickness(24), Child = panel };
        panel.Children.Add(Heading(T("Before entering your token", "Przed podaniem tokenu")));
        panel.Children.Add(Copy(T("The token is used only during installation to download pyannote. It is not saved.", "Token jest używany tylko podczas instalacji do pobrania pyannote. Nie jest zapisywany.")));
        panel.Children.Add(Copy(T("1. Create a Hugging Face account and sign in.\n2. Open the pyannote model page, complete its access form and accept the terms.\n3. In Settings → Access Tokens, create a new read-only token (Read).\n4. Copy it into the installer and check access.", "1. Załóż konto Hugging Face i zaloguj się.\n2. Otwórz stronę modelu pyannote, wypełnij formularz dostępu i zaakceptuj warunki.\n3. W Settings → Access Tokens utwórz nowy token tylko do odczytu (Read).\n4. Wklej go do instalatora i sprawdź dostęp.")));
        panel.Children.Add(Link(T("Create account", "Załóż konto"), () => Open("https://huggingface.co/join")));
        panel.Children.Add(Link(T("Read model terms", "Przeczytaj warunki modelu"), () => Open("https://huggingface.co/pyannote/speaker-diarization-community-1")));
        panel.Children.Add(Link("Settings → Access Tokens", () => Open("https://huggingface.co/settings/tokens")));
        panel.Children.Add(Link(T("Full instructions in the repository", "Pełna instrukcja w repozytorium"), () => Open("https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/HUGGINGFACE_ACCESS" + (Pl ? "_PL" : "") + ".md")));
        var footer = new Grid { Margin = new Thickness(0, 12, 0, 0) }; footer.ColumnDefinitions.Add(new ColumnDefinition()); footer.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        var licenses = Link(T("Licenses and artwork", "Licencje i autorstwo"), ShowLicenses); licenses.VerticalAlignment = VerticalAlignment.Center; footer.Children.Add(licenses);
        var close = ActionButton(T("Close", "Zamknij"), () => help.Close()); Grid.SetColumn(close, 1); footer.Children.Add(close); panel.Children.Add(footer);
        help.PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) help.Close(); }; help.ShowDialog();
    }
    async Task CheckHost()
    {
        if (busy) return;
        busy = true; notice = ""; File.Delete(CancelFile); Render();
        try { int code = await Worker("check", false); hostReady = code == 0; if (!hostReady) notice = "check_failed"; }
        catch { hostReady = false; notice = "check_unavailable"; }
        finally { busy = false; Render(); }
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
        page = 3; busy = true; finished = successful = false; progressStage = ""; File.Delete(CancelFile); Render();
        try { successful = await Worker(operation == "models" ? "repair" : operation, true) == 0; }
        catch { successful = false; log.AppendText("INSTALLER_OPERATION_FAILED\n"); }
        finally { busy = false; finished = true; hfSecret = orSecret = ""; hfValid = orValid = false; terms.IsChecked = false; Render(); }
    }
    void RenderHostRows()
    {
        hostRows.Children.Clear();
        if (host is not JsonElement result) return;
        foreach (var row in result.GetProperty("checks").EnumerateArray())
        {
            string status = row.GetProperty("status").GetString()!;
            var grid = new Grid { Margin = new Thickness(0, 4, 0, 4) }; grid.ColumnDefinitions.Add(new ColumnDefinition()); grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100) });
            grid.Children.Add(new TextBlock { Text = HostText(row), TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 14, 0) });
            var state = new TextBlock { Text = status == "pass" ? "OK" : status == "warning" ? T("check", "sprawdź") : T("action required", "wymaga działania"), Foreground = status == "pass" ? Success : status == "warning" ? Muted : Error, FontWeight = FontWeights.SemiBold, VerticalAlignment = VerticalAlignment.Center };
            Grid.SetColumn(state, 1); grid.Children.Add(state); hostRows.Children.Add(grid);
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
            "disk" => T("Disk space: ", "Miejsce na dysku: ") + "(" + GB(context.GetProperty("free_bytes").GetInt64()) + T(" GB free; ", " GB wolne; ") + GB(context.GetProperty("installation_bytes").GetInt64()) + T(" GB required)", " GB wymagane)"),
            "gpu" => T("GPU driver: ", "Sterownik GPU: ") + (context.TryGetProperty("devices", out var devices) && devices.GetArrayLength() > 0 ? string.Join("; ", devices.EnumerateArray().Select(d => d.GetProperty("name").GetString() + " · " + d.GetProperty("driver").GetString())) : T("not detected", "nie wykryto")),
            "vc_runtime" => T("Visual C++ libraries", "Biblioteki Visual C++"),
            _ => "FFmpeg / ffprobe"
        };
    }
    async Task<int> Worker(string op, bool confirm)
    {
        if (testing) throw new InvalidOperationException("A self-test must never invoke installation or network workers");
        string script = Path.Combine(temporary, "payload/control/Install-EwP.ps1");
        var info = new ProcessStartInfo("powershell.exe") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, RedirectStandardInput = true };
        foreach (string arg in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Action", op, "-Root", root.Text, "-Bundle", embedded, "-SecretsStdin", "-CancelFile", CancelFile }) info.ArgumentList.Add(arg);
        if (confirm || op == "check") info.ArgumentList.Add("-Yes");
        bool prepare = op is "install" or "update" or "repair";
        if (prepare && LocalSelected) info.ArgumentList.Add("-Local"); else info.ArgumentList.Add("-CloudOnly");
        if (prepare && terms.IsChecked == true) info.ArgumentList.Add("-AcceptModelTerms");
        if (removeModels.IsChecked == true && op == "uninstall") info.ArgumentList.Add("-RemoveModels");
        if (removeKey.IsChecked == true && op == "uninstall") info.ArgumentList.Add("-RemoveKey");
        info.Environment["EWP_BOOTSTRAP_RUNTIME"] = Path.Combine(temporary, "runtime");
        using var process = new Process { StartInfo = info }; process.Start();
        string token = prepare && LocalSelected && hfValid ? hfSecret : "", key = prepare && orValid ? orSecret : "";
        await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new { hf_token = token, openrouter_key = key, wizard_source = Environment.ProcessPath, wizard_pid = Environment.ProcessId })); process.StandardInput.Close();
        async Task Read(StreamReader reader)
        {
            while (await reader.ReadLineAsync() is string line)
            {
                if (token.Length > 0) line = line.Replace(token, "[redacted]"); if (key.Length > 0) line = line.Replace(key, "[redacted]");
                string text = line, stage = ""; JsonElement? item = null;
                try { using var json = JsonDocument.Parse(line); item = json.RootElement.Clone(); if (item.Value.TryGetProperty("message", out var m)) text = m.GetString() ?? line; if (item.Value.TryGetProperty("stage", out var st)) stage = st.GetString() ?? ""; }
                catch { }
                await Dispatcher.InvokeAsync(() =>
                {
                    log.AppendText(text + Environment.NewLine); if (log.Text.Length > 100000) log.Text = log.Text[^80000..]; log.ScrollToEnd();
                    if (item is JsonElement data && data.TryGetProperty("checks", out _)) { host = data; RenderHostRows(); }
                    if (item is JsonElement plan && stage == "preview") removal = plan;
                    if (stage != "log" && stage.Length > 0 && page == 3 && progressStage != "cancel") { progressStage = stage; Render(); }
                });
            }
        }
        await Task.WhenAll(Read(process.StandardOutput), Read(process.StandardError)); await process.WaitForExitAsync(); return process.ExitCode;
    }
    void SaveReport()
    {
        var picker = new SaveFileDialog { Filter = "Text (*.txt)|*.txt", FileName = "EwP-setup-report.txt" };
        if (picker.ShowDialog(this) == true) File.WriteAllText(picker.FileName, log.Text);
    }
    void Launch()
    {
        string path = Path.Combine(root.Text, "EwP.cmd");
        if (File.Exists(path)) { Process.Start(new ProcessStartInfo(path) { UseShellExecute = true }); Close(); }
    }
    internal void ShowLicenses() => Open(Path.Combine(temporary, "payload/app/src/ewp_transcripts/web_assets/brand/NOTICE.txt"));
    static void Open(string value) => Process.Start(new ProcessStartInfo(value) { UseShellExecute = true });
    static string? RegisteredRoot()
    {
        using var existing = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\EwPTranscripts");
        return existing?.GetValue("InstallLocation") as string;
    }
    static void VerifyBundle(string path)
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
