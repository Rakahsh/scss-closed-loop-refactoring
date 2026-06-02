# -*- coding: utf-8 -*-
import json
import math
import os
import config

def load_brand_guide():
    if os.path.exists(config.BRAND_GUIDE_FILE):
        with open(config.BRAND_GUIDE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"colors": {}}

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3: hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_closest_brand_color(target_hex, brand_colors):
    if not brand_colors: return None, 0.0
    try:
        t_rgb = hex_to_rgb(target_hex)
    except:
        return None, 0.0

    best_match = None
    best_score = 0.0
    MAX_DIST = 441.67 # math.sqrt((255**2)*3)

    for brand_name, brand_hex in brand_colors.items():
        try:
            b_rgb = hex_to_rgb(brand_hex)
            dist = math.sqrt((t_rgb[0]-b_rgb[0])**2 + (t_rgb[1]-b_rgb[1])**2 + (t_rgb[2]-b_rgb[2])**2)
            score = 100.0 - ((dist / MAX_DIST) * 100.0)
            if score > best_score:
                best_score = score
                best_match = brand_name
        except:
            continue

    return best_match, round(best_score, 2)
