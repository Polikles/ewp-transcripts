using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;

namespace EwP.Desktop;

static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        string? Option(string name) { int index = Array.IndexOf(args, name); return index >= 0 && index + 1 < args.Length ? args[index + 1] : null; }
        try
        {
            SetCurrentProcessExplicitAppUserModelID("EtykaWPetli.EwPTranscripts");
            var config = AppConfig.Load(Option("--root") ?? AppContext.BaseDirectory);
            using var instance = new SingleInstance(config.InstanceKey);
            if (!instance.Owned) { instance.ActivateExisting().GetAwaiter().GetResult(); return 0; }
            var app = new Application { ShutdownMode = ShutdownMode.OnMainWindowClose };
            var window = new DesktopWindow(config, Option("--self-test-report"), Option("--preview-dir"));
            instance.Listen(() => app.Dispatcher.BeginInvoke(new Action(window.BringToFront)));
            return app.Run(window);
        }
        catch (Exception error)
        {
            if (Option("--self-test-report") is string report) { File.WriteAllText(report, System.Text.Json.JsonSerializer.Serialize(new { result = "FAIL", error = error.Message })); return 2; }
            bool pl = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName == "pl";
            MessageBox.Show(pl ? "Nie udało się uruchomić EwP Transcripts. Sprawdź, czy program jest już uruchomiony, albo wybierz Napraw w instalatorze." : "EwP Transcripts could not start. Check whether it is already running, or choose Repair in the installer.", "EwP Transcripts", MessageBoxButton.OK, MessageBoxImage.Warning);
            return 2;
        }
    }
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] static extern int SetCurrentProcessExplicitAppUserModelID(string id);
}
