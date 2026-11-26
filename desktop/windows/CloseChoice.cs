using System.Windows;
using System.Windows.Controls;

namespace EwP.Desktop;

enum CloseAction { Stay, Wait, Stop }

sealed class CloseChoice : Window
{
    public CloseAction Choice { get; private set; }
    CloseChoice(Window owner, bool pl)
    {
        Owner = owner; Title = "EwP Transcripts"; SizeToContent = SizeToContent.WidthAndHeight; ResizeMode = ResizeMode.NoResize; WindowStartupLocation = WindowStartupLocation.CenterOwner; ShowInTaskbar = false;
        Background = owner.Background; Foreground = owner.Foreground;
        var panel = new StackPanel { Margin = new Thickness(24), MaxWidth = 560 };
        panel.Children.Add(new TextBlock { Text = pl ? "Trwa przetwarzanie" : "Work is still running", FontSize = 21, FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 0, 0, 12) });
        panel.Children.Add(new TextBlock { Text = pl ? "Możesz zaczekać na zakończenie zadań albo je zatrzymać i zamknąć program. Przed zamknięciem stan pracy zostanie zapisany. Przerwane zadania nie uruchomią się same po ponownym otwarciu." : "Wait for active work to finish, or stop it and close the program. Work state is saved before closing. Interrupted tasks will not restart automatically when you reopen the program.", TextWrapping = TextWrapping.Wrap, FontSize = 14 });
        var actions = new WrapPanel { Margin = new Thickness(0, 20, 0, 0) };
        foreach (var (action, label) in new[] { (CloseAction.Stay, pl ? "Kontynuuj pracę" : "Keep working"), (CloseAction.Wait, pl ? "Zaczekaj i zamknij" : "Wait and close"), (CloseAction.Stop, pl ? "Zatrzymaj i zamknij" : "Stop and close") })
        {
            var button = new Button { Tag = action, Content = label, Padding = new Thickness(12, 8, 12, 8), Margin = new Thickness(0, 0, 8, 8), IsCancel = action == CloseAction.Stay, IsDefault = action == CloseAction.Stay };
            button.Click += (_, _) => { Choice = action; Close(); }; actions.Children.Add(button);
        }
        panel.Children.Add(actions); Content = panel;
    }
    public static CloseAction Show(Window owner, bool pl) { var dialog = new CloseChoice(owner, pl); dialog.ShowDialog(); return dialog.Choice; }
    internal static void CaptureAndCheck(Window owner, string folder)
    {
        foreach (bool pl in new[] { false, true })
        foreach (var action in Enum.GetValues<CloseAction>())
        {
            var dialog = new CloseChoice(owner, pl); dialog.Show(); dialog.UpdateLayout();
            if (action == CloseAction.Stay)
            {
                var target = (FrameworkElement)dialog.Content;
                var bitmap = new System.Windows.Media.Imaging.RenderTargetBitmap((int)target.ActualWidth, (int)target.ActualHeight, 96, 96, System.Windows.Media.PixelFormats.Pbgra32); bitmap.Render(target);
                var encoder = new System.Windows.Media.Imaging.PngBitmapEncoder(); encoder.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(bitmap));
                using var file = System.IO.File.Create(System.IO.Path.Combine(folder, pl ? "pl-native-close-dialog.png" : "en-native-close-dialog.png")); encoder.Save(file);
            }
            var panel = (StackPanel)dialog.Content; var buttons = (WrapPanel)panel.Children[2];
            buttons.Children.OfType<Button>().Single(b => (CloseAction)b.Tag == action).RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            if (dialog.Choice != action) throw new InvalidOperationException("Native close choice mismatch");
        }
    }
}
