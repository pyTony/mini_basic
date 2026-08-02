"""Probe Wilson-format BBC BASIC file structure."""
import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Tony\Downloads\calcexe\CalcEXE'
data = open(path, 'rb').read()
i = 0
while i < len(data):
    if data[i] == 0xFF:
        print('terminator FF at', i)
        break
    if data[i] != 0x0D:
        print('expected CR at', i, 'got', hex(data[i]))
        break
    if i + 4 > len(data):
        break
    line = (data[i + 1] << 8) | data[i + 2]
    ln = data[i + 3]
    text = data[i + 4 : i + 4 + ln]
    i = i + 4 + ln
    print(f'line {line:5} len={ln:3} tail={text[-3:].hex() if text else ""}')