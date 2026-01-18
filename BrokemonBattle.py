#!/usr/bin/env python3
import curses
import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


# -------------------------
# Curses Color Manager
# -------------------------
class CursesColors:
    def __init__(self):
        self.color_pairs = {}
        self.init_colors()
    
    def init_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_BLUE, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_CYAN, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
            
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)
            curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_BLUE)

            self.color_pairs = {
                'red': curses.color_pair(1),
                'green': curses.color_pair(2), 
                'yellow': curses.color_pair(3),
                'blue': curses.color_pair(4),
                'magenta': curses.color_pair(5),
                'cyan': curses.color_pair(6),
                'white': curses.color_pair(7),
                
                'bright_red': curses.color_pair(1),
                'bright_green': curses.color_pair(2),
                'bright_yellow': curses.color_pair(3),
                'bright_blue': curses.color_pair(4),
                'bright_magenta': curses.color_pair(5),
                'bright_cyan': curses.color_pair(6),
                'bright_white': curses.color_pair(7),

                'black_on_green': curses.color_pair(8),
                'black_on_red': curses.color_pair(9),
                'black_on_yellow': curses.color_pair(10),
                'black_on_blue': curses.color_pair(11),

                'dim_white': curses.color_pair(7),
            }
    
    def get_color_attr(self, color_name: str):
        attr = 0
        
        if color_name.startswith('bright_'):
            attr |= curses.A_BOLD
            base_color_name = color_name[len('bright_'):]
            color_pair = self.color_pairs.get(base_color_name, curses.A_NORMAL)
        elif color_name.startswith('dim_'):
            attr |= curses.A_DIM
            base_color_name = color_name[len('dim_'):]
            color_pair = self.color_pairs.get(base_color_name, curses.A_NORMAL)
        else:
            color_pair = self.color_pairs.get(color_name, curses.A_NORMAL)
        
        return color_pair | attr

