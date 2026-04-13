# ================================================================
# REALISTIC ECONOMICS OVERHAUL v3.0
# A comprehensive economic simulation mod for Democracy 4
# Author: Vasilios Artemiou
# ================================================================

# INSTALLATION
# ------------
# Option 1: Run the Patcher (Recommended)
#   1. Extract this zip to any folder
#   2. Run D4_Economics_Patcher.exe
#   3. The patcher auto-detects your Democracy 4 installation
#      and copies the mod files to the correct location
#   4. Launch Democracy 4, enable "Realistic Economics Overhaul"
#      in the mod manager
#
# Option 2: Manual Install
#   1. Extract this zip
#   2. Copy everything EXCEPT D4_Economics_Patcher.exe/.py and
#      _generate.py/_gen_dilemmas.py into:
#      Documents/My Games/democracy4/mods/economics_overhaul/
#   3. Launch Democracy 4, enable "Realistic Economics Overhaul"
#      in the mod manager
#
# Option 3: Run from Source (developers)
#   1. Install Python 3.8+
#   2. Run: python D4_Economics_Patcher.py

# FILE INVENTORY
# --------------
# D4_Economics_Patcher.exe   - Standalone patcher (no Python needed)
# D4_Economics_Patcher.py    - Patcher source code
# _generate.py               - Country profile generator (dev tool)
# _gen_dilemmas.py            - Dilemma generator (dev tool)
# config.txt                  - Mod configuration
# preview.jpg                 - Mod thumbnail
# economics_overhaul.jpg      - Mod banner image
#
# data/
#   simconfig.txt             - Game config overrides (interest rates,
#                               credit thresholds, debt-to-GDP limits)
#   simulation/
#     simulation.csv          - 14 new simulation values
#     situations.csv          - 4 crisis situations
#     policies.csv            - 3 new policies
#     prereqs.txt             - Eurozone prerequisite definition
#     dilemmas/               - 53 economic dilemma files
#   overrides/                - 22 global feedback loop overrides
#   missions/                 - 140 country profiles (8 overrides each)
#   svg/                      - 16 custom icons
# translations/English/
#   simulation.csv            - Simulation value names/descriptions
#   situations.csv            - Crisis names/descriptions
#   policies.csv              - Policy names/descriptions
#   dilemmas.csv              - Dilemma text and option descriptions
#   events.csv                - Credit rating event text
#   strings.ini               - UI strings for credit display

# OVERVIEW
# --------
# This mod completely reworks Democracy 4's economic simulation by
# adding a full sovereign bond market with yield curve dynamics,
# debt maturity modeling, fiscal dominance feedback, and crisis
# mechanics.

# NEW SIMULATION VALUES (14)
# --------------------------
# Short-Term Yield (2Y)    - Policy rate proxy, fastest inflation response
# Medium-Term Yield (10Y)  - Benchmark government borrowing rate
# Long-Term Yield (30Y)    - Structural outlook, pension and mortgage costs
# Yield Curve Slope        - Long minus short; inversion = recession signal
# Real Interest Rate       - Sovereign debt rate feeding into yields
# Debt Service Ratio       - Interest payments as share of revenue
# Sovereign Risk Premium   - Credit risk feeding back into all yields
# Money Supply (M2)        - Monetary conditions driving inflation
# Nominal GDP              - GDP including inflation, for debt ratios
# Fiscal Balance           - Government surplus or deficit
# GDP Per Capita (PPP)     - Living standards adjusted for prices
# Term Premium             - Extra yield for holding long-duration bonds
# Energy Price Index       - Aggregate energy costs driving inflation
# Central Bank Rate        - Policy rate (also appears as a policy slider)

# NEW POLICIES (3)
# ----------------
# Central Bank Rate    - Set overnight policy rate
# Fiscal Rule          - Legally binding spending limits
# Yield Curve Control  - Cap long yields (Japan-style)
#
# Eurozone countries have these policies available but weakened
# by ~90% via per-country overrides, reflecting ECB control.

# NEW CRISIS SITUATIONS (4)
# -------------------------
# Yield Curve Inversion  - Classic recession predictor
# Stagflation            - High inflation + stagnant growth
# Deflation              - Falling prices, debt spiral risk
# Bond Market Crisis     - Sovereign debt doom loop

