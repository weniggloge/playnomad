#!/usr/bin/env python3
"""Generate 20 gear items per slot (8 common, 6 uncommon, 5 epic, 1 legendary).
Each slot's single legendary drops at 0.001%. Prints a JS GEAR object."""
import random
random.seed(42)

STATS = ['strength','knowledge','endurance','social','creativity','mindfulness']

# slot -> (icons, noun pool, primary stat bias)
SLOTS = {
  'head':  {'icons':['🧢','👒','⛑️','🎩','🪖','🎓','👓','🕶️'],
            'nouns':['Kappe','Helm','Haube','Hut','Maske','Kapuze','Reif','Visier'],
            'bias':['knowledge','creativity','mindfulness']},
  'chest': {'icons':['👕','🦺','🥼','🧥','🛡️','🥋','👔'],
            'nouns':['Wams','Panzer','Harnisch','Robe','Kürass','Brustplatte','Mantel'],
            'bias':['strength','endurance','social']},
  'legs':  {'icons':['👖','🩳','🦿','🥋'],
            'nouns':['Hose','Beinschienen','Beinlinge','Schurz','Hosen','Leggings'],
            'bias':['endurance','strength','creativity']},
  'feet':  {'icons':['🥾','👟','🩴','🥿','👢'],
            'nouns':['Stiefel','Schuhe','Sandalen','Treter','Schritte','Sohlen'],
            'bias':['endurance','mindfulness','creativity']},
  'acc':   {'icons':['💍','📿','🧿','⏱️','🔆','🎒','🪬','🔮'],
            'nouns':['Amulett','Ring','Kette','Talisman','Brosche','Anhänger','Siegel','Tasche'],
            'bias':['social','knowledge','creativity','mindfulness']},
}

ADJ = ['Leder','Eisen','Bronze','Stahl','Samt','Seiden','Gelehrten','Jäger','Späher','Runen',
       'Kristall','Schatten','Sturm','Sonnen','Mond','Wolfs','Adler','Nebel','Frost','Glut',
       'Silber','Gold','Smaragd','Rubin','Saphir','Obsidian','Elfen','Zwergen','Nomaden','Pilger']

LEG_NAMES = {
  'head':  ('Krone der Ewigkeit','👑'),
  'chest': ('Drachenherz-Panzer','🐲'),
  'legs':  ('Titanen-Beinschienen','🦿'),
  'feet':  ('Siebenmeilenstiefel','✨'),
  'acc':   ('Auge des Schicksals','🔆'),
}

# stat budget by rarity (total points distributed)
BUDGET = {'common':3,'uncommon':5,'epic':9,'legendary':17}
NSTATS = {'common':1,'uncommon':2,'epic':3,'legendary':4}
COUNTS = {'common':8,'uncommon':6,'epic':5,'legendary':1}

def pick_stats(slot, rarity):
    bias = SLOTS[slot]['bias']
    n = NSTATS[rarity]
    # build a weighted pool: bias stats more likely
    pool = bias*3 + STATS
    chosen=[]
    while len(chosen)<n:
        s=random.choice(pool)
        if s not in chosen: chosen.append(s)
    # distribute budget
    budget=BUDGET[rarity]
    vals={s:1 for s in chosen}
    budget-=len(chosen)
    while budget>0:
        vals[random.choice(chosen)]+=1
        budget-=1
    return vals

used_names=set()
def uniq_name(base):
    nm=base; k=2
    while nm in used_names:
        nm=f"{base} {'I'*k}"; k+=1
    used_names.add(nm); return nm

lines=[]
slug_idx=0
for slot,info in SLOTS.items():
    lines.append(f"  // ── {slot} ──")
    for rarity in ['common','uncommon','epic','legendary']:
        for j in range(COUNTS[rarity]):
            slug_idx+=1
            sid=f"{slot}_{rarity[0]}{j+1}"
            if rarity=='legendary':
                name,icon=LEG_NAMES[slot]
            else:
                adj=random.choice(ADJ); noun=random.choice(info['nouns'])
                name=uniq_name(f"{adj}{'' if adj.endswith(('s','n')) else ''}-{noun}".replace('-',' ' if False else '-'))
                name=f"{adj}-{noun}"
                name=uniq_name(name)
                icon=random.choice(info['icons'])
            vals=pick_stats(slot,rarity)
            b=','.join(f"{k}:{v}" for k,v in vals.items())
            lines.append(f"  {sid}: {{n:'{name}', slot:'{slot}', r:'{rarity}', i:'{icon}', b:{{{b}}}}},")

print("const GEAR = {")
print("\n".join(lines))
print("};")
