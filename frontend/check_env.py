import os

output_path = "env_check_result.txt"
with open(output_path, "w", encoding="utf-8") as out:
    paths = [
        ".env",
        "ai_receptionist/.env"
    ]

    for p in paths:
        if os.path.exists(p):
            out.write(f"File {p} exists.\n")
            with open(p, 'r') as f:
                content = f.read()
                if "OPENAI_API_KEY" in content:
                    out.write(f"  Found OPENAI_API_KEY in {p}\n")
                    for line in content.splitlines():
                        if line.startswith("OPENAI_API_KEY"):
                            parts = line.split("=", 1)
                            if len(parts) > 1:
                                key_val = parts[1].strip()
                                out.write(f"  Key length: {len(key_val)}\n")
                                out.write(f"  Starts with quote: {key_val.startswith(chr(34)) or key_val.startswith(chr(39))}\n")
                                out.write(f"  Ends with quote: {key_val.endswith(chr(34)) or key_val.endswith(chr(39))}\n")
                                out.write(f"  First 5 chars: {key_val[:5]}\n")
                                out.write(f"  Last 5 chars: {key_val[-5:]}\n")
                else:
                    out.write(f"  OPENAI_API_KEY NOT found in {p}\n")
        else:
            out.write(f"File {p} does NOT exist.\n")

print(f"Written to {output_path}")
