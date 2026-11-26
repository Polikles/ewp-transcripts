using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Win32.SafeHandles;

namespace EwP.Desktop;

sealed class OwnedBackend : IDisposable
{
    public Process? Process { get; private set; }
    readonly HttpClient client = new(new HttpClientHandler { AllowAutoRedirect = false, UseProxy = false }) { Timeout = TimeSpan.FromSeconds(3) };
    readonly SafeFileHandle job;
    readonly string token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
    readonly Queue<string> errors = new();
    public string Diagnostic { get { lock (errors) return string.Join(Environment.NewLine, errors); } }
    void Capture(string? value) { if (value == null) return; string safe = value.Replace(token, "[private]"); lock (errors) { errors.Enqueue(safe[..Math.Min(safe.Length, 4096)]); while (errors.Count > 40) errors.Dequeue(); } }
    public OwnedBackend()
    {
        job = new SafeFileHandle(CreateJobObject(IntPtr.Zero, null), true);
        if (job.IsInvalid) throw new System.ComponentModel.Win32Exception();
        var limits = new JobLimits { Basic = new BasicLimits { Flags = 0x2000 } };
        int size = Marshal.SizeOf<JobLimits>(); var pointer = Marshal.AllocHGlobal(size);
        try { Marshal.StructureToPtr(limits, pointer, false); if (!SetInformationJobObject(job, 9, pointer, (uint)size)) throw new System.ComponentModel.Win32Exception(); }
        finally { Marshal.FreeHGlobal(pointer); }
    }
    public void Start(AppConfig config)
    {
        var start = new ProcessStartInfo(config.Python) { WorkingDirectory = config.WorkingDirectory, UseShellExecute = false, CreateNoWindow = true, RedirectStandardError = true, RedirectStandardOutput = true };
        foreach (string value in new[] { Path.Combine(config.Root, "manager.py"), "launch", "--root", config.Root, "--native-session" }) start.ArgumentList.Add(value);
        start.Environment["EWP_NATIVE_TOKEN"] = token;
        start.Environment["EWP_DESKTOP_HOST_PID"] = Environment.ProcessId.ToString();
        start.Environment["EWP_DESKTOP_HOST_IDENTITY"] = System.Diagnostics.Process.GetCurrentProcess().StartTime.ToFileTimeUtc().ToString();
        start.Environment["PYTHONIOENCODING"] = "utf-8";
        Process = SuspendedProcess.Start(start, job, Capture);
    }
    public async Task<JsonElement?> Request(string? close = null)
    {
        using var request = new HttpRequestMessage(close == null ? HttpMethod.Get : HttpMethod.Post, AppConfig.Origin + "/api/v1/runtime-control" + (close is "commit" or "refuse" ? "?close=" + close : ""));
        request.Headers.Add("X-EWP-Runtime-Token", token); request.Headers.Add("Origin", AppConfig.Origin);
        if (close != null) request.Content = new StringContent("", Encoding.UTF8);
        try
        {
            using var response = await client.SendAsync(request);
            if (!response.IsSuccessStatusCode) return null;
            using var json = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
            return json.RootElement.Clone();
        }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException or JsonException) { return null; }
    }
    public void Dispose() { client.Dispose(); job.Dispose(); Process?.Dispose(); }
    [StructLayout(LayoutKind.Sequential)] struct BasicLimits { public long ProcessTime, JobTime; public uint Flags; public UIntPtr MinWorkingSet, MaxWorkingSet; public uint ActiveProcessLimit; public UIntPtr Affinity; public uint PriorityClass, SchedulingClass; }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters { public ulong ReadOperations, WriteOperations, OtherOperations, ReadBytes, WriteBytes, OtherBytes; }
    [StructLayout(LayoutKind.Sequential)] struct JobLimits { public BasicLimits Basic; public IoCounters Io; public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory; }
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr CreateJobObject(IntPtr attributes, string? name);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetInformationJobObject(SafeFileHandle job, int type, IntPtr value, uint length);
}
