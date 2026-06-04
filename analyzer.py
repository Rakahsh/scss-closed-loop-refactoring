# -*- coding: utf-8 -*-
import os
import cssutils
import logging
import config

def parse_css(filepath):
    cssutils.log.setLevel(logging.CRITICAL)
    parser = cssutils.CSSParser()
    try: stylesheet = parser.parseFile(filepath, encoding='utf-8')
    except:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            stylesheet = parser.parseString(f.read())

    rules = {}

    # RECURSIVE ENGINE: Now crawls inside nested @media blocks
    def process_rule(rule, media_prefix=""):
        if rule.type == rule.STYLE_RULE:
            raw_sel = rule.selectorText.strip().lower() if config.CRAWL_SETTINGS["lowercase_selectors"] else rule.selectorText.strip()
            selector = f"{media_prefix} {raw_sel}".strip()
            properties = {p.name.strip(): p.value.strip() for p in rule.style}
            if selector in rules: rules[selector].update(properties)
            else: rules[selector] = properties
        elif rule.type == rule.MEDIA_RULE:
            try:
                media_query = f"@media {rule.media.mediaText}"
                for sub_rule in rule.cssRules:
                    process_rule(sub_rule, media_prefix=media_query)
            except: pass

    for rule in stylesheet:
        process_rule(rule)

    return rules

def compute_discrepancies(file_a, file_b, elapsed_time):
    data_a, data_b = parse_css(file_a), parse_css(file_b)
    name_a, name_b = os.path.basename(file_a), os.path.basename(file_b)
    all_selectors = set(data_a.keys()).union(set(data_b.keys()))
    metrics = []
    for sel in all_selectors:
        p_a, p_b = data_a.get(sel, {}), data_b.get(sel, {})
        if p_a and not p_b: metrics.append({"Selector": sel, "Status": "Isolated Variance", "Source": name_a, "Context": str(p_a), "Drift Count": len(p_a), "Session Aging (s)": elapsed_time})
        elif p_b and not p_a: metrics.append({"Selector": sel, "Status": "Isolated Variance", "Source": name_b, "Context": str(p_b), "Drift Count": len(p_b), "Session Aging (s)": elapsed_time})
        else:
            if p_a == p_b: metrics.append({"Selector": sel, "Status": "Identical Match (Ready)", "Source": f"{name_a}, {name_b}", "Context": str(p_a), "Drift Count": 0, "Session Aging (s)": elapsed_time})
            else:
                diffs = {p: f"[{name_a}]: {p_a.get(p)} | [{name_b}]: {p_b.get(p)}" for p in set(p_a.keys()).union(set(p_b.keys())) if p_a.get(p) != p_b.get(p)}
                metrics.append({"Selector": sel, "Status": "Structural Drift", "Source": f"{name_a}, {name_b}", "Context": str(diffs), "Drift Count": len(diffs), "Session Aging (s)": elapsed_time})
    return metrics
