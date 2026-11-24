using System.IO;
using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using System.Windows;

namespace EwP.Setup;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        if (string.Equals(Path.GetFileName(Environment.ProcessPath), "uninstall.exe", StringComparison.OrdinalIgnoreCase))
        {
            // Run the version-matched wizard, releasing the root entry point before repair/removal.
            string root = Path.GetDirectoryName(Environment.ProcessPath!)!;
            try
            {
                using var state = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "installation.json")));
                string wizard = state.RootElement.GetProperty("wizard").GetString()!;
                if (!Path.GetFullPath(wizard).StartsWith(Path.GetFullPath(Path.Combine(root, "wizards")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException();
                var start = new ProcessStartInfo(wizard) { UseShellExecute = false };
                foreach (string value in new[] { "--local-maintenance", "--root", root }) start.ArgumentList.Add(value);
                Process.Start(start); return;
            }
            catch { args = ["--local-maintenance", "--root", root]; }
        }
        if (args.Contains("--elevated-operation"))
        {
            string? pipe = Argument(args, "--pipe");
            if (pipe == null || !int.TryParse(Argument(args, "--parent"), out int parent)) { Environment.ExitCode = 2; return; }
            Environment.ExitCode = OperationRunner.WorkerMain(pipe, parent, args.Contains("--broker-self-test")).GetAwaiter().GetResult();
            return;
        }
        var app = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        bool test = args.Contains("--self-test");
        string? report = Argument(args, "--self-test-report");
        app.Startup += async (_, _) =>
        {
            try
            {
                var wizard = new Wizard(args);
                if (!test)
                {
                    app.ShutdownMode = ShutdownMode.OnMainWindowClose;
                    app.MainWindow = wizard;
                    wizard.Show();
                    return;
                }
                await wizard.SelfTest(Argument(args, "--preview-dir"));
                wizard.Close();
                if (report != null) File.WriteAllText(report, JsonSerializer.Serialize(new
                {
                    result = "PASS",
                    platform = Environment.OSVersion.ToString(),
                    version = Assembly.GetExecutingAssembly().GetName().Version?.ToString(3),
                    checks = Wizard.TestChecks
                }));
                app.Shutdown(0);
            }
            catch (Exception error)
            {
                if (test && report != null)
                    File.WriteAllText(report, JsonSerializer.Serialize(new { result = "FAIL", type = error.GetType().FullName, message = error.Message, stack = error.StackTrace }));
                else MessageBox.Show("Cannot prepare EwP Setup. Download the complete installer again. / Nie można przygotować instalatora. Pobierz go ponownie.", "EwP Setup");
                app.Shutdown(2);
            }
        };
        app.Run();
    }

    static string? Argument(string[] args, string name)
    {
        int index = Array.IndexOf(args, name);
        return index >= 0 && index + 1 < args.Length ? args[index + 1] : null;
    }
}
