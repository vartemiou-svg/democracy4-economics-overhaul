import os
import re
import json
import time
import sys
import shutil
from pathlib import Path
from datetime import datetime

VERSION = "2.0"

# Debt maturity weights for new issuance
NEW_DEBT_WEIGHTS = {'short': 0.15, 'medium': 0.55, 'long': 0.30}
MATURITY_TURNS = {'short': 8, 'medium': 40, 'long': 120}

# Credit rating (0=C..8=AAA) -> base sovereign risk
CREDIT_TO_RISK = {8:0.05, 7:0.10, 6:0.18, 5:0.28, 4:0.40, 3:0.55, 2:0.70, 1:0.85, 0:0.95}
CR_NAMES = {0:'C', 1:'CC', 2:'CCC', 3:'B', 4:'BB', 5:'BBB', 6:'A', 7:'AA', 8:'AAA'}
RATE_MAX = 0.20
POLL_INTERVAL = 2

def find_d4_paths():
    """Auto-detect Democracy 4 installation and save directories."""
    # Common Steam paths
    steam_paths = [
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Democracy 4"),
        Path(r"C:\Program Files\Steam\steamapps\common\Democracy 4"),
        Path(r"D:\SteamLibrary\steamapps\common\Democracy 4"),
        Path(r"E:\SteamLibrary\steamapps\common\Democracy 4"),
    ]
    game_dir = None
    for p in steam_paths:
        if p.exists():
            game_dir = p; break
    # Save directory
    docs = Path(os.path.expanduser("~")) / "OneDrive" / "Documents" / "My Games" / "democracy4"
    if not docs.exists():
        docs = Path(os.path.expanduser("~")) / "Documents" / "My Games" / "democracy4"
    save_dir = docs / "savegames"
    mods_dir = docs / "mods"
    return game_dir, save_dir, mods_dir

def install_mod(mods_dir):
    """Install mod files from bundled mod/ directory."""
    mod_dest = mods_dir / "economics_overhaul"
    # Check if running from PyInstaller bundle or script dir
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys.executable).parent / "mod"
    else:
        bundle_dir = Path(__file__).parent / "mod"
    if not bundle_dir.exists():
        bundle_dir = Path(__file__).parent / "mods" / "economics_overhaul"
    if bundle_dir.exists():
        if mod_dest.exists():
            shutil.rmtree(mod_dest)
        shutil.copytree(bundle_dir, mod_dest)
        print(f"  Mod installed to: {mod_dest}")
        return True
    else:
        print(f"  Mod files not found in bundle, skipping install.")
        return False

def patch_simconfig(game_dir):
    """Widen the interest rate range in simconfig.txt."""
    cfg = game_dir / "data" / "simconfig.txt"
    if not cfg.exists():
        print("  simconfig.txt not found, skipping."); return False
    content = cfg.read_text(encoding='utf-8')
    patched = False
    for old, new in [("interest_rate_min = 0.01", "interest_rate_min = 0.002"),
                      ("interest_rate_max = 0.10", "interest_rate_max = 0.20")]:
        if old in content:
            content = content.replace(old, new); patched = True
    if patched:
        cfg.write_text(content, encoding='utf-8')
        print("  simconfig.txt patched (rate range 0.2%-20%)")
    return patched

class DebtTranche:
    def __init__(self, amount, rate, mat_type, issued_turn):
        self.amount = amount
        self.rate = rate
        self.mat_type = mat_type
        self.issued_turn = issued_turn
        self.maturity_turn = issued_turn + MATURITY_TURNS[mat_type]
    def is_matured(self, turn):
        return turn >= self.maturity_turn
    def to_dict(self):
        return {'a':self.amount,'r':self.rate,'m':self.mat_type,'i':self.issued_turn,'t':self.maturity_turn}
    @classmethod
    def from_dict(cls, d):
        t = cls(d['a'], d['r'], d['m'], d['i']); t.maturity_turn = d['t']; return t

class State:
    def __init__(self, save_dir):
        self.state_file = save_dir / 'patcher_state.json'
        self.tranches = []; self.last_turn = -1; self.last_debt = 0
        self.last_mtime = 0; self.history = []
    def save(self):
        d = {'lt':self.last_turn,'ld':self.last_debt,'lm':self.last_mtime,
             'tr':[t.to_dict() for t in self.tranches],'h':self.history[-100:]}
        with open(self.state_file,'w') as f: json.dump(d,f)
    def load(self):
        if self.state_file.exists():
            with open(self.state_file,'r') as f: d = json.load(f)
            self.last_turn=d.get('lt',-1); self.last_debt=d.get('ld',0); self.last_mtime=d.get('lm',0)
            self.tranches=[DebtTranche.from_dict(x) for x in d.get('tr',[])]
            self.history=d.get('h',[])

