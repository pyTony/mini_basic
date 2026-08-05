"""Restore animal.bbc CLS line: @%=0 padded to same length as @%=&90A (7 bytes)."""
from pathlib import Path
from mini_basic.bbc_detokenize import parse_russell_program, detect_bbc_binary_format

p = Path("examples/games/animal.bbc")
d = bytearray(p.read_bytes())

# Prefer a clean rebuild: if we can find @%=&90A or broken @%=0 variants
for needle in (b"@%=&90A", b"@%=&000", b"@%=0   ", b"@%=0  ", b"@%=0 "):
    i = d.find(needle)
    print("find", needle, i, "len", len(needle) if i >= 0 else None)

# Force-correct the CLS line by locating CLS token 0xDB and following ANIMAL
cls = d.find(bytes([0xDB]))
print("CLS token at", cls, d[cls : cls + 40])

# Find ANIMAL string after CLS
ani = d.find(b'"ANIMAL"')
print("ANIMAL at", ani)

# Expected body from CLS through ANIMAL CR:
# \xdb : @ % = 0 sp sp sp : \xfe sp 0 : \xf1 sp \x8a 15) "ANIMAL" \r
# Rebuild from known structure around CLS line number 0 record

# Locate record start: scan for length byte before CLS
# Record starts a few bytes before 0xDB: [len][ln][ln][body...]
# From earlier good dump: b' \x00\x00\xdb:@%=&90A:...' length=0x20 at position of space

# Search for pattern \x00\x00\xdb:
pat = d.find(b"\x00\x00\xdb:")
print("pat", pat, d[pat - 1 : pat + 35] if pat > 0 else None)

if pat > 0:
    # length byte is pat-1
    # Replace @% assignment with exactly 7 bytes
    start = pat + 3  # after \x00\x00\xdb — wait body starts at pat+2? 
    # d[pat]=0, d[pat+1]=0, d[pat+2]=0xdb, d[pat+3]=ord(':')
    # find @%=
    j = d.find(b"@%=", pat)
    # take until next ':'
    k = d.find(b":", j + 3)
    print("assign", d[j:k+1], "span", k - j)
    # replace j:k with @%=0 + spaces to keep same end k
    # We need the assignment part length preserved between @%= and trailing :
    # Original: @%=&90A (7 chars) then :
    # Want: @%=0 + 3 spaces = 7 then :
    new_assign = b"@%=0   "  # 7 bytes
    old_span = d[j:k]
    print("old_span", old_span, len(old_span))
    if len(old_span) != 7:
        # normalize: replace whatever is between j and k with 7-byte assign
        # and adjust file length + length byte of this record
        rec_start = pat - 1
        old_len = d[rec_start]
        delta = 7 - len(old_span)
        d[j:k] = new_assign
        d[rec_start] = (old_len + delta) & 0xFF
        print("adjusted rec len", old_len, "->", d[rec_start], "delta", delta)
    else:
        d[j:k] = new_assign
        print("same-length replace")

p.write_bytes(d)
print("wrote size", len(d))

# verify parse
lines = parse_russell_program(bytes(d))
print("parsed lines", len(lines))
for num, text in lines[:8]:
    print(num, text[:70])
print("fmt", detect_bbc_binary_format(bytes(d)))
