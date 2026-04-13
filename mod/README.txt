# ================================================================
# REALISTIC ECONOMICS OVERHAUL v3.0
# A comprehensive economic simulation mod for Democracy 4
# Author: Vasman
# ================================================================
#
# OVERVIEW
# --------
# This mod completely reworks Democracy 4's economic simulation by
# adding 13 simulation values, 4 policies, 4 crisis situations,
# 21 dilemmas (28 files), 136 country credit profiles, a eurozone
# monetary restriction system, and slope-based transitory inflation.
#
# NEW SIMULATION VALUES (13)
# --------------------------
# Short-Term Yield (2Y)    - Policy rate proxy, fastest inflation response
# Medium-Term Yield (10Y)  - Benchmark government borrowing rate
# Long-Term Yield (30Y)    - Structural outlook, pension and mortgage costs
# Yield Curve Slope        - Long minus short; inversion = recession signal
# Real Interest Rate       - Inflation-adjusted rate (Fisher equation)
# Debt Service Ratio       - Interest payments as share of revenue
# Sovereign Risk Premium   - Credit risk feeding back into all yields
# Money Supply (M2)        - Monetary conditions driving inflation
# Nominal GDP              - GDP including inflation, for debt ratios
# Fiscal Balance           - Government surplus or deficit
# GDP Per Capita (PPP)     - Living standards adjusted for prices
# Term Premium             - Extra yield for holding long-duration bonds
# Energy Price Index       - Aggregate energy costs (NEW in v3.0)
#
# NEW POLICIES (4)
# ----------------
# Central Bank Rate    - Set overnight policy rate
# Quantitative Easing  - Buy bonds to suppress long-term yields
# Fiscal Rule          - Legally binding spending limits
# Yield Curve Control  - Cap long yields (Japan-style)
#
# Eurozone countries have these policies available but weakened
# by ~90% via per-country overrides. This reflects the reality
# that ECB policy affects all member states, not just yours.
#
# NEW CRISIS SITUATIONS (4)
# -------------------------
# Yield Curve Inversion  - Classic recession predictor
# Stagflation            - High inflation + stagnant growth
# Deflation              - Falling prices, debt spiral risk
# Bond Market Crisis     - Sovereign debt doom loop
#
# DILEMMAS (21 dilemmas, 28 files)
# --------------------------------
# 13 universal dilemmas work for all countries.
# 7 dilemmas have dual sovereign/eurozone versions with
# different options reflecting whether you control monetary
# policy. 1 dilemma (ECB Rate Decision) is eurozone-only.
#
# Crisis dilemmas: Failed Bond Auction, Currency Crisis,
#   Banking Crisis Contagion, Doom Loop Escalation,
#   Capital Flight Emergency, Inflation Riots
# Policy dilemmas: Stagflation Policy, Deflation Emergency,
#   Fiscal Rule Suspension, CB Governor Appointment,
#   ECB Rate Decision, IMF Stabilization Package
# Fiscal dilemmas: Debt Rollover, Sovereign Wealth Fund,
#   Natural Disaster Response, State Enterprise Bailout,
#   Tech Company Tax Holiday, Credit Rating Warning
# Trap dilemma: Declare Debt Risk-Free (backfires)
#
# COUNTRY CREDIT PROFILES (136 countries, 309 folders)
# ---------------------------------------------------
# Every rated sovereign nation has a credit profile based on
# S&P ratings as of 2024. Seven tiers from AAA to SD/Default:
#
#   AAA: Australia, Canada, Denmark, Germany, Luxembourg,
#        Netherlands, Norway, Singapore, Sweden, Switzerland
#   AA:  Austria, Finland, USA, UK, Belgium, Ireland, Qatar,
#        South Korea, UAE, Czechia, Hong Kong, New Zealand
#   A:   Chile, China, France, Japan, Israel, Malaysia, Poland,
#        Portugal, Saudi Arabia, Croatia, Cyprus, Estonia,
#        Latvia, Lithuania, Malta, Slovakia, Slovenia, Iceland
#   BBB: Spain (baseline), Greece, Italy, India, Indonesia,
#        Mexico, Brazil, Thailand, Philippines, Romania, etc.
#   BB:  South Africa, Turkey, Colombia, Vietnam, etc.
#   B:   Egypt, Nigeria, Pakistan, Bangladesh, etc.
#   CCC/SD: Argentina, Venezuela, Ethiopia, Lebanon, etc.
#
# Unknown/custom countries default to BBB (baseline) with
# full monetary policy access.
#
# EUROZONE SYSTEM
# ---------------
# 20 eurozone countries receive:
# - Monetary policy weakened by ~90% (CentralBankRate, QE, YCC)
# - Spread-based sovereign risk (10Y spread vs German Bund proxy)
# - Eurozone-specific dilemma variants
# - ECB Rate Decision dilemma (eurozone-only)
#
# The spread system means your sovereign risk is driven by
# YOUR fiscal problems relative to the eurozone average.
# Global inflation raises all yields equally so the spread
# stays narrow — only domestic mismanagement widens it.
#
# SLOPE-BASED TRANSITORY INFLATION (NEW in v3.0)
# -----------------------------------------------
# Inflation is now driven by the RATE OF CHANGE of prices
# and taxes, not their level. A 20% VAT doesn't cause
# perpetual inflation — but RAISING VAT from 15% to 20%
# causes a temporary inflation spike that fades over time.
#
# This uses a dual-inertia cancellation trick: two opposing
# override channels (fast inertia=2, slow inertia=10) cancel
# at equilibrium. When prices CHANGE, the fast channel reacts
# first, creating a transitory push that fades as the slow
# channel catches up.
#
# Sources with CPI-weighted coefficients:
#   Energy prices  (25% CPI) -> coefficient 0.12
#   Oil/fuel       (10% CPI) -> coefficient 0.06
#   Food prices    (15% CPI) -> coefficient 0.08
#   Sales tax      (60% spending) -> coefficient 0.10
#   Carbon tax     (15-20%) -> coefficient 0.06
#   Petrol tax     (8-10%)  -> coefficient 0.04
#
# Tax CUTS produce NEGATIVE (deflationary) push — this is
# why governments cut VAT during cost-of-living crises.
#
# COMPATIBILITY
# -------------
# Tested with: D4 Overhaul, Latin America mod, D4+,
#   Poland mod, China mod
# Country folder aliases cover common naming variants.
#
# HOW TO ADD YOUR COUNTRY
# -----------------------
# Create data/missions/yourcountry/overrides/ with
# credit_stability.ini and credit_gdp.ini using the
# appropriate tier equations from the mod documentation.
# For eurozone countries, also add eurozone_cb/qe/ycc.ini,
# spread_yield/inflation/global.ini, and prereqs.txt.
#
# ================================================================
