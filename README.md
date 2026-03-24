# Realistic Economics Overhaul for Democracy 4

Completely reworks Democracy 4's economic simulation by adding a full sovereign bond market with yield curve dynamics, debt maturity modeling, fiscal dominance feedback, and crisis mechanics.

## What This Mod Does

The base game's simplistic credit-rating-step interest rate is replaced with yield-curve-driven borrowing costs that respond to inflation, debt, stability, and business confidence in real time.

### New Simulation Values (12)

- **Short-Term Yield (2Y)** — Policy rate proxy, fastest inflation response
- **Medium-Term Yield (10Y)** — Benchmark borrowing rate
- **Long-Term Yield (30Y)** — Structural outlook, pension costs
- **Yield Curve Slope** — Long minus short; inversion signals recession
- **Real Interest Rate** — Nominal rate minus inflation (Fisher equation)
- **Debt Service Ratio** — Share of revenue consumed by interest payments
- **Sovereign Risk Premium** — Credit risk that feeds back into all yields
- **Money Supply (M2)** — Monetary conditions with bidirectional inflation feedback
- **Nominal GDP, Fiscal Balance, GDP per Capita (PPP), Term Premium**

### New Policies (4)

- **Central Bank Policy Rate** — Set the overnight rate to fight inflation or stimulate growth
- **Quantitative Easing** — Buy bonds to suppress long-term yields at the cost of currency weakness
- **Fiscal Discipline Rule** — Binding spending limits that improve credit but constrain crisis response
- **Yield Curve Control** — Cap long yields through unlimited bond purchases (Japan-style)

### New Crisis Situations (4)

- **Yield Curve Inversion** — Historically the most reliable recession predictor
- **Stagflation** — High inflation meets high unemployment
- **Deflation** — Falling prices create a negative spiral
- **Bond Market Crisis** — Sovereign debt doom loop cascading into a funding crisis

### Country Profiles

34 countries with calibrated credit profiles. Strong economies (USA, Japan, UK, Germany) get credit buffers. Weak economies (Argentina, Venezuela, Haiti) face structural penalties.

## Installation

### Option 1: Run the Patcher (Recommended)

1. Download the release zip from [Nexus Mods](https://www.nexusmods.com/democracy4/mods/16)
2. Extract and run `D4_Economics_Patcher.exe`
3. The patcher auto-detects your game installation and installs the mod
4. Launch Democracy 4, enable "Realistic Economics Overhaul" in the mod manager
5. Play a turn → patcher patches autosave → load autosave → repeat

### Option 2: Run from Source

1. Clone this repository
2. Install Python 3.8+
3. Run `python D4_Economics_Patcher.py`

## Building the Executable

The standalone `.exe` is built with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --name D4_Economics_Patcher D4_Economics_Patcher.py
```

The resulting exe bundles the Python runtime so users don't need Python installed.

## Project Structure

```
├── D4_Economics_Patcher.py    # Patcher source code (what compiles into the .exe)
├── README.md
└── mod/                       # Democracy 4 mod files
    ├── config.txt
    ├── data/
    │   ├── overrides/         # Debt↔inflation feedback loops
    │   ├── simulation/        # Simulation values, policies, situations
    │   ├── svg/               # 12 custom icons
    │   └── missions/          # 34 country profiles
    └── translations/English/  # Localization strings
```

## License

This mod is free to use, modify, and distribute.
