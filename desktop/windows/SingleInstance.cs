using System.IO;
using System.IO.Pipes;

namespace EwP.Desktop;

sealed class SingleInstance : IDisposable
{
    readonly Mutex mutex;
    readonly string pipeName;
    readonly CancellationTokenSource stop = new();
    public bool Owned { get; }
    public SingleInstance(string key)
    {
        pipeName = "EwP.Desktop." + key;
        mutex = new Mutex(false, @"Local\" + pipeName);
        try { Owned = mutex.WaitOne(0); } catch (AbandonedMutexException) { Owned = true; }
    }
    public async Task ActivateExisting()
    {
        using var pipe = new NamedPipeClientStream(".", pipeName, PipeDirection.InOut, PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        await pipe.ConnectAsync(10000);
        using var writer = new StreamWriter(pipe, leaveOpen: true) { AutoFlush = true };
        using var reader = new StreamReader(pipe, leaveOpen: true);
        await writer.WriteLineAsync("activate");
        if (await reader.ReadLineAsync().WaitAsync(TimeSpan.FromSeconds(3)) != "ok") throw new IOException("Application activation failed");
    }
    public void Listen(Action activate) => _ = Task.Run(async () =>
    {
        while (!stop.IsCancellationRequested)
        {
            try
            {
                using var pipe = new NamedPipeServerStream(pipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
                await pipe.WaitForConnectionAsync(stop.Token);
                using var reader = new StreamReader(pipe, leaveOpen: true);
                using var writer = new StreamWriter(pipe, leaveOpen: true) { AutoFlush = true };
                string? message = await reader.ReadLineAsync().WaitAsync(TimeSpan.FromSeconds(3), stop.Token);
                if (message == "activate") { activate(); await writer.WriteLineAsync("ok"); }
            }
            catch (Exception e) when (e is IOException or OperationCanceledException or TimeoutException) { }
        }
    });
    public void Dispose() { stop.Cancel(); if (Owned) mutex.ReleaseMutex(); mutex.Dispose(); stop.Dispose(); }
}
