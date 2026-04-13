import os

# Target: the actual mod directory
MOD_DIR = r"C:\Users\varte\OneDrive\Documents\My Games\democracy4\mods\economics_overhaul"

TIERS = {
    "AAA":  ("-0.12+(0.15*x)", "-0.04+(0.06*x)"),
    "AA":   ("-0.08+(0.10*x)", "-0.03+(0.04*x)"),
    "A":    ("-0.04+(0.06*x)", "-0.02+(0.03*x)"),
    "BBB":  (None, None),
    "BB":   ("0.02-(0.02*x)", "0.01-(0.01*x)"),
    "B":    ("0.04-(0.04*x)", "0.02-(0.02*x)"),
    "CCC":  ("0.08-(0.06*x)", "0.04-(0.03*x)"),
    "SD":   ("0.12-(0.08*x)", "0.06-(0.04*x)"),
}

def r2t(rating):
    if rating in ("AAA",): return "AAA"
    if rating in ("AA+","AA","AA-"): return "AA"
    if rating in ("A+","A","A-"): return "A"
    if rating in ("BBB+","BBB","BBB-"): return "BBB"
    if rating in ("BB+","BB","BB-"): return "BB"
    if rating in ("B+","B","B-"): return "B"
    if rating in ("CCC+","CCC","CCC-","CC","C"): return "CCC"
    return "SD"

EUROZONE = {"austria","belgium","croatia","cyprus","estonia","finland",
    "france","germany","greece","ireland","italy","latvia",
    "lithuania","luxembourg","malta","netherlands","portugal",
    "slovakia","slovenia","spain","bavaria","catalonia"}

# Non-eurozone, non-sovereign (dollarized/uses euro without membership)
NON_SOVEREIGN = {"panama","ecuador","elsalvador","montenegro","liechtenstein"}

# Countries with hand-tuned credit profiles that must NOT be overwritten.
# These have custom v3.0-rebalanced equations in credit_stab.ini / credit_gdp.ini.
HAND_TUNED = {
    "argentina", "australia", "canada", "france", "germany",
    "italy", "japan", "southkorea", "spain", "uk", "usa",
}

# (folder, rating, sovereign_currency)
# Primary folder names only — no aliases (aliases create ghost folders
# that don't match any D4 mission and were cleaned up in Session 5).
COUNTRIES = [
    # AAA tier
    ("australia","AAA",True),("canada","AAA",True),
    ("denmark","AAA",True),("germany","AAA",False),
    ("luxembourg","AAA",False),("netherlands","AAA",False),
    ("norway","AAA",True),("singapore","AAA",True),
    ("sweden","AAA",True),("switzerland","AAA",True),
    ("liechtenstein","AAA",False),
    # AA tier
    ("austria","AA+",False),("finland","AA+",False),
    ("newzealand","AA+",True),("taiwan","AA+",True),
    ("usa","AA+",True),("belgium","AA",False),
    ("hongkong","AA+",True),("ireland","AA",False),
    ("kuwait","AA-",True),("qatar","AA",True),
    ("southkorea","AA",True),("uae","AA",True),
    ("uk","AA",True),("czechia","AA-",True),
    # A tier
    ("chile","A",True),("china","A+",True),
    ("croatia","A-",False),("cyprus","A-",False),
    ("estonia","A+",False),("france","A+",False),
    ("iceland","A+",True),("israel","A",True),
    ("japan","A+",True),("latvia","A",False),
    ("lithuania","A",False),("malaysia","A-",True),
    ("malta","A-",False),
    ("poland","A-",True),
    ("portugal","A+",False),
    ("saudiarabia","A+",True),
    ("slovakia","A+",False),("slovenia","A-",False),
    # BBB tier (baseline — no credit overrides generated)
    ("spain","BBB",False),("botswana","BBB",True),
    ("bulgaria","BBB+",True),("greece","BBB",False),
    ("hungary","BBB-",True),("india","BBB",True),
    ("indonesia","BBB",True),("italy","BBB+",False),
    ("kazakhstan","BBB-",True),("mexico","BBB",True),
    ("morocco","BBB-",True),("panama","BBB-",False),
    ("paraguay","BBB-",True),("peru","BBB-",True),
    ("philippines","BBB+",True),("romania","BBB-",True),
    ("serbia","BBB-",True),
    ("thailand","BBB+",True),
    ("trinidadandtobago","BBB-",True),
    ("uruguay","BBB+",True),
    # BB tier
    ("albania","BB",True),("armenia","BB-",True),
    ("azerbaijan","BB+",True),("bahamas","BB-",True),
    ("brazil","BB",True),("colombia","BB",True),
    ("costarica","BB",True),
    ("cotedivoire","BB",True),
    ("dominicanrepublic","BB",True),
    ("georgia","BB",True),("guatemala","BB+",True),
    ("honduras","BB-",True),("jamaica","BB",True),
    ("jordan","BB-",True),("mongolia","BB-",True),
    ("northmacedonia","BB-",True),
    ("southafrica","BB",True),
    ("turkey","BB-",True),
    ("uzbekistan","BB",True),("vietnam","BB+",True),
    # B tier
    ("angola","B-",True),("bahrain","B",True),
    ("bangladesh","B+",True),("barbados","B+",True),
    ("belize","B-",True),("benin","BB-",True),
    ("bosniaandherzegovina","B+",True),
    ("caboverde","B",True),
    ("cameroon","B-",True),("chad","B-",True),
    ("drcongo","B-",True),("ecuador","B-",False),
    ("egypt","B",True),
    ("elsalvador","B-",False),
    ("fiji","B+",True),("ghana","B-",True),
    ("guinea","B+",True),("kenya","B",True),
    ("kyrgyzstan","B+",True),("madagascar","B-",True),
    ("moldova","BB-",True),("montenegro","B+",False),
    ("nicaragua","B+",True),("nigeria","B-",True),
    ("oman","BBB-",True),("pakistan","B-",True),
    ("papuanewguinea","B-",True),
    ("rwanda","B+",True),("tajikistan","B",True),
    ("togo","B+",True),("uganda","B-",True),
    # CCC / Default tier
    ("argentina","CCC+",True),("bolivia","CCC-",True),
    ("burkinafaso","CCC+",True),
    ("congo","CCC+",True),
    ("ethiopia","SD",True),("haiti","SD",True),
    ("laos","CCC+",True),("lebanon","SD",True),
    ("mozambique","CCC+",True),
    ("srilanka","CCC+",True),
    ("suriname","CCC+",True),("ukraine","CCC+",True),
    ("venezuela","SD",True),("zambia","CCC+",True),
    # Community mod countries
    ("scotland","A",True),("catalonia","A-",False),
    ("bavaria","AAA",False),("greenland","BBB",True),
    ("cuba","CCC",True),
    ("neoliberalusa","AA+",True),("usaoverhaul","AA+",True),
    ("ukoverhaul","AA",True),
    # D4 Latin America mod aliases used as folder names
    ("guyana","BB-",True),("puertorico","BBB-",False),
    ("rdominicana","BB",True),("rp","A-",True),
]

