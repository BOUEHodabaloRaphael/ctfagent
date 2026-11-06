# GDB Scripting for Exploitation

Automate debugging with GDB scripts and Python.

## Basic GDB Commands File

Create `.gdbinit` or pass with `-x script.gdb`:

```gdb
# script.gdb
set disable-randomization on
file ./binary

# Set breakpoints
b main
b *0x401234

# Commands to run at breakpoint
commands 1
    silent
    printf "RBP: %p\n", $rbp
    continue
end

# Run
run
```

## GDB Python Scripting

### Basic Script
```python
# script.py - run with: gdb -x script.py ./binary

import gdb

# Execute GDB command
gdb.execute("b main")
gdb.execute("run")

# Read register using gdb.parse_and_eval
rsp = int(gdb.parse_and_eval("$rsp"))
print(f"RSP: {hex(rsp)}")

# Read memory
inferior = gdb.selected_inferior()
data = inferior.read_memory(rsp, 8)
print(f"Stack top: {data.hex()}")
```

### Custom Command
```python
class LeakCanary(gdb.Command):
    """Leak the stack canary value."""

    def __init__(self):
        super().__init__("leak-canary", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        # Canary typically at fs:0x28
        try:
            canary = gdb.parse_and_eval("*(long*)($fs_base + 0x28)")
            print(f"Canary: {hex(int(canary))}")
        except:
            # Alternative: find on stack
            rbp = int(gdb.parse_and_eval("$rbp"))
            canary_addr = rbp - 8
            canary = int(gdb.parse_and_eval(f"*(long*)({canary_addr})"))
            print(f"Canary (from stack): {hex(canary)}")

LeakCanary()
```

### Breakpoint with Python Action
```python
class BreakpointHandler(gdb.Breakpoint):
    def __init__(self, spec):
        super().__init__(spec)

    def stop(self):
        # Called when breakpoint hit
        rdi = int(gdb.parse_and_eval("$rdi"))
        print(f"Arg 1 (rdi): {hex(rdi)}")

        # Return False to continue, True to stop
        return False

# Set breakpoint on vulnerable function
BreakpointHandler("*vuln")
```

## Automation Scripts

### Auto-find Offset Script
```python
# find_offset.py
import gdb
import subprocess

def find_offset():
    # Generate cyclic pattern
    pattern = subprocess.check_output(
        ["python3", "-c", "from pwn import *; print(cyclic(200).decode())"]
    ).strip()

    # Set up inferior
    gdb.execute("file ./binary")
    gdb.execute("run <<< " + pattern.decode())

    # Get crash address
    try:
        rsp_val = gdb.parse_and_eval("*(long*)$rsp")
        # Find offset
        result = subprocess.check_output([
            "python3", "-c",
            f"from pwn import *; print(cyclic_find({int(rsp_val)}))"
        ])
        print(f"Offset: {result.decode().strip()}")
    except Exception as e:
        print(f"Error: {e}")

find_offset()
```

### Heap State Logger
```python
# heap_logger.py
import gdb

class HeapLogger(gdb.Breakpoint):
    def __init__(self, spec, name):
        super().__init__(spec)
        self.name = name
        self.count = 0

    def stop(self):
        self.count += 1
        print(f"\n[{self.count}] {self.name} called")

        # Log arguments
        if "malloc" in self.name:
            size = int(gdb.parse_and_eval("$rdi"))
            print(f"  Size: {hex(size)}")
        elif "free" in self.name:
            ptr = int(gdb.parse_and_eval("$rdi"))
            print(f"  Ptr: {hex(ptr)}")

        return False  # Continue execution

# Set up logging
HeapLogger("*malloc", "malloc")
HeapLogger("*free", "free")
```

### Memory Dump on Crash
```python
# dump_on_crash.py
import gdb

def dump_context():
    """Dump useful info after crash."""
    print("\n=== CRASH CONTEXT ===")

    # Registers
    for reg in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rsp', 'rbp', 'rip']:
        try:
            val = int(gdb.parse_and_eval(f"${reg}"))
            print(f"{reg.upper()}: {hex(val)}")
        except:
            pass

    # Stack
    print("\n=== STACK ===")
    try:
        rsp = int(gdb.parse_and_eval("$rsp"))
        gdb.execute(f"x/16gx {rsp}")
    except:
        pass

def handle_stop(event):
    if isinstance(event, gdb.SignalEvent):
        if event.stop_signal in ['SIGSEGV', 'SIGBUS', 'SIGABRT']:
            dump_context()

gdb.events.stop.connect(handle_stop)
```

## pwntools GDB Integration

### Debug with Script
```python
from pwn import *

context.binary = './binary'

# Debug with GDB script
io = gdb.debug('./binary', '''
    b main
    b *0x401234
    commands 2
        info registers
    end
    c
''')

io.sendline(b'payload')
io.interactive()
```

### Attach to Process
```python
from pwn import *

# Start process
io = process('./binary')

# Attach GDB
gdb.attach(io, '''
    b *0x401234
    c
''')

# Continue exploit
io.sendline(b'payload')
io.interactive()
```

## Tips

1. Use `set pagination off` for scripting
2. `set logging on` to save output
3. Test scripts interactively first
4. Use `gdb.execute("cmd", to_string=True)` to capture output
5. Handle exceptions - GDB can be finicky