# ECONOMIC DILEMMAS (53 files)
# ----------------------------
# Crisis dilemmas (rare, need bad conditions):
#   Banking Crisis, Bond Auction Failure, Capital Flight,
#   Currency Crisis, Doom Loop, Fiscal Cliff, IMF Package,
#   Foreign Debt Restructuring, Sovereign Downgrade,
#   Stagflation Dilemma, Sudden Stop
#
# Conditional dilemmas (moderate, context-dependent):
#   Austerity Protests, Commodity Price Shock, Deflation Response,
#   Housing Bubble, Trade War Escalation, Natural Disaster Response
#
# Policy choice dilemmas (common, routine governance):
#   Central Bank Governor, Digital Currency, Green Bond Initiative,
#   Inflation Target Review, Pension Reform, Public Debt Transparency,
#   Sovereign Wealth Fund, Tax Haven Crackdown
#
# Eurozone/Sovereign variants (28 files):
#   Banking Crisis Contagion, Capital Flight Emergency,
#   Currency Crisis Response, Deflation Emergency Response,
#   Doom Loop Escalation, Failed Bond Auction,
#   Stagflation Policy Choice, ECB Rate Decision,
#   Eurobond Proposal, Eurozone Exit Debate, and more
#
# Every dilemma has at least one GDP-positive or neutral option.
# Trigger probabilities are tuned by category (0.05-0.50).

# GLOBAL OVERRIDES (22 files)
# ---------------------------
# Yield/interest rate transmission:
#   yield_interest_rate.ini, sovrisk_interest_rate.ini,
#   yield_debt_medium.ini, yield_debt_long.ini, sovrisk_debt.ini
# Crisis recovery:
#   crisis_gdp_recovery.ini (BusinessConfidence -> GDP)
# Inflation channels (dual-inertia transitory system):
#   energy_inflation.ini, energy_inflation_fast/slow.ini,
#   oil_inflation_fast/slow.ini, food_inflation_fast/slow.ini,
#   salestax_inflation_fast/slow.ini, carbontax_inflation_fast/slow.ini,
#   petroltax_inflation_fast/slow.ini
# Debt feedback:
#   inflation_debt.ini, inflation_debt_feedback.ini,
#   debt_inflation_relief.ini

# COUNTRY PROFILES (140 countries)
# ---------------------------------
# Every country has 8 override files controlling:
#   credit_gdp.ini       - GDP sensitivity to credit conditions
#   credit_stab.ini      - Stability sensitivity to credit conditions
#   eurozone_cb.ini      - Central Bank Rate eurozone dampening
#   eurozone_qe.ini      - QE eurozone dampening
#   eurozone_ycc.ini     - YCC eurozone dampening
#   spread_global.ini    - Global economy spread sensitivity
#   spread_inflation.ini - Inflation spread sensitivity
#   spread_yield.ini     - Yield spread sensitivity
#
# Seven credit tiers based on S&P ratings (2024):
#   AAA: Australia, Canada, Denmark, Germany, Luxembourg,
#        Netherlands, Norway, Singapore, Sweden, Switzerland
#   AA:  Austria, Finland, USA, UK, Belgium, Ireland, Qatar,
#        South Korea, UAE, Czechia, Hong Kong, New Zealand
#   A:   Chile, China, France, Japan, Israel, Malaysia, Poland,
#        Portugal, Saudi Arabia, Croatia, Estonia, etc.
#   BBB: Spain (baseline), Greece, Italy, India, Indonesia,
#        Mexico, Brazil, Thailand, Philippines, Romania, etc.
#   BB:  South Africa, Turkey, Colombia, Vietnam, etc.
#   B:   Egypt, Nigeria, Pakistan, Bangladesh, etc.
#   CCC/SD: Argentina, Venezuela, Ethiopia, Lebanon, etc.

# COMPATIBILITY
# -------------
# Tested with: D4 Overhaul, Latin America mod, D4+,
#   Poland mod, China mod
# Country folder aliases cover common naming variants.

# SOURCE CODE
# -----------
# GitHub: https://github.com/vartemiou-svg/democracy4-economics-overhaul

# ================================================================
