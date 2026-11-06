#!/bin/bash
# PWN Binary Auto-Detector
# Runs at session start to detect ELF binaries and run checksec
# Part of pwn-htb plugin

set -euo pipefail

# Read input (not used but consume it)
cat > /dev/null

# Find ELF binaries in current directory (not recursive, avoid system files)
binaries=()
while IFS= read -r -d '' file; do
    # Check if it's an ELF file
    if file "$file" 2>/dev/null | grep -q "ELF"; then
        binaries+=("$file")
    fi
done < <(find . -maxdepth 1 -type f -executable -print0 2>/dev/null || true)

# Also check common CTF binary names even if not executable
for name in vuln challenge pwn binary target main; do
    if [ -f "./$name" ] && file "./$name" 2>/dev/null | grep -q "ELF"; then
        # Add if not already in list
        if [[ ! " ${binaries[*]:-} " =~ " ./$name " ]]; then
            binaries+=("./$name")
        fi
    fi
done

# If no binaries found, exit silently
if [ ${#binaries[@]} -eq 0 ]; then
    exit 0
fi

# Build output message
output="## PWN Session Initialized\n\n"
output+="**Detected ELF binaries in current directory:**\n\n"

for binary in "${binaries[@]}"; do
    output+="### $(basename "$binary")\n"

    # Get file info
    file_info=$(file "$binary" 2>/dev/null | cut -d: -f2 | xargs)
    output+="\`\`\`\n$file_info\n\`\`\`\n"

    # Run checksec if available
    if command -v checksec &>/dev/null; then
        checksec_output=$(checksec --file="$binary" 2>/dev/null || echo "checksec failed")
        output+="\n**Protections:**\n\`\`\`\n$checksec_output\n\`\`\`\n"
    elif python3 -c "from pwn import *" &>/dev/null; then
        # Fallback to pwntools checksec
        checksec_output=$(python3 -c "from pwn import *; print(ELF('$binary', checksec=False).checksec())" 2>/dev/null || echo "pwntools checksec failed")
        output+="\n**Protections:**\n\`\`\`\n$checksec_output\n\`\`\`\n"
    fi

    output+="\n"
done

output+="**Suggested next steps:**\n"
output+="- Run \`/pwn <binary>\` for full analysis\n"
output+="- Run \`/pwn-recon <binary>\` for reconnaissance only\n"

# Output as system message for Claude
echo -e "{\"systemMessage\": \"$output\"}"
