"""Map imported APIs and telltale strings to behavioural capabilities (capa-style, lightweight).

Every output is an *indicator*: single APIs are ubiquitous in benign software, so severity only
rises when several independent signals agree. ATT&CK ids are hints for analysts, not conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Cap:
    id: str
    title: str
    attack: tuple[str, ...]
    apis: frozenset[str]
    combos: tuple[frozenset[str], ...] = ()      # any fully-present combo => strong
    base: str = "info"                            # severity when only weak evidence
    strong: str = "medium"                        # severity when a combo is present


def _s(*names: str) -> frozenset[str]:
    return frozenset(n.lower() for n in names)


CAPS: tuple[Cap, ...] = (
    Cap("inject", "Process injection primitives", ("T1055",),
        _s("VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "CreateRemoteThreadEx", "NtCreateThreadEx",
           "QueueUserAPC", "NtQueueApcThread", "SetThreadContext", "NtMapViewOfSection", "NtUnmapViewOfSection",
           "RtlCreateUserThread", "NtWriteVirtualMemory", "NtAllocateVirtualMemory", "ResumeThread", "OpenProcess"),
        (_s("VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread"), _s("VirtualAllocEx", "WriteProcessMemory", "NtCreateThreadEx"),
         _s("VirtualAllocEx", "WriteProcessMemory", "QueueUserAPC"), _s("WriteProcessMemory", "SetThreadContext", "ResumeThread"),
         _s("NtUnmapViewOfSection", "WriteProcessMemory", "SetThreadContext")), "low", "high"),
    Cap("antidebug", "Debugger detection / evasion", ("T1622",),
        _s("IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess", "NtSetInformationThread",
           "OutputDebugString", "DebugActiveProcess", "ptrace", "NtQuerySystemInformation"),
        (_s("IsDebuggerPresent", "CheckRemoteDebuggerPresent"), _s("NtQueryInformationProcess", "NtSetInformationThread")), "info", "medium"),
    Cap("service", "Windows service creation", ("T1543.003",),
        _s("CreateService", "OpenSCManager", "StartService", "ChangeServiceConfig", "StartServiceCtrlDispatcher"),
        (_s("OpenSCManager", "CreateService"),), "info", "medium"),
    Cap("registry", "Registry modification", ("T1112",),
        _s("RegSetValueEx", "RegCreateKeyEx", "RegDeleteValue", "RegSetKeyValue", "RegOpenKeyEx", "NtSetValueKey"),
        (_s("RegCreateKeyEx", "RegSetValueEx"),), "info", "low"),
    Cap("network", "Network communication", ("T1071",),
        _s("InternetOpen", "InternetOpenUrl", "InternetConnect", "InternetReadFile", "HttpOpenRequest", "HttpSendRequest",
           "WinHttpOpen", "WinHttpConnect", "WinHttpSendRequest", "WSAStartup", "WSASocket", "socket", "connect", "bind",
           "listen", "accept", "send", "recv", "sendto", "recvfrom", "gethostbyname", "getaddrinfo", "curl_easy_perform",
           "curl_easy_init", "DnsQuery", "URLDownloadToFile", "inet_addr", "inet_aton", "inet_pton", "select"),
        (_s("socket", "connect", "send", "recv"), _s("WSAStartup", "socket", "connect"), _s("InternetOpen", "InternetReadFile"),
         _s("WinHttpOpen", "WinHttpConnect")), "info", "low"),
    Cap("server", "Listening socket (bind/listen/accept)", ("T1571",), _s("bind", "listen", "accept"),
        (_s("socket", "bind", "listen", "accept"),), "info", "low"),
    Cap("download", "Download / ingress tool transfer", ("T1105",),
        _s("URLDownloadToFile", "URLDownloadToCacheFile", "InternetReadFile", "WinHttpReadData", "curl_easy_perform"),
        (_s("URLDownloadToFile", "WinExec"), _s("URLDownloadToFile", "ShellExecute"), _s("URLDownloadToFile", "CreateProcess"),
         _s("InternetReadFile", "WriteFile", "CreateProcess")), "info", "medium"),
    Cap("exec", "Process / command execution", ("T1106", "T1059"),
        _s("CreateProcess", "CreateProcessAsUser", "WinExec", "ShellExecute", "ShellExecuteEx", "system", "popen", "execve",
           "execv", "execl", "execlp", "execvp", "posix_spawn", "NtCreateUserProcess"),
        (), "info", "low"),
    Cap("crypto", "Cryptographic API usage", ("T1486", "T1027"),
        _s("CryptEncrypt", "CryptDecrypt", "CryptAcquireContext", "CryptGenKey", "CryptImportKey", "CryptCreateHash",
           "BCryptEncrypt", "BCryptDecrypt", "BCryptGenerateSymmetricKey", "BCryptOpenAlgorithmProvider", "EVP_EncryptInit_ex",
           "EVP_CIPHER_CTX_new", "AES_encrypt", "AES_set_encrypt_key", "RSA_public_encrypt", "gcry_cipher_open", "mbedtls_aes_crypt_cbc"),
        (), "info", "low"),
    Cap("fileenum", "File and directory enumeration", ("T1083",),
        _s("FindFirstFile", "FindNextFile", "FindFirstFileEx", "GetLogicalDrives", "GetLogicalDriveStrings", "GetDriveType",
           "opendir", "readdir", "scandir", "fts_open", "ftw", "nftw", "glob"), (), "info", "info"),
    Cap("keylog", "Keystroke / input capture", ("T1056.001",),
        _s("SetWindowsHookEx", "GetAsyncKeyState", "GetKeyState", "GetKeyboardState", "RegisterRawInputDevices", "GetForegroundWindow",
           "GetRawInputData", "MapVirtualKey"),
        (_s("SetWindowsHookEx", "GetAsyncKeyState"), _s("GetAsyncKeyState", "GetForegroundWindow"),
         _s("SetWindowsHookEx", "GetForegroundWindow")), "info", "medium"),
    Cap("screen", "Screen capture", ("T1113",),
        _s("BitBlt", "GetDC", "GetWindowDC", "GetDesktopWindow", "CreateCompatibleBitmap", "StretchBlt", "PrintWindow"),
        (_s("GetDC", "BitBlt", "CreateCompatibleBitmap"), _s("GetDesktopWindow", "BitBlt")), "info", "low"),
    Cap("clipboard", "Clipboard access", ("T1115",), _s("OpenClipboard", "GetClipboardData", "SetClipboardData", "AddClipboardFormatListener"),
        (_s("OpenClipboard", "GetClipboardData"),), "info", "low"),
    Cap("privilege", "Token / privilege manipulation", ("T1134",),
        _s("AdjustTokenPrivileges", "OpenProcessToken", "LookupPrivilegeValue", "DuplicateToken", "DuplicateTokenEx",
           "ImpersonateLoggedOnUser", "SetTokenInformation", "setuid", "setgid", "seteuid", "setresuid", "capset"),
        (_s("OpenProcessToken", "LookupPrivilegeValue", "AdjustTokenPrivileges"),), "info", "medium"),
    Cap("dynapi", "Dynamic API / library resolution", ("T1027.007",),
        _s("GetProcAddress", "LoadLibrary", "LoadLibraryEx", "LdrGetProcedureAddress", "LdrLoadDll", "dlopen", "dlsym"),
        (_s("GetProcAddress", "LoadLibrary"), _s("dlopen", "dlsym")), "info", "low"),
    Cap("memperm", "Memory permission changes (RWX staging)", ("T1027", "T1055"),
        _s("VirtualAlloc", "VirtualProtect", "VirtualProtectEx", "NtProtectVirtualMemory", "mprotect", "mmap"),
        (_s("VirtualAlloc", "VirtualProtect"),), "info", "low"),
    Cap("sysinfo", "System information discovery", ("T1082",),
        _s("GetComputerName", "GetUserName", "GetSystemInfo", "GetNativeSystemInfo", "GetVersionEx", "RtlGetVersion", "uname",
           "gethostname", "GetAdaptersInfo", "GetAdaptersAddresses", "sysinfo", "GlobalMemoryStatusEx", "GetSystemFirmwareTable"),
        (), "info", "info"),
    Cap("procenum", "Process discovery", ("T1057",),
        _s("CreateToolhelp32Snapshot", "Process32First", "Process32Next", "EnumProcesses", "NtQuerySystemInformation"),
        (_s("CreateToolhelp32Snapshot", "Process32First", "Process32Next"),), "info", "low"),
    Cap("credaccess", "Credential access primitives", ("T1003", "T1555"),
        _s("MiniDumpWriteDump", "CredEnumerate", "CryptUnprotectData", "LsaRetrievePrivateData", "SamConnect", "SamEnumerateUsersInDomain",
           "getspnam", "getpwnam", "crypt"),
        (_s("MiniDumpWriteDump", "OpenProcess"),), "info", "medium"),
    Cap("hook", "API hooking / patching of running code", ("T1056.004",),
        _s("SetWindowsHookEx", "VirtualProtect", "NtProtectVirtualMemory", "FlushInstructionCache"),
        (_s("VirtualProtect", "FlushInstructionCache"),), "info", "low"),
    Cap("selfdelete", "File deletion / self-removal", ("T1070.004",),
        _s("DeleteFile", "MoveFileEx", "unlink", "remove", "rmdir", "SHFileOperation"), (), "info", "info"),
    Cap("fork", "Process creation / daemonisation (Unix)", ("T1106",), _s("fork", "vfork", "daemon", "setsid", "clone"),
        (_s("fork", "setsid"), _s("daemon",)), "info", "info"),
)

# (marker lowercase, capability title, attack ids, severity, note)
STRING_RULES: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("currentversion\\run", "Run-key persistence", ("T1547.001",), "medium"),
    ("vssadmin delete shadows", "Shadow-copy deletion", ("T1490",), "high"),
    ("vssadmin.exe delete shadows", "Shadow-copy deletion", ("T1490",), "high"),
    ("wmic shadowcopy delete", "Shadow-copy deletion", ("T1490",), "high"),
    ("recoveryenabled no", "Boot recovery disabled (bcdedit)", ("T1490",), "high"),
    ("wevtutil cl", "Event-log clearing", ("T1070.001",), "high"),
    ("schtasks /create", "Scheduled task creation", ("T1053.005",), "medium"),
    ("-encodedcommand", "Encoded PowerShell command", ("T1059.001", "T1027"), "medium"),
    ("powershell -enc", "Encoded PowerShell command", ("T1059.001", "T1027"), "medium"),
    ("frombase64string", "Base64 decoding in script", ("T1140",), "low"),
    ("invoke-expression", "PowerShell dynamic evaluation", ("T1059.001",), "medium"),
    ("downloadstring", "PowerShell download cradle", ("T1105", "T1059.001"), "medium"),
    ("certutil -urlcache", "certutil used as downloader", ("T1105",), "medium"),
    ("certutil -decode", "certutil used as decoder", ("T1140",), "medium"),
    ("bitsadmin /transfer", "BITS job transfer", ("T1197",), "medium"),
    ("mshta ", "mshta proxy execution", ("T1218.005",), "medium"),
    ("regsvr32 /s", "regsvr32 proxy execution", ("T1218.010",), "medium"),
    ("set-mppreference", "Defender configuration change", ("T1562.001",), "medium"),
    ("disablerealtimemonitoring", "Defender real-time protection disabled", ("T1562.001",), "high"),
    ("sekurlsa", "Credential-dumping tool vocabulary (mimikatz-like)", ("T1003.001",), "high"),
    ("mimikatz", "Credential-dumping tool name", ("T1003.001",), "high"),
    ("/etc/ld.so.preload", "ld.so.preload reference", ("T1574.006",), "medium"),
    ("ld_preload", "LD_PRELOAD reference", ("T1574.006",), "low"),
    ("authorized_keys", "SSH authorized_keys reference", ("T1098.004",), "medium"),
    ("/etc/crontab", "cron persistence reference", ("T1053.003",), "low"),
    ("/etc/rc.local", "rc.local persistence reference", ("T1037.004",), "low"),
    ("/dev/tcp/", "bash /dev/tcp (reverse shell idiom)", ("T1059.004",), "high"),
    ("nc -e", "netcat -e shell", ("T1059.004",), "high"),
    ("mkfifo", "named pipe (shell relay idiom)", ("T1059.004",), "low"),
    ("/bin/busybox", "BusyBox invocation (IoT malware idiom)", ("T1059.004",), "low"),
    ("iptables -f", "Firewall flush", ("T1562.004",), "medium"),
    ("history -c", "Shell history clearing", ("T1070.003",), "medium"),
    ("your files have been encrypted", "Ransom-note wording", ("T1486",), "high"),
    ("all your files", "Ransom-note wording", ("T1486",), "low"),
    ("vboxservice", "VirtualBox artefact check", ("T1497.001",), "low"),
    ("vmwaretray", "VMware artefact check", ("T1497.001",), "low"),
    ("sbiedll", "Sandboxie artefact check", ("T1497.001",), "medium"),
    ("tracerpid", "/proc/self/status TracerPid (debugger check)", ("T1622",), "medium"),
)

SEV_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}


def _normalise(name: str) -> str:
    n = name.lower().lstrip("_")
    for pref in ("imp_", "imp__"):
        if n.startswith(pref):
            n = n[len(pref):]
    return n.split("@")[0]


def _variants(name: str) -> set[str]:
    n = _normalise(name)
    out = {n}
    if len(n) > 4 and n[-1] in "aw" and name[-1] in "AW":
        out.add(n[:-1])
    if n.endswith("ex") and len(n) > 4:
        out.add(n[:-2])
    if n.endswith(("exa", "exw")):
        out.add(n[:-3])
    return out


def analyze_capabilities(imports: Iterable[dict[str, Any]], strings: Iterable[str] = ()) -> list[dict[str, Any]]:
    names: dict[str, str] = {}
    for imp in imports:
        nm = imp.get("name")
        if nm:
            for v in _variants(nm):
                names.setdefault(v, nm)
    results: list[dict[str, Any]] = []
    for cap in CAPS:
        present = {a for a in cap.apis if a in names}
        if not present:
            continue
        strong = any(combo <= present for combo in cap.combos)
        count = len(present)
        if strong:
            sev, conf = cap.strong, "high" if count >= 3 else "medium"
        elif count >= 4:
            sev, conf = cap.base if cap.base != "info" else ("low" if cap.strong != "info" else "info"), "medium"
        else:
            sev, conf = cap.base, "low"
        results.append({"id": f"CAP-{cap.id.upper()}", "title": cap.title, "attack": list(cap.attack),
                        "severity": sev, "confidence": conf, "apis": sorted({names[a] for a in present}),
                        "combo": strong, "source": "imports"})
    blob = "\n".join(s.lower() for s in strings)
    seen: set[str] = set()
    for marker, title, attack, sev in STRING_RULES:
        if marker in blob and title not in seen:
            seen.add(title)
            results.append({"id": "STR-" + "".join(c for c in title.upper() if c.isalnum())[:24], "title": title,
                            "attack": list(attack), "severity": sev, "confidence": "medium" if sev != "low" else "low",
                            "apis": [], "markers": [marker], "combo": False, "source": "strings"})
    ids = {r["id"] for r in results}
    titles = {r["title"] for r in results}
    ransom_hints = {"Shadow-copy deletion", "Boot recovery disabled (bcdedit)", "Ransom-note wording"} & titles
    if "CAP-CRYPTO" in ids and "CAP-FILEENUM" in ids and ransom_hints:
        results.append({"id": "CMB-RANSOM", "title": "Ransomware-like combination", "attack": ["T1486", "T1490"],
                        "severity": "high", "confidence": "medium", "combo": True, "source": "combination",
                        "apis": [], "markers": sorted(ransom_hints),
                        "note": "crypto APIs + file enumeration + recovery-inhibiting or ransom-note strings"})
    return sorted(results, key=lambda r: (-SEV_ORDER[r["severity"]], r["id"]))