def find_simvalue(content, name):
    for tag in ['name', 'n']:
        idx = content.find(f'<{tag}>{name}</{tag}>')
        if idx >= 0:
            vs = content.find('<value>', idx) + 7
            ve = content.find('</value>', vs)
            if vs > 6 and ve > vs:
                return float(content[vs:ve])
    return None

def parse_save(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    data = {}
    fs = content.find('<finances>'); fe = content.find('</finances>')
    if fs >= 0 and fe >= 0:
        fin = content[fs:fe+12]
        labels = ['deficit','expenditure','income','interest_rate','interest_payment','total_debt','debt_gdp']
        for i in range(7):
            s = fin.find(f'<{i}>') + len(f'<{i}>'); e = fin.find(f'</{i}>')
            if s > len(f'<{i}>') - 1 and e > s:
                data[labels[i]] = float(fin[s:e])
        cr = fin.find('<creditrating>') + 14; cre = fin.find('</creditrating>')
        if cr > 13 and cre > cr:
            data['credit_rating'] = int(fin[cr:cre])
        ihs = fin.find('<inthist>') + 9; ihe = fin.find('</inthist>')
        if ihs > 8 and ihe > ihs:
            rates = [float(x) for x in fin[ihs:ihe].strip(',').split(',') if x.strip()]
            data['turn_count'] = len(rates)
    for name in ['ShortTermYield','MediumTermYield','LongTermYield','SovereignRisk',
                 'RealInterestRate','DebtServiceRatio','BusinessConfidence',
                 'Stability','Inflation','GDP','YieldCurveSlope','MoneySupply','TermPremium']:
        val = find_simvalue(content, name)
        if val is not None:
            data[name] = val
    data['_content'] = content
    return data

def compute_weighted_rate(state, data):
    turn = data.get('turn_count', 0)
    total_debt = data.get('total_debt', 0)
    rates = {
        'short': data.get('ShortTermYield', 0.35) * RATE_MAX,
        'medium': data.get('MediumTermYield', 0.40) * RATE_MAX,
        'long': data.get('LongTermYield', 0.45) * RATE_MAX,
    }
    matured_amt = sum(t.amount for t in state.tranches if t.is_matured(turn))
    state.tranches = [t for t in state.tranches if not t.is_matured(turn)]
    for mtype, w in NEW_DEBT_WEIGHTS.items():
        if matured_amt > 0:
            state.tranches.append(DebtTranche(matured_amt * w, rates[mtype], mtype, turn))
    if data.get('deficit', 0) < 0:
        new_borrow = abs(data['deficit'])
        for mtype, w in NEW_DEBT_WEIGHTS.items():
            state.tranches.append(DebtTranche(new_borrow * w, rates[mtype], mtype, turn))
    if not state.tranches and total_debt > 0:
        for mtype, w in NEW_DEBT_WEIGHTS.items():
            state.tranches.append(DebtTranche(
                total_debt * w, rates[mtype], mtype,
                max(0, turn - MATURITY_TURNS[mtype] // 2)))
    total_out = sum(t.amount for t in state.tranches)
    if total_out > 0:
        blended = sum(t.amount * t.rate for t in state.tranches) / total_out
    else:
        blended = rates['medium']
    # Use mod-computed SovereignRisk directly (v2: properly calculated)
    sov_risk = data.get('SovereignRisk', 0.25)
    blended += sov_risk * 0.04  # up to 4% premium at max risk
    blended = max(0.001, min(RATE_MAX, blended))
    return blended, sov_risk, total_out

def patch_save(filepath, new_rate, new_sov_risk, data):
    content = data['_content']
    original = content
    old_rate_str = f'{data["interest_rate"]:.8f}'
    new_rate_str = f'{new_rate:.8f}'
    content = content.replace(f'<3>{old_rate_str}</3>', f'<3>{new_rate_str}</3>', 1)
    total_debt = data.get('total_debt', 0)
    new_payment = total_debt * new_rate / 4.0
    old_pay_str = f'{data["interest_payment"]:.8f}'
    new_pay_str = f'{new_payment:.8f}'
    content = content.replace(f'<4>{old_pay_str}</4>', f'<4>{new_pay_str}</4>', 1)
    old_exp = data['expenditure']
    exp_diff = new_payment - data['interest_payment']
    new_exp = old_exp + exp_diff
    new_deficit = data['income'] - new_exp
    content = content.replace(f'<1>{old_exp:.8f}</1>', f'<1>{new_exp:.8f}</1>', 1)
    content = content.replace(f'<0>{data["deficit"]:.8f}</0>', f'<0>{new_deficit:.8f}</0>', 1)
    ihs = content.find('<inthist>') + 9; ihe = content.find('</inthist>')
    if ihs > 8 and ihe > ihs:
        hist_str = content[ihs:ihe]; entries = hist_str.strip(',').split(',')
        if entries:
            entries[-1] = f'{new_rate:.3f}'
            content = content[:ihs] + ','.join(entries) + ',' + content[ihe:]
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def print_status(data, blended, sov_risk, state):
    cr = data.get('credit_rating', 0)
    print(f'\n{"="*60}')
    print(f'  TURN {data.get("turn_count","?"):>3}  |  Credit: {CR_NAMES.get(cr,"?"):>3}  |  Debt/GDP: {data.get("debt_gdp",0)*100:.1f}%')
    print(f'{"="*60}')
    sty = data.get("ShortTermYield", 0)
    mty = data.get("MediumTermYield", 0)
    lty = data.get("LongTermYield", 0)
    dsr = data.get("DebtServiceRatio", 0)
    ms = data.get("MoneySupply", 0)
    print(f'  YIELD CURVE:')
    print(f'    2Y:  {sty*RATE_MAX*100:.2f}%  (raw {sty:.3f})')
    print(f'    10Y: {mty*RATE_MAX*100:.2f}%  (raw {mty:.3f})')
    print(f'    30Y: {lty*RATE_MAX*100:.2f}%  (raw {lty:.3f})')
    print(f'  RISK: SovRisk={sov_risk:.3f}  DSR={dsr:.3f}  M2={ms:.3f}')
    print(f'  DEBT PORTFOLIO: {len(state.tranches)} tranches')
    for mtype in ['short','medium','long']:
        amt = sum(t.amount for t in state.tranches if t.mat_type == mtype)
        mcount = [t for t in state.tranches if t.mat_type == mtype]
        wavg = sum(t.amount*t.rate for t in mcount) / max(1, amt) if mcount else 0
        lbl = {'short':'2Y','medium':'10Y','long':'30Y'}[mtype]
        print(f'    {lbl}: {amt/1000:.0f}B at avg {wavg*100:.2f}%')
    print(f'  RATES:')
    print(f'    Engine rate:  {data.get("interest_rate",0)*100:.2f}%')
    print(f'    Blended rate: {blended*100:.2f}%')
    print(f'    Sov premium:  {sov_risk*0.04*100:.2f}% (risk={sov_risk:.3f})')
    new_pmt = data.get('total_debt',0) * blended / 4
    print(f'  FISCAL:')
    print(f'    Debt:     {data.get("total_debt",0)/1000:.0f}B')
    print(f'    Income:   {data.get("income",0)/1000:.1f}B/qtr')
    print(f'    Interest: {new_pmt/1000:.1f}B/qtr (was {data.get("interest_payment",0)/1000:.1f}B)')
    print(f'{"="*60}')

def main():
    print('=' * 60)
    print(f'  D4 REALISTIC ECONOMICS PATCHER v{VERSION}')
    print('  Yield curve + sovereign risk + debt maturity model')
    print('=' * 60)
    game_dir, save_dir, mods_dir = find_d4_paths()
    print(f'\n  Game:  {game_dir or "NOT FOUND"}')
    print(f'  Saves: {save_dir}')
    print(f'  Mods:  {mods_dir}')
    if not save_dir.exists():
        save_dir.mkdir(parents=True, exist_ok=True)
    save_file = save_dir / 'autosave.xml'
    # Install mod
    print(f'\n  Installing mod...')
    install_mod(mods_dir)
    # Patch simconfig
    if game_dir:
        print(f'  Patching simconfig...')
        patch_simconfig(game_dir)
    print(f'\n  WORKFLOW:')
    print(f'  1. Launch Democracy 4, enable "Realistic Economics Overhaul"')
    print(f'  2. Play a turn -> game autosaves')
    print(f'  3. Patcher patches autosave -> load it in-game')
    print(f'  4. Repeat from step 2')
    print(f'\n  Press Ctrl+C to stop')
    print('=' * 60)
    state = State(save_dir)
    state.load()
    last_mtime = state.last_mtime
    try:
        while True:
            if not save_file.exists():
                time.sleep(POLL_INTERVAL); continue
            mtime = os.path.getmtime(save_file)
            if mtime > last_mtime:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f'\n[{ts}] Save changed, processing...')
                try:
                    time.sleep(0.5)
                    data = parse_save(save_file)
                    turn = data.get('turn_count', 0)
                    if turn > state.last_turn:
                        blended, sov_risk, _ = compute_weighted_rate(state, data)
                        if patch_save(save_file, blended, sov_risk, data):
                            print_status(data, blended, sov_risk, state)
                            print('  >> PATCHED! Load autosave in-game. <<')
                        state.last_turn = turn
                        state.last_debt = data.get('total_debt', 0)
                        state.last_mtime = mtime
                        state.save()
                except Exception as e:
                    import traceback
                    print(f'  ERROR: {e}'); traceback.print_exc()
                last_mtime = os.path.getmtime(save_file)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print('\nPatcher stopped.'); state.save()

if __name__ == '__main__':
    main()
