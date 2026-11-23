using System.IO;
using System.Text;

namespace EwP.Setup;

static class Credits
{
    // Presentation only: preserve original attribution text/assets, unwrap editorial soft lines.
    internal static string Format(string source)
    {
        var paragraphs = source.Replace("\r\n", "\n").Split("\n\n", StringSplitOptions.RemoveEmptyEntries);
        var result = new List<string>();
        foreach (string raw in paragraphs)
        {
            var lines = raw.Split('\n', StringSplitOptions.RemoveEmptyEntries).Select(l => l.Trim()).ToList();
            if (lines.Count > 1 && lines[0].Contains('—'))
            {
                result.Add(lines[0]); result.Add(string.Join(" ", lines.Skip(1)));
            }
            else
            {
                string joined = string.Join(" ", lines);
                // The original first paragraph contains independent attribution topics.
                foreach (string marker in new[] { " Rights holder:", " English:", " Creator URL:", " See LICENSE-ASSETS", " Fonts:", " Icons:", " Assets copied" })
                    joined = joined.Replace(marker, "\n\n" + marker.TrimStart());
                joined = System.Text.RegularExpressions.Regex.Replace(joined, @"(?<=[.!?]) (?=[A-Z])", "\n");
                result.Add(joined);
            }
        }
        return string.Join("\n\n", result).Replace("\r\n", "\n").Replace("\n", "\r\n") + "\r\n";
    }

    internal static string Prepare(string original, string output)
    {
        File.WriteAllText(output, Format(File.ReadAllText(original)), new UTF8Encoding(true));
        return output;
    }
}
