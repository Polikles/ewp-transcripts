using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace EwP.Setup;

static class ModernTheme
{
    public static void TextInput(TextBox input)
    {
        input.Background = Brushes.White; input.Foreground = Wizard.Ink;
        input.BorderBrush = (Brush)new BrushConverter().ConvertFromInvariantString("#AABCC9")!;
        input.BorderThickness = new Thickness(1); input.Padding = new Thickness(10, 6, 10, 6);
        input.Height = 36;
        input.VerticalContentAlignment = VerticalAlignment.Center;
        var border = new FrameworkElementFactory(typeof(Border), "InputFrame");
        border.SetValue(Border.CornerRadiusProperty, new CornerRadius(7));
        border.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Control.BackgroundProperty));
        border.SetValue(Border.BorderBrushProperty, new TemplateBindingExtension(Control.BorderBrushProperty));
        border.SetValue(Border.BorderThicknessProperty, new TemplateBindingExtension(Control.BorderThicknessProperty));
        border.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Control.PaddingProperty));
        var host = new FrameworkElementFactory(typeof(ScrollViewer), "PART_ContentHost"); border.AppendChild(host);
        var template = new ControlTemplate(typeof(TextBox)) { VisualTree = border };
        var focus = new Trigger { Property = UIElement.IsKeyboardFocusWithinProperty, Value = true };
        focus.Setters.Add(new Setter(Border.BorderThicknessProperty, new Thickness(2), "InputFrame")); template.Triggers.Add(focus);
        input.Template = template;
    }
}
