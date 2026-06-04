# -*- coding: utf-8 -*-
import re

class PropertyClassifier:
    """
    A dedicated engine for inferring SCSS token taxonomy based on explicit CSS property context,
    preventing ambiguous values (e.g., '2px') from mis-categorizing.
    """

    def __init__(self):
        # Expanded taxonomy to catch all shorthands and mixin contexts
        self.property_map = {
            'colors': ['color', 'fill', 'stroke', 'background', 'bg-'],
            'typography': ['font', 'line-height', 'letter-spacing', 'text', 'white-space', 'word-'],
            'spacing': ['padding', 'margin', 'gap', 'top', 'bottom', 'left', 'right', 'inset'],
            'borders': ['border', 'outline', 'ring', 'radius'],
            'shadows': ['shadow'],
            'sizing': ['width', 'height', 'flex', 'grid', 'size', 'aspect', 'resolution']
        }

    def determine_category(self, prop, val):
        """
        Calculates the category by prioritizing explicit property intent over raw value assumptions.
        """
        prop = prop.lower().strip()
        val = str(val).lower().strip()

        # 1. Primary Filter: Explicit Property Intent
        for category, keywords in self.property_map.items():
            if any(k in prop for k in keywords):
                return category

        # 2. Secondary Filter: Value-Based Inference (Fallback)
        if re.search(r'#[0-9a-f]{3,8}|rgba?\(|hsla?\(', val):
            return "colors"
        if any(unit in val for unit in ['px', 'rem', 'em', 'vh', 'vw', '%']):
            return "sizing"

        # 3. Tertiary Filter: Unidentifiable
        return "misc"