# Override templates
def credit_ini(host, eq):
    return f'[override]\nTargetName = "_effectivedebt_"\nHostName = "{host}"\nEquation = "{eq}"\nInertia = 8\n'

EZ_CB  = '[override]\nTargetName = "ShortTermYield"\nHostName = "CentralBankRate"\nEquation = "0+(0.05*x)"\nInertia = 2\n'
EZ_QE  = '[override]\nTargetName = "LongTermYield"\nHostName = "QuantitativeEasing"\nEquation = "0-(0.03*x)"\nInertia = 4\n'
EZ_YCC = '[override]\nTargetName = "LongTermYield"\nHostName = "YieldCurveControl"\nEquation = "0-(0.04*x)"\nInertia = 2\n'
SP_Y   = '[override]\nTargetName = "SovereignRisk"\nHostName = "MediumTermYield"\nEquation = "-0.12+(0.35*x)"\nInertia = 4\n'
SP_I   = '[override]\nTargetName = "SovereignRisk"\nHostName = "Inflation"\nEquation = "0.05-(0.12*x)"\nInertia = 4\n'
SP_G   = '[override]\nTargetName = "SovereignRisk"\nHostName = "_globaleconomy_"\nEquation = "0.02-(0.04*x)"\nInertia = 4\n'

# Fixed: slot 40, not slot 20 (slot 20 collides with base game _prereq_earthquake)
EZ_PREREQ = '[config]\n40 = 1\n'

# Deduplicate by primary folder name
seen = set()
unique = []
for entry in COUNTRIES:
    if entry[0] not in seen:
        seen.add(entry[0])
        unique.append(entry)

stats = {"folders": 0, "credit_new": 0, "credit_skip": 0, "eurozone": 0, "prereqs": 0}

for folder, rating, sov_curr in unique:
    tier = r2t(rating)
    stab_eq, gdp_eq = TIERS[tier]
    is_ez = folder in EUROZONE
    is_nonsov = folder in NON_SOVEREIGN
    is_hand_tuned = folder in HAND_TUNED

    odir = os.path.join(MOD_DIR, "data", "missions", folder, "overrides")
    os.makedirs(odir, exist_ok=True)
    stats["folders"] += 1

    # Credit profile (skip baseline BBB and hand-tuned countries)
    if stab_eq is not None:
        if is_hand_tuned:
            stats["credit_skip"] += 1
        else:
            with open(os.path.join(odir, "credit_stab.ini"), "w") as f:
                f.write(credit_ini("Stability", stab_eq))
            with open(os.path.join(odir, "credit_gdp.ini"), "w") as f:
                f.write(credit_ini("GDP", gdp_eq))
            stats["credit_new"] += 1

    # Eurozone or non-sovereign: monetary restriction + spread risk overrides
    if is_ez or is_nonsov:
        with open(os.path.join(odir, "eurozone_cb.ini"), "w") as f:
            f.write(EZ_CB)
        with open(os.path.join(odir, "eurozone_qe.ini"), "w") as f:
            f.write(EZ_QE)
        with open(os.path.join(odir, "eurozone_ycc.ini"), "w") as f:
            f.write(EZ_YCC)
        with open(os.path.join(odir, "spread_yield.ini"), "w") as f:
            f.write(SP_Y)
        with open(os.path.join(odir, "spread_inflation.ini"), "w") as f:
            f.write(SP_I)
        with open(os.path.join(odir, "spread_global.ini"), "w") as f:
            f.write(SP_G)
        stats["eurozone"] += 1

    # Eurozone prereqs (only for actual eurozone members, not just non-sovereign)
    if is_ez:
        mdir = os.path.join(MOD_DIR, "data", "missions", folder)
        with open(os.path.join(mdir, "prereqs.txt"), "w") as f:
            f.write(EZ_PREREQ)
        stats["prereqs"] += 1

print(f"Done!")
print(f"  Country folders: {stats['folders']}")
print(f"  Credit profiles generated: {stats['credit_new']}")
print(f"  Credit profiles skipped (hand-tuned): {stats['credit_skip']}")
print(f"  Eurozone/non-sovereign restricted: {stats['eurozone']}")
print(f"  Eurozone prereqs written: {stats['prereqs']}")
