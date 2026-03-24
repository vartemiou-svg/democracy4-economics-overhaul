# Realistic Economics Overhaul v2.0 for Democracy 4
# ==================================================
#
# One-click installer + runtime patcher for realistic bond market economics.
#
# QUICK START:
#   1. Run D4_Economics_Patcher.exe (installs mod + patches simconfig)
#   2. Launch Democracy 4
#   3. Enable "Realistic Economics Overhaul" in the mod manager
#   4. Start a new game
#   5. Play a turn -> patcher patches autosave -> load autosave -> repeat
#
# WHAT THIS MOD DOES:
#
#   Adds a full sovereign bond market with yield curve dynamics, debt maturity
#   modeling, fiscal dominance feedback, and crisis mechanics. The base game's
#   simplistic credit-rating-step interest rate is replaced with yield-curve-
#   driven borrowing costs that respond to inflation, debt, stability, and
#   business confidence in real time.
#
# NEW SIMULATION VALUES (12):
#
#   Short-Term Yield (2Y)   - Policy rate proxy, fastest inflation response
#   Medium-Term Yield (10Y) - Benchmark borrowing rate, mortgages, corporate debt
#   Long-Term Yield (30Y)   - Structural outlook, pension costs, infrastructure
#   Yield Curve Slope       - Long minus short; inversion signals recession
#   Real Interest Rate      - Fisher equation: nominal minus inflation
#   Debt Service Ratio      - Interest share of revenue; doom-loop trigger
#   Sovereign Risk          - Credit risk premium; feeds back into all yields
#   Money Supply (M2)       - Monetary conditions; bidirectional with inflation
#   Nominal GDP             - Current-price GDP for debt ratio calculations
#   Fiscal Balance          - Revenue minus spending
#   GDP per Capita (PPP)    - Living standard measure; drives migration
#   Term Premium            - Extra yield for holding longer-duration bonds
#
#   Each value has a unique custom SVG icon in the Economy panel.
#
# NEW POLICIES (4):
#
#   Central Bank Policy Rate  - Overnight lending rate; anchors short yields
#   Quantitative Easing       - Bond purchases; suppresses long yields
#   Fiscal Discipline Rule    - Binding spending limits; reduces sovereign risk
#   Yield Curve Control       - Caps long yields; massive money creation
#
# NEW SITUATIONS (4):
#
#   Yield Curve Inversion     - Short rates exceed long rates; recession signal
#   Stagflation               - High inflation + high unemployment
#   Deflation                 - Falling prices create negative spiral
#   Bond Market Crisis        - Debt spiral cascades into funding crisis
#
# COUNTRY PROFILES (34):
#
#   Each country has calibrated credit profile overrides that determine
#   how GDP and Stability affect effective debt levels. Strong economies
#   (USA, Japan, UK, Germany) get credit buffers. Weak economies
#   (Argentina, Venezuela, Haiti) face structural penalties.
#
# V2.0 CHANGES (from v1.1):
#
#   - Added _effectivedebt_ as direct input to yields, DSR, SovereignRisk,
#     and MoneySupply. Debt levels now directly affect borrowing costs.
#   - Raised DSR and SovereignRisk defaults from 0.15 to 0.25 to prevent
#     floor-pinning in stable economies.
#   - Flattened BusinessConfidence coefficients on DSR/SovereignRisk so they
#     no longer collapse to zero when BC exceeds 0.375.
#   - Added BusinessConfidence doom-loop outputs from DSR and SovereignRisk.
#   - Added Corruption as direct input to LongTermYield.
#   - Doubled MoneySupply GDP coefficient and halved its inertia for
#     better responsiveness to economic conditions.
#   - Strengthened Corruption coefficient on SovereignRisk.
#   - 12 custom SVG icons replacing generic GDP/currency icons.
#   - Updated patcher v2.0: auto-detect paths, uses mod SovereignRisk
#     directly, sovereign risk premium increased to 4%.
#
#   Stress test results (v1 -> v2):
#     Goal violations: 165 -> 13 (92% reduction)
#     Floor/ceiling pins: 76 -> 0 (eliminated)
#     USA-Italy 10Y spread: 5bp -> 97bp (20x wider)
#     USA-Argentina SovRisk spread: 0.076 -> 0.370 (5x wider)
#
# TECHNICAL NOTES:
#
#   - The patcher is optional. Without it, the mod works standalone but
#     interest payments use the engine's credit rating steps.
#   - Starting a new game resets the patcher's debt portfolio state.
#     Delete patcher_state.json in your savegames folder to reset.
#   - Compatible with Democracy 4 v1.67+
#   - Tested with 20 community mods simultaneously
#   - No Python installation required (standalone exe)
#   - All text files are pure ASCII (no encoding issues)
#
# COMPATIBILITY:
#
#   Supports base game + DLC countries plus community country mods:
#   ukoverhaul, usaoverhaul, neoliberalusa, foreignpolicy (rp), china
#
# CREDITS:
#
#   Macroeconomic modeling based on real sovereign debt market dynamics
