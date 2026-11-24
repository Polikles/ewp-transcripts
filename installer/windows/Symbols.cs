using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Automation;
using System.Windows.Input;

namespace EwP.Setup;

static class Symbols
{
    public static Image Info()
    {
        var drawing = new DrawingGroup();
        var ink = (Brush)new BrushConverter().ConvertFromInvariantString("#355880")!;
        drawing.Children.Add(new GeometryDrawing(null, new Pen(ink, 1.5), new EllipseGeometry(new Point(10, 10), 8, 8)));
        drawing.Children.Add(new GeometryDrawing(ink, null, new EllipseGeometry(new Point(10, 6), .9, .9)));
        drawing.Children.Add(new GeometryDrawing(null, new Pen(ink, 1.7), new LineGeometry(new Point(10, 9), new Point(10, 14))));
        drawing.Freeze();
        return new Image { Source = new DrawingImage(drawing), Width = 22, Height = 22, Stretch = Stretch.Uniform };
    }

    public static Image Warning()
    {
        var ink = (Brush)new BrushConverter().ConvertFromInvariantString("#986511")!;
        var drawing = new DrawingGroup();
        drawing.Children.Add(new GeometryDrawing(null, new Pen(ink, 1.5), Geometry.Parse("M10,2 L19,18 L1,18 Z")));
        drawing.Children.Add(new GeometryDrawing(null, new Pen(ink, 1.7), new LineGeometry(new Point(10, 7), new Point(10, 12))));
        drawing.Children.Add(new GeometryDrawing(ink, null, new EllipseGeometry(new Point(10, 15), .9, .9)));
        drawing.Freeze();
        return new Image { Source = new DrawingImage(drawing), Width = 18, Height = 18 };
    }

    public static Button InfoButton(string name, Action callback)
    {
        var button = new Button
        {
            Content = Info(),
            Padding = new Thickness(4),
            Background = Brushes.Transparent,
            BorderThickness = new Thickness(0),
            Width = 34,
            Height = 34,
            VerticalAlignment = VerticalAlignment.Center,
            Margin = new Thickness(0, 0, 8, 0),
            ToolTip = name
        };
        button.Cursor = Cursors.Hand;
        ToolTipService.SetInitialShowDelay(button, 200);
        ToolTipService.SetShowDuration(button, 6000);
        var border = new FrameworkElementFactory(typeof(Border), "InfoFrame"); border.SetValue(Border.CornerRadiusProperty, new CornerRadius(17)); border.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Control.BackgroundProperty));
        var content = new FrameworkElementFactory(typeof(ContentPresenter)); content.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center); content.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); border.AppendChild(content);
        var template = new ControlTemplate(typeof(Button)) { VisualTree = border };
        var hover = new Trigger { Property = UIElement.IsMouseOverProperty, Value = true }; hover.Setters.Add(new Setter(Border.BackgroundProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#DDEAF5")!, "InfoFrame")); template.Triggers.Add(hover);
        var focus = new Trigger { Property = UIElement.IsKeyboardFocusedProperty, Value = true }; focus.Setters.Add(new Setter(Border.BackgroundProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#C5DDF0")!, "InfoFrame")); template.Triggers.Add(focus);
        button.Template = template;
        AutomationProperties.SetName(button, name); button.Click += (_, _) => callback();
        return button;
    }

    public static RadioButton ActionChoice(string title, string code, bool selected, Action choose)
    {
        var button = new RadioButton
        {
            Content = title,
            Tag = code,
            GroupName = "Operation",
            IsChecked = selected,
            FontSize = 15,
            Padding = new Thickness(14, 10, 14, 10),
            MinHeight = 46,
            HorizontalContentAlignment = HorizontalAlignment.Stretch,
            VerticalContentAlignment = VerticalAlignment.Center,
            Margin = new Thickness(0, 0, 0, 8),
            Foreground = Wizard.Ink,
            Background = Brushes.White,
            BorderBrush = (Brush)new BrushConverter().ConvertFromInvariantString("#D5DFE6")!,
            BorderThickness = new Thickness(1)
        };
        var border = new FrameworkElementFactory(typeof(Border), "ChoiceFrame");
        border.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Control.BackgroundProperty));
        border.SetValue(Border.BorderBrushProperty, new TemplateBindingExtension(Control.BorderBrushProperty));
        border.SetValue(Border.BorderThicknessProperty, new TemplateBindingExtension(Control.BorderThicknessProperty));
        border.SetValue(Border.CornerRadiusProperty, new CornerRadius(9)); border.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Control.PaddingProperty));
        var dock = new FrameworkElementFactory(typeof(DockPanel)); dock.SetValue(DockPanel.LastChildFillProperty, true);
        var glyph = new FrameworkElementFactory(typeof(Grid), "RadioGlyph"); glyph.SetValue(FrameworkElement.WidthProperty, 18.0); glyph.SetValue(FrameworkElement.HeightProperty, 18.0); glyph.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); glyph.SetValue(FrameworkElement.MarginProperty, new Thickness(0, 0, 12, 0));
        var ring = new FrameworkElementFactory(typeof(Ellipse)); ring.SetValue(Shape.StrokeProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#7C8E9E")!); ring.SetValue(Shape.StrokeThicknessProperty, 1.5); glyph.AppendChild(ring);
        var dot = new FrameworkElementFactory(typeof(Ellipse), "RadioDot"); dot.SetValue(FrameworkElement.WidthProperty, 8.0); dot.SetValue(FrameworkElement.HeightProperty, 8.0); dot.SetValue(Shape.FillProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#355880")!); dot.SetValue(UIElement.VisibilityProperty, Visibility.Hidden); glyph.AppendChild(dot); dock.AppendChild(glyph);
        var content = new FrameworkElementFactory(typeof(ContentPresenter), "RadioText"); content.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center); content.SetValue(ContentPresenter.RecognizesAccessKeyProperty, true); dock.AppendChild(content); border.AppendChild(dock);
        var template = new ControlTemplate(typeof(RadioButton)) { VisualTree = border };
        var checkedState = new Trigger { Property = System.Windows.Controls.Primitives.ToggleButton.IsCheckedProperty, Value = true };
        checkedState.Setters.Add(new Setter(UIElement.VisibilityProperty, Visibility.Visible, "RadioDot")); checkedState.Setters.Add(new Setter(Control.BackgroundProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#EDF4FA")!)); checkedState.Setters.Add(new Setter(Control.BorderBrushProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#355880")!)); template.Triggers.Add(checkedState);
        var focus = new Trigger { Property = UIElement.IsKeyboardFocusedProperty, Value = true }; focus.Setters.Add(new Setter(Border.BorderThicknessProperty, new Thickness(2), "ChoiceFrame")); template.Triggers.Add(focus);
        var hover = new Trigger { Property = UIElement.IsMouseOverProperty, Value = true }; hover.Setters.Add(new Setter(Control.BackgroundProperty, (Brush)new BrushConverter().ConvertFromInvariantString("#E8F0F7")!)); template.Triggers.Add(hover);
        button.Template = template; button.Checked += (_, _) => choose(); return button;
    }
}
