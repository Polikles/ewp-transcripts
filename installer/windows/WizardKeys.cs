using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;

namespace EwP.Setup;

sealed partial class Wizard
{
    TextBlock TokenWarning()
    {
        var text = Copy(T("Treat tokens like passwords", "Traktuj tokeny jak hasła"));
        text.Foreground = Error; text.FontWeight = FontWeights.SemiBold; return text;
    }
    void LinkedStep(Panel panel, string before, string label, string url, string after)
    {
        var text = Copy(""); text.Inlines.Add(new Run(before));
        var link = new Hyperlink(new Run(label)) { NavigateUri = new Uri(url) };
        link.RequestNavigate += (_, e) => { Open(e.Uri.AbsoluteUri); e.Handled = true; };
        text.Inlines.Add(link); text.Inlines.Add(new Run(after)); panel.Children.Add(text);
    }
    void RenderOpenRouter()
    {
        body.Children.Add(Heading(T("4. OpenRouter key", "4. Klucz OpenRouter")));
        body.Children.Add(Copy(T("Optional. OpenRouter enables cloud transcription, correction and translation. You can add a key later in the program.", "Opcjonalnie. OpenRouter umożliwia transkrypcję, korektę i tłumaczenie w chmurze. Klucz możesz dodać także później w programie.")));
        body.Children.Add(TokenWarning());
        var key = ActionButton(T("Enter OpenRouter key", "Podaj klucz OpenRouter"), () => EnterCredential(false), secondary: true);
        key.IsEnabled = !orValid; body.Children.Add(key);
        if (orValid) body.Children.Add(Copy(T("Key valid", "Klucz prawidłowy")));
        LinkedStep(body, "1. ", T("Create an account", "Załóż konto"), "https://openrouter.ai/", T(" on OpenRouter and sign in.", " OpenRouter i zaloguj się."));
        LinkedStep(body, "2. ", T("Add credits", "Doładuj konto"), "https://openrouter.ai/settings/credits", T(" for the models you want to use.", " na korzystanie z wybranych modeli."));
        LinkedStep(body, "3. ", T("Open workspaces", "Otwórz obszary robocze"), "https://openrouter.ai/workspaces", T(" and choose Default for this program.", " i wybierz Default dla tego programu."));
        LinkedStep(body, "4. ", T("Create an API key", "Utwórz klucz API"), "https://openrouter.ai/workspaces/default/keys", T(" in that workspace. Set a low credit limit* and paste the key into the installer.", " w wybranym obszarze. Ustaw niski limit wydatków klucza* i wklej go do instalatora."));
        var spendingNote = Copy(T("*in our testing $2 was enough for a few transcriptions", "*w naszych testach $2 wystarczyło na wiele transkrypcji"), muted: true);
        spendingNote.Margin = new Thickness(0, -8, 0, 14); body.Children.Add(spendingNote);
        body.Children.Add(Copy(T("The key is checked without sending recordings and saved in the OS credential store during installation. This does not grant consent to upload audio.", "Klucz jest sprawdzany bez wysyłania nagrań i zapisywany w magazynie systemowym podczas instalacji. Nie oznacza to zgody na wysyłanie audio."), muted: true));
        body.Children.Add(Link(T("Detailed instructions for this procedure", "Szczegółowa instrukcja tej procedury"), () => Open("https://learn.openrouter.ai/courses/first-request/create-an-api-key")));
    }
}
