using System.Globalization;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Media;
using System.Xml.Linq;

namespace EwP.Setup;

static class Branding
{
    public static ImageSource Svg(string name)
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name)!; var xml = XDocument.Load(stream); var svg = xml.Root!; var values = svg.Attribute("viewBox")!.Value.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray(); var bounds = new Rect(values[0], values[1], values[2], values[3]);
        var styles = new System.Collections.Generic.Dictionary<string, string>(); foreach (var element in svg.Descendants().Where(e => e.Name.LocalName == "style")) foreach (Match m in Regex.Matches(element.Value, @"\.(cls-\d+)\s*\{([^}]+)\}")) styles[m.Groups[1].Value] = m.Groups[2].Value;
        var group = new DrawingGroup() { ClipGeometry = new RectangleGeometry(bounds) }; group.Children.Add(new GeometryDrawing(Brushes.Transparent, null, new RectangleGeometry(bounds)));
        foreach (var element in svg.Descendants().Where(e => e.Name.LocalName is "path" or "circle" or "rect"))
        {
            if (element.Ancestors().Any(e => e.Name.LocalName == "defs")) continue;
            string css = element.Attribute("class") is XAttribute c && styles.TryGetValue(c.Value, out string? v) ? v : "";
            string Value(string key, string fallback) { var attr = element.Attribute(key); if (attr != null) return attr.Value; string found = Regex.Match(css, Regex.Escape(key) + @"\s*:\s*([^;]+)").Groups[1].Value.Trim(); return found.Length > 0 ? found : fallback; }
            double Number(string key) => double.Parse(element.Attribute(key)?.Value ?? "0", CultureInfo.InvariantCulture);
            Geometry? geometry = element.Name.LocalName switch { "path" => Geometry.Parse(element.Attribute("d")!.Value).Clone(), "circle" => new EllipseGeometry(new Point(Number("cx"), Number("cy")), Number("r"), Number("r")), "rect" => new RectangleGeometry(new Rect(Number("x"), Number("y"), Number("width"), Number("height")), Number("rx"), Number("ry") == 0 ? Number("rx") : Number("ry")), _ => null };
            if (geometry == null) continue; if (geometry is StreamGeometry shape) shape.FillRule = FillRule.Nonzero; string fill = Value("fill", "#356A80"), stroke = Value("stroke", "none"); Brush? BrushFor(string x) => x == "none" ? null : (Brush)new BrushConverter().ConvertFromInvariantString(x)!;
            var pen = stroke == "none" ? null : new Pen(BrushFor(stroke), double.Parse(Value("stroke-width", "1").Replace("px", ""), CultureInfo.InvariantCulture)); var drawing = new DrawingGroup() { Opacity = double.Parse(Value("opacity", "1"), CultureInfo.InvariantCulture) }; drawing.Children.Add(new GeometryDrawing(BrushFor(fill), pen, geometry));
            // The framed favicon nests the original vector in a centered SVG viewport.
            foreach (var viewport in element.Ancestors().Where(e => e != svg && e.Name.LocalName == "svg"))
            {
                var box = viewport.Attribute("viewBox")!.Value.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray();
                double N(string key) => double.Parse(viewport.Attribute(key)?.Value ?? "0", CultureInfo.InvariantCulture);
                double scale = Math.Min(N("width") / box[2], N("height") / box[3]);
                var wrapper = new DrawingGroup(); wrapper.Children.Add(drawing);
                wrapper.Transform = new MatrixTransform(scale, 0, 0, scale, N("x") + (N("width") - box[2] * scale) / 2 - box[0] * scale, N("y") + (N("height") - box[3] * scale) / 2 - box[1] * scale);
                drawing = wrapper;
            }
            group.Children.Add(drawing);
        }
        return new DrawingImage(group);
    }
}
