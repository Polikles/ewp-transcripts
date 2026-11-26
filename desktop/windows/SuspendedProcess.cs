using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace EwP.Desktop;

static class SuspendedProcess
{
    // Assign before Python's venv redirector can create the real interpreter or any workers.
    public static Process Start(ProcessStartInfo start, SafeFileHandle job, Action<string?> capture)
    {
        var output = new AnonymousPipeServerStream(PipeDirection.In, HandleInheritability.Inheritable);
        var error = new AnonymousPipeServerStream(PipeDirection.In, HandleInheritability.Inheritable);
        using var input = new AnonymousPipeServerStream(PipeDirection.Out, HandleInheritability.Inheritable);
        var startup = new StartupInfo { Size = Marshal.SizeOf<StartupInfo>(), Flags = 0x100,
            Input = input.ClientSafePipeHandle.DangerousGetHandle(), Output = output.ClientSafePipeHandle.DangerousGetHandle(), Error = error.ClientSafePipeHandle.DangerousGetHandle() };
        var command = new StringBuilder(Quote(start.FileName) + " " + string.Join(" ", start.ArgumentList.Select(Quote)));
        var environment = Marshal.StringToHGlobalUni(string.Join("\0", start.Environment.OrderBy(item => item.Key, StringComparer.OrdinalIgnoreCase).Select(item => item.Key + "=" + item.Value)) + "\0\0");
        ProcessInfo information = default;
        bool resumed = false;
        try
        {
            if (!CreateProcess(start.FileName, command, IntPtr.Zero, IntPtr.Zero, true, 0x08000404, environment, start.WorkingDirectory, ref startup, out information)) throw new Win32Exception();
            if (!AssignProcessToJobObject(job, information.Process)) throw new Win32Exception();
            var process = Process.GetProcessById(information.Pid);
            _ = process.Handle;
            output.DisposeLocalCopyOfClientHandle(); error.DisposeLocalCopyOfClientHandle(); input.DisposeLocalCopyOfClientHandle();
            if (ResumeThread(information.Thread) == uint.MaxValue) { process.Dispose(); throw new Win32Exception(); }
            resumed = true;
            Drain(output, capture); Drain(error, capture);
            return process;
        }
        finally
        {
            Marshal.FreeHGlobal(environment);
            if (information.Process != IntPtr.Zero)
            {
                if (!resumed) TerminateProcess(information.Process, 2);
                CloseHandle(information.Process); CloseHandle(information.Thread);
            }
            if (!resumed) { output.Dispose(); error.Dispose(); }
        }
    }
    static void Drain(Stream pipe, Action<string?> capture) => _ = Task.Run(async () =>
    {
        using var reader = new StreamReader(pipe, Encoding.UTF8);
        try { while (await reader.ReadLineAsync() is string line) capture(line); }
        catch (IOException) { }
    });
    internal static string Quote(string value)
    {
        var result = new StringBuilder("\""); int slashes = 0;
        foreach (char character in value)
        {
            if (character == '\\') { slashes++; continue; }
            result.Append('\\', character == '"' ? slashes * 2 + 1 : slashes); slashes = 0; result.Append(character);
        }
        return result.Append('\\', slashes * 2).Append('"').ToString();
    }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct StartupInfo
    {
        public int Size; public string? Reserved, Desktop, Title;
        public uint X, Y, XSize, YSize, XChars, YChars, Fill, Flags;
        public ushort Show, ReservedSize; public IntPtr ReservedBytes, Input, Output, Error;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInfo { public IntPtr Process, Thread; public int Pid, Tid; }
    [DllImport("kernel32.dll", EntryPoint = "CreateProcessW", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool CreateProcess(string application, StringBuilder command, IntPtr processAttributes, IntPtr threadAttributes, bool inherit, uint flags, IntPtr environment, string directory, ref StartupInfo startup, out ProcessInfo process);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool AssignProcessToJobObject(SafeFileHandle job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr process, uint code);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
}
