using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace EwP.Setup;

record CredentialResult(bool Valid, string Code, string English, string Polish)
{
    public string Text(bool pl) => Valid ? "OK" : Code + " · " + (pl ? Polish : English);
}

static class CredentialChecks
{
    public static async Task<CredentialResult> Check(bool hf, string value, CancellationToken token)
    {
        string prefix = hf ? "HF" : "OR";
        if (value.Length is < 8 or > 512 || value.Any(c => c > 127 || char.IsWhiteSpace(c)))
            return new(false, prefix + "_TOKEN_INVALID", "Paste one key without whitespace.", "Wklej jeden klucz bez białych znaków.");
        try
        {
            using var handler = new HttpClientHandler { AllowAutoRedirect = false };
            using var client = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(20) };
            using var request = new HttpRequestMessage(HttpMethod.Get, hf
                ? "https://huggingface.co/api/models/pyannote/speaker-diarization-community-1/auth-check"
                : "https://openrouter.ai/api/v1/key");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", value);
            using var response = await client.SendAsync(request, token);
            if (response.StatusCode == HttpStatusCode.OK)
            {
                if (!hf)
                {
                    using var json = JsonDocument.Parse(await response.Content.ReadAsStringAsync(token));
                    if (!json.RootElement.TryGetProperty("data", out var data) || data.ValueKind != JsonValueKind.Object)
                        return new(false, "OR_RESPONSE_INVALID", "Unexpected key-check response.", "Nieprawidłowa odpowiedź testu klucza.");
                }
                return new(true, "OK", "OK", "OK");
            }
            if (hf && response.StatusCode == HttpStatusCode.Forbidden)
                return new(false, "HF_HTTP_403", "Accept pyannote terms and grant this token read access.", "Zaakceptuj warunki pyannote i nadaj tokenowi dostęp do odczytu.");
            return new(false, prefix + "_HTTP_" + (int)response.StatusCode,
                "Check the key, access and connection.", "Sprawdź klucz, uprawnienia i połączenie.");
        }
        catch (OperationCanceledException) when (token.IsCancellationRequested) { throw; }
        catch
        {
            return new(false, prefix + "_CONNECTION_FAILED", "Check connection and retry.", "Sprawdź połączenie i spróbuj ponownie.");
        }
    }
}

sealed class CredentialDialog : Window
{
    readonly bool hf, pl;
    readonly PasswordBox input = new() { Padding = new Thickness(10), MinWidth = 320 };
    readonly Button check, accept;
    readonly TextBlock status = new() { TextWrapping = TextWrapping.Wrap, VerticalAlignment = VerticalAlignment.Center };
    readonly Image gear = Wizard.BusyGear();
    readonly Func<bool, string, CancellationToken, Task<CredentialResult>> validator;
    CancellationTokenSource? pending;
    string checkedValue = "";
    bool valid;
    internal string Value { get; private set; } = "";
    string T(string en, string local) => pl ? local : en;

    public CredentialDialog(Window owner, bool forHf, bool polish,
        Func<bool, string, CancellationToken, Task<CredentialResult>>? checker = null)
    {
        Owner = owner; hf = forHf; pl = polish; validator = checker ?? CredentialChecks.Check;
        Title = hf ? "Hugging Face" : "OpenRouter";
        Width = 570; MinWidth = 460; SizeToContent = SizeToContent.Height;
        WindowStartupLocation = WindowStartupLocation.CenterOwner; ResizeMode = ResizeMode.NoResize;
        Background = Wizard.Paper; Foreground = Wizard.Ink; FontFamily = new FontFamily("Segoe UI"); FontSize = 14;
        var body = new StackPanel { Margin = new Thickness(24) }; Content = body;
        body.Children.Add(Wizard.Heading(hf ? T("Hugging Face read token", "Token odczytu Hugging Face") : T("OpenRouter API key", "Klucz API OpenRouter")));
        body.Children.Add(Wizard.Copy(hf
            ? T("Used only during installation to download pyannote. It is not saved.", "Używany tylko podczas instalacji do pobrania pyannote. Nie jest zapisywany.")
            : T("Checked without sending audio. Saved in the OS store only during installation.", "Sprawdzany bez wysyłania audio. Zapis w magazynie systemowym nastąpi dopiero podczas instalacji."), muted: true));
        body.Children.Add(input);
        var row = new Grid { Margin = new Thickness(0, 14, 0, 8) };
        row.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        row.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        row.ColumnDefinitions.Add(new ColumnDefinition());
        check = Wizard.ActionButton(hf ? T("Check token", "Sprawdź token") : T("Check key", "Sprawdź klucz"), async () => await Validate(false), secondary: true);
        row.Children.Add(check); Grid.SetColumn(gear, 1); row.Children.Add(gear);
        Grid.SetColumn(status, 2); status.Margin = new Thickness(12, 0, 0, 0); row.Children.Add(status); body.Children.Add(row);
        var footer = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0) };
        footer.Children.Add(Wizard.ActionButton(T("Cancel", "Anuluj"), () => Close(), secondary: true));
        accept = Wizard.ActionButton("OK", Accept); accept.IsEnabled = false; accept.IsDefault = true; footer.Children.Add(accept); body.Children.Add(footer);
        input.PasswordChanged += async (_, _) => await Validate(true);
        PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) { e.Handled = true; Close(); } };
        Loaded += (_, _) => input.Focus();
        Closed += (_, _) => { pending?.Cancel(); input.Clear(); };
    }

    async Task Validate(bool debounce)
    {
        pending?.Cancel(); pending = new CancellationTokenSource();
        var token = pending.Token;
        valid = false; checkedValue = ""; accept.IsEnabled = false;
        string value = input.Password;
        if (value.Length == 0) { status.Text = ""; gear.Visibility = Visibility.Collapsed; return; }
        try
        {
            if (debounce) await Task.Delay(500, token);
            check.IsEnabled = false; gear.Visibility = Visibility.Visible;
            status.Text = T("Checking…", "Sprawdzanie…"); status.Foreground = Wizard.Muted;
            var result = await validator(hf, value, token);
            if (token.IsCancellationRequested || input.Password != value) return;
            valid = result.Valid; checkedValue = valid ? value : "";
            status.Text = result.Text(pl); status.Foreground = valid ? Wizard.Success : Wizard.Error;
            accept.IsEnabled = valid;
        }
        catch (OperationCanceledException) { }
        finally
        {
            if (!token.IsCancellationRequested) { check.IsEnabled = true; gear.Visibility = Visibility.Collapsed; }
        }
    }

    void Accept()
    {
        if (!valid || input.Password != checkedValue) return;
        Value = checkedValue; DialogResult = true;
    }

    internal async Task TestPaste(string value)
    {
        input.Password = value;
        await Task.Delay(650);
    }
    internal void TestAccept() => Accept();
    internal bool CanAccept => accept.IsEnabled;
    internal string Status => status.Text;
    internal string TestAcceptedValue() => valid ? checkedValue : "";
}
