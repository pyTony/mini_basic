# MODE 7 teletext test screen

## Run

```powershell
cd <mini_basic root>
python -m mini_basic --dialect bbc --display pygame examples/teletext/mode7_test_screen.bas
```

Use pygame so mosaics and colours render; terminal mode is limited.

## What you should see

| Section | Codes | Expectation |
|---------|--------|-------------|
| 1 Alpha FG | 129–135 | Coloured words |
| 2 Graphics | 145–151 + mosaics | Coloured block graphics |
| 3 Separated | 154 / 155 | Spaced vs solid sextants |
| 4 Background | 156 / 157 | Yellow band then black |
| 5 Flash | 136 / 137 | Flashing then steady |
| 6 Hold | 158 / 159 | Partial hold behaviour |
| 7 Mosaic strip | 160–175 | Glyph progression |
| **[F] rows** | 140/141, 152… | **May be wrong** until full SAA5050 |

Rows marked **[F]** are the **acceptance screen for future work**: when double-height and conceal match a Beeb/BBCSDL reference, those rows stop looking broken.

## Automated tests

```powershell
python -m pytest -q test/test_teletext_screen.py --timeout=30
```

Current behaviour is asserted; incomplete SAA5050 features are `xfail` so the suite stays green while documenting the target.