def curses_center_text(stdscr, text, y, color_attr=curses.A_NORMAL):
    """Centers text horizontally on the given y-coordinate in curses."""
    max_y, max_x = stdscr.getmaxyx()
    x = max(0, (max_x - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text, color_attr)
    except curses.error:
        pass

def curses_bar(stdscr, y, x, value, maximum, length=20, color_type="hp", color_mgr=None):
    """Draw a colored HP/energy bar using curses"""
    if maximum <= 0:
        ratio = 0
    else:
        ratio = value / maximum
    
    filled = int(ratio * length)
    empty = length - filled
    
    if color_type == "hp":
        if ratio > 0.5:
            color_name = 'bright_green'
        elif ratio > 0.25:
            color_name = 'bright_yellow'
        else:
            color_name = 'bright_red'
    elif color_type == "energy":
        color_name = 'cyan'
    else:
        color_name = 'white'
    
    color_attr = color_mgr.get_color_attr(color_name) if color_mgr else curses.A_NORMAL
    
    bar_str = "[" + "\u2588" * filled + "-" * empty + "]"
    max_y, max_x = stdscr.getmaxyx()
    if y < max_y and x + len(bar_str) < max_x:
        try:
            stdscr.addstr(y, x, bar_str, color_attr)
        except curses.error:
            pass

def draw_menu(stdscr, items, selected_idx, start_y, start_x, title="", color_mgr=None, show_arrow=True):
    """Draw a menu with arrow navigation support"""
    max_height, max_width = stdscr.getmaxyx()
    
    if title and color_mgr:
        title_attr = color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD
        stdscr.addstr(start_y, start_x, title, title_attr)
        start_y += 1
    
    for i, item in enumerate(items):
        y = start_y + i
        if y >= max_height - 2:
            break
            
        if i == selected_idx:
            attr = color_mgr.get_color_attr('black_on_yellow') | curses.A_BOLD if color_mgr else curses.A_REVERSE
            prefix = "\u25ba " if show_arrow else ""
            stdscr.addstr(y, start_x, f"{prefix}{item}", attr)
        else:
            attr = color_mgr.get_color_attr('white') if color_mgr else curses.A_NORMAL
            prefix = "  " if show_arrow else ""
            stdscr.addstr(y, start_x, f"{prefix}{item}", attr)

def get_menu_selection(stdscr, items, title="", start_y=2, start_x=2, color_mgr=None):
    """Handle arrow key navigation for menu selection"""
    selected_idx = 0
    max_height, max_width = stdscr.getmaxyx()
    
    while True:
        stdscr.clear()
        draw_menu(stdscr, items, selected_idx, start_y, start_x, title, color_mgr)
        
        if color_mgr:
            inst_attr = color_mgr.get_color_attr('bright_yellow')
            stdscr.addstr(max_height - 3, start_x, "Use \u2191\u2193 to navigate, ENTER to select", inst_attr)
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(items)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(items)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            return selected_idx
        elif key == ord('q'):
            return -1

def get_multi_selection(stdscr, items, min_selections, max_selections, title="", start_y=2, start_x=2, color_mgr=None):
    """Handle arrow key navigation for multiple item selection, with space to toggle."""
    selected_indices = []
    current_idx = 0
    max_height, max_width = stdscr.getmaxyx()

    while True:
        stdscr.clear()
        
        if title and color_mgr:
            title_attr = color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD
            stdscr.addstr(start_y, start_x, title, title_attr)
        
        display_y = start_y + (1 if title else 0)

        for i, item in enumerate(items):
            y = display_y + i
            if y >= max_height - 3:
                break
            
            prefix = "[ ]"
            attr = color_mgr.get_color_attr('white') if color_mgr else curses.A_NORMAL
            
            if i in selected_indices:
                prefix = "[X]"
            
            if i == current_idx:
                attr = (color_mgr.get_color_attr('black_on_yellow') | curses.A_BOLD) if color_mgr else curses.A_REVERSE
            
            display_text = f"{prefix} {item}"
            stdscr.addstr(y, start_x, display_text, attr)

        inst_y = max_height - 3
        if color_mgr:
            stdscr.addstr(inst_y, start_x, "Use \u2191\u2193 to navigate, SPACE to toggle, ENTER to confirm", color_mgr.get_color_attr('bright_yellow'))
            stdscr.addstr(inst_y + 1, start_x, f"Selected: {len(selected_indices)}/{max_selections}", color_mgr.get_color_attr('white'))
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(items)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(items)
        elif key == ord(' '):
            if current_idx in selected_indices:
                selected_indices.remove(current_idx)
            else:
                if len(selected_indices) < max_selections:
                    selected_indices.append(current_idx)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            if len(selected_indices) >= min_selections:
                return selected_indices
        elif key == ord('q'):
            return []

# -------------------------
# Data classes
# -------------------------
@dataclass
class Move:
    name: str
    power: int
    energy_cost: int
    category: str
    description: str = ""
    effect: Optional[Callable] = None

@dataclass
class Pokemon:
    name: str
    lvl: int
    max_hp: int
    atk: int
    dfns: int
    spd: int
    energy_max: int
    moves: List[Move]
    hp: int = field(init=False)
    energy: int = field(init=False)
    status: dict = field(default_factory=dict)
    ascii_art: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.hp = self.max_hp
        self.energy = self.energy_max

    def alive(self):
        return self.hp > 0

# -------------------------
# Pokemon roster (12+ total)
# -------------------------
cbroman = Pokemon(
    name="Cbroman",
    lvl=104,
    max_hp=1758,
    atk=1824,
    dfns=1102,
    spd=1387,
    energy_max=1406,
    moves=[
       Move("Lightning Rush", power=40, energy_cost=81, category="special",
             description="A decisive electric strike."),
       Move("Broman's Curse", power=0, energy_cost=38, category="status",
             description="Curse: lowers foe's defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_lower(stdscr, color_mgr, def_p, 2, 3)),
       Move("Thunder Shock", power=35, energy_cost=59, category="special-status",
             description="Paralyzing thunder attack.", effect=lambda stdscr, color_mgr, atk_p, def_p: apply_paralysis(stdscr, color_mgr, def_p, 4)),
       Move("Breezing Thunder Shivering", power=80, energy_cost=119, category="mystical-special",
             description="A huge mystical-special thunder blast.")
    ],
    ascii_art=[
        r"   ____  ",
        r"  / __ \ ",
        r" | 0\/0 |",
        r" | |--| |",
        r" | |--| |",
        r"  \____/ "
    ]
)

ishowpig = Pokemon(
    name="HappyPIG",
    lvl=115,
    max_hp=1943,
    atk=2016,
    dfns=1218,
    spd=1533,
    energy_max=1554,
    moves=[
       Move("Scream-Louder-n-Louder", power=30, energy_cost=89, category="special",
           description="Piercing scream."),
       Move("SnakeGambit Rush", power=60, energy_cost=42, category="mystical-special",
           description="Mystical venomous rush."),
       Move("HomelessShot", power=25, energy_cost=65, category="physical",
           description="Quick tongue strike."),
       Move("7 Goals", power=95, energy_cost=131, category="mystical-special",
           description="Powerful mystical goal-blast.")
    ],
    ascii_art=[
        r"  (\____/)",
        r"  /  0 0 \ ",
        r" (   *^*  )",
        r"  \  \_/  /",
        r"   \_____/"
    ]
)

emberfox = Pokemon(
    name="Emberfox",
    lvl=99,
    max_hp=1665,
    atk=1728,
    dfns=1044,
    spd=1314,
    energy_max=1332,
    moves=[
       Move("Ember Flick", power=90, energy_cost=77, category="special-status",
           description="Small burst of fire that may burn.", effect=lambda stdscr, color_mgr, atk_p, def_p: apply_burn(stdscr, color_mgr, def_p, 8, 5)),
       Move("Fox Dash", power=18, energy_cost=36, category="physical",
           description="Swift physical lunge."),
       Move("Heat Mirage", power=0, energy_cost=56, category="status",
           description="Raises speed.", effect=lambda stdscr, color_mgr, atk_p, def_p: speed_boost(stdscr, color_mgr, atk_p, 1, 3)),
       Move("Flame Nova", power=120, energy_cost=113, category="mystical-special",
           description="Big fire blast.")
    ],
    ascii_art=[
        r"   /\_/\ ",
        r"  ( o.o )",
        r"   > ^ < "
    ]
)

shelltron = Pokemon(
    name="Shelltron",
    lvl=121,
    max_hp=2035,
    atk=2112,
    dfns=1276,
    spd=1606,
    energy_max=1628,
    moves=[
       Move("Shell Bash", power=28, energy_cost=94, category="physical",
           description="Heavy shell strike."),
       Move("Aqua Reflex", power=25, energy_cost=44, category="special",
           description="Waterjolt."),
       Move("Fortify", power=0, energy_cost=68, category="status",
           description="Raises defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr, atk_p, 2, 3)),
       Move("Tidal Crush", power=95, energy_cost=138, category="mystical-special",
           description="Crushing water wave.",effect= lambda s,c,a,d: deal_percent_max_hp(s,c,d,70))
    ],
    ascii_art=[
        r"   _____ ",
        r"  / ____\ ",
        r" [| o o |]",
        r"  \_==_/ "
    ]
)

mossgoliath = Pokemon(
    name="Mossgoliath",
    lvl=107,
    max_hp=1813,
    atk=1882,
    dfns=1137,
    spd=1431,
    energy_max=1450,
    moves=[
       Move("Vine Crack", power=30, energy_cost=83, category="physical",
           description="Ropes of vine attack."),
       Move("Spore Haze", power=0, energy_cost=39, category="status",
           description="Poison over time.", effect=lambda stdscr, color_mgr, atk_p, def_p: apply_poison(stdscr, color_mgr, def_p, 6, 3)),
       Move("Stone Root", power=45, energy_cost=61, category="special",
           description="Rooted heavy hit."),
       Move("Earth Rend", power=85, energy_cost=123, category="mystical-special",
           description="Massive earth slam.")
    ],
    ascii_art=[
        r"   _____ ",
        r"  /     \ ",
        r" |  ^ ^  |",
        r" (  ---  )",
        r"  \_===_/ "
    ]
)

aquabyte = Pokemon(
    name="AquaByte",
    lvl=101,
    max_hp=1702,
    atk=1766,
    dfns=1067,
    spd=1343,
    energy_max=1362,
    moves=[
       Move("Bubble Punch", power=22, energy_cost=78, category="physical",
           description="Bubbly jab."),
       Move("Data Wave", power=40, energy_cost=37, category="special",
           description="Digital water wave."),
       Move("System Cleanse", power=0, energy_cost=57, category="status",
           description="Heals small HP.", effect=lambda stdscr, color_mgr, atk_p, def_p: heal(stdscr, color_mgr, atk_p, 40)),
       Move("Cyber Torrent", power=68, energy_cost=115, category="mystical-special",
           description="Cyber-infused tidal wave.")
    ],
    ascii_art=[
        r"    .--. ",
        r"  .'_\/_'.",
        r"  '. /\ .'",
        r"    \"\"  "
    ]
)

voltaicor = Pokemon(
    name="Voltaicor",
    lvl=114,
    max_hp=1924,
    atk=1997,
    dfns=1206,
    spd=1518,
    energy_max=1539,
    moves=[
       Move("Air Slice", power=110, energy_cost=88, category="physical",
           description="A razor-sharp aerial slash."),
       Move("Static Field", power=0, energy_cost=42, category="status",
           description="Paralyzes foes in an electric field.", effect=lambda s,c,a,d: apply_paralysis(s,c,d,5)),
       Move("Bleed Wind", power=90, energy_cost=64, category="special-status",
           description="Wind that causes bleeding.", effect=lambda s,c,a,d: apply_poison(s,c,d,60,5)),
       Move("Sky Verdict", power=210, energy_cost=130, category="mystical-special",
           description="Judgment from the skies.")
    ],
    ascii_art=[
        r"   /\\  ",
        r"  /  \\ ",
        r" |    | ",
        r"  \  /  ",
        r"   \/   "
    ]
)

shadowalker = Pokemon(
    name="Shadowalker",
    lvl=108,
    max_hp=1832,
    atk=1901,
    dfns=1148,
    spd=1445,
    energy_max=1465,
    moves=[
       Move("Shadow Sneak", power=40, energy_cost=84, category="physical",
           description="Attacks from the shadows."),
       Move("Evasion", power=0, energy_cost=40, category="status",
           description="Raises defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr, atk_p, 2, 3)),
       Move("Night Slash", power=72, energy_cost=61, category="physical",
           description="A slashing attack in the dark."),
       Move("Abyssal Blade", power=95, energy_cost=124, category="mystical-special",
           description="A blade from the abyss.")
    ],
    ascii_art=[
        r"   .---.  ",
        r"  /     \ ",
        r" | (o o) |",
        r"  \  ^  / ",
        r"   `---'  "
    ]
)

codezilla = Pokemon(
    name="CodeZilla",
    lvl=112,
    max_hp=1887,
    atk=1958,
    dfns=1583,
    spd=1489,
    energy_max=1510,
    moves=[
       Move("Syntax Error", power=255, energy_cost=187, category="special",
           description="A confusing error message.",effect=lambda stdscr, color_mgr, atk_p, def_p: deal_percent_max_hp(stdscr, color_mgr, def_p, 38)),
       Move("Git Push Force", power=390, energy_cost=141, category="physical",
           description="A forceful push to the repository."),
       Move("Spaghetti Code", power=0, energy_cost=63, category="status",
           description="Lowers foe's defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_lower(stdscr, color_mgr, def_p, 2, 3)),
       Move("Debug Strike", power=35, energy_cost=127, category="physical",
           description="A precise strike to fix a bug.")
    ],
    ascii_art=[
        r"    /_\   ",
        r"  <[0_0]> ",
        r"   / \" \  ",
        r"  / / \ \ "
    ]
)

chaddoge = Pokemon(
    name="ChadDoge",
    lvl=103,
    max_hp=1739,
    atk=1805,
    dfns=1090,
    spd=1372,
    energy_max=1391,
    moves=[
       Move("Much Wow", power=35, energy_cost=80, category="special",
           description="A powerful meme attack."),
       Move("HODL Defense", power=0, energy_cost=38, category="status",
           description="Raises defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr, atk_p, 2, 3)),
       Move("Moon Rocket", power=540, energy_cost=98, category="mystical-special",
           description="A rocket to the moon."),
       Move("Bork", power=210, energy_cost=118, category="physical",
           description="A simple bark.")
    ],
    ascii_art=[
        r"   / \\_  ",
        r"  (    C\___",
        r"  /         @",
        r" /   (_____/",
        r"/_____/   U"
    ]
)

gigapixel = Pokemon(
    name="GigaPixel",
    lvl=116,
    max_hp=1961,
    atk=2035,
    dfns=1230,
    spd=1548,
    energy_max=1569,
    moves=[
       Move("Resolution Drop", power=45, energy_cost=90, category="special",
           description="Lowers the resolution of the foe."),
       Move("Sprite Crash", power=40, energy_cost=42, category="physical",
           description="A crashing sprite attack."),
       Move("RGB Split", power=115, energy_cost=66, category="mystical-special",
           description="Splits the foe into RGB colors."),
       Move("Frame Skip", power=0, energy_cost=133, category="status",
           description="Raises speed.", effect=lambda stdscr, color_mgr, atk_p, def_p: speed_boost(stdscr, color_mgr, atk_p, 1, 3))
    ],
    ascii_art=[
        r"  [\u25a0 \u25a0 \u25a0] ",
        r"  [\u25a0 _ \u25a0] ",
        r"  /[\u25a0\u25a0\u25a0]\ ",
        r"   | | |  "
    ]
)

nullvoid = Pokemon(
    name="NullVoid",
    lvl=106,
    max_hp=1795,
    atk=1862,
    dfns=1125,
    spd=1416,
    energy_max=1436,
    moves=[
       Move("Blue Screen", power=110, energy_cost=82, category="mystical-special",
           description="A fatal error."),
       Move("Data Leak", power=80, energy_cost=39, category="special",
           description="Leaks the foe's data."),
       Move("Lag Spike", power=0, energy_cost=60, category="status",
           description="Lowers foe's speed.", effect=lambda stdscr, color_mgr, atk_p, def_p: speed_boost(stdscr, color_mgr, def_p, -1, 3)),
       Move("Ping", power=30, energy_cost=121, category="physical",
           description="A simple ping.")
    ],
    ascii_art=[
        r"  ?%#@!   ",
        r"  ERROR   ",
        r"  !@#$?   "
    ],
)

LoraValora = Pokemon(
    name="LoraValora",
    lvl=113,
    max_hp=1906,
    atk=1978,
    dfns=1195,
    spd=1504,
    energy_max=1524,
    moves=[
       Move("Valor Strike", power=490, energy_cost=88, category="mystical-special",
           description="A strike filled with valor."),
       Move("Lora's Blessing", power=0, energy_cost=41, category="status",
           description="Heals a large amount of HP.", effect=lambda stdscr, color_mgr, atk_p, def_p: heal(stdscr, color_mgr, atk_p, 750)),
       Move("Courageous Roar", power=60, energy_cost=64, category="special",
           description="A roar that boosts morale."),
       Move("Shield of Honor", power=0, energy_cost=129, category="status",
           description="Raises defense significantly.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr, atk_p, 108, 18))
    ],
    ascii_art=[
        r"   /\ /\   ",
        r"  { O O }  ",
        r"  \  v  /  ",
        r"  '-----'  ",
    ],
)

SuddyyModa = Pokemon(
    name="Suddymoodda",
    lvl=102,
    max_hp=2021,
    atk=2186,
    dfns=1999,
    spd=1358,
    energy_max=1176,
    moves=[
        Move("KillerStrike", power=380,energy_cost=79, category="special",description="A strike filled with blood",effect=lambda s,c,a,d:deal_percent_max_hp(s,c,d,40)),
        Move("Bloodlust", power=100, energy_cost=37, category="physical", description="A powerful bloodthirsty attack."),
        Move("Heal",power=0,energy_cost=58, category="status", description="Heals a large amount of HP.", effect=lambda stdscr, color_mgr, atk_p, def_p: heal(stdscr, color_mgr, atk_p, 100,)),
        Move("KILL",power=400,energy_cost=116,category="mystical-special", description="An attack that ends all life.")
    ],
    ascii_art=[
        r"   /\_/\    ",
        r"  ( ^.^ )   ",
        r"  (  -  )   ",
        r"   \___/    ",
        r"  /|   |\   ",
        r" (_|___|_)  ",
        r"   /   \    "
    ]
)

GigaCodes = Pokemon(
    name="GigaCodes",
    lvl=117,
    max_hp=2080,
    atk=2254,
    dfns=2001,
    spd=1562,
    energy_max=1284,
    moves=[
       Move("Code Blast", power=290, energy_cost=91, category="special",
           description="A powerful blast of code.",effect=lambda stdscr, color_mgr, atk_p, def_p: deal_percent_max_hp(stdscr, color_mgr, def_p, 40)),
       Move("Compile Error", power=0, energy_cost=43, category="status",
           description="Lowers foe's defense.", effect=lambda stdscr, color_mgr, atk_p, def_p: def_lower(stdscr, color_mgr, def_p, 125, 6)),
       Move("Binary Strike", power=190, energy_cost=66, category="physical",
           description="A precise binary attack."),
       Move("Algorithm Overload", power=370, energy_cost=194, category="status-special",
           description="Overloads the foe with complex algorithms. and heals the user's energy.", effect=lambda stdscr, color_mgr, atk_p, def_p: heal(stdscr, color_mgr, atk_p, 990)),
    ],
    ascii_art=[
    r"       _-----_       ",
    r"      /  1-0  \      ",
    r" |^|-|  {* *}  |-|^| ",
    r" | | |  ^---^  | | | ",
    r" | | \___0_1___/ | | ",
    r" <->     <->     <-> ",
    ]
)


CuteWings = Pokemon(
    name="CuteWings",
    lvl=105,
    max_hp=1976,
    atk=1999,
    dfns=1414,
    spd=1402,
    energy_max=1421,
    moves=[
        Move("Dusty Waves", power=80,energy_cost=82, category="special",description="it releases dust waves",effect= lambda s,c,a,d: deal_percent_max_hp(s,c,d,25)),
        Move("Feather Stake",power=50, energy_cost=38, category="status", description="Lowers foe's speed.", effect=lambda stdscr, color_mgr, atk_p, def_p: speed_boost(stdscr, color_mgr, def_p, 132, 4)),
        Move("Wing Power",power=120,energy_cost=60, category="physical-status", description="A powerful wing attack.",effect=lambda stdscr, color_mgr, atk_p, def_p: apply_poison(stdscr, color_mgr, def_p, 370, 5) ),
        Move("Will of the Wings",power=230,energy_cost=120,category="mystical-special-status", description="An attack that soars high with the power of wings.",effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr,atk_p, 180, 5))
   
    ],
    ascii_art=[
     r"      /\*****/\      ",
     r"     /  0   0  \     ",
     r"  /-|     ^     |-\  ",
     r" /\/\   \___/   /\/\ ",
     r" \|  \_________/  |/ ",
    ]
)


Atackker = Pokemon(
    name="Atackker",
    lvl=97,
    max_hp=1847,
    atk=2029,
    dfns=1132,
    spd=1299,
    energy_max=1317,
    moves=[
        Move("Attack Mode", power=150, energy_cost=76, category="physical", description="A powerful attack mode.",effect=lambda stdscr, color_mgr, atk_p, def_p: def_boost(stdscr, color_mgr, atk_p, 250,8)),
        Move("Power Boost", power=200, energy_cost=36, category="status-physical", description="Boosts attack power.", effect=lambda stdscr, color_mgr, atk_p, def_p: atk_boost(stdscr, color_mgr, atk_p, 300, 4)),
        Move("Energy Drain", power=120, energy_cost=55, category="special-status", description="Drains energy from the foe.",effect= lambda stdscr, color_mgr, atk_p, def_p: heal(stdscr, color_mgr, atk_p, 200)),
        Move("Final Strike", power=350, energy_cost=111, category="mystical-special", description="A devastating final strike.",effect=lambda stdscr, color_mgr, atk_p, def_p: bonus_damage_if_hp_above(stdscr, color_mgr, atk_p, def_p, 30))
    ],
    ascii_art=[
        r"   /-----\   ",
        r"  |  * *  |  ",
        r"  |   -   |  ",
        r" /|_______|\ ",
        r"<_|_O___O_|_>",
        r"  \_______/   "
    ]
)

HexaBreak = Pokemon(
    name="HexaBreak",
    lvl=110,
    max_hp=1850,
    atk=1920,
    dfns=1160,
    spd=1460,
    energy_max=1480,
    moves=[
        Move(
            "Overflow Strike",
            power=180,
            energy_cost=85,
            category="physical",
            description="A brutal strike that scales with the foe's max HP.",
            effect=lambda stdscr, color_mgr, atk_p, def_p: deal_percent_max_hp(stdscr, color_mgr, def_p, 36)
        ),
        Move(
            "Memory Corruption",
            power=200,
            energy_cost=40,
            category="status-special",
            description="Corrupts memory, lowering foe's defense.",
            effect=lambda stdscr, color_mgr, atk_p, def_p: def_lower(stdscr, color_mgr, def_p, 42, 4)
        ),
        Move(
            "ClockCycle Slash",
            power=95,
            energy_cost=62,
            category="physical",
            description="If the user is faster, then the opposition tastes poison!.",
            effect=lambda stdscr, color_mgr, atk_p, def_p: apply_poison(stdscr, color_mgr, def_p, 120, 7)
        ),
        Move(
            "Kernel Panic",
            power=220,
            energy_cost=125,
            category="mystical-special",
            description="Deals massive damage if the foe has high HP.",
            effect=lambda stdscr, color_mgr, atk_p, def_p: bonus_damage_if_hp_above(stdscr, color_mgr, atk_p, def_p, 20)
        )
    ],
    ascii_art=[
        r"    /=====\   ",
        r"   |  X  X |  ",
        r"   |  ---  |  ",
        r"  /|_______|\ ",
        r" <_|_0___1_|_>",
        r"   \------/   "
    ]
)

SkyRazor = Pokemon(
    name="SkyRazor",
    lvl=114,
    max_hp=1924,
    atk=1997,
    dfns=1206,
    spd=1518,
    energy_max=1539,
    moves=[
       Move("Lightning Strike", power=110, energy_cost=88, category="physical-status",
           description="A shocking aerial slash.", effect=lambda s,c,a,d: apply_paralysis(s,c,d,3)),
       Move("Pressure Dive", power=0, energy_cost=42, category="status",
           description="Lowers foe defense.", effect=lambda s,c,a,d: def_lower(s,c,d,40,4)),
       Move("Bleed Wind", power=90, energy_cost=64, category="special-status",
           description="Wind that causes bleeding.", effect=lambda s,c,a,d: apply_poison(s,c,d,60,4)),
       Move("Sky Verdict", power=210, energy_cost=130, category="mystical-special",
           description="Judgment from the skies.")
    ],
    ascii_art=[
        r"     /\___/\     ",
        r"    (  o   o )   ",
        r"  /-|     ^  |-\ ",
        r"  \_\^^^^^^^^/_/ ",
        r"      /\/\/\     "
    ]
)

BronBull = Pokemon(
    name="BronBULL",
    lvl=110,
    max_hp=2200,
    atk=2120,
    dfns=2160,
    spd=1460,
    energy_max=1180,
    moves=[
        Move("Steel Claw OF the WRATH", power=100, energy_cost=85, category="physical-status",
             description="Hard metallic Claw.",effect=lambda s,c,a,d: heal(s,c,d, 340)),
        Move("Guard Stance", power=0, energy_cost=40, category="status",
             description="Greatly raises defense.", effect=lambda s,c,a,d: def_boost(s,c,a,90,7)),
        Move("Flaming Breath", power=100, energy_cost=62, category="special-status",
             description="Fiery breath that burns foes.", effect=lambda s,c,a,d: apply_burn(s,c,d,12,6)),
        Move("Devestating Raid", power=220, energy_cost=125, category="mystical-special-status",
             description="A devastating metallic storm.",effect=lambda s,c,a,d: deal_percent_max_hp(s,c,d,50))
    ],
    ascii_art=[
    r"   /\  /\    ",
    r"  /--\/--\   ",
    r"  | *__* |   ",
    r"  | /^^\ |   ",
    r"  ||V--V||   ",
    r"  |------|   ",
    r"  \******/   "
    ]
)

MetaGross = Pokemon(
    name="MetaGross",
    lvl=200,
    max_hp=2458,
    atk=2570,
    dfns=2333,
    spd=1466,
    energy_max=1790,
    moves=[
        Move("Meteor mash",power=230, energy_cost=120, category="physical",description="Avg metagross attack"),
        Move("Bullet Punch",power=180,energy_cost=100,category="physical-status",description="Again a avg atk",effect=lambda s,c,a,d: apply_paralysis(s,c,d,3)),
        Move("Hyper Beam",power=280,energy_cost=200,category="special-status",description="A power beam",effect=lambda s,c,a,d: apply_burn(s,c,d,90,5)),
        Move("Zen Headbutt",power=140,energy_cost=100,category="special-physical",description="A powerful psyheatbutt",effect=lambda s,c,a,d: deal_percent_max_hp(s,c,d,45))
    ],
    ascii_art=[
r"       --------       ", 
r"  A--/--\\--//--\--A  ",
r" |^|[ [0]\\//[0] ]|^| ",
r" [M] \   //\\   / [M] ",
r" [M]  \_//__\\_/  [M] ",
r"\[0]/  '-'  '-'  \[0]/"
    ]


)




ROSTER = [cbroman, ishowpig, emberfox, shelltron, mossgoliath, aquabyte, 
          voltaicor, shadowalker, codezilla, chaddoge, gigapixel, nullvoid,LoraValora,SuddyyModa,GigaCodes,CuteWings,HexaBreak,Atackker,SkyRazor,BronBull,MetaGross]

# -------------------------
# Statistics System
# -------------------------
STATS_FILE = "brokemon_stats.json"

def load_stats():
    """Load statistics from file or create new ones"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Create default stats for all Brokemon
    default_stats = {}
    for pokemon in ROSTER:
        default_stats[pokemon.name] = {
            "wins": 0,
            "losses": 0,
            "matches": 0,
            "win_percentage": 0.0
        }
    
    return default_stats

def save_stats(stats):
    """Save statistics to file"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

def update_stats(stats, winner_pokemon, loser_pokemon):
    """Update statistics after a match"""
    # Update winner
    if winner_pokemon.name not in stats:
        stats[winner_pokemon.name] = {"wins": 0, "losses": 0, "matches": 0, "win_percentage": 0.0}
    
    stats[winner_pokemon.name]["wins"] += 1
    stats[winner_pokemon.name]["matches"] += 1
    
    # Update loser
    if loser_pokemon.name not in stats:
        stats[loser_pokemon.name] = {"wins": 0, "losses": 0, "matches": 0, "win_percentage": 0.0}
    
    stats[loser_pokemon.name]["losses"] += 1
    stats[loser_pokemon.name]["matches"] += 1
    
    # Calculate win percentages
    for pokemon_name in stats:
        if stats[pokemon_name]["matches"] > 0:
            stats[pokemon_name]["win_percentage"] = round(
                (stats[pokemon_name]["wins"] / stats[pokemon_name]["matches"]) * 100, 2
            )
        else:
            stats[pokemon_name]["win_percentage"] = 0.0

def display_stats_checker(stdscr, color_mgr):
    """Display beautiful statistics for all Brokemon"""
    while True:
        stats = load_stats()
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Beautiful header
        header_art = [
            "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557",
            "\u2551                    [STATS] BROKEMON STATS [STATS]                    \u2551",
            "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
        ]
        
        start_y = 2
        for i, line in enumerate(header_art):
            if max_x >= len(line):
                x_pos = (max_x - len(line)) // 2
                stdscr.addstr(start_y + i, x_pos, line, color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD)
        
        # Sort stats by win rate (descending) then by name
        sorted_stats = sorted(stats.items(), key=lambda x: (-x[1]['win_percentage'], x[0]))
        
        y_pos = start_y + len(header_art) + 2
        
        # Column headers
        header_line = "\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510"
        stdscr.addstr(y_pos, (max_x - len(header_line)) // 2, header_line, color_mgr.get_color_attr('white'))
        y_pos += 1
        
        col_headers = "\u2502 Name                \u2502 Wins \u2502 Losses \u2502 Matches \u2502 Win %     \u2502"
        stdscr.addstr(y_pos, (max_x - len(col_headers)) // 2, col_headers, color_mgr.get_color_attr('bright_yellow') | curses.A_BOLD)
        y_pos += 1
        
        separator = "\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524"
        stdscr.addstr(y_pos, (max_x - len(separator)) // 2, separator, color_mgr.get_color_attr('white'))
        y_pos += 1
        
        # Stats data
        for name, stat in sorted_stats:
            if y_pos >= max_y - 4:  # Leave space for footer
                break
                
            # Color coding based on performance
            if stat['win_percentage'] >= 70:
                name_color = 'bright_green'
            elif stat['win_percentage'] >= 50:
                name_color = 'bright_yellow'
            elif stat['win_percentage'] > 0:
                name_color = 'bright_red'
            else:
                name_color = 'dim_white'
            
            # Format the line
            name_formatted = f"{name[:19]:19}"
            wins_formatted = f"{stat['wins']:4}"
            losses_formatted = f"{stat['losses']:6}"
            matches_formatted = f"{stat['matches']:7}"
            win_rate_formatted = f"{stat['win_percentage']:7.1f}%"
            
            line = f"\u2502 {name_formatted} \u2502 {wins_formatted} \u2502 {losses_formatted} \u2502 {matches_formatted} \u2502 {win_rate_formatted} \u2502"
            
            x_pos = (max_x - len(line)) // 2
            
            # Draw the vertical borders
            stdscr.addstr(y_pos, x_pos, "\u2502", color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 22, "\u2502", color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 29, "\u2502", color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 38, "\u2502", color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 48, "\u2502", color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 59, "\u2502", color_mgr.get_color_attr('white'))
            
            # Draw the actual data with colors
            stdscr.addstr(y_pos, x_pos + 2, name_formatted, color_mgr.get_color_attr(name_color))
            stdscr.addstr(y_pos, x_pos + 24, wins_formatted, color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 31, losses_formatted, color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 40, matches_formatted, color_mgr.get_color_attr('white'))
            stdscr.addstr(y_pos, x_pos + 50, win_rate_formatted, color_mgr.get_color_attr(name_color))
            
            y_pos += 1
        
        # Bottom border
        bottom_line = "\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518"
        if y_pos < max_y - 2:
            stdscr.addstr(y_pos, (max_x - len(bottom_line)) // 2, bottom_line, color_mgr.get_color_attr('white'))
            y_pos += 1
        
        # Footer with legend
        y_pos += 1
        if y_pos < max_y - 2:
            legend = "Legend: [GREEN] Excellent (70%+) [YELLOW] Good (50-69%) [RED] Poor (1-49%) [WHITE] No battles (0%)"
            stdscr.addstr(y_pos, (max_x - len(legend)) // 2, legend, color_mgr.get_color_attr('bright_cyan'))
        
        y_pos += 1
        if y_pos < max_y - 1:
            instructions = "Press 'r' to refresh | 'q' to return to main menu"
            stdscr.addstr(y_pos, (max_x - len(instructions)) // 2, instructions, color_mgr.get_color_attr('bright_yellow'))
        
        stdscr.refresh()
        
        # Handle input
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('r') or key == ord('R'):
            continue  # Refresh stats
        else:
            break  # Any other key also exits

def display_match_stats(stdscr, color_mgr, player1_team, player2_team, winner, player_num):
    """Display statistics at the end of a match"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    # Title
    curses_center_text(stdscr, "[TROPHY] MATCH COMPLETE [TROPHY]", 1, 
                      color_mgr.get_color_attr('bright_yellow') | curses.A_BOLD)
    
    # Winner announcement
    if winner:
        curses_center_text(stdscr, f"Player {player_num} Wins with {winner.name}!", 3,
                          color_mgr.get_color_attr('bright_green') | curses.A_BOLD)
    else:
        curses_center_text(stdscr, "Draw Match!", 3,
                          color_mgr.get_color_attr('bright_yellow') | curses.A_BOLD)
        return
    
    # Load current stats
    stats = load_stats()
    
    y_pos = 6
    curses_center_text(stdscr, "BROKEMON STATISTICS", y_pos,
                      color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD)
    
    y_pos += 2
    curses_center_text(stdscr, f"{winner.name} Statistics:", y_pos,
                      color_mgr.get_color_attr('bright_green'))
    
    y_pos += 1
    winner_stats = stats.get(winner.name, {"wins": 0, "losses": 0, "matches": 0, "win_percentage": 0.0})
    curses_center_text(stdscr, f"Wins: {winner_stats['wins']} | Losses: {winner_stats['losses']} | Matches: {winner_stats['matches']}", y_pos,
                      color_mgr.get_color_attr('white'))
    
    y_pos += 1
    curses_center_text(stdscr, f"Win Rate: {winner_stats['win_percentage']}%", y_pos,
                      color_mgr.get_color_attr('bright_green'))
    
    y_pos += 3
    curses_center_text(stdscr, "Top 5 Brokemon by Win Rate:", y_pos,
                      color_mgr.get_color_attr('bright_cyan'))
    
    # Sort by win rate and display top 5
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['win_percentage'], reverse=True)[:5]
    y_pos += 1
    
    for i, (name, stat) in enumerate(sorted_stats):
        if stat['matches'] > 0:  # Only show Brokemon that have actually fought
            text = f"{i+1}. {name}: {stat['win_percentage']}% ({stat['wins']}W/{stat['losses']}L)"
            curses_center_text(stdscr, text, y_pos + i, color_mgr.get_color_attr('white'))
    
    y_pos += 6
    curses_center_text(stdscr, "Press any key to continue...", y_pos,
                      color_mgr.get_color_attr('bright_yellow'))
    
    stdscr.refresh()
    stdscr.getch()

# -------------------------
# Effects / status functions
# -------------------------
def def_lower(stdscr, color_mgr, pokemon: Pokemon, amount: int, turns: int):
    key = 'def_down'
    pokemon.status[key] = pokemon.status.get(key, 0) + turns
    pokemon.status.setdefault('def_down_amt', 0)
    pokemon.status['def_down_amt'] = pokemon.status.get('def_down_amt', 0) + amount

def def_boost(stdscr, color_mgr, pokemon: Pokemon, amount: int, turns: int):
    key = 'def_up'
    pokemon.status[key] = pokemon.status.get(key, 0) + turns
    pokemon.status.setdefault('def_up_amt', 0)
    pokemon.status['def_up_amt'] = pokemon.status.get('def_up_amt', 0) + amount

def speed_boost(stdscr, color_mgr, pokemon: Pokemon, amount: int, turns: int):
    if amount > 0:
        pokemon.status['spd_up'] = pokemon.status.get('spd_up', 0) + turns
        pokemon.status.setdefault('spd_up_amt', 0)
        pokemon.status['spd_up_amt'] = pokemon.status.get('spd_up_amt', 0) + amount
    else:
        pokemon.status['spd_down'] = pokemon.status.get('spd_down', 0) + turns
        pokemon.status.setdefault('spd_down_amt', 0)
        pokemon.status['spd_down_amt'] = pokemon.status.get('spd_down_amt', 0) + abs(amount)

def atk_boost(stdscr, color_mgr, pokemon: Pokemon, amount: int, turns: int):
    key = 'atk_up'
    pokemon.status[key] = pokemon.status.get(key, 0) + turns
    pokemon.status.setdefault('atk_up_amt', 0)
    pokemon.status['atk_up_amt'] = pokemon.status.get('atk_up_amt', 0) + amount

def apply_poison(stdscr, color_mgr, target: Pokemon, dmg_per_turn: int, turns: int):
    target.status['poison'] = {'dmg': dmg_per_turn, 'turns': turns}

def apply_paralysis(stdscr, color_mgr, target: Pokemon, turns: int):
    target.status['paralysis'] = {'turns': turns}

def apply_burn(stdscr, color_mgr, target: Pokemon, dmg_per_turn: int, turns: int):
    target.status['burn'] = {'dmg': dmg_per_turn, 'turns': turns}

def heal(stdscr, color_mgr, pokemon: Pokemon, amount: int):
    old = pokemon.hp
    pokemon.hp = min(pokemon.max_hp, pokemon.hp + amount)
def deal_percent_max_hp(stdscr, color_mgr, target, percent):
    """
    Deals damage equal to a percentage of the target's max HP.
    """
    dmg = int(target.max_hp * (percent / 100))
    target.hp = max(0, target.hp - dmg)

    stdscr.addstr(
        f"\n{target.name} lost {dmg} HP due to HP overflow!",
        color_mgr.get_color_attr('bright_red')
    )
    stdscr.refresh()
    time.sleep(1.6)


def double_hit_if_faster(stdscr, color_mgr, attacker, defender):
    """
    Returns the number of hits based on speed comparison.
    """
    return 2 if attacker.spd > defender.spd else 1


def bonus_damage_if_hp_above(stdscr, color_mgr, attacker, defender, threshold=70):
    """
    Returns damage multiplier based on defender HP percentage.
    """
    hp_percent = (defender.hp / defender.max_hp) * 100
    if hp_percent >= threshold:
        return 2  # Double damage
    return 1  # Normal damage

# -------------------------
# Damage formula
# -------------------------
def compute_damage(attacker: Pokemon, defender: Pokemon, move: Move) -> Tuple[int, bool]:
    base = move.power
    if base <= 0:
        return 0, False

    def_effective = defender.dfns
    if defender.status.get('def_down', 0) > 0:
        def_effective = max(1, def_effective - defender.status.get('def_down_amt', 0))
    if defender.status.get('def_up', 0) > 0:
        def_effective = def_effective + defender.status.get('def_up_amt', 0)

    atk_effective = attacker.atk
    if attacker.status.get('atk_up', 0) > 0:
        atk_effective += attacker.status.get('atk_up_amt', 0)

    ratio = atk_effective / max(1, def_effective)
    raw = base * ratio
    raw *= (1 + (attacker.lvl - defender.lvl) * 0.005)
    variance = random.uniform(0.85, 1.15)
    dmg = int(max(1, raw * variance))
    
    crit = random.random() < 0.07
    if crit:
        dmg = int(dmg * 1.8)
        
    return dmg, crit

# -------------------------
# COMPLETE BATTLE UI - ALWAYS VISIBLE
# -------------------------
def draw_battle_ui(stdscr, color_mgr, player1_team: List[Pokemon], player2_team: List[Pokemon], 
                   p1_idx=0, p2_idx=0, message="", current_player=1):
    """Draw complete battle UI that's always visible"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    # Draw border
    stdscr.box()
    
    # Title
    curses_center_text(stdscr, "\u2694 TERMINAL POK\u00c9 BATTLE \u2694", 0, color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD)
    
    # Player 2 (TOP - OPPONENT)
    opponent = player2_team[p2_idx]
    opponent_color = 'green' if opponent.alive() else 'red'
    
    # Opponent info at top
    stdscr.addstr(2, 2, "PLAYER 2: ", color_mgr.get_color_attr('bright_magenta'))
    stdscr.addstr(2, 12, f"{opponent.name}", color_mgr.get_color_attr(opponent_color) | curses.A_BOLD)
    stdscr.addstr(2, 12 + len(opponent.name) + 1, f"LVL:{opponent.lvl}", color_mgr.get_color_attr('dim_white'))
    
    # Opponent HP bar
    stdscr.addstr(3, 2, "HP ", color_mgr.get_color_attr('red'))
    curses_bar(stdscr, 3, 5, opponent.hp, opponent.max_hp, color_type='hp', color_mgr=color_mgr)
    stdscr.addstr(3, 28, f"{opponent.hp}/{opponent.max_hp}", color_mgr.get_color_attr('white'))
    
    # Opponent Energy bar
    stdscr.addstr(4, 2, "EN ", color_mgr.get_color_attr('cyan'))
    curses_bar(stdscr, 4, 5, opponent.energy, opponent.energy_max, color_type='energy', color_mgr=color_mgr)
    stdscr.addstr(4, 28, f"{opponent.energy}/{opponent.energy_max}", color_mgr.get_color_attr('white'))
    
    # Opponent ASCII art (top right)
    if opponent.ascii_art:
        art_y = 2
        art_x = max_x - 20
        for i, line in enumerate(opponent.ascii_art):
            if art_y + i < max_y // 2:
                stdscr.addstr(art_y + i, art_x, line, color_mgr.get_color_attr('white'))
    
    # Separator line
    sep_y = max_y // 2 - 1
    for x in range(2, max_x - 2):
        try:
            stdscr.addch(sep_y, x, '\u2500', color_mgr.get_color_attr('dim_white'))
        except:
            pass
    
    # Player 1 (BOTTOM - PLAYER)
    player = player1_team[p1_idx]
    player_color = 'green' if player.alive() else 'red'
    
    # Player info at bottom
    player_y = sep_y + 2
    stdscr.addstr(player_y, 2, "PLAYER 1: ", color_mgr.get_color_attr('bright_blue'))
    stdscr.addstr(player_y, 12, f"{player.name}", color_mgr.get_color_attr(player_color) | curses.A_BOLD)
    stdscr.addstr(player_y, 12 + len(player.name) + 1, f"LVL:{player.lvl}", color_mgr.get_color_attr('dim_white'))
    
    # Player HP bar
    stdscr.addstr(player_y + 1, 2, "HP ", color_mgr.get_color_attr('red'))
    curses_bar(stdscr, player_y + 1, 5, player.hp, player.max_hp, color_type='hp', color_mgr=color_mgr)
    stdscr.addstr(player_y + 1, 28, f"{player.hp}/{player.max_hp}", color_mgr.get_color_attr('white'))
    
    # Player Energy bar
    stdscr.addstr(player_y + 2, 2, "EN ", color_mgr.get_color_attr('cyan'))
    curses_bar(stdscr, player_y + 2, 5, player.energy, player.energy_max, color_type='energy', color_mgr=color_mgr)
    stdscr.addstr(player_y + 2, 28, f"{player.energy}/{player.energy_max}", color_mgr.get_color_attr('white'))
    
    # Player ASCII art (bottom right)
    if player.ascii_art:
        art_y = player_y
        art_x = max_x - 20
        for i, line in enumerate(player.ascii_art):
            if art_y + i < max_y - 2:
                stdscr.addstr(art_y + i, art_x, line, color_mgr.get_color_attr('white'))
    
    # Status effects
    if player.status:
        status_y = player_y + 4
        status_text = []
        for k, v in player.status.items():
            if not k.endswith('_amt') and isinstance(v, int) and v > 0:
                status_text.append(f"{k.replace('_', ' ').title()}: {v}T")
            elif k == 'poison' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Poison: {v['turns']}T")
            elif k == 'burn' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Burn: {v['turns']}T")
            elif k == 'paralysis' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Paralysis: {v['turns']}T")
        if status_text and status_y < max_y - 2:
            stdscr.addstr(status_y, 2, "Status: " + " | ".join(status_text[:3]), color_mgr.get_color_attr('yellow'))
    
    if opponent.status:
        status_y = 6
        status_text = []
        for k, v in opponent.status.items():
            if not k.endswith('_amt') and isinstance(v, int) and v > 0:
                status_text.append(f"{k.replace('_', ' ').title()}: {v}T")
            elif k == 'poison' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Poison: {v['turns']}T")
            elif k == 'burn' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Burn: {v['turns']}T")
            elif k == 'paralysis' and isinstance(v, dict) and v.get('turns', 0) > 0:
                status_text.append(f"Paralysis: {v['turns']}T")
        if status_text:
            stdscr.addstr(status_y, 2, "Status: " + " | ".join(status_text[:3]), color_mgr.get_color_attr('yellow'))
    
    # Battle message area
    if message:
        msg_y = sep_y - 2
        if msg_y > 6:  # Make sure we don't overlap with opponent status
            msg_lines = message.split('\n')
            for i, line in enumerate(msg_lines[:3]):  # Show max 3 lines
                if msg_y - i >= 7:
                    stdscr.addstr(msg_y - i, 2, line[:max_x - 4], color_mgr.get_color_attr('bright_yellow'))
    
    # Turn indicator
    if current_player == 1:
        turn_text = "\u25b6 PLAYER 1'S TURN"
        turn_x = 2
        turn_y = max_y - 1
        stdscr.addstr(turn_y, turn_x, turn_text, color_mgr.get_color_attr('bright_green') | curses.A_BOLD)
    else:
        turn_text = "\u25b6 PLAYER 2'S TURN"
        turn_x = max_x - len(turn_text) - 2
        turn_y = 1
        stdscr.addstr(turn_y, turn_x, turn_text, color_mgr.get_color_attr('bright_magenta') | curses.A_BOLD)
    
    stdscr.refresh()

# -------------------------
# Battle System for 2-PLAYER PVP
# -------------------------
def get_player_action(stdscr, color_mgr, player_team, opponent_team, 
                     player_idx, opponent_idx, current_player, can_switch=True):
    """Get action from current player with UI always visible"""
    max_y, max_x = stdscr.getmaxyx()
    selected_idx = 0
    
    # Show action menu
    actions = ["Attack", "Pass"]
    if can_switch and len([p for p in player_team if p.alive()]) > 1:
        actions.insert(1, "Switch Pokemon")
    
    menu_y = max_y - len(actions) - 4
    
    while True:
        draw_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                      player_idx, opponent_idx, 
                      f"Player {current_player}'s Turn", current_player)
        
        # Draw action menu
        draw_menu(stdscr, actions, selected_idx, menu_y, 2, 
                 f"Player {current_player} - Choose action:", color_mgr)
        
        # Instructions
        stdscr.addstr(max_y - 2, 2, "\u2191\u2193: Navigate  ENTER: Select", color_mgr.get_color_attr('dim_white'))
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(actions)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(actions)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            action = actions[selected_idx]
            
            if action == "Attack":
                # Show ALL 4 moves
                move_selected = 0
                player_pokemon = player_team[player_idx]
                move_names = []
                move_objects = []
                
                # Display all 4 moves
                for move in player_pokemon.moves:
                    energy_status = "\u2713" if move.energy_cost <= player_pokemon.energy else "\u2717"
                    # Make sure we show the full move info
                    move_name = f"{move.name}"
                    move_power = f"Pow:{move.power}" if move.power > 0 else "Status"
                    move_info = f"{move_name} ({move_power}|EN:{move.energy_cost}{energy_status})"
                    move_names.append(move_info)
                    move_objects.append(move)
                
                # Make sure we have exactly 4 moves
                if len(move_names) < 4:
                    # Add placeholder if needed (shouldn't happen with our roster)
                    for i in range(len(move_names), 4):
                        move_names.append(f"Move {i+1} (No data)")
                        move_objects.append(Move("Empty", 0, 0, "status"))
                
                while True:
                    draw_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                                  player_idx, opponent_idx, 
                                  "Choose a move:", current_player)
                    
                    # Draw the moves menu with proper positioning
                    draw_menu(stdscr, move_names, move_selected, menu_y, 2, 
                             f"{player_pokemon.name}'s moves (4 total):", color_mgr)
                     
                    stdscr.addstr(max_y - 2, 2, "\u2191\u2193: Navigate  ENTER: Select  q: Back", 
                                 color_mgr.get_color_attr('dim_white'))
                    
                    key = stdscr.getch()
                    
                    if key == curses.KEY_UP:
                        move_selected = (move_selected - 1) % len(move_names)
                    elif key == curses.KEY_DOWN:
                        move_selected = (move_selected + 1) % len(move_names)
                    elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
                        # Make sure we don't select a placeholder move
                        if move_objects[move_selected].name != "Empty":
                            return "attack", move_objects[move_selected], player_idx
                        else:
                            # Show error for placeholder
                            draw_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                                          player_idx, opponent_idx, 
                                          "Invalid move! Please select a valid move.", current_player)
                            stdscr.refresh()
                            time.sleep(1)
                    elif key == ord('q'):
                        break
                        
            elif action == "Switch Pokemon":
                # Show available Pok\u00e9mon to switch to
                options = [i for i, p in enumerate(player_team) 
                          if p.alive() and i != player_idx]
                
                if not options:
                    continue
                
                switch_items = [f"{player_team[i].name} (HP: {player_team[i].hp}/{player_team[i].max_hp})" 
                               for i in options]
                switch_selected = 0
                
                while True:
                    draw_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                                  player_idx, opponent_idx, 
                                  "Choose Pok\u00e9mon to switch to:", current_player)
                    
                    draw_menu(stdscr, switch_items, switch_selected, menu_y, 2, 
                             "Available Pok\u00e9mon:", color_mgr)
                     
                    stdscr.addstr(max_y - 2, 2, "\u2191\u2193: Navigate  ENTER: Select  q: Back", 
                                 color_mgr.get_color_attr('dim_white'))
                    
                    key = stdscr.getch()
                    
                    if key == curses.KEY_UP:
                        switch_selected = (switch_selected - 1) % len(switch_items)
                    elif key == curses.KEY_DOWN:
                        switch_selected = (switch_selected + 1) % len(switch_items)
                    elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
                        new_idx = options[switch_selected]
                        return "switch", None, new_idx
                    elif key == ord('q'):
                        break
                        
            elif action == "Pass":
                return "pass", None, player_idx
                
        elif key == ord('q'):
            return "pass", None, player_idx

def animate_ascii_pokemon(stdscr, color_mgr, pokemon: Pokemon, x: int, y: int, animation_type="idle"):
    """Animate ASCII Pokemon with different states"""
    if not pokemon.ascii_art:
        return
    
    # Apply animation effects based on type
    animated_art = []
    for line in pokemon.ascii_art:
        if animation_type == "damage":
            # Replace some characters with damage indicators
            animated_line = line.replace('O', 'X').replace('0', 'x').replace('@', '#')
        elif animation_type == "heal":
            # Add healing sparkles
            animated_line = line + " +"
        elif animation_type == "attack":
            # Add attack effect
            animated_line = "!" + line
        else:
            animated_line = line
        
        animated_art.append(animated_line)
    
    # Display the animated art
    for i, line in enumerate(animated_art):
        # Choose color based on animation
        if animation_type == "damage":
            color_attr = color_mgr.get_color_attr('bright_red')
        elif animation_type == "heal":
            color_attr = color_mgr.get_color_attr('bright_green')
        elif animation_type == "attack":
            color_attr = color_mgr.get_color_attr('bright_yellow')
        else:
            color_attr = color_mgr.get_color_attr('white')
        
        try:
            stdscr.addstr(y + i, x, line, color_attr)
        except curses.error:
            pass

def animate_hp_drain(stdscr, color_mgr, p1_team, p2_team, p1_idx, p2_idx, target_pokemon, damage, current_player, message):
    """Animates the HP bar draining with a more realistic effect."""
    start_hp = target_pokemon.hp
    end_hp = max(0, start_hp - damage)
    hp_lost = start_hp - end_hp

    if hp_lost <= 0:
        # If there's no HP to lose, just show the message and return
        draw_battle_ui(stdscr, color_mgr, p1_team, p2_team, p1_idx, p2_idx, message, current_player)
        stdscr.refresh()
        time.sleep(1)
        return
    
    duration = 0.7
    frames = 40
    interval = duration / frames

    for i in range(frames + 1):
        progress = i / frames
        ease_progress = 1 - (1 - progress) ** 2
        
        current_drain = int(hp_lost * ease_progress)
        display_hp = start_hp - current_drain
        
        # Ensure HP doesn't go below the calculated end_hp
        target_pokemon.hp = max(end_hp, display_hp)
        
        # Redraw the UI in each frame
        draw_battle_ui(stdscr, color_mgr, p1_team, p2_team, p1_idx, p2_idx, message, current_player)
        stdscr.refresh()
        time.sleep(interval)

    # Ensure final state is accurate
    target_pokemon.hp = end_hp
    draw_battle_ui(stdscr, color_mgr, p1_team, p2_team, p1_idx, p2_idx, message, current_player)
    
    curses.beep()
    stdscr.refresh()
    time.sleep(0.3)

def perform_move(stdscr, color_mgr, attacker: Pokemon, defender: Pokemon, move: Move, p1_team, p2_team, p1_idx, p2_idx, current_player):
    """Execute a move and return battle messages"""
    messages = []
    
    # Check paralysis
    paralysis = attacker.status.get('paralysis')
    if paralysis and isinstance(paralysis, dict) and paralysis.get('turns', 0) > 0:
        if random.random() < 0.25:  # 25% chance to be fully paralyzed
            messages.append(f"{attacker.name} is fully paralyzed!")
            return messages
    
    if move.energy_cost > attacker.energy:
        messages.append(f"{attacker.name} tried to use {move.name} but lacked energy!")
        return messages
    
    # Deduct energy
    attacker.energy = max(0, attacker.energy - move.energy_cost)
    messages.append(f"{attacker.name} used {move.name}!")
    
    if move.category == "status":
        # Apply status effect
        if move.effect:
            try:
                result = move.effect(stdscr, color_mgr, attacker, defender)
                # Handle HexaBreak special effects that return tuples
                if result and isinstance(result, tuple):
                    effect_type = result[0]
                    if effect_type == "def_lower":
                        target, amount, turns = result[1], result[2], result[3]
                        def_lower(stdscr, color_mgr, target, amount, turns)
                        messages.append(f"{target.name}'s defense fell!")
                    elif effect_type == "percent_max_hp":
                        percent = result[1]
                        deal_percent_max_hp(stdscr, color_mgr, defender, percent)
                        messages.append(f"HP overflow damage dealt!")
                    else:
                        # For other effects, call the original function if it exists
                        pass
                else:
                    # Original behavior for other moves
                    pass
            except:
                # Fallback for original lambda functions
                move.effect(stdscr, color_mgr, attacker, defender)
        
        # Add appropriate message based on move
        if "heal" in move.name.lower():
            messages.append(f"{attacker.name} recovered HP!")
        elif "defense" in move.name.lower() and "lower" not in move.name.lower():
            messages.append(f"{attacker.name}'s defense rose!")
        elif "speed" in move.name.lower():
            if "boost" in move.name.lower() or "raise" in move.name.lower():
                messages.append(f"{attacker.name}'s speed rose!")
            else:
                messages.append(f"{defender.name}'s speed fell!")
        elif "poison" in move.name.lower():
            messages.append(f"{defender.name} was poisoned!")
        elif "burn" in move.name.lower() or "fire" in move.name.lower():
            messages.append(f"{defender.name} was burned!")
        elif "paralyze" in move.name.lower() or "shock" in move.name.lower() or "thunder" in move.name.lower():
            messages.append(f"{defender.name} was paralyzed!")
        elif "curse" in move.name.lower():
            messages.append(f"{defender.name}'s defense fell!")
        elif "memory corruption" in move.name.lower():
            messages.append(f"{defender.name}'s defense was corrupted!")
        else:
            messages.append(f"{move.name} took effect!")
    else:
        # Calculate and apply damage
        dmg, crit = compute_damage(attacker, defender, move)
        
        # Apply special effects for damage moves
        if move.effect:
            try:
                result = move.effect(stdscr, color_mgr, attacker, defender)
                # Handle HexaBreak special effects that return tuples
                if result and isinstance(result, tuple):
                    effect_type = result[0]
                    if effect_type == "double_hit_if_faster":
                        hits = double_hit_if_faster(stdscr, color_mgr, attacker, defender)
                        if hits > 1:
                            messages.append(f"Struck {hits} times!")
                            # Apply damage for additional hits
                            for _ in range(hits - 1):
                                additional_dmg, _ = compute_damage(attacker, defender, move)
                                defender.hp = max(0, defender.hp - additional_dmg)
                                dmg += additional_dmg
                    elif effect_type == "bonus_damage_if_hp_above":
                        threshold = result[1]
                        multiplier = bonus_damage_if_hp_above(stdscr, color_mgr, attacker, defender, threshold)
                        if multiplier > 1:
                            messages.append("KERNEL PANIC! Damage doubled!")
                            dmg *= multiplier
                    elif effect_type == "percent_max_hp":
                        percent = result[1]
                        deal_percent_max_hp(stdscr, color_mgr, defender, percent)
                        messages.append("Overflow damage dealt!")
                        # Don't apply normal damage for percent-based moves
                        dmg = 0
            except:
                # Fallback for original lambda functions
                pass
        
        # Apply the calculated damage
        if dmg > 0:
            # Animate HP drain with battle effects
            message_for_anim = f"{attacker.name} used {move.name}!"
            
            # Apply damage with animation
            animate_hp_drain(stdscr, color_mgr, p1_team, p2_team, p1_idx, p2_idx, defender, dmg, current_player, message_for_anim)
            
            if crit:
                messages.append(f"Critical hit! Dealt {dmg} damage!")
            else:
                messages.append(f"Dealt {dmg} damage!")
        
        if not defender.alive():
            messages.append(f"{defender.name} fainted!")
    
    return messages

def apply_end_of_turn(stdscr, color_mgr, poke: Pokemon):
    """Apply end of turn status effects"""
    if not poke.alive():
        return
    
    # Apply poison damage
    poison = poke.status.get('poison')
    if poison and isinstance(poison, dict) and poison.get('turns', 0) > 0:
        dmg = poison.get('dmg', 0)
        poke.hp = max(0, poke.hp - dmg)
        poison['turns'] -= 1
        if poison['turns'] <= 0:
            poke.status.pop('poison', None)
    
    # Apply burn damage
    burn = poke.status.get('burn')
    if burn and isinstance(burn, dict) and burn.get('turns', 0) > 0:
        dmg = burn.get('dmg', 0)
        poke.hp = max(0, poke.hp - dmg)
        burn['turns'] -= 1
        if burn['turns'] <= 0:
            poke.status.pop('burn', None)
    
    # Decrement status durations
    for key in list(poke.status.keys()):
        if key.endswith('_amt') or key in ['poison', 'burn', 'paralysis']:
            continue

        if key in poke.status and isinstance(poke.status.get(key), int):
            poke.status[key] -= 1
            if poke.status[key] <= 0:
                poke.status.pop(key, None)
                poke.status.pop(f"{key}_amt", None)
    
    # Handle paralysis duration
    paralysis = poke.status.get('paralysis')
    if paralysis and isinstance(paralysis, dict) and paralysis.get('turns', 0) > 0:
        paralysis['turns'] -= 1
        if paralysis['turns'] <= 0:
            poke.status.pop('paralysis', None)

def prompt_switch(stdscr, color_mgr, team, player_name, player_color_name):
    """Prompt a player to switch Pok\u00e9mon"""
    options = [i for i, p in enumerate(team) if p.alive()]
    
    if not options:
        return None
    
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    curses_center_text(stdscr, f"{player_name}, choose your next Pok\u00e9mon!", 0, 
                      color_mgr.get_color_attr(player_color_name))
    
    menu_items = []
    for idx in options:
        p = team[idx]
        hp_percent = p.hp / p.max_hp
        hp_color = 'green' if hp_percent > 0.5 else 'yellow' if hp_percent > 0.25 else 'red'
        menu_items.append(f"{p.name} (HP: {p.hp}/{p.max_hp})")
    
    selected_idx = get_menu_selection(stdscr, menu_items, 
                                     title="Available Pok\u00e9mon:", 
                                     start_y=3, start_x=2, color_mgr=color_mgr)
    
    if selected_idx == -1:
        return options[0] if options else None
    
    return options[selected_idx]

def battle_pvp(stdscr, player1_team: List[Pokemon], player2_team: List[Pokemon], color_mgr):
    """Main 2-player battle loop"""
    p1_idx, p2_idx = 0, 0
    
    # Initial display
    draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                  p1_idx, p2_idx, "Battle Start! Player 1 goes first.", current_player=1)
    stdscr.refresh()
    time.sleep(2)
    
    while any(p.alive() for p in player1_team) and any(p.alive() for p in player2_team):
        # Player 1's turn
        player1 = player1_team[p1_idx]
        player2 = player2_team[p2_idx]
        
        # Check if Player 1's Pok\u00e9mon is alive
        if not player1.alive():
            p1_idx = prompt_switch(stdscr, color_mgr, player1_team, "Player 1", 'bright_blue')
            if p1_idx is None:
                break
            player1 = player1_team[p1_idx]
        
        # Player 1's action
        can_switch = len([p for p in player1_team if p.alive()]) > 1
        p1_action, p1_move, p1_idx = get_player_action(stdscr, color_mgr, 
                                                      player1_team, player2_team,
                                                      p1_idx, p2_idx, 1, can_switch)
        
        # Execute Player 1's action
        if p1_action == "attack" and p1_move:
            messages = perform_move(stdscr, color_mgr, player1, player2, p1_move, player1_team, player2_team, p1_idx, p2_idx, 1)
            message = "\n".join(messages)
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(2)
            
        elif p1_action == "switch":
            message = f"Player 1 switched to {player1_team[p1_idx].name}!"
            player1_team[p1_idx].energy = min(player1_team[p1_idx].energy_max, 
                                             player1_team[p1_idx].energy + 8)
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(1.5)
            
        elif p1_action == "pass":
            player1.energy = min(player1.energy_max, player1.energy + 5)
            message = f"{player1.name} passes and regains energy!"
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(1)
        
        # Check if Player 2 fainted
        if not player2_team[p2_idx].alive():
            if not any(p.alive() for p in player2_team):
                break
            
            message = f"{player2_team[p2_idx].name} fainted! Player 2, choose your next Pok\u00e9mon."
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=2)
            stdscr.refresh()
            time.sleep(2)
            
            p2_idx = prompt_switch(stdscr, color_mgr, player2_team, "Player 2", 'bright_magenta')
            if p2_idx is None:
                break
        
        # Player 2's turn
        player1 = player1_team[p1_idx]
        player2 = player2_team[p2_idx]
        
        # Check if Player 2's Pok\u00e9mon is alive
        if not player2.alive():
            p2_idx = prompt_switch(stdscr, color_mgr, player2_team, "Player 2", 'bright_magenta')
            if p2_idx is None:
                break
            player2 = player2_team[p2_idx]
        
        # Player 2's action
        can_switch = len([p for p in player2_team if p.alive()]) > 1
        p2_action, p2_move, p2_idx = get_player_action(stdscr, color_mgr, 
                                                      player2_team, player1_team,
                                                      p2_idx, p1_idx, 2, can_switch)
        
        # Execute Player 2's action
        if p2_action == "attack" and p2_move:
            messages = perform_move(stdscr, color_mgr, player2, player1, p2_move, player1_team, player2_team, p1_idx, p2_idx, 2)
            message = "\n".join(messages)
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=2)
            stdscr.refresh()
            time.sleep(2)
            
        elif p2_action == "switch":
            message = f"Player 2 switched to {player2_team[p2_idx].name}!"
            player2_team[p2_idx].energy = min(player2_team[p2_idx].energy_max, 
                                             player2_team[p2_idx].energy + 8)
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=2)
            stdscr.refresh()
            time.sleep(1.5)
            
        elif p2_action == "pass":
            player2.energy = min(player2.energy_max, player2.energy + 5)
            message = f"{player2.name} passes and regains energy!"
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=2)
            stdscr.refresh()
            time.sleep(1)
        
        # Check if Player 1 fainted
        if not player1_team[p1_idx].alive():
            if not any(p.alive() for p in player1_team):
                break
            
            message = f"{player1_team[p1_idx].name} fainted! Player 1, choose your next Pok\u00e9mon."
            draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                          p1_idx, p2_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(2)
            
            p1_idx = prompt_switch(stdscr, color_mgr, player1_team, "Player 1", 'bright_blue')
            if p1_idx is None:
                break
        
        # Apply end of turn effects
        apply_end_of_turn(stdscr, color_mgr, player1_team[p1_idx])
        apply_end_of_turn(stdscr, color_mgr, player2_team[p2_idx])
        
        # Regen energy for both
        player1_team[p1_idx].energy = min(player1_team[p1_idx].energy_max, 
                                         player1_team[p1_idx].energy + 3)
        player2_team[p2_idx].energy = min(player2_team[p2_idx].energy_max, 
                                         player2_team[p2_idx].energy + 3)
    
    # Determine winner and update statistics
    max_y, max_x = stdscr.getmaxyx()
    winner_pokemon = None
    winner_player = 0
    loser_pokemon = None
    
    if any(p.alive() for p in player1_team):
        message = "[PARTY] PLAYER 1 WINS THE BATTLE! [PARTY]"
        color = 'bright_green'
        winner_player = 1
        # Get the winning Pokemon (first alive one)
        for p in player1_team:
            if p.alive():
                winner_pokemon = p
                break
        # Get the losing Pokemon (the one that fainted from player 2)
        for p in reversed(player2_team):
            if not p.alive():  # pick a fainted Pok\u00e9mon as the loser
                loser_pokemon = p
                break
    else:
        message = "[PARTY] PLAYER 2 WINS THE BATTLE! [PARTY]"
        color = 'bright_magenta'
        winner_player = 2
        # Get the winning Pokemon (first alive one from player 2)
        for p in player2_team:
            if p.alive():
                winner_pokemon = p
                break
        # Get the losing Pokemon (the one that fainted from player 1)
        for p in reversed(player1_team):
            if not p.alive():  # pick a fainted Pok\u00e9mon as the loser
                loser_pokemon = p
                break
    
    # Update and save statistics
    if winner_pokemon and loser_pokemon:
        stats = load_stats()
        update_stats(stats, winner_pokemon, loser_pokemon)
        save_stats(stats)
    
    # Ensure indices are valid for final display
    final_p1_idx = p1_idx if p1_idx is not None and p1_idx < len(player1_team) else 0
    final_p2_idx = p2_idx if p2_idx is not None and p2_idx < len(player2_team) else 0
    
    draw_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                  final_p1_idx, final_p2_idx, message, current_player=1)
    stdscr.refresh()
    time.sleep(3)
    
    # Display match statistics
    display_match_stats(stdscr, color_mgr, player1_team, player2_team, winner_pokemon, winner_player)

def pick_team(stdscr, roster: List[Pokemon], prompt: str, team_size: int, color_mgr):
    """Team selection"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    curses_center_text(stdscr, "PICK YOUR TEAM", 0, color_mgr.get_color_attr('bright_cyan'))
    
    pokemon_display_items = []
    for i, p in enumerate(roster):
        display_str = f"{i+1}. {p.name}  LVL:{p.lvl}  HP:{p.max_hp}  ATK:{p.atk}  DEF:{p.dfns}  SPD:{p.spd}  EN:{p.energy_max}"
        pokemon_display_items.append(display_str)
    
    selected_indices = []
    while True:
        stdscr.clear()
        curses_center_text(stdscr, "PICK YOUR TEAM", 0, color_mgr.get_color_attr('bright_cyan'))
        curses_center_text(stdscr, prompt, 2, color_mgr.get_color_attr('yellow'))
        
        selected_indices = get_multi_selection(stdscr, pokemon_display_items, team_size, team_size, 
                                              title=f"{prompt} (Select {team_size}):", 
                                              start_y=4, start_x=2, color_mgr=color_mgr)
        
        if len(selected_indices) == team_size:
            break
        elif not selected_indices:
            curses_center_text(stdscr, f"You must select exactly {team_size} Pokemon. Press any key to retry.", 
                             max_y - 2, color_mgr.get_color_attr('red'))
            stdscr.getch()
            continue

    team = []
    for idx in selected_indices:
        original = roster[idx]
        clone = Pokemon(
            name=original.name,
            lvl=original.lvl,
            max_hp=original.max_hp,
            atk=original.atk,
            dfns=original.dfns,
            spd=original.spd,
            energy_max=original.energy_max,
            moves=original.moves,
            ascii_art=original.ascii_art.copy()
        )
        team.append(clone)
    return team

def battle_1v3(stdscr, player_team: List[Pokemon], enemy_team: List[Pokemon], color_mgr):
    """1 vs 3 battle mode where player fights against 3 opponents"""
    p1_idx, enemy_idx = 0, 0
    
    # Initial display
    draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                  p1_idx, enemy_idx, "1v3 BATTLE START! Player vs 3 Enemies!", current_player=1)
    stdscr.refresh()
    time.sleep(2)
    
    while any(p.alive() for p in player_team) and any(p.alive() for p in enemy_team):
        # Player's turn
        player = player_team[p1_idx]
        enemy = enemy_team[enemy_idx]
        
        # Check if Player's Pok\u00e9mon is alive
        if not player.alive():
            new_p1_idx = prompt_switch(stdscr, color_mgr, player_team, "Player", 'bright_blue')
            if new_p1_idx is None:
                break
            p1_idx = new_p1_idx
            player = player_team[p1_idx]
        
        # Player's action
        can_switch = len([p for p in player_team if p.alive()]) > 1
        p1_action, p1_move, new_p1_idx = get_player_action(stdscr, color_mgr, 
                                                          player_team, enemy_team,
                                                          p1_idx, enemy_idx, 1, can_switch)
        
        if p1_action == "attack" and p1_move:
            messages = perform_move(stdscr, color_mgr, player, enemy, p1_move, player_team, enemy_team, p1_idx, enemy_idx, 1)
            message = "\n".join(messages)
            draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                          p1_idx, enemy_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(2)
            
        elif p1_action == "switch":
            p1_idx = new_p1_idx
            message = f"Player switched to {player_team[p1_idx].name}!"
            player_team[p1_idx].energy = min(player_team[p1_idx].energy_max, 
                                           player_team[p1_idx].energy + 8)
            draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                          p1_idx, enemy_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(1.5)
            
        elif p1_action == "pass":
            player.energy = min(player.energy_max, player.energy + 5)
            message = f"{player.name} passes and regains energy!"
            draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                          p1_idx, enemy_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(1)
        
        # Check if current enemy fainted, switch to next available enemy
        if not enemy_team[enemy_idx].alive():
            # Find next alive enemy
            enemy_found = False
            for i in range(len(enemy_team)):
                if i != enemy_idx and enemy_team[i].alive():
                    enemy_idx = i
                    enemy_found = True
                    break
            
            if not enemy_found or not any(p.alive() for p in enemy_team):
                break
            
            message = f"{enemy_team[enemy_idx].name} is now fighting!"
            draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                          p1_idx, enemy_idx, message, current_player=2)
            stdscr.refresh()
            time.sleep(1.5)
        
        # Enemy's turn (simple AI - random actions)
        player = player_team[p1_idx]
        enemy = enemy_team[enemy_idx]
        
        # Check if Enemy is alive
        if not enemy.alive():
            # Find next alive enemy
            enemy_found = False
            for i in range(len(enemy_team)):
                if enemy_team[i].alive():
                    enemy_idx = i
                    enemy_found = True
                    break
            
            if not enemy_found:
                break
            enemy = enemy_team[enemy_idx]
        
        # Simple AI: Choose random available move
        available_moves = [move for move in enemy.moves if move.energy_cost <= enemy.energy]
        if available_moves:
            enemy_move = random.choice(available_moves)
            messages = perform_move(stdscr, color_mgr, enemy, player, enemy_move, player_team, enemy_team, p1_idx, enemy_idx, 2)
            message = "\n".join(messages)
        else:
            enemy.energy = min(enemy.energy_max, enemy.energy + 5)
            message = f"{enemy.name} passes and regains energy!"
        
        draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                      p1_idx, enemy_idx, message, current_player=2)
        stdscr.refresh()
        time.sleep(2)
        
        # Check if Player fainted
        if not player_team[p1_idx].alive():
            if not any(p.alive() for p in player_team):
                break
            
            message = f"{player_team[p1_idx].name} fainted! Player, choose your next Pok\u00e9mon."
            draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                          p1_idx, enemy_idx, message, current_player=1)
            stdscr.refresh()
            time.sleep(2)
            
            new_p1_idx = prompt_switch(stdscr, color_mgr, player_team, "Player", 'bright_blue')
            if new_p1_idx is None:
                break
            p1_idx = new_p1_idx
        
        # Apply end of turn effects
        apply_end_of_turn(stdscr, color_mgr, player_team[p1_idx])
        apply_end_of_turn(stdscr, color_mgr, enemy_team[enemy_idx])
        
        # Regen energy for both
        player_team[p1_idx].energy = min(player_team[p1_idx].energy_max, 
                                         player_team[p1_idx].energy + 3)
        enemy_team[enemy_idx].energy = min(enemy_team[enemy_idx].energy_max, 
                                          enemy_team[enemy_idx].energy + 3)
    
    # Determine winner
    if any(p.alive() for p in player_team):
        message = "[PARTY] PLAYER DEFEATS ALL 3 ENEMIES! [PARTY]"
    else:
        message = "[SKULL] PLAYER DEFEATED BY THE ENEMIES! [SKULL]"
    
    draw_battle_ui(stdscr, color_mgr, player_team, enemy_team, 
                  p1_idx, enemy_idx, message, current_player=1)
    stdscr.refresh()
    time.sleep(3)

def draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                       p1_active, p2_active, message="", current_player=1):
    """Draw enhanced VGC battle UI with side-by-side Pokemon display and ASCII art"""
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    # Enhanced border with corners
    try:
        stdscr.border('│', '│', '─', '─', '┌', '┐', '└', '┘')
    except:
        stdscr.box()
    
    # Title with decoration
    title = "⚔ VGC DOUBLE BATTLE ⚔"
    curses_center_text(stdscr, title, 0, 
                       color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD)
    
    # Subtitle showing format
    subtitle = "4v4 Format | 2 vs 2 Active"
    curses_center_text(stdscr, subtitle, 1, 
                       color_mgr.get_color_attr('dim_white'))
    
    # Calculate layout for side-by-side display
    section_width = max_x // 2 - 4
    p1_x = 2
    p2_x = max_x // 2 + 2
    
    # Player 2 Section (TOP RIGHT - OPPONENT)
    p2_title = "≡ PLAYER 2 - OPPONENT ≡"
    stdscr.addstr(3, p2_x, p2_title[:section_width], 
                  color_mgr.get_color_attr('bright_magenta') | curses.A_BOLD)
    
    # Draw Player 2 active Pokemon side by side
    for i in range(2):
        if i < len(p2_active) and p2_active[i] < len(player2_team):
            p2_pokemon = player2_team[p2_active[i]]
            y_start = 5 + i * 4
            x_offset = p2_x + (i % 2) * (section_width // 2)
            
            # Slot indicator
            slot_text = f"[{i+1}]"
            stdscr.addstr(y_start, x_offset, slot_text, 
                          color_mgr.get_color_attr('bright_magenta') | curses.A_BOLD)
            
            # Pokemon name (truncated if needed)
            name_display = p2_pokemon.name[:12]
            color = 'bright_green' if p2_pokemon.alive() else 'bright_red'
            stdscr.addstr(y_start, x_offset + 3, name_display, 
                          color_mgr.get_color_attr(color) | curses.A_BOLD)
            
            # Level
            level_text = f"Lv{p2_pokemon.lvl}"
            stdscr.addstr(y_start, x_offset + 16, level_text, 
                          color_mgr.get_color_attr('white'))
            
            # HP bar (compact)
            hp_ratio = p2_pokemon.hp / max(1, p2_pokemon.max_hp)
            hp_bar_length = int(12 * hp_ratio)
            hp_bar = "█" * hp_bar_length + "░" * (12 - hp_bar_length)
            stdscr.addstr(y_start + 1, x_offset + 3, f"HP:{hp_bar} {p2_pokemon.hp}/{p2_pokemon.max_hp}", 
                          color_mgr.get_color_attr('red'))
            
            # Energy bar (compact)
            en_ratio = p2_pokemon.energy / max(1, p2_pokemon.energy_max)
            en_bar_length = int(12 * en_ratio)
            en_bar = "█" * en_bar_length + "░" * (12 - en_bar_length)
            stdscr.addstr(y_start + 2, x_offset + 3, f"EN:{en_bar} {p2_pokemon.energy}/{p2_pokemon.energy_max}", 
                          color_mgr.get_color_attr('cyan'))
            
            # Status indicators
            if p2_pokemon.status:
                status_chars = []
                for k, v in p2_pokemon.status.items():
                    if isinstance(v, dict) and v.get('turns', 0) > 0:
                        if k == 'poison':
                            status_chars.append('P')
                        elif k == 'burn':
                            status_chars.append('B')
                        elif k == 'paralysis':
                            status_chars.append('Z')
                    elif isinstance(v, int) and v > 0:
                        if 'def_up' in k:
                            status_chars.append('D')
                        elif 'atk_up' in k:
                            status_chars.append('⚔')
                        elif 'spd_up' in k:
                            status_chars.append('💨')
                
                if status_chars:
                    status_line = ''.join(status_chars[:3])
                    stdscr.addstr(y_start + 2, x_offset + 25, status_line, 
                                  color_mgr.get_color_attr('yellow'))
    
    # Player 2 ASCII Art Display (Bottom of their section)
    p2_ascii_y = 14
    for i in range(2):
        if i < len(p2_active) and p2_active[i] < len(player2_team):
            p2_pokemon = player2_team[p2_active[i]]
            if p2_pokemon.ascii_art and p2_pokemon.alive():
                art_x = p2_x + i * (section_width // 2)
                # Use animated ASCII with idle state
                animate_ascii_pokemon(stdscr, color_mgr, p2_pokemon, art_x, p2_ascii_y, "idle")
    
    # Middle separator
    sep_y = max_y // 2
    for x in range(1, max_x - 1):
        try:
            if x % 4 == 0:
                stdscr.addch(sep_y, x, '┼', color_mgr.get_color_attr('dim_white'))
            else:
                stdscr.addch(sep_y, x, '─', color_mgr.get_color_attr('dim_white'))
        except:
            pass
    
    # Player 1 Section (BOTTOM LEFT - YOU)
    p1_y = sep_y + 2
    p1_title = "≡ PLAYER 1 - YOU ≡"
    stdscr.addstr(p1_y + 1, p1_x, p1_title[:section_width], 
                  color_mgr.get_color_attr('bright_blue') | curses.A_BOLD)
    
    # Draw Player 1 active Pokemon side by side
    for i in range(2):
        if i < len(p1_active) and p1_active[i] < len(player1_team):
            p1_pokemon = player1_team[p1_active[i]]
            y_start = p1_y + 3 + i * 4
            x_offset = p1_x + (i % 2) * (section_width // 2)
            
            # Slot indicator with highlighting for current player
            slot_text = f"[{i+1}]"
            slot_color = 'bright_blue' if current_player == 1 else 'dim_white'
            stdscr.addstr(y_start, x_offset, slot_text, 
                          color_mgr.get_color_attr(slot_color) | curses.A_BOLD)
            
            # Pokemon name
            name_display = p1_pokemon.name[:12]
            color = 'bright_green' if p1_pokemon.alive() else 'bright_red'
            stdscr.addstr(y_start, x_offset + 3, name_display, 
                          color_mgr.get_color_attr(color) | curses.A_BOLD)
            
            # Level
            level_text = f"Lv{p1_pokemon.lvl}"
            stdscr.addstr(y_start, x_offset + 16, level_text, 
                          color_mgr.get_color_attr('white'))
            
            # HP bar with color coding
            hp_ratio = p1_pokemon.hp / max(1, p1_pokemon.max_hp)
            hp_bar_length = int(12 * hp_ratio)
            hp_bar = "█" * hp_bar_length + "░" * (12 - hp_bar_length)
            hp_color = 'bright_green' if hp_ratio > 0.5 else 'bright_yellow' if hp_ratio > 0.25 else 'bright_red'
            stdscr.addstr(y_start + 1, x_offset + 3, f"HP:{hp_bar} {p1_pokemon.hp}/{p1_pokemon.max_hp}", 
                          color_mgr.get_color_attr(hp_color))
            
            # Energy bar
            en_ratio = p1_pokemon.energy / max(1, p1_pokemon.energy_max)
            en_bar_length = int(12 * en_ratio)
            en_bar = "█" * en_bar_length + "░" * (12 - en_bar_length)
            stdscr.addstr(y_start + 2, x_offset + 3, f"EN:{en_bar} {p1_pokemon.energy}/{p1_pokemon.energy_max}", 
                          color_mgr.get_color_attr('cyan'))
            
            # Status indicators
            if p1_pokemon.status:
                status_chars = []
                for k, v in p1_pokemon.status.items():
                    if isinstance(v, dict) and v.get('turns', 0) > 0:
                        if k == 'poison':
                            status_chars.append('P')
                        elif k == 'burn':
                            status_chars.append('B')
                        elif k == 'paralysis':
                            status_chars.append('Z')
                    elif isinstance(v, int) and v > 0:
                        if 'def_up' in k:
                            status_chars.append('D')
                        elif 'atk_up' in k:
                            status_chars.append('⚔')
                        elif 'spd_up' in k:
                            status_chars.append('💨')
                
                if status_chars:
                    status_line = ''.join(status_chars[:3])
                    stdscr.addstr(y_start + 2, x_offset + 25, status_line, 
                                  color_mgr.get_color_attr('yellow'))
    
    # Player 1 ASCII Art Display
    p1_ascii_y = sep_y + 11
    for i in range(2):
        if i < len(p1_active) and p1_active[i] < len(player1_team):
            p1_pokemon = player1_team[p1_active[i]]
            if p1_pokemon.ascii_art and p1_pokemon.alive():
                art_x = p1_x + i * (section_width // 2)
                # Use animated ASCII with idle state
                animate_ascii_pokemon(stdscr, color_mgr, p1_pokemon, art_x, p1_ascii_y, "idle")
    
    # Battle message area
    if message:
        msg_y = sep_y - 2
        msg_lines = message.split('\n')
        for i, line in enumerate(msg_lines[:2]):
            if msg_y - i >= 5:
                curses_center_text(stdscr, line[:max_x - 8], msg_y - i, 
                                  color_mgr.get_color_attr('bright_yellow'))
    
    # Turn indicator with animation effect
    if current_player == 1:
        turn_text = "▶▶ PLAYER 1'S TURN ◀◀"
        turn_color = 'bright_green'
    else:
        turn_text = "▶▶ PLAYER 2'S TURN ◀◀"
        turn_color = 'bright_magenta'
    
    curses_center_text(stdscr, turn_text, max_y - 4, 
                       color_mgr.get_color_attr(turn_color) | curses.A_BOLD)
    
    # Enhanced control hints
    hint_lines = [
        "1-2: Select Slot | m: Move Menu | s: Switch | t: Target",
        "Enter: Confirm | q: Back | ESC: Main Menu"
    ]
    
    for i, hint in enumerate(hint_lines):
        if max_y - 2 + i < max_y - 1:
            curses_center_text(stdscr, hint, max_y - 2 + i, 
                              color_mgr.get_color_attr('dim_white'))
    
    # Speed indicators (show which Pokemon is faster)
    try:
        if len(p1_active) >= 2 and len(p2_active) >= 2:
            p1_pokemon = player1_team[p1_active[0]]
            p2_pokemon = player2_team[p2_active[0]]
            speed_text = f"SPD: P1:{p1_pokemon.spd} vs P2:{p2_pokemon.spd}"
            curses_center_text(stdscr, speed_text, 2, 
                              color_mgr.get_color_attr('cyan'))
    except:
        pass
    
    stdscr.refresh()

def get_vgc_action(stdscr, color_mgr, pokemon: Pokemon, player_team, opponent_team, 
                   player_active, opponent_active, slot_idx, player_num):
    """Get action for VGC battle with enhanced controls"""
    max_y, max_x = stdscr.getmaxyx()
    
    while True:
        draw_vgc_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                           player_active, opponent_active, 
                           f"Player {player_num} - {pokemon.name} (Slot {slot_idx + 1}) - Choose action:", player_num)
        
        # Create action menu with enhanced move information
        actions = []
        # Add attack options with all moves
        for i, move in enumerate(pokemon.moves):
            energy_status = "Y" if move.energy_cost <= pokemon.energy else "N"
            power_text = f"Pow:{move.power}" if move.power > 0 else "Status"
            cat_emoji = {"physical": "[P]", "special": "[S]", "mystical-special": "[M]", "status": "[?]"}.get(move.category, "[?]")
            actions.append(f"{i+1}. {move.name} {cat_emoji} ({power_text}|EN:{move.energy_cost}{energy_status})")
        
        # Add switch option if other Pokemon available
        available_switch = [idx for idx in range(len(player_team)) 
                          if idx not in player_active and player_team[idx].alive()]
        if available_switch:
            actions.append(f"S. Switch Pokemon")
        
        actions.append("P. Pass Turn")
        
        # Draw menu with move details
        menu_y = max_y - len(actions) - 6
        for i, action in enumerate(actions):
            y_pos = menu_y + i
            color = 'bright_yellow' if i == 0 else 'white'
            stdscr.addstr(y_pos, 2, action, color_mgr.get_color_attr(color))
        
        # Show details for first/highlighted move
        if pokemon.moves:
            move = pokemon.moves[0]  # Default to first move for display
            details_y = menu_y + len(actions) + 1
            
            move_info = [
                f"Move: {move.name}",
                f"Category: {move.category.replace('-', ' ').title()}",
                f"Power: {move.power}" if move.power > 0 else "Status Effect",
                f"Energy Cost: {move.energy_cost}",
                f"Description: {move.description[:40]}{'...' if len(move.description) > 40 else ''}"
            ]
            
            for i, info in enumerate(move_info):
                if details_y + i < max_y - 2:
                    stdscr.addstr(details_y + i, 2, info, color_mgr.get_color_attr('cyan'))
        
        # Instructions
        instructions = "1-4: Choose Move | S: Switch | P: Pass | Enter: Confirm"
        curses_center_text(stdscr, instructions, max_y - 1, color_mgr.get_color_attr('dim_white'))
        
        key = stdscr.getch()
        
        # Handle number keys for moves
        if key >= ord('1') and key <= ord('4'):
            move_idx = key - ord('1')
            if move_idx < len(pokemon.moves):
                move = pokemon.moves[move_idx]
                if move.energy_cost <= pokemon.energy:
                    # For attacks, need to choose target
                    if move.power > 0 or move.category.endswith('-status'):
                        available_targets = []
                        for i in range(2):
                            if i < len(opponent_active) and opponent_active[i] < len(opponent_team):
                                target_pokemon = opponent_team[opponent_active[i]]
                                if target_pokemon.alive():
                                    available_targets.append((i, target_pokemon))
                        
                        if available_targets:
                            # Target selection
                            target_idx = select_vgc_target(stdscr, color_mgr, available_targets, player_num)
                            if target_idx is not None:
                                return {
                                    'type': 'attack',
                                    'pokemon': pokemon,
                                    'move': move,
                                    'target': available_targets[target_idx][1],
                                    'slot': slot_idx
                                }
                    else:
                        # Status move, no target needed
                        return {
                            'type': 'status',
                            'pokemon': pokemon,
                            'move': move,
                            'slot': slot_idx
                        }
                else:
                    # Not enough energy
                    draw_vgc_battle_ui(stdscr, color_mgr, player_team, opponent_team, 
                                       player_active, opponent_active, 
                                       "Not enough energy!", player_num)
                    stdscr.refresh()
                    time.sleep(1)
        
        elif key in [ord('s'), ord('S')]:
            # Switch Pokemon
            if available_switch:
                new_pokemon_idx = select_vgc_switch(stdscr, color_mgr, player_team, available_switch, player_num)
                if new_pokemon_idx is not None:
                    return {
                        'type': 'switch',
                        'pokemon': pokemon,
                        'new_pokemon': player_team[new_pokemon_idx],
                        'slot': slot_idx
                    }
        
        elif key in [ord('p'), ord('P')]:
            # Pass turn
            return {
                'type': 'pass',
                'pokemon': pokemon,
                'slot': slot_idx
            }
        
        elif key in [ord('q'), ord('Q'), 27]:  # ESC
            # Back out (treated as pass)
            return {
                'type': 'pass',
                'pokemon': pokemon,
                'slot': slot_idx
            }

def select_vgc_target(stdscr, color_mgr, available_targets, player_num):
    """Select target for VGC battle"""
    max_y, max_x = stdscr.getmaxyx()
    selected = 0
    
    while True:
        draw_vgc_battle_ui(stdscr, color_mgr, [], [], [], [], 
                           f"Player {player_num} - Choose target:", player_num)
        
        # Draw target options
        menu_y = max_y // 2 - 5
        for i, (slot_idx, target) in enumerate(available_targets):
            y_pos = menu_y + i
            color = 'black_on_yellow' if i == selected else 'white'
            text = f"Slot {slot_idx + 1}: {target.name} (HP:{target.hp}/{target.max_hp})"
            stdscr.addstr(y_pos, max_x // 2 - 20, text, color_mgr.get_color_attr(color))
        
        # Instructions
        instructions = "↑↓: Navigate | Enter: Select | q: Cancel"
        curses_center_text(stdscr, instructions, max_y - 2, color_mgr.get_color_attr('dim_white'))
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(available_targets)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(available_targets)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            return selected
        elif key in [ord('q'), ord('Q'), 27]:
            return None

def select_vgc_switch(stdscr, color_mgr, player_team, available_indices, player_num):
    """Select Pokemon to switch in"""
    max_y, max_x = stdscr.getmaxyx()
    selected = 0
    
    while True:
        draw_vgc_battle_ui(stdscr, color_mgr, [], [], [], [], 
                           f"Player {player_num} - Choose Pokemon to switch in:", player_num)
        
        # Draw switch options
        menu_y = max_y // 2 - 5
        for i, idx in enumerate(available_indices):
            y_pos = menu_y + i
            color = 'black_on_yellow' if i == selected else 'white'
            pokemon = player_team[idx]
            text = f"{pokemon.name} (HP:{pokemon.hp}/{pokemon.max_hp}) LVL:{pokemon.lvl}"
            stdscr.addstr(y_pos, max_x // 2 - 20, text, color_mgr.get_color_attr(color))
        
        # Instructions
        instructions = "↑↓: Navigate | Enter: Select | q: Cancel"
        curses_center_text(stdscr, instructions, max_y - 2, color_mgr.get_color_attr('dim_white'))
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(available_indices)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(available_indices)
        elif key in [ord('\n'), ord('\r'), curses.KEY_ENTER]:
            return available_indices[selected]
        elif key in [ord('q'), ord('Q'), 27]:
            return None

def battle_vgc(stdscr, player1_team: List[Pokemon], player2_team: List[Pokemon], color_mgr):
    """Enhanced VGC style battle with realistic rules, simultaneous turns, and better UI"""
    # VGC format: 4 Pokemon per player, 2 active at a time
    # Players select which 2 Pokemon to start with
    p1_active = [0, 1]  # indices of active Pokemon for player 1
    p2_active = [0, 1]  # indices of active Pokemon for player 2
    
    # Enhanced team selection for VGC (4 Pokemon each with preview)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    curses_center_text(stdscr, "⚔ VGC MODE - TEAM PREVIEW ⚔", 2, 
                       color_mgr.get_color_attr('bright_cyan') | curses.A_BOLD)
    curses_center_text(stdscr, "Each player selects 4 Pokemon, then chooses 2 to start", 3, 
                       color_mgr.get_color_attr('white'))
    
    stdscr.refresh()
    time.sleep(2)
    
    # Player 1 selects 2 active Pokemon with better UI
    p1_names = [f"{i+1}. {p.name} Lv{p.lvl} | HP:{p.max_hp} | ATK:{p.atk} | DEF:{p.dfns} | SPD:{p.spd}" 
                for i, p in enumerate(player1_team)]
    p1_active_indices = get_multi_selection(stdscr, p1_names, 2, 2,
                                          title="Player 1 - Choose 2 active Pokemon:",
                                          start_y=6, start_x=2, color_mgr=color_mgr)
    
    # Player 2 selects 2 active Pokemon
    p2_names = [f"{i+1}. {p.name} Lv{p.lvl} | HP:{p.max_hp} | ATK:{p.atk} | DEF:{p.dfns} | SPD:{p.spd}" 
                for i, p in enumerate(player2_team)]
    p2_active_indices = get_multi_selection(stdscr, p2_names, 2, 2,
                                          title="Player 2 - Choose 2 active Pokemon:",
                                          start_y=6, start_x=2, color_mgr=color_mgr)
    
    p1_active = p1_active_indices
    p2_active = p2_active_indices
    
    # Show initial battle setup
    draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                       p1_active, p2_active, "Battle Start! Prepare for VGC combat!", 1)
    stdscr.refresh()
    time.sleep(2)
    
    # Main VGC battle loop with simultaneous turns
    turn_count = 1
    while any(p.alive() for p in player1_team) and any(p.alive() for p in player2_team):
        # Check if we need to force switch for fainted Pokemon
        for i in range(2):
            if i < len(p1_active) and p1_active[i] is not None and p1_active[i] < len(player1_team) and not player1_team[p1_active[i]].alive():
                # Find replacement
                available = [idx for idx in range(len(player1_team)) 
                           if idx not in p1_active and player1_team[idx].alive()]
                if available:
                    old_pokemon = player1_team[p1_active[i]]
                    p1_active[i] = available[0]
                    new_pokemon = player1_team[p1_active[i]]
                    draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                                       p1_active, p2_active, 
                                       f"{old_pokemon.name} fainted! {new_pokemon.name} switches in!", 1)
                    stdscr.refresh()
                    time.sleep(1.5)
            
            if i < len(p2_active) and p2_active[i] is not None and p2_active[i] < len(player2_team) and not player2_team[p2_active[i]].alive():
                # Find replacement
                available = [idx for idx in range(len(player2_team)) 
                           if idx not in p2_active and player2_team[idx].alive()]
                if available:
                    old_pokemon = player2_team[p2_active[i]]
                    p2_active[i] = available[0]
                    new_pokemon = player2_team[p2_active[i]]
                    draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                                       p1_active, p2_active, 
                                       f"{old_pokemon.name} fainted! {new_pokemon.name} switches in!", 2)
                    stdscr.refresh()
                    time.sleep(1.5)
        
        # Display VGC battle state
        draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                           p1_active, p2_active, 
                           f"Turn {turn_count} - Select actions", 1)
        
        # Simultaneous turn selection - both players choose actions
        p1_actions = []
        p2_actions = []
        
        # Player 1 selects actions for both Pokemon
        for slot_idx in range(2):
            if slot_idx < len(p1_active) and p1_active[slot_idx] is not None and p1_active[slot_idx] < len(player1_team) and player1_team[p1_active[slot_idx]].alive():
                pokemon = player1_team[p1_active[slot_idx]]
                action = get_vgc_action(stdscr, color_mgr, pokemon, player1_team, player2_team, 
                                       p1_active, p2_active, slot_idx, 1)
                if action:
                    p1_actions.append(action)
        
        # Player 2 selects actions for both Pokemon
        for slot_idx in range(2):
            if slot_idx < len(p2_active) and p2_active[slot_idx] is not None and p2_active[slot_idx] < len(player2_team) and player2_team[p2_active[slot_idx]].alive():
                pokemon = player2_team[p2_active[slot_idx]]
                action = get_vgc_action(stdscr, color_mgr, pokemon, player2_team, player1_team, 
                                       p2_active, p1_active, slot_idx, 2)
                if action:
                    p2_actions.append(action)
        
        # Execute actions in speed order (VGC style)
        all_actions = p1_actions + p2_actions
        # Sort by speed: Pokemon with higher speed acts first
        all_actions.sort(key=lambda x: x['pokemon'].spd, reverse=True)
        
        for action in all_actions:
            if action['type'] == 'attack':
                attacker = action['pokemon']
                move = action['move']
                target = action['target']
                
                # Find team indices for perform_move
                if attacker in player1_team:
                    attacker_idx = player1_team.index(attacker)
                    current_player = 1
                else:
                    attacker_idx = player2_team.index(attacker)
                    current_player = 2
                
                if target in player1_team:
                    target_idx = player1_team.index(target)
                else:
                    target_idx = player2_team.index(target)
                
                messages = perform_move(stdscr, color_mgr, attacker, target, move, 
                                       player1_team, player2_team, attacker_idx, target_idx, current_player)
                message = "\n".join(messages)
                
                draw_vgc_battle_ui(stdscr, color_mgr, player1_team, player2_team, 
                                   p1_active, p2_active, message, current_player)
                stdscr.refresh()
                time.sleep(2)
        
        # Apply end of turn effects to all active Pokemon
        for i in range(2):
            if i < len(p1_active) and p1_active[i] is not None and p1_active[i] < len(player1_team):
                apply_end_of_turn(stdscr, color_mgr, player1_team[p1_active[i]])
                player1_team[p1_active[i]].energy = min(player1_team[p1_active[i]].energy_max, 
                                                        player1_team[p1_active[i]].energy + 3)
            
            if i < len(p2_active) and p2_active[i] is not None and p2_active[i] < len(player2_team):
                apply_end_of_turn(stdscr, color_mgr, player2_team[p2_active[i]])
                player2_team[p2_active[i]].energy = min(player2_team[p2_active[i]].energy_max, 
                                                        player2_team[p2_active[i]].energy + 3)
        
        turn_count += 1
    
    # Determine winner
    p1_alive = any(p.alive() for p in player1_team)
    p2_alive = any(p.alive() for p in player2_team)
    
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    
    if p1_alive and not p2_alive:
        message = "[PARTY] PLAYER 1 WINS THE VGC BATTLE! [PARTY]"
        color = 'bright_green'
        winner_player = 1
    elif p2_alive and not p1_alive:
        message = "[PARTY] PLAYER 2 WINS THE VGC BATTLE! [PARTY]"
        color = 'bright_magenta'
        winner_player = 2
    else:
        message = "[DRAW] THE BATTLE ENDS IN A DRAW! [DRAW]"
        color = 'bright_yellow'
        winner_player = 0
    
    curses_center_text(stdscr, message, max_y//2, 
                       color_mgr.get_color_attr(color) | curses.A_BOLD)
    stdscr.refresh()
    time.sleep(3)
    
    # Update stats (update all Pokemon that participated)
    stats = load_stats()
    if winner_player == 1:
        # Find winner and loser Pokemon for stats
        for p1_pokemon in player1_team:
            if p1_pokemon.alive():
                for p2_pokemon in player2_team:
                    if not p2_pokemon.alive():
                        update_stats(stats, p1_pokemon, p2_pokemon)
                        break
                break
    elif winner_player == 2:
        for p2_pokemon in player2_team:
            if p2_pokemon.alive():
                for p1_pokemon in player1_team:
                    if not p1_pokemon.alive():
                        update_stats(stats, p2_pokemon, p1_pokemon)
                        break
                break
    
    save_stats(stats)

def main(stdscr):
    """Main game loop"""
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    color_mgr = CursesColors()
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        if max_y < 24 or max_x < 80:
            curses_center_text(stdscr, "Terminal too small! Resize to at least 80x24.", max_y//2, 
                             color_mgr.get_color_attr('red') | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            continue
        
        title_y = max_y // 2 - 5
        
        welcome_art = [
            "\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557",
            "\u2551     WELCOME \u2014 TERMINAL POK\u00c9 BATTLE     \u2551",
            "\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d"
        ]
        
        for i, line in enumerate(welcome_art):
            stdscr.addstr(title_y + i, (max_x - len(line)) // 2, line, color_mgr.get_color_attr('bright_cyan'))
        
        stdscr.addstr(title_y + 4, (max_x - len("2-Player PvP Battle!")) // 2, 
                     "2-Player PvP Battle!", color_mgr.get_color_attr('bright_white'))
        stdscr.refresh()
        time.sleep(0.5)

        menu_items = ["1v1 Battle", "1v3 Battle", "3v3 Battle", "6v6 Battle", "VGC 4v4 Double Battle", "View Stats", "Exit Game"]
        
        selected_format_idx = get_menu_selection(stdscr, menu_items, title="Select Battle Format:", 
                                                start_y=title_y + 7, start_x=(max_x - 20) // 2, color_mgr=color_mgr)
        
        if selected_format_idx == -1 or selected_format_idx == 6:
            return
        
        # Handle View Stats option
        if selected_format_idx == 5:
            display_stats_checker(stdscr, color_mgr)
            continue

        team_size = {0: 1, 1: 3, 2: 3, 3: 6, 4: 4}[selected_format_idx]
        
        # Player 1 picks team
        team1 = pick_team(stdscr, ROSTER, f"Player 1, pick {team_size} Pok\u00e9mon:", team_size, color_mgr)
        if not team1:
            continue
            
        if selected_format_idx == 1:  # 1v3 mode
            # Player picks team of 1
            team1 = pick_team(stdscr, ROSTER, "Player, pick 1 Pok\u00e9mon:", 1, color_mgr)
            if not team1:
                continue
                
            # Auto-select 3 random enemies for 1v3
            enemy_team = []
            available_pokemon = [p for p in ROSTER]
            selected_indices = random.sample(range(len(available_pokemon)), min(3, len(available_pokemon)))
            
            for idx in selected_indices:
                original = available_pokemon[idx]
                clone = Pokemon(
                    name=original.name,
                    lvl=original.lvl,
                    max_hp=original.max_hp,
                    atk=original.atk,
                    dfns=original.dfns,
                    spd=original.spd,
                    energy_max=original.energy_max,
                    moves=original.moves,
                    ascii_art=original.ascii_art.copy()
                )
                enemy_team.append(clone)
            
            # Start 1v3 battle
            battle_1v3(stdscr, team1, enemy_team, color_mgr)
        else:
            # Player 2 picks team
            team2 = pick_team(stdscr, ROSTER, f"Player 2, pick {team_size} Pok\u00e9mon:", team_size, color_mgr)
            if not team2:
                continue
            
            # Start appropriate battle
            if selected_format_idx == 4:  # VGC mode
                battle_vgc(stdscr, team1, team2, color_mgr)
            else:
                battle_pvp(stdscr, team1, team2, color_mgr)
        
        # Ask to play again
        stdscr.clear()
        play_again = get_menu_selection(stdscr, ["Play Again", "Exit"], 
                                       title="Battle Over! Play again?",
                                       start_y=max_y//2 - 2, start_x=(max_x - 20)//2, color_mgr=color_mgr)
        
        if play_again != 0:
            break

if __name__ == "__main__":
    curses.wrapper(main)
