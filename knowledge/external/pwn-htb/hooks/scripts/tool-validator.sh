#!/bin/bash
# PWN Tool Validator
# PreToolUse hook to check if required tools exist before running pwn commands
# Part of pwn-htb plugin

set -euo pipefail

# Read hook input
input=$(cat)

# Extract the command being run
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Skip if not a pwn-related command
# Only validate when using specific pwn tools
if [[ -z "$command" ]]; then
    echo '{"continue": true}'
    exit 0
fi

# Check for pwn-specific tool usage
missing_tools=()

# Check if command uses checksec
if echo "$command" | grep -qE '\bchecksec\b'; then
    if ! command -v checksec &>/dev/null; then
        # Check if pwntools has checksec
        if ! python3 -c "from pwn import *" &>/dev/null; then
            missing_tools+=("checksec (install via: apt install checksec OR pip install pwntools)")
        fi
    fi
fi

# Check if command uses ROPgadget
if echo "$command" | grep -qiE '\bROPgadget\b'; then
    if ! python3 -c "import ROPGadget" &>/dev/null; then
        missing_tools+=("ROPgadget (install via: pip install ROPgadget)")
    fi
fi

# Check if command uses ropper
if echo "$command" | grep -qiE '\bropper\b'; then
    if ! python3 -c "import ropper" &>/dev/null; then
        missing_tools+=("ropper (install via: pip install ropper)")
    fi
fi

# Check if command uses one_gadget
if echo "$command" | grep -qiE '\bone_gadget\b'; then
    if ! command -v one_gadget &>/dev/null; then
        missing_tools+=("one_gadget (install via: gem install one_gadget)")
    fi
fi

# Check if command uses seccomp-tools
if echo "$command" | grep -qiE '\bseccomp-tools\b'; then
    if ! command -v seccomp-tools &>/dev/null; then
        missing_tools+=("seccomp-tools (install via: gem install seccomp-tools)")
    fi
fi

# Check if command uses gdb
if echo "$command" | grep -qE '\bgdb\b'; then
    if ! command -v gdb &>/dev/null; then
        missing_tools+=("gdb (install via: apt install gdb)")
    fi
fi

# Check if command uses radare2/r2
if echo "$command" | grep -qE '\br2\b|\bradare2\b'; then
    if ! command -v r2 &>/dev/null; then
        missing_tools+=("radare2 (install via: apt install radare2)")
    fi
fi

# Check if command uses pwntools
if echo "$command" | grep -qE 'from pwn import|import pwn'; then
    if ! python3 -c "from pwn import *" &>/dev/null; then
        missing_tools+=("pwntools (install via: pip install pwntools)")
    fi
fi

# If missing tools, provide helpful message
if [ ${#missing_tools[@]} -gt 0 ]; then
    message="**Missing PWN tools detected:**\n\n"
    for tool in "${missing_tools[@]}"; do
        message+="- $tool\n"
    done
    message+="\nRun \`/pwn-setup --install\` to install missing Python packages."

    # Allow execution but warn
    echo "{\"continue\": true, \"systemMessage\": \"$message\"}"
else
    echo '{"continue": true}'
fi

exit 0
