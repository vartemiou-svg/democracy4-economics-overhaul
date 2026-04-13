import os

D = r"C:\Users\varte\OneDrive\Documents\My Games\democracy4\mods\economics_overhaul\data\simulation\dilemmas"

def w(name, content):
    with open(os.path.join(D, name), "w") as f:
        f.write(content)

# #1A Failed Bond Auction - Sovereign
w("FailedBondAuction_Sovereign.txt", """[dilemma]
name = FailedBondAuction_Sovereign

[influences]
0 = _random_,0,0.12
1 = SovereignRisk,0+(0.5*x)
2 = DebtServiceRatio,0+(0.4*x)
3 = BusinessConfidence,0.3-(0.4*x)
4 = _prereq_eurozone,0-(1.0*x)

[option0]
OnImplement = CreateGrudge(MediumTermYield,0.08,0.92f);CreateGrudge(DebtServiceRatio,0.06,0.92f);CreateGrudge(Capitalist,-0.04,0.88f);CreateGrudge(_All_,-0.03,0.88f);

[option1]
OnImplement = CreateGrudge(MoneySupply,0.10,0.93f);CreateGrudge(Inflation,0.06,0.93f);CreateGrudge(CurrencyStrength,-0.08,0.91f);CreateGrudge(MediumTermYield,-0.04,0.88f);CreateGrudge(Capitalist,-0.06,0.90f);CreateGrudge(Socialist,0.03,0.88f);

[option2]
OnImplement = CreateGrudge(ShortTermYield,0.06,0.90f);CreateGrudge(DebtServiceRatio,0.03,0.90f);CreateGrudge(SovereignRisk,0.04,0.92f);CreateGrudge(BusinessConfidence,-0.03,0.90f);
""")

# #1B Failed Bond Auction - Eurozone
w("FailedBondAuction_Eurozone.txt", """[dilemma]
name = FailedBondAuction_Eurozone

[influences]
0 = _random_,0,0.12
1 = SovereignRisk,0+(0.5*x)
2 = DebtServiceRatio,0+(0.4*x)
3 = BusinessConfidence,0.3-(0.4*x)
4 = _prereq_eurozone,-1.0+(1.0*x)

[option0]
OnImplement = CreateGrudge(MediumTermYield,0.08,0.92f);CreateGrudge(DebtServiceRatio,0.06,0.92f);CreateGrudge(Capitalist,-0.04,0.88f);CreateGrudge(_All_,-0.03,0.88f);

[option1]
OnImplement = CreateGrudge(MoneySupply,0.04,0.93f);CreateGrudge(Inflation,0.02,0.93f);CreateGrudge(CurrencyStrength,-0.03,0.91f);CreateGrudge(MediumTermYield,-0.03,0.88f);CreateGrudge(SovereignRisk,-0.04,0.92f);CreateGrudge(FiscalBalance,-0.03,0.92f);CreateGrudge(BusinessConfidence,0.02,0.90f);CreateGrudge(Capitalist,-0.03,0.90f);CreateGrudge(_All_,-0.04,0.91f);CreateGrudge(Socialist,-0.03,0.88f);

[option2]
OnImplement = CreateGrudge(ShortTermYield,0.06,0.90f);CreateGrudge(DebtServiceRatio,0.03,0.90f);CreateGrudge(SovereignRisk,0.04,0.92f);CreateGrudge(BusinessConfidence,-0.03,0.90f);
""")

# #2 Debt Rollover Timing - Universal
w("DebtRolloverTiming.txt", """[dilemma]
name = DebtRolloverTiming

[influences]
0 = _random_,0,0.10
1 = MediumTermYield,0+(0.45*x)
2 = DebtServiceRatio,0+(0.35*x)
3 = _effectivedebt_,0+(0.3*x)
