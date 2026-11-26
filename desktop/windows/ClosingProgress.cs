using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace EwP.Desktop;

sealed class ClosingProgress : Window
{
    readonly TextBlock message = new() { TextWrapping = TextWrapping.Wrap, FontSize = 17, FontWeight = FontWeights.SemiBold };
    bool finished;
    public ClosingProgress(Window owner, bool applicationDark)
    {
        Owner = owner; ShowInTaskbar = false; WindowStyle = WindowStyle.None; ResizeMode = ResizeMode.NoResize;
        SizeToContent = SizeToContent.Height; Width = Math.Min(520, Math.Max(280, owner.ActualWidth - 40));
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Background = (Brush)new BrushConverter().ConvertFromInvariantString(applicationDark ? "#f5f2e9" : "#12303f")!;
        Foreground = (Brush)new BrushConverter().ConvertFromInvariantString(applicationDark ? "#273342" : "#f5f7fa")!;
        var panel = new StackPanel(); panel.Children.Add(message);
        panel.Children.Add(new ProgressBar { IsIndeterminate = true, Height = 5, Margin = new Thickness(0, 18, 0, 0) });
        Content = new Border { Padding = new Thickness(28), Background = Background, BorderBrush = Foreground, BorderThickness = new Thickness(1), Child = panel };
        Closing += (_, e) => e.Cancel = !finished;
    }
    public void SetMessage(string text) { message.Text = text; Title = text; }
    public void Complete() { finished = true; Close(); }
}
