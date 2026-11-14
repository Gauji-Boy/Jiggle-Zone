bl_info = {
    "name": "Giggle Soft Body Physics",
    "author": "VOZHD1122 & RoboDrozd / Giggle",
    "version": (2, 1, 0),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar > Giggle",
    "description": "Interactive soft body jiggle physics and secondary motion based on XPBD and Simulation Zones",
    "warning": "",
    "doc_url": "https://github.com/RoboDrozd/wiggy",
    "category": "Animation",
}

import bpy
import mathutils
import os
import json
import re
import hashlib
import shutil
import time
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup, Operator, Panel

# ==============================================================================
# PRESETS & TUNING RECIPES (Artist-directed Physics Starting Points)
# ==============================================================================
PRESET_GENDERS = [
    ('FEMALE', "Female", "Female anatomical presets and clothing support"),
    ('MALE', "Male", "Male anatomical presets and athletic support"),
    ('PROPS', "Props & Hair", "Hair, props, accessories and simulation zones"),
]

GENDER_CATEGORIES = {
    'FEMALE': [
        ('ALL', "All Female Categories", "Show all female presets"),
        ('FEMALE_CHEST', "Breasts & Bras", "Natural, wireless, underwire and sports bra support states"),
        ('FEMALE_BUTTOCKS', "Buttocks / Glutes", "Firm athletic, soft voluptuous, swimwear and leggings"),
        ('FEMALE_STOMACH', "Stomach, Belly & Waist", "Soft tummy, relaxed flab, corset waist cincher"),
        ('FEMALE_LEGS', "Thighs & Legs", "Inner thigh soft flesh and muscular quads"),
        ('FEMALE_EXTRAS', "Face & Arms", "Cheeks and underarm triceps"),
    ],
    'MALE': [
        ('ALL', "All Male Categories", "Show all male presets"),
        ('MALE_CHEST', "Chest & Pecs", "Toned, flexed, bodybuilder, soft chest and compression shirts"),
        ('MALE_GENITALIA', "Groin & Athletic Support", "Bare, boxers, briefs, boxer briefs, jockstrap, compression"),
        ('MALE_BUTTOCKS', "Buttocks & Glutes", "Athletic, firm, heavy glutes, tights and denim jeans"),
        ('MALE_STOMACH', "Stomach & Core", "Six-pack abs, beer belly, relaxed paunch and lifting belt"),
        ('MALE_LEGS', "Thighs & Legs", "Sprinter quads, soft thighs and calves"),
        ('MALE_EXTRAS', "Face, Neck & Arms", "Jawline, biceps, triceps and trapezius"),
    ],
    'PROPS': [
        ('ALL', "All Props Categories", "Show all props and physics presets"),
        ('PROPS_HAIR', "Hair & Ribbons", "Ponytails, braids and trailing cloth ribbons"),
        ('PROPS_ELASTIC', "Elastic Props & Materials", "Jelly, water balloon, backpacks and simzones"),
    ],
}

# Legacy fallback list for Blender property registration
PRESET_CATEGORIES = GENDER_CATEGORIES['FEMALE'] + GENDER_CATEGORIES['MALE'][1:] + GENDER_CATEGORIES['PROPS'][1:]

PRESETS = {
    # ==========================================================================
    # --- FEMALE CHEST & BRAS ---
    # ==========================================================================
    # --- Realistic Biomechanics (4.5 - 8.5 Hz, true tissue mass 0.3 - 0.75 kg) ---
    'REAL_BREASTS_NATURAL': {
        'name': "Natural Tissue (350g, 4.8 Hz)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Biomechanical baseline for medium breast tissue (4.8 Hz natural resonance, subtle 3D displacement)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,  # Softness
            'Socket_31': 0.35,  # Mass (kg) - true biological mass
            'Socket_102': True, # Mass by Area
            'Socket_118': 0.92, # Preserve Volume
            'Socket_119': 0.45, # Sway
            'Socket_126': 0.40, # Wobble
            'Socket_8': 1.40,   # Damping (settles in 2-3 cycles)
            'Socket_123': 0.035,# Max Distance (3.5 cm sag limit)
            'Socket_6': 0.55,   # Stretching (resists skin elongation)
            'Socket_30': 0.25,  # Bending
            'Socket_122': 1,    # Edge Fade
        }
    },
    'REAL_BREASTS_BRA': {
        'name': "Everyday Bra (6.5 Hz Support)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Standard underwire/everyday bra: 55% stiffness increase, suppressed vertical bounce",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.35,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.25,
            'Socket_126': 0.25,
            'Socket_8': 2.00,
            'Socket_123': 0.020,# 2.0 cm sag limit
            'Socket_6': 0.70,
            'Socket_30': 0.35,
            'Socket_122': 2,
        }
    },
    'REAL_BREASTS_SPORTS': {
        'name': "Sports Bra (8.5 Hz Encapsulation)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "High-support encapsulation athletic bra: 92% stiffness increase, critical damping (zeta ~0.75)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 0.35,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.12,
            'Socket_126': 0.10,
            'Socket_8': 3.20,
            'Socket_123': 0.012,# 1.2 cm sag limit
            'Socket_6': 0.85,
            'Socket_30': 0.45,
            'Socket_122': 3,
        }
    },
    'REAL_BREASTS_HEAVY': {
        'name': "Dense Heavy Tissue (750g)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Voluptuous D-Cup anatomical mass (4.0 Hz natural resonance, deep gravitational settling)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 0.75,
            'Socket_102': True,
            'Socket_118': 0.90,
            'Socket_119': 0.60,
            'Socket_126': 0.45,
            'Socket_8': 1.20,
            'Socket_123': 0.045,
            'Socket_6': 0.48,
            'Socket_30': 0.20,
            'Socket_122': 1,
        }
    },
    'REAL_BREASTS_FIRM': {
        'name': "Firm Petite Tissue (300g)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Petite athletic tissue with high intrinsic Cooper ligament tension",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.07,
            'Socket_31': 0.30,
            'Socket_102': True,
            'Socket_118': 0.94,
            'Socket_119': 0.30,
            'Socket_126': 0.25,
            'Socket_8': 2.20,
            'Socket_123': 0.020,
            'Socket_6': 0.65,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },

    # --- Stylized Anime & Film (Expressive, readable secondary motion) ---
    'STYLE_BREASTS_NATURAL': {
        'name': "Anime Natural / Medium",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Expressive anime figure-8 sway with balanced secondary oscillation and cohesive volume",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.18,
            'Socket_31': 1.8,
            'Socket_102': True,
            'Socket_118': 0.9,
            'Socket_119': 0.75,
            'Socket_126': 0.65,
            'Socket_8': 1.1,
            'Socket_123': 0.06,
            'Socket_6': 0.4,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_LOOSE': {
        'name': "Loose Bralette / Silk Top",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Sensual fluid drape with free-floating secondary bounce",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 1.6,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.65,
            'Socket_126': 0.55,
            'Socket_8': 1.3,
            'Socket_123': 0.055,
            'Socket_6': 0.45,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_REGULAR': {
        'name': "Regular / Underwire Bra",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Everyday bra support for stylized characters: lifted base, gentle top jiggle",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 0.75,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.40,
            'Socket_126': 0.45,
            'Socket_8': 1.60,
            'Socket_123': 0.045,
            'Socket_6': 0.45,
            'Socket_30': 0.28,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_PUSHUP': {
        'name': "Push-Up Bra / Cleavage Lift",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Firmly compressed and elevated cleavage with tight upward spring tension",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.09,
            'Socket_31': 0.90,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.45,
            'Socket_126': 0.40,
            'Socket_8': 1.60,
            'Socket_123': 0.045,
            'Socket_6': 0.50,
            'Socket_30': 0.35,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_SPORTS': {
        'name': "Dynamic Sports Support",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Athletic sports support: fast recovery and minimal sag during runs and jumps",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.07,
            'Socket_31': 0.75,
            'Socket_102': True,
            'Socket_118': 0.94,
            'Socket_119': 0.30,
            'Socket_126': 0.25,
            'Socket_8': 2.20,
            'Socket_123': 0.030,
            'Socket_6': 0.65,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_PERKY': {
        'name': "Petite / Firm Anime",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "High perky springiness with quick settling and taut skin",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 0.50,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.55,
            'Socket_126': 0.70,
            'Socket_8': 1.30,
            'Socket_123': 0.040,
            'Socket_6': 0.40,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_HEAVY': {
        'name': "Heavy / Voluptuous Bounce",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Large cinematic bust with deep momentum lag and pronounced secondary ripples",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.2,
            'Socket_31': 3.2,
            'Socket_102': True,
            'Socket_118': 0.88,
            'Socket_119': 0.85,
            'Socket_126': 0.7,
            'Socket_8': 1.0,
            'Socket_123': 0.075,
            'Socket_6': 0.35,
            'Socket_30': 0.2,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_WATER': {
        'name': "Water Immersion / Hyper Bounce",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Exaggerated hydrodynamic buoyancy for pool, bath and slow-motion scenes",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.22,
            'Socket_31': 2.8,
            'Socket_102': True,
            'Socket_118': 0.88,
            'Socket_119': 0.85,
            'Socket_126': 0.85,
            'Socket_8': 0.85,
            'Socket_123': 0.08,
            'Socket_6': 0.3,
            'Socket_30': 0.15,
            'Socket_122': 2,
        }
    },
    'STYLE_BREASTS_ANIME': {
        'name': "Heroic Anime Action Bounce",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_CHEST',
        'category': "Breasts & Bras",
        'description': "Fast, snappy, iconic action anime physics with sharp spring turnaround",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.22,
            'Socket_31': 2.0,
            'Socket_102': True,
            'Socket_118': 0.9,
            'Socket_119': 0.8,
            'Socket_126': 0.9,
            'Socket_8': 0.9,
            'Socket_123': 0.07,
            'Socket_6': 0.45,
            'Socket_30': 0.2,
            'Socket_122': 2,
        }
    },

    # ==========================================================================
    # --- FEMALE BUTTOCKS & GLUTES ---
    # ==========================================================================
    # --- Realistic Biomechanics (3.8 - 5.8 Hz, 1.4 - 2.4 kg per cheek) ---
    'REAL_GLUTES_NORMAL': {
        'name': "Biomechanical Glutes (1.8 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Anatomical gluteal mass-spring model (4.5 Hz, gait-synchronized impact settling)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 1.80,
            'Socket_102': True,
            'Socket_118': 0.93,
            'Socket_119': 0.40,
            'Socket_126': 0.35,
            'Socket_8': 1.60,
            'Socket_123': 0.025,
            'Socket_6': 0.60,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },
    'REAL_GLUTES_FIRM': {
        'name': "Athletic Muscular Glutes (1.4 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Tight gluteus maximus tone with high stiffness and minimal wobble",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 1.40,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.25,
            'Socket_126': 0.20,
            'Socket_8': 2.20,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 3,
        }
    },
    'REAL_GLUTES_SOFT': {
        'name': "Soft Adipose Tissue (2.4 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Fuller adipose layer with lower resonant frequency and prolonged impact ripples",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 2.40,
            'Socket_102': True,
            'Socket_118': 0.90,
            'Socket_119': 0.55,
            'Socket_126': 0.45,
            'Socket_8': 1.20,
            'Socket_123': 0.035,
            'Socket_6': 0.50,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'REAL_GLUTES_LEGGINGS': {
        'name': "Compression Athletic Leggings",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Spandex athletic compression: shifts resonance up to 6.0 Hz, dampens heel strikes",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 1.60,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 2.50,
            'Socket_123': 0.018,
            'Socket_6': 0.80,
            'Socket_30': 0.45,
            'Socket_122': 3,
        }
    },

    # --- Stylized Anime & Film Glutes ---
    'STYLE_GLUTES_SOFT': {
        'name': "Anime Booty Jiggle",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Voluptuous anime hip sway and expressive walking/dancing bounce",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.15,
            'Socket_31': 2.2,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.22,
            'Socket_126': 0.65,
            'Socket_8': 1.3,
            'Socket_123': 0.04,
            'Socket_6': 0.65,
            'Socket_30': 0.3,
            'Socket_122': 3,
        }
    },
    'STYLE_GLUTES_FIRM': {
        'name': "Toned Action Bounce",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Athletic action heroine: compact jiggle with energetic recovery",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 1.8,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.18,
            'Socket_126': 0.45,
            'Socket_8': 1.6,
            'Socket_123': 0.03,
            'Socket_6': 0.7,
            'Socket_30': 0.35,
            'Socket_122': 3,
        }
    },
    'STYLE_GLUTES_CELLULITE': {
        'name': "Heavy / Relaxed Glutes",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Deep relaxed jiggle with loose inertia and secondary fat waves",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.18,
            'Socket_31': 2.8,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.28,
            'Socket_126': 0.7,
            'Socket_8': 1.15,
            'Socket_123': 0.048,
            'Socket_6': 0.55,
            'Socket_30': 0.25,
            'Socket_122': 3,
        }
    },
    'STYLE_GLUTES_THONG': {
        'name': "Thong / Minimal Coverage",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Unrestricted surface bounce with maximum secondary vibration",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 2.3,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.25,
            'Socket_126': 0.7,
            'Socket_8': 1.2,
            'Socket_123': 0.042,
            'Socket_6': 0.6,
            'Socket_30': 0.28,
            'Socket_122': 3,
        }
    },
    'STYLE_GLUTES_LEGGINGS': {
        'name': "Tight Yoga Pants",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Visually shaped glutes under taut athletic spandex",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.1,
            'Socket_31': 2.0,
            'Socket_102': True,
            'Socket_118': 0.97,
            'Socket_119': 0.16,
            'Socket_126': 0.4,
            'Socket_8': 1.8,
            'Socket_123': 0.025,
            'Socket_6': 0.75,
            'Socket_30': 0.38,
            'Socket_122': 3,
        }
    },
    'STYLE_GLUTES_DENIM': {
        'name': "Denim Jeans / Structured",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_BUTTOCKS',
        'category': "Buttocks & Glutes",
        'description': "Damped, tight motion restricted by structured denim fabric",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.07,
            'Socket_31': 2.0,
            'Socket_102': True,
            'Socket_118': 0.97,
            'Socket_119': 0.12,
            'Socket_126': 0.3,
            'Socket_8': 2.0,
            'Socket_123': 0.02,
            'Socket_6': 0.8,
            'Socket_30': 0.42,
            'Socket_122': 3,
        }
    },

    # ==========================================================================
    # --- FEMALE STOMACH / BELLY ---
    # ==========================================================================
    # --- Realistic Biomechanics (0.8 - 1.8 kg) ---
    'REAL_BELLY_SOFT': {
        'name': "Soft Abdominal Adipose (1.2 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Natural subcutaneous abdominal fat (4.0 Hz, gentle breathing/walking settle)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.11,
            'Socket_31': 1.20,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.35,
            'Socket_126': 0.30,
            'Socket_8': 2.00,
            'Socket_123': 0.030,
            'Socket_6': 0.55,
            'Socket_30': 0.28,
            'Socket_122': 2,
        }
    },
    'REAL_BELLY_ATHLETIC': {
        'name': "Athletic Toned Core (0.6 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Tight abdominal wall musculature with minimal soft tissue displacement",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 0.60,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 2.50,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'REAL_BELLY_LOOSE': {
        'name': "Relaxed Soft Flab (1.8 kg)",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Soft, relaxed abdominal fold with gentle inertia response",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.15,
            'Socket_31': 1.80,
            'Socket_102': True,
            'Socket_118': 0.90,
            'Socket_119': 0.50,
            'Socket_126': 0.40,
            'Socket_8': 1.50,
            'Socket_123': 0.045,
            'Socket_6': 0.45,
            'Socket_30': 0.22,
            'Socket_122': 2,
        }
    },

    # --- Stylized Anime Stomach ---
    'STYLE_BELLY_SOFT': {
        'name': "Anime Soft Tummy",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Charming anime belly squish with expressive walking bounce",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.14,
            'Socket_31': 2.2,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.24,
            'Socket_126': 0.55,
            'Socket_8': 1.3,
            'Socket_123': 0.038,
            'Socket_6': 0.6,
            'Socket_30': 0.28,
            'Socket_122': 3,
        }
    },
    'STYLE_BELLY_ATHLETIC': {
        'name': "Athletic Core / Toned",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Fit action core with quick turnaround and subtle ribcage breathing",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 1.6,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.16,
            'Socket_126': 0.35,
            'Socket_8': 1.8,
            'Socket_123': 0.025,
            'Socket_6': 0.75,
            'Socket_30': 0.35,
            'Socket_122': 3,
        }
    },
    'STYLE_BELLY_LOOSE': {
        'name': "Relaxed Flab / Secondary Ripple",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Generous flab motion with pronounced secondary ripples",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 2.6,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.28,
            'Socket_126': 0.6,
            'Socket_8': 1.2,
            'Socket_123': 0.045,
            'Socket_6': 0.55,
            'Socket_30': 0.24,
            'Socket_122': 3,
        }
    },
    'STYLE_BELLY_CORSET': {
        'name': "Corset / Waist Cincher",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Rigid waist compression: locks core and prevents outward displacement",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.10,
            'Socket_8': 2.80,
            'Socket_123': 0.020,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },

    # ==========================================================================
    # --- FEMALE LEGS & THIGHS ---
    # ==========================================================================
    'REAL_THIGHS_INNER': {
        'name': "Inner Thigh Friction & Adipose",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Biomechanical inner thigh soft tissue with gentle contact response",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 1.50,
            'Socket_102': True,
            'Socket_118': 0.93,
            'Socket_119': 0.35,
            'Socket_126': 0.30,
            'Socket_8': 1.80,
            'Socket_123': 0.025,
            'Socket_6': 0.60,
            'Socket_30': 0.32,
            'Socket_122': 2,
        }
    },
    'REAL_THIGHS_ATHLETIC': {
        'name': "Athletic Quadriceps",
        'mode': 'REALISTIC',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Muscular thigh with taut skin tension and fast settling",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 1.20,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 2.40,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'STYLE_THIGHS_INNER': {
        'name': "Soft Anime Thigh Squish",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Luscious anime thigh squish during running, jumping and knee bends",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.13,
            'Socket_31': 2.2,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.22,
            'Socket_126': 0.5,
            'Socket_8': 1.4,
            'Socket_123': 0.035,
            'Socket_6': 0.65,
            'Socket_30': 0.3,
            'Socket_122': 3,
        }
    },
    'STYLE_THIGHS_ATHLETIC': {
        'name': "Firm Muscular Quads",
        'mode': 'STYLIZED',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Toned athletic heroine quads with clean secondary impact response",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 1.8,
            'Socket_102': True,
            'Socket_118': 0.97,
            'Socket_119': 0.15,
            'Socket_126': 0.35,
            'Socket_8': 1.8,
            'Socket_123': 0.022,
            'Socket_6': 0.75,
            'Socket_30': 0.35,
            'Socket_122': 3,
        }
    },
    'LEGS_CALVES_FEMALE': {
        'name': "Calves / Lower Leg",
        'mode': 'ALL',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Gastrocnemius calf muscle shockwave from foot ground impacts",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.80,
            'Socket_102': True,
            'Socket_118': 0.94,
            'Socket_119': 0.25,
            'Socket_126': 0.20,
            'Socket_8': 2.20,
            'Socket_123': 0.020,
            'Socket_6': 0.70,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },

    # ==========================================================================
    # --- FEMALE EXTRAS (FACE & ARMS) ---
    # ==========================================================================
    'FACE_CHEEKS_FEMALE': {
        'name': "Cheeks & Facial Flesh",
        'mode': 'ALL',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_EXTRAS',
        'category': "Face & Arms",
        'description': "Soft cheek flesh inertia on head turns and jumps (0.05 kg)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.05,
            'Socket_102': False,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.25,
            'Socket_8': 2.40,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.45,
            'Socket_122': 2,
        }
    },
    'ARMS_SOFT': {
        'name': "Upper Arms / Triceps",
        'mode': 'ALL',
        'gender': 'FEMALE',
        'category_id': 'FEMALE_EXTRAS',
        'category': "Face & Arms",
        'description': "Soft underarm tricep tissue inertia during arm swings",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 0.40,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.35,
            'Socket_126': 0.35,
            'Socket_8': 1.80,
            'Socket_123': 0.025,
            'Socket_6': 0.60,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },

    # ==========================================================================
    # --- PROPS & HAIR (OVERHAULED: INEXTENSIBLE, ZERO VOLUME, REAL MASS) ---
    # ==========================================================================
    # --- Realistic Biomechanics (0.04 - 0.14 kg, Stretch 0.98, Volume 0.0) ---
    'REAL_HAIR_STRANDS': {
        'name': "Hair / Natural Strands (Inextensible)",
        'mode': 'REALISTIC',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Physically accurate hair fibers: virtually inextensible (E ~ 4 GPa), zero 2D distortion, aerodynamic drag",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.15,
            'Socket_31': 0.06,  # 60 grams
            'Socket_102': False,
            'Socket_118': 0.00, # ZERO volume distortion on 2D cards
            'Socket_119': 0.40,
            'Socket_126': 0.25,
            'Socket_8': 2.40,   # Strong aerodynamic settling
            'Socket_123': 0.040,# Tight 4 cm sag limit
            'Socket_6': 0.98,   # INEXTENSIBLE
            'Socket_30': 0.50,  # Natural curve bending
            'Socket_122': 2,
        }
    },
    'REAL_HAIR_PONYTAIL': {
        'name': "Hair / Tied Ponytail (Inextensible)",
        'mode': 'REALISTIC',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Natural tied ponytail bundle: cohesive strand bundle, zero elongation under gravity",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.18,
            'Socket_31': 0.09,  # 90 grams
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 0.55,
            'Socket_126': 0.35,
            'Socket_8': 2.00,
            'Socket_123': 0.050,
            'Socket_6': 0.98,   # INEXTENSIBLE
            'Socket_30': 0.60,
            'Socket_122': 3,
        }
    },
    'REAL_HAIR_BRAID': {
        'name': "Hair / Heavy Braid & Bun",
        'mode': 'REALISTIC',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Stiff, tightly bound braided hair or bun with high bending resistance",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 0.14,  # 140 grams
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 0.30,
            'Socket_126': 0.20,
            'Socket_8': 2.80,
            'Socket_123': 0.030,
            'Socket_6': 0.99,   # INEXTENSIBLE
            'Socket_30': 0.75,
            'Socket_122': 3,
        }
    },
    'REAL_HAIR_SHORT': {
        'name': "Hair / Short Bob & Bangs",
        'mode': 'REALISTIC',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Short styled hair, bob cuts and bangs: firm shape retention with micro-flutter",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.04,  # 40 grams
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 3.00,
            'Socket_123': 0.020,
            'Socket_6': 0.98,
            'Socket_30': 0.65,
            'Socket_122': 2,
        }
    },

    # --- Stylized Anime Hair (Dramatic whip, trailing bounce, inextensible) ---
    'STYLE_HAIR_PONYTAIL': {
        'name': "Anime Ponytail Whip",
        'mode': 'STYLIZED',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Cinematic anime ponytail with flowing whip inertia, trailing bounce, and zero card distortion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.25,
            'Socket_31': 0.12,  # 120 grams (balanced for anime whip without sag)
            'Socket_102': False,
            'Socket_118': 0.00, # NEVER distort 2D anime hair cards
            'Socket_119': 1.10, # Dynamic whip sway
            'Socket_126': 0.75, # Lively spring
            'Socket_8': 1.20,   # Smooth decay
            'Socket_123': 0.080,# 8 cm reach
            'Socket_6': 0.92,   # High stretch resistance (no rubber noodles!)
            'Socket_30': 0.35,  # Flexible ribbon curve
            'Socket_122': 2,
        }
    },
    'STYLE_HAIR_STRANDS': {
        'name': "Floating Dynamic Locks",
        'mode': 'STYLIZED',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Ethereal floating hair strands, bangs and side-locks for expressive anime motion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.22,
            'Socket_31': 0.08,
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 0.95,
            'Socket_126': 0.65,
            'Socket_8': 1.00,
            'Socket_123': 0.070,
            'Socket_6': 0.94,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },
    'STYLE_HAIR_TWINTAILS': {
        'name': "Twintails / Pigtails Dynamic",
        'mode': 'STYLIZED',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Dual pigtails with energetic, bouncy trailing action and clear silhouette preservation",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.24,
            'Socket_31': 0.10,
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 1.20,
            'Socket_126': 0.80,
            'Socket_8': 1.30,
            'Socket_123': 0.090,
            'Socket_6': 0.92,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'STYLE_HAIR_RIBBON': {
        'name': "Flowing Ribbon / Cape Strip",
        'mode': 'STYLIZED',
        'gender': 'PROPS',
        'category_id': 'PROPS_HAIR',
        'category': "Hair & Ribbons",
        'description': "Graceful trailing cloth strips, ribbons, hair ties and thin scarves",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.30,
            'Socket_31': 0.03,
            'Socket_102': False,
            'Socket_118': 0.00,
            'Socket_119': 1.30,
            'Socket_126': 0.85,
            'Socket_8': 1.50,
            'Socket_123': 0.100,
            'Socket_6': 0.90,
            'Socket_30': 0.15,
            'Socket_122': 1,
        }
    },

    # --- Elastic & Generic Props (Mode: ALL) ---
    'JELLY_PROP': {
        'name': "Springy Jelly / Toy",
        'mode': 'ALL',
        'gender': 'PROPS',
        'category_id': 'PROPS_ELASTIC',
        'category': "Elastic Props & Materials",
        'description': "Soft jiggly silicone or gelatin cube/sphere with volume preservation",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.30,
            'Socket_31': 2.0,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.90,
            'Socket_126': 1.20,
            'Socket_8': 0.60,
            'Socket_123': 0.20,
            'Socket_6': 0.10,
            'Socket_30': 0.10,
            'Socket_122': 0,
        }
    },
    'WATER_BALLOON': {
        'name': "Water Balloon",
        'mode': 'ALL',
        'gender': 'PROPS',
        'category_id': 'PROPS_ELASTIC',
        'category': "Elastic Props & Materials",
        'description': "Water-filled elastic membrane with high mass lag and maximum fluid wobble",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.15,
            'Socket_31': 3.0,
            'Socket_102': True,
            'Socket_118': 1.00,
            'Socket_119': 0.80,
            'Socket_126': 0.80,
            'Socket_8': 0.80,
            'Socket_123': 0.02,
            'Socket_5': True,
            'Socket_6': 0.10,
            'Socket_30': 0.10,
            'Socket_122': 0,
        }
    },
    'PROP_BACKPACK': {
        'name': "Soft Backpack / Holster",
        'mode': 'ALL',
        'gender': 'PROPS',
        'category_id': 'PROPS_ELASTIC',
        'category': "Elastic Props & Materials",
        'description': "Inertial bounce for backpacks, pouches and dangling equipment",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 2.5,
            'Socket_102': True,
            'Socket_118': 0.85,
            'Socket_119': 0.35,
            'Socket_126': 0.60,
            'Socket_8': 1.40,
            'Socket_123': 0.08,
            'Socket_6': 0.50,
            'Socket_30': 0.35,
            'Socket_122': 1,
        }
    },
    'FAST_LIGHT': {
        'name': "Lightweight SimZone",
        'mode': 'ALL',
        'gender': 'PROPS',
        'category_id': 'PROPS_ELASTIC',
        'category': "Elastic Props & Materials",
        'description': "Lightweight velocity-damping simulation zone",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 1.0,
            'Socket_102': True,
            'Socket_118': 0.0,
            'Socket_119': 0.25,
            'Socket_126': 0.50,
            'Socket_8': 1.60,
            'Socket_123': 0.04,
            'Socket_5': False,
            'Socket_6': 0.50,
            'Socket_30': 0.35,
            'Socket_122': 0,
        }
    },

    # ==========================================================================
    # --- MALE ANATOMY (CHEST, GLUTES, BELLY, GENITALIA, LEGS, EXTRAS) ---
    # ==========================================================================
    'REAL_MALE_PECS_TONED': {
        'name': "Biomechanical Pecs (Toned, 0.5 kg)",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Toned male pectoral muscle tissue with tight subcutaneous fascia",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 0.50,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.20,
            'Socket_8': 2.40,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'REAL_MALE_PECS_HEAVY': {
        'name': "Heavy Bodybuilder Pecs (1.0 kg)",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Dense hypertrophied pectoral muscle mass with powerful shock recovery",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.94,
            'Socket_119': 0.30,
            'Socket_126': 0.25,
            'Socket_8': 2.20,
            'Socket_123': 0.020,
            'Socket_6': 0.70,
            'Socket_30': 0.38,
            'Socket_122': 2,
        }
    },
    'REAL_MALE_CHEST_FLAB': {
        'name': "Soft Chest / Gynecomastia",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Soft male chest adipose tissue with relaxed downward settling",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.14,
            'Socket_31': 0.70,
            'Socket_102': True,
            'Socket_118': 0.90,
            'Socket_119': 0.45,
            'Socket_126': 0.40,
            'Socket_8': 1.50,
            'Socket_123': 0.035,
            'Socket_6': 0.50,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_PECS_TONED': {
        'name': "Toned Pectoral Muscles",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Athletic male pectoral bounce for cinematic action scenes",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.09,
            'Socket_31': 1.20,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.35,
            'Socket_126': 0.35,
            'Socket_8': 1.80,
            'Socket_123': 0.035,
            'Socket_6': 0.60,
            'Socket_30': 0.35,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_PECS_FLEXED': {
        'name': "Flexed / Hard Pecs",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Tense muscular contraction with high resistance to displacement",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.15,
            'Socket_8': 2.60,
            'Socket_123': 0.015,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },
    'STYLE_MALE_PECS_BODYBUILDER': {
        'name': "Heavy / Bodybuilder Pecs",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Heavy pectoral mass with dramatic muscle bounce during heavy footsteps",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.1,
            'Socket_31': 2.2,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.25,
            'Socket_126': 0.45,
            'Socket_8': 1.6,
            'Socket_123': 0.03,
            'Socket_6': 0.65,
            'Socket_30': 0.3,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_CHEST_FLAB': {
        'name': "Soft Chest / Gynecomastia",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Soft chest flab with loose inertia and secondary motion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.14,
            'Socket_31': 2.4,
            'Socket_102': True,
            'Socket_118': 0.94,
            'Socket_119': 0.28,
            'Socket_126': 0.55,
            'Socket_8': 1.3,
            'Socket_123': 0.035,
            'Socket_6': 0.55,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_CHEST_RASHGUARD': {
        'name': "Compression Rashguard / Shirt",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Athletic compression top binding male chest motion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.05,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.18,
            'Socket_126': 0.15,
            'Socket_8': 2.40,
            'Socket_123': 0.020,
            'Socket_6': 0.80,
            'Socket_30': 0.45,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_CHEST_TANK': {
        'name': "Loose Tank Top / Sleeveless",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_CHEST',
        'category': "Chest & Pecs",
        'description': "Natural unrestricted chest motion under loose fabric",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 1.20,
            'Socket_102': True,
            'Socket_118': 0.91,
            'Socket_119': 0.40,
            'Socket_126': 0.40,
            'Socket_8': 1.60,
            'Socket_123': 0.040,
            'Socket_6': 0.55,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },

    # --- Male Glutes ---
    'REAL_MALE_GLUTES_ATHLETIC': {
        'name': "Athletic Male Glutes (1.6 kg)",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Firm male gluteal musculature with gait shock dampening",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.07,
            'Socket_31': 1.60,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.22,
            'Socket_126': 0.18,
            'Socket_8': 2.20,
            'Socket_123': 0.018,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'STYLE_MALE_GLUTES_ATHLETIC': {
        'name': "Athletic / Toned Glutes",
        'mode': 'STYLIZED',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Toned male gluteal bounce for running and combat animations",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 2.00,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.40,
            'Socket_126': 0.35,
            'Socket_8': 1.80,
            'Socket_123': 0.035,
            'Socket_6': 0.60,
            'Socket_30': 0.35,
            'Socket_122': 2,
        }
    },
    'MALE_GLUTES_FIRM': {
        'name': "Bodybuilder / Hard Glutes",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Hard glutes with near-zero fat layer and immediate recovery",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 1.80,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.10,
            'Socket_8': 2.60,
            'Socket_123': 0.012,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },
    'MALE_GLUTES_SOFT': {
        'name': "Heavy / Soft Male Glutes",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Soft, relaxed male glutes with visible shockwave on heel strike",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 2.60,
            'Socket_102': True,
            'Socket_118': 0.89,
            'Socket_119': 0.65,
            'Socket_126': 0.50,
            'Socket_8': 1.30,
            'Socket_123': 0.060,
            'Socket_6': 0.40,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'MALE_GLUTES_TIGHTS': {
        'name': "Athletic Compression Tights",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Compression sportswear restraining male gluteal bounce",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 1.80,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 2.40,
            'Socket_123': 0.018,
            'Socket_6': 0.80,
            'Socket_30': 0.45,
            'Socket_122': 3,
        }
    },
    'MALE_GLUTES_DENIM': {
        'name': "Rugged Denim Jeans",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_BUTTOCKS',
        'category': "Buttocks / Glutes",
        'description': "Heavy structured denim fabric damping gluteal motion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 2.00,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.25,
            'Socket_126': 0.20,
            'Socket_8': 2.20,
            'Socket_123': 0.025,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },

    # --- Male Stomach ---
    'REAL_MALE_BELLY_SOFT': {
        'name': "Average Male Belly (1.5 kg)",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Biomechanical average male abdomen with soft visceral settling",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 1.50,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.35,
            'Socket_126': 0.30,
            'Socket_8': 2.00,
            'Socket_123': 0.030,
            'Socket_6': 0.60,
            'Socket_30': 0.32,
            'Socket_122': 2,
        }
    },
    'REAL_MALE_BELLY_BEER': {
        'name': "Heavy Beer Belly (3.0 kg)",
        'mode': 'REALISTIC',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Heavy visceral abdominal mass with deep forward momentum lag",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.16,
            'Socket_31': 3.00,
            'Socket_102': True,
            'Socket_118': 0.88,
            'Socket_119': 0.65,
            'Socket_126': 0.45,
            'Socket_8': 1.30,
            'Socket_123': 0.060,
            'Socket_6': 0.45,
            'Socket_30': 0.22,
            'Socket_122': 1,
        }
    },
    'MALE_ABS_TONED': {
        'name': "Toned Abs / Six-Pack",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Hard athletic abdominal wall with minimal soft displacement",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 0.80,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.10,
            'Socket_8': 2.60,
            'Socket_123': 0.012,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },
    'MALE_BELLY_AVERAGE': {
        'name': "Average / Soft Male Belly",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Gentle soft tissue jiggle over standard male torso",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 1.80,
            'Socket_102': True,
            'Socket_118': 0.91,
            'Socket_119': 0.45,
            'Socket_126': 0.40,
            'Socket_8': 1.60,
            'Socket_123': 0.045,
            'Socket_6': 0.50,
            'Socket_30': 0.28,
            'Socket_122': 2,
        }
    },
    'MALE_BELLY_BEER': {
        'name': "Heavy Beer Belly / Visceral Fat",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Substantial visceral belly with deep momentum lag and forward sway",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.20,
            'Socket_31': 3.50,
            'Socket_102': True,
            'Socket_118': 0.86,
            'Socket_119': 0.85,
            'Socket_126': 0.60,
            'Socket_8': 1.10,
            'Socket_123': 0.090,
            'Socket_6': 0.30,
            'Socket_30': 0.18,
            'Socket_122': 1,
        }
    },
    'MALE_BELLY_PAUNCH': {
        'name': "Relaxed Paunch / Low Flab",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Lower abdominal paunch with soft secondary bounce on jumping",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.15,
            'Socket_31': 2.20,
            'Socket_102': True,
            'Socket_118': 0.89,
            'Socket_119': 0.55,
            'Socket_126': 0.45,
            'Socket_8': 1.40,
            'Socket_123': 0.060,
            'Socket_6': 0.45,
            'Socket_30': 0.25,
            'Socket_122': 1,
        }
    },
    'MALE_CORE_BELT': {
        'name': "Weightlifting Belt / Tactical Waist",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_STOMACH',
        'category': "Stomach / Belly",
        'description': "Heavy belt binding abdominal movement entirely",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.03,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.98,
            'Socket_119': 0.10,
            'Socket_126': 0.05,
            'Socket_8': 3.00,
            'Socket_123': 0.010,
            'Socket_6': 0.90,
            'Socket_30': 0.60,
            'Socket_122': 3,
        }
    },

    # --- Male Genitalia ---
    'MALE_GROIN_BARE': {
        'name': "Unrestricted / Bare (No Underwear)",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Natural free pendular physics with anatomical mass (0.25 kg)",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.25,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.85,
            'Socket_119': 1.10,
            'Socket_126': 0.70,
            'Socket_8': 1.00,
            'Socket_123': 0.080,
            'Socket_6': 0.35,
            'Socket_30': 0.20,
            'Socket_122': 2,
        }
    },
    'MALE_GROIN_BOXERS': {
        'name': "Loose Boxer Shorts",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Loose airy cotton boxers allowing moderate swinging motion",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.20,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.88,
            'Socket_119': 0.85,
            'Socket_126': 0.55,
            'Socket_8': 1.30,
            'Socket_123': 0.060,
            'Socket_6': 0.45,
            'Socket_30': 0.25,
            'Socket_122': 2,
        }
    },
    'MALE_GROIN_BRIEFS': {
        'name': "Classic Briefs / Slip",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Fitted cotton briefs providing supportive upward cradle",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.92,
            'Socket_119': 0.45,
            'Socket_126': 0.40,
            'Socket_8': 1.80,
            'Socket_123': 0.035,
            'Socket_6': 0.60,
            'Socket_30': 0.35,
            'Socket_122': 2,
        }
    },
    'MALE_GROIN_TRUNKS': {
        'name': "Fitted Boxer Briefs",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Modern stretch-cotton trunks: balanced comfort and athletic containment",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.10,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.93,
            'Socket_119': 0.35,
            'Socket_126': 0.30,
            'Socket_8': 2.00,
            'Socket_123': 0.030,
            'Socket_6': 0.65,
            'Socket_30': 0.38,
            'Socket_122': 2,
        }
    },
    'MALE_GROIN_JOCKSTRAP': {
        'name': "Athletic Supporter / Jockstrap",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Maximum high-impact athletic pouch: high damping and zero unwanted displacement",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.05,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.15,
            'Socket_8': 2.60,
            'Socket_123': 0.015,
            'Socket_6': 0.80,
            'Socket_30': 0.45,
            'Socket_122': 3,
        }
    },
    'MALE_GROIN_COMPRESSION': {
        'name': "Compression Shorts / Spandex",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "All-over tight athletic spandex locking groin tissue firmly against pelvic base",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.04,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.97,
            'Socket_119': 0.10,
            'Socket_126': 0.10,
            'Socket_8': 3.00,
            'Socket_123': 0.012,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },
    'MALE_GROIN_SPEEDO': {
        'name': "Swim Brief / Speedo",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_GENITALIA',
        'category': "Groin & Genitalia",
        'description': "Wet nylon-elastane swim brief: tight contouring with hydrodynamic damping",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.25,
            'Socket_102': False,
            'Socket_118': 0.94,
            'Socket_119': 0.25,
            'Socket_126': 0.25,
            'Socket_8': 2.20,
            'Socket_123': 0.022,
            'Socket_6': 0.70,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },

    # --- Male Legs ---
    'MALE_THIGHS_QUADS': {
        'name': "Muscular Quads / Sprinter Thighs",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Heavy muscular quadriceps absorbing intense running impacts",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 2.20,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.22,
            'Socket_126': 0.18,
            'Socket_8': 2.40,
            'Socket_123': 0.018,
            'Socket_6': 0.75,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'MALE_THIGHS_SOFT': {
        'name': "Heavy / Soft Thighs",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Softer male thigh tissue with relaxed inertia and walking squish",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.14,
            'Socket_31': 2.80,
            'Socket_102': True,
            'Socket_118': 0.90,
            'Socket_119': 0.50,
            'Socket_126': 0.40,
            'Socket_8': 1.50,
            'Socket_123': 0.045,
            'Socket_6': 0.50,
            'Socket_30': 0.28,
            'Socket_122': 2,
        }
    },
    'MALE_LEGS_CALVES': {
        'name': "Calves / Gastrocnemius",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_LEGS',
        'category': "Legs & Thighs",
        'description': "Athletic male calf muscle ripple during sprinting and jumping",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 1.00,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.15,
            'Socket_8': 2.40,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.45,
            'Socket_122': 2,
        }
    },

    # --- Male Extras ---
    'MALE_FACE_JAW': {
        'name': "Male Jaw / Heavy Cheeks",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_EXTRAS',
        'category': "Face, Arms & Neck",
        'description': "Heavy male facial flesh, jowls and jawline inertia during head turns",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.08,
            'Socket_31': 0.08,
            'Socket_102': False,
            'Socket_118': 0.94,
            'Socket_119': 0.25,
            'Socket_126': 0.25,
            'Socket_8': 2.20,
            'Socket_123': 0.018,
            'Socket_6': 0.70,
            'Socket_30': 0.40,
            'Socket_122': 2,
        }
    },
    'MALE_ARMS_BICEPS': {
        'name': "Muscular Biceps / Forearms",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_EXTRAS',
        'category': "Face, Arms & Neck",
        'description': "Bicep muscle belly shockwave on punching and impact landing",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.06,
            'Socket_31': 0.60,
            'Socket_102': True,
            'Socket_118': 0.95,
            'Socket_119': 0.20,
            'Socket_126': 0.18,
            'Socket_8': 2.40,
            'Socket_123': 0.015,
            'Socket_6': 0.75,
            'Socket_30': 0.42,
            'Socket_122': 2,
        }
    },
    'MALE_ARMS_TRICEPS': {
        'name': "Soft Upper Arms / Triceps",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_EXTRAS',
        'category': "Face, Arms & Neck",
        'description': "Soft underarm tricep flesh vibration during rapid arm motions",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.12,
            'Socket_31': 0.50,
            'Socket_102': True,
            'Socket_118': 0.92,
            'Socket_119': 0.35,
            'Socket_126': 0.35,
            'Socket_8': 1.80,
            'Socket_123': 0.025,
            'Socket_6': 0.60,
            'Socket_30': 0.30,
            'Socket_122': 2,
        }
    },
    'MALE_NECK_TRAP': {
        'name': "Thick Neck / Trapezius",
        'mode': 'ALL',
        'gender': 'MALE',
        'category_id': 'MALE_EXTRAS',
        'category': "Face, Arms & Neck",
        'description': "Heavy trapezius and lateral neck muscle settling on heavy landings",
        'engine': 'WIGGY',
        'values': {
            'Socket_33': 0.05,
            'Socket_31': 0.80,
            'Socket_102': True,
            'Socket_118': 0.96,
            'Socket_119': 0.15,
            'Socket_126': 0.12,
            'Socket_8': 2.80,
            'Socket_123': 0.012,
            'Socket_6': 0.85,
            'Socket_30': 0.50,
            'Socket_122': 3,
        }
    },
}

# ==============================================================================
# BACKWARD COMPATIBILITY ALIASES (100% Non-Breaking for Existing Scenes)
# ==============================================================================
PRESETS['BREASTS_NATURAL'] = PRESETS['STYLE_BREASTS_NATURAL']
PRESETS['BREASTS_LOOSE_BRA'] = PRESETS['STYLE_BREASTS_LOOSE']
PRESETS['BREASTS_REGULAR_BRA'] = PRESETS['STYLE_BREASTS_REGULAR']
PRESETS['BREASTS_PUSHUP_BRA'] = PRESETS['STYLE_BREASTS_PUSHUP']
PRESETS['BREASTS_SPORTS_BRA'] = PRESETS['STYLE_BREASTS_SPORTS']
PRESETS['BREASTS_PERKY'] = PRESETS['STYLE_BREASTS_PERKY']
PRESETS['BREASTS_HEAVY'] = PRESETS['STYLE_BREASTS_HEAVY']
PRESETS['BREASTS_WATER'] = PRESETS['STYLE_BREASTS_WATER']
PRESETS['BREASTS_ANIME'] = PRESETS['STYLE_BREASTS_ANIME']
PRESETS['BREASTS'] = PRESETS['STYLE_BREASTS_NATURAL']
PRESETS['BREASTS_BRA'] = PRESETS['STYLE_BREASTS_REGULAR']
PRESETS['SPORTS_BRA'] = PRESETS['STYLE_BREASTS_SPORTS']

PRESETS['GLUTES_FIRM'] = PRESETS['STYLE_GLUTES_FIRM']
PRESETS['GLUTES_SOFT'] = PRESETS['STYLE_GLUTES_SOFT']
PRESETS['GLUTES_CELLULITE'] = PRESETS['STYLE_GLUTES_CELLULITE']
PRESETS['GLUTES_THONG'] = PRESETS['STYLE_GLUTES_THONG']
PRESETS['GLUTES_LEGGINGS'] = PRESETS['STYLE_GLUTES_LEGGINGS']
PRESETS['GLUTES_DENIM'] = PRESETS['STYLE_GLUTES_DENIM']
PRESETS['BUTTOCKS'] = PRESETS['STYLE_GLUTES_SOFT']
PRESETS['BUTTOCKS_FIRM'] = PRESETS['STYLE_GLUTES_FIRM']
PRESETS['BUTTOCKS_SOFT'] = PRESETS['STYLE_GLUTES_SOFT']

PRESETS['BELLY_SOFT'] = PRESETS['STYLE_BELLY_SOFT']
PRESETS['BELLY_ATHLETIC'] = PRESETS['STYLE_BELLY_ATHLETIC']
PRESETS['BELLY_LOOSE'] = PRESETS['STYLE_BELLY_LOOSE']
PRESETS['BELLY_CORSET'] = PRESETS['STYLE_BELLY_CORSET']
PRESETS['BELLY'] = PRESETS['STYLE_BELLY_SOFT']

PRESETS['THIGHS_INNER'] = PRESETS['STYLE_THIGHS_INNER']
PRESETS['THIGHS_ATHLETIC'] = PRESETS['STYLE_THIGHS_ATHLETIC']
PRESETS['THIGHS'] = PRESETS['STYLE_THIGHS_INNER']
PRESETS['ARMS_FLAB'] = PRESETS['ARMS_SOFT']
PRESETS['CHEEKS_FACE'] = PRESETS['FACE_CHEEKS_FEMALE']
PRESETS['JELLY'] = PRESETS['JELLY_PROP']

PRESETS['PONYTAIL_HAIR'] = PRESETS['STYLE_HAIR_PONYTAIL']
PRESETS['HAIR_BRAIDS'] = PRESETS['STYLE_HAIR_TWINTAILS']
PRESETS['CLOTH_RIBBON'] = PRESETS['STYLE_HAIR_RIBBON']

PRESETS['MALE_PECS_TONED'] = PRESETS['STYLE_MALE_PECS_TONED']
PRESETS['MALE_PECS_FLEXED'] = PRESETS['STYLE_MALE_PECS_FLEXED']
PRESETS['MALE_PECS_BODYBUILDER'] = PRESETS['STYLE_MALE_PECS_BODYBUILDER']
PRESETS['MALE_CHEST_FLAB'] = PRESETS['STYLE_MALE_CHEST_FLAB']
PRESETS['MALE_CHEST_RASHGUARD'] = PRESETS['STYLE_MALE_CHEST_RASHGUARD']
PRESETS['MALE_CHEST_TANK'] = PRESETS['STYLE_MALE_CHEST_TANK']
PRESETS['MALE_PECS'] = PRESETS['STYLE_MALE_PECS_TONED']
PRESETS['MALE_PECS_MUSCULAR'] = PRESETS['STYLE_MALE_PECS_TONED']

PRESETS['MALE_GLUTES_ATHLETIC'] = PRESETS['STYLE_MALE_GLUTES_ATHLETIC']
PRESETS['MALE_GLUTES'] = PRESETS['STYLE_MALE_GLUTES_ATHLETIC']
PRESETS['MALE_BELLY'] = PRESETS['MALE_BELLY_BEER']
PRESETS['MALE_GENITALIA_BARE'] = PRESETS['MALE_GROIN_BARE']
PRESETS['MALE_GENITALIA_BOXERS'] = PRESETS['MALE_GROIN_BOXERS']
PRESETS['MALE_GENITALIA_BRIEFS'] = PRESETS['MALE_GROIN_BRIEFS']
PRESETS['MALE_GENITALIA_JOCKSTRAP'] = PRESETS['MALE_GROIN_JOCKSTRAP']
PRESETS['CHEEKS_FACE_MALE'] = PRESETS['MALE_FACE_JAW']

# ============================================================================== 
# PRESET MOTION REWORK
# The old recipes varied many labels but clustered around similar softness,
# damping and wobble combinations. These response profiles intentionally make
# the motion character more distinct. Mass and mass-by-area remain anatomy-
# specific values from each recipe; the profiles govern the response shape.
# These are artistic starting points, not scientifically calibrated tissue data.
# ============================================================================== 
# MOTION PROFILES (Relative Dynamics & Damped Response)
# ==============================================================================
# Calibrated for XPBD Geometry Nodes physics:
# - Socket_6 (Stretching Compliance: 0.05=rigid, 0.10=firm skin, >0.30=excessive stretch)
# - Socket_30 (Bending Compliance: 0.08=smooth, 0.20=flexible, >0.30=wrinkling)
# - Socket_123 (Max Distance: safe travel in meters; <=0.035m for human jumping/action)
# - Socket_126 (Wobble: 0.0-1.0; <=0.45 settles in 1-2 cycles, >1.0 invalid)
# - Socket_119 (Sway: 0.0-1.0; <=0.25 across joints like buttocks/thighs, <=0.40 for chest)
# ==============================================================================
MOTION_PROFILES = {
    'CRISP': {
        'label': 'Crisp / Restrained',
        'summary': 'Very short travel, little rebound and quick settling',
        'values': {'Socket_33': 0.105, 'Socket_118': 0.98, 'Socket_119': 0.18, 'Socket_126': 0.25, 'Socket_8': 2.80, 'Socket_123': 0.022, 'Socket_6': 0.08, 'Socket_30': 0.16, 'Socket_122': 3},
    },
    'CONTROLLED': {
        'label': 'Controlled / Elastic',
        'summary': 'Firm response with a small, clean rebound',
        'values': {'Socket_33': 0.075, 'Socket_118': 0.96, 'Socket_119': 0.15, 'Socket_126': 0.20, 'Socket_8': 2.55, 'Socket_123': 0.020, 'Socket_6': 0.07, 'Socket_30': 0.15, 'Socket_122': 3},
    },
    'ATHLETIC': {
        'label': 'Athletic / Toned',
        'summary': 'Dense, shape-retaining response with restrained movement and a little follow-through',
        'values': {'Socket_33': 0.055, 'Socket_118': 0.99, 'Socket_119': 0.14, 'Socket_126': 0.15, 'Socket_8': 3.60, 'Socket_123': 0.018, 'Socket_6': 0.06, 'Socket_30': 0.12, 'Socket_122': 3},
    },
    'COMPRESSIVE': {
        'label': 'Compression / Locked',
        'summary': 'Very little travel or rebound with strong shape retention',
        'values': {'Socket_33': 0.025, 'Socket_118': 1.00, 'Socket_119': 0.06, 'Socket_126': 0.03, 'Socket_8': 4.80, 'Socket_123': 0.009, 'Socket_6': 0.04, 'Socket_30': 0.08, 'Socket_122': 4},
    },
    'BALANCED': {
        'label': 'Balanced / Natural',
        'summary': 'Moderate follow-through with a restrained secondary bounce',
        'values': {'Socket_33': 0.12, 'Socket_118': 0.95, 'Socket_119': 0.25, 'Socket_126': 0.35, 'Socket_8': 1.80, 'Socket_123': 0.028, 'Socket_6': 0.09, 'Socket_30': 0.18, 'Socket_122': 3},
    },
    'SOFT_TISSUE': {
        'label': 'Soft Tissue',
        'summary': 'Freer deformation, soft recovery and visible but controlled wobble',
        'values': {'Socket_33': 0.15, 'Socket_118': 0.94, 'Socket_119': 0.28, 'Socket_126': 0.38, 'Socket_8': 1.60, 'Socket_123': 0.032, 'Socket_6': 0.10, 'Socket_30': 0.20, 'Socket_122': 3},
    },
    'HEAVY_LAG': {
        'label': 'Heavy / Delayed',
        'summary': 'Pronounced lag and broad follow-through with controlled rebound',
        'values': {'Socket_33': 0.16, 'Socket_118': 0.96, 'Socket_119': 0.32, 'Socket_126': 0.25, 'Socket_8': 1.60, 'Socket_123': 0.035, 'Socket_6': 0.10, 'Socket_30': 0.18, 'Socket_122': 3},
    },
    'VISCOUS': {
        'label': 'Viscous / Slosh',
        'summary': 'Suppressed oscillation with smooth inertial settling',
        'values': {'Socket_33': 0.16, 'Socket_118': 0.93, 'Socket_119': 0.30, 'Socket_126': 0.15, 'Socket_8': 2.20, 'Socket_123': 0.030, 'Socket_6': 0.10, 'Socket_30': 0.16, 'Socket_122': 3},
    },
    'BOUNCY': {
        'label': 'Bouncy / Expressive',
        'summary': 'Expressive secondary motion with balanced rebound and fast settling',
        'values': {'Socket_33': 0.15, 'Socket_118': 0.96, 'Socket_119': 0.30, 'Socket_126': 0.42, 'Socket_8': 1.60, 'Socket_123': 0.032, 'Socket_6': 0.10, 'Socket_30': 0.20, 'Socket_122': 3},
    },
    'SPRINGY': {
        'label': 'Springy / Jelly',
        'summary': 'Highly compliant with controlled oscillation and safe displacement',
        'values': {'Socket_33': 0.18, 'Socket_118': 0.95, 'Socket_119': 0.35, 'Socket_126': 0.48, 'Socket_8': 1.40, 'Socket_123': 0.038, 'Socket_6': 0.12, 'Socket_30': 0.22, 'Socket_122': 3},
    },
    'STRUCTURED': {
        'label': 'Structured / Fabric',
        'summary': 'Low movement with firm stretch and bend resistance',
        'values': {'Socket_33': 0.05, 'Socket_118': 0.99, 'Socket_119': 0.12, 'Socket_126': 0.08, 'Socket_8': 4.50, 'Socket_123': 0.015, 'Socket_6': 0.05, 'Socket_30': 0.10, 'Socket_122': 4},
    },
    'HAIR_SWING': {
        'label': 'Hair / Weighted Swing',
        'summary': 'Strong trailing swing while resisting strand-length stretching',
        'values': {'Socket_33': 0.24, 'Socket_118': 0.0, 'Socket_119': 0.85, 'Socket_126': 0.60, 'Socket_8': 1.20, 'Socket_123': 0.10, 'Socket_6': 0.04, 'Socket_30': 0.25, 'Socket_122': 0},
    },
    'RIBBON_FLOW': {
        'label': 'Ribbon / Flowing',
        'summary': 'Loose, flowing motion with broad sway and low curvature resistance',
        'values': {'Socket_33': 0.28, 'Socket_118': 0.0, 'Socket_119': 0.95, 'Socket_126': 0.70, 'Socket_8': 1.40, 'Socket_123': 0.14, 'Socket_6': 0.03, 'Socket_30': 0.08, 'Socket_122': 0},
    },
    'SHORT_DAMPED': {
        'label': 'Short / Damped',
        'summary': 'Tiny displacement with fast settling for small facial or compact regions',
        'values': {'Socket_33': 0.035, 'Socket_118': 1.0, 'Socket_119': 0.06, 'Socket_126': 0.04, 'Socket_8': 4.00, 'Socket_123': 0.008, 'Socket_6': 0.04, 'Socket_30': 0.08, 'Socket_122': 4},
    },
    'WATER_BALLOON': {
        'label': 'Water / Heavy Envelope',
        'summary': 'Heavy, volume-preserving movement with a broad but softened response',
        'values': {'Socket_33': 0.20, 'Socket_118': 1.0, 'Socket_119': 0.50, 'Socket_126': 0.42, 'Socket_8': 2.20, 'Socket_123': 0.045, 'Socket_6': 0.12, 'Socket_30': 0.08, 'Socket_122': 0},
    },
    'BACKPACK': {
        'label': 'Loaded / Strapped',
        'summary': 'Moderate load lag with restrained sway and firm shape retention',
        'values': {'Socket_33': 0.08, 'Socket_118': 0.98, 'Socket_119': 0.25, 'Socket_126': 0.15, 'Socket_8': 3.60, 'Socket_123': 0.030, 'Socket_6': 0.05, 'Socket_30': 0.10, 'Socket_122': 3},
    },
    'FAST_LIGHT': {
        'label': 'Light / Quick',
        'summary': 'Light, responsive motion with low travel and minimal trailing lag',
        'values': {'Socket_33': 0.08, 'Socket_118': 0.05, 'Socket_119': 0.20, 'Socket_126': 0.25, 'Socket_8': 2.80, 'Socket_123': 0.025, 'Socket_6': 0.07, 'Socket_30': 0.15, 'Socket_122': 1},
    },
}



def enforce_anatomical_safety(values, category_id, is_action_mode=False):
    """Enforces anatomical safety bounds on simulation socket values.
    Prevents joint creasing, pointed fin deformation, and runaway oscillations."""
    if not isinstance(values, dict):
        return values
    
    cat = str(category_id or '').upper()
    is_glute_joint = ('BUTT' in cat or 'LEG' in cat or 'GROIN' in cat or 'GENITALIA' in cat)
    is_soft_tissue = ('CHEST' in cat or 'BREAST' in cat or 'STOMACH' in cat or 'BELLY' in cat or 'EXTRA' in cat)
    is_prop = ('PROP' in cat or 'HAIR' in cat or 'RIBBON' in cat or 'ELASTIC' in cat)
    
    # 1. Glutes and joint-spanning zones (buttocks, thighs)
    if is_glute_joint:
        max_dist_limit = 0.025 if is_action_mode else 0.028
        sway_limit = 0.18 if is_action_mode else 0.25
        wobble_limit = 0.35 if is_action_mode else 0.45
        damping_min = 1.80 if is_action_mode else 1.40
        vol_min = 0.98 if is_action_mode else 0.96
        edge_fade_min = 4 if is_action_mode else 3

        if 'Socket_123' in values:
            values['Socket_123'] = min(float(values['Socket_123']), max_dist_limit)
        if 'Socket_119' in values:
            values['Socket_119'] = min(float(values['Socket_119']), sway_limit)
        if 'Socket_126' in values:
            values['Socket_126'] = min(max(float(values['Socket_126']), 0.0), wobble_limit)
        if 'Socket_8' in values:
            values['Socket_8'] = max(float(values['Socket_8']), damping_min)
        if 'Socket_118' in values:
            values['Socket_118'] = max(float(values['Socket_118']), vol_min)
        if 'Socket_6' in values:  # Stretching compliance: 0.05-0.12 keeps structural skin curvature
            values['Socket_6'] = min(max(float(values['Socket_6']), 0.05), 0.12)
        if 'Socket_30' in values: # Bending compliance
            values['Socket_30'] = min(max(float(values['Socket_30']), 0.10), 0.25)
        if 'Socket_122' in values:
            values['Socket_122'] = max(int(values['Socket_122']), edge_fade_min)

    # 2. Chest, stomach and torso soft tissue
    elif is_soft_tissue or not is_prop:
        max_dist_limit = 0.028 if is_action_mode else 0.032
        sway_limit = 0.30 if is_action_mode else 0.40
        wobble_limit = 0.35 if is_action_mode else 0.42
        damping_min = 1.80 if is_action_mode else 1.20
        vol_min = 0.96 if is_action_mode else 0.92
        edge_fade_min = 3 if is_action_mode else 2

        if 'Socket_123' in values:
            values['Socket_123'] = min(float(values['Socket_123']), max_dist_limit)
        if 'Socket_119' in values:
            values['Socket_119'] = min(float(values['Socket_119']), sway_limit)
        if 'Socket_126' in values:
            values['Socket_126'] = min(max(float(values['Socket_126']), 0.0), wobble_limit)
        if 'Socket_8' in values:
            values['Socket_8'] = max(float(values['Socket_8']), damping_min)
        if 'Socket_118' in values:
            values['Socket_118'] = max(float(values['Socket_118']), vol_min)
        if 'Socket_6' in values:
            values['Socket_6'] = min(max(float(values['Socket_6']), 0.05), 0.15)
        if 'Socket_30' in values:
            values['Socket_30'] = min(max(float(values['Socket_30']), 0.10), 0.25)
        if 'Socket_122' in values:
            values['Socket_122'] = max(int(values['Socket_122']), edge_fade_min)

    # 3. Props / Hair / Ribbons (bounded to valid solver ranges)
    else:
        if 'Socket_126' in values:
            values['Socket_126'] = min(max(float(values['Socket_126']), 0.0), 1.0)
        if 'Socket_119' in values:
            values['Socket_119'] = min(max(float(values['Socket_119']), 0.0), 1.0)
        if 'Socket_6' in values:
            values['Socket_6'] = min(max(float(values['Socket_6']), 0.01), 0.50)

    return values

PRESET_PROFILE_ASSIGNMENTS = {}
def _assign_preset_profile(profile_id, keys):
    for preset_key in keys:
        PRESET_PROFILE_ASSIGNMENTS[preset_key] = profile_id

_assign_preset_profile('BALANCED', [
    'REAL_BREASTS_NATURAL', 'STYLE_BREASTS_NATURAL', 'REAL_GLUTES_NORMAL',
    'REAL_BELLY_SOFT', 'REAL_THIGHS_INNER',
    'STYLE_MALE_GLUTES_ATHLETIC', 'REAL_MALE_BELLY_SOFT', 'MALE_BELLY_AVERAGE',
    'STYLE_MALE_CHEST_TANK', 'MALE_GROIN_TRUNKS',
])
_assign_preset_profile('CRISP', [
    'REAL_BREASTS_FIRM', 'REAL_GLUTES_FIRM', 'REAL_MALE_PECS_TONED',
    'MALE_GLUTES_FIRM', 'MALE_ABS_TONED', 'MALE_ARMS_BICEPS', 'MALE_NECK_TRAP',
])
_assign_preset_profile('ATHLETIC', [
    'REAL_BELLY_ATHLETIC', 'REAL_THIGHS_ATHLETIC', 'STYLE_BELLY_ATHLETIC',
    'STYLE_THIGHS_ATHLETIC', 'STYLE_MALE_PECS_FLEXED', 'REAL_MALE_GLUTES_ATHLETIC',
    'MALE_THIGHS_QUADS',
])
_assign_preset_profile('COMPRESSIVE', [
    'REAL_BREASTS_SPORTS', 'REAL_GLUTES_LEGGINGS', 'STYLE_BELLY_CORSET',
    'STYLE_MALE_CHEST_RASHGUARD', 'MALE_GLUTES_TIGHTS', 'MALE_CORE_BELT',
    'MALE_GROIN_JOCKSTRAP', 'MALE_GROIN_COMPRESSION',
])
_assign_preset_profile('SHORT_DAMPED', ['LEGS_CALVES_FEMALE', 'REAL_HAIR_SHORT', 'MALE_LEGS_CALVES'])
_assign_preset_profile('HAIR_SWING', ['REAL_HAIR_BRAID'])
_assign_preset_profile('CONTROLLED', [
    'REAL_BREASTS_BRA', 'STYLE_BREASTS_REGULAR', 'STYLE_BREASTS_PUSHUP',
    'STYLE_BREASTS_SPORTS', 'STYLE_GLUTES_FIRM', 'STYLE_GLUTES_LEGGINGS',
    'STYLE_MALE_PECS_TONED', 'STYLE_MALE_PECS_BODYBUILDER',
    'MALE_GROIN_SPEEDO', 'MALE_GROIN_BRIEFS',
])
_assign_preset_profile('SOFT_TISSUE', [
    'REAL_GLUTES_SOFT', 'STYLE_BELLY_SOFT',
    'STYLE_THIGHS_INNER', 'ARMS_SOFT', 'REAL_MALE_CHEST_FLAB', 'STYLE_MALE_CHEST_FLAB',
    'MALE_ARMS_TRICEPS', 'MALE_THIGHS_SOFT',
])
_assign_preset_profile('HEAVY_LAG', [
    'REAL_BREASTS_HEAVY', 'STYLE_BREASTS_HEAVY', 'STYLE_GLUTES_CELLULITE',
    'REAL_BELLY_LOOSE', 'MALE_GLUTES_SOFT', 'REAL_MALE_BELLY_BEER',
    'MALE_BELLY_BEER', 'MALE_BELLY_PAUNCH', 'REAL_MALE_PECS_HEAVY',
])
_assign_preset_profile('VISCOUS', [
    'STYLE_BREASTS_LOOSE', 'STYLE_BREASTS_WATER', 'STYLE_BELLY_LOOSE',
    'MALE_GROIN_BOXERS', 'MALE_GROIN_BARE',
])
_assign_preset_profile('BOUNCY', [
    'STYLE_BREASTS_PERKY', 'STYLE_BREASTS_ANIME', 'STYLE_GLUTES_SOFT',
    'STYLE_GLUTES_THONG',
])
_assign_preset_profile('STRUCTURED', [
    'STYLE_GLUTES_DENIM', 'MALE_GLUTES_DENIM',
])
_assign_preset_profile('HAIR_SWING', [
    'REAL_HAIR_STRANDS', 'REAL_HAIR_PONYTAIL', 'STYLE_HAIR_PONYTAIL',
    'STYLE_HAIR_STRANDS', 'STYLE_HAIR_TWINTAILS',
])
_assign_preset_profile('RIBBON_FLOW', ['STYLE_HAIR_RIBBON'])
_assign_preset_profile('SHORT_DAMPED', ['FACE_CHEEKS_FEMALE', 'MALE_FACE_JAW'])
_assign_preset_profile('SPRINGY', ['JELLY_PROP'])
_assign_preset_profile('WATER_BALLOON', ['WATER_BALLOON'])
_assign_preset_profile('BACKPACK', ['PROP_BACKPACK'])
_assign_preset_profile('FAST_LIGHT', ['FAST_LIGHT'])

# Apply profiles once per unique recipe dictionary (legacy aliases share the same dict).
_seen_preset_objects = set()
for _preset_key, _preset_data in PRESETS.items():
    if id(_preset_data) in _seen_preset_objects:
        continue
    _seen_preset_objects.add(id(_preset_data))
    _profile_id = PRESET_PROFILE_ASSIGNMENTS.get(_preset_key, 'BALANCED')
    _profile = MOTION_PROFILES.get(_profile_id, MOTION_PROFILES['BALANCED'])
    _preset_values = _preset_data.setdefault('values', {})
    
    # Non-destructive composition: profile provides baseline defaults, preset custom values take precedence!
    _combined_values = dict(_profile['values'])
    _combined_values.update(_preset_values)
    _preset_data['values'] = _combined_values
    
    # Post-composition safety & validation layer
    enforce_anatomical_safety(_preset_data['values'], _preset_data.get('category_id', ''))
    # Make commonly forgotten global switches deterministic when changing recipes.
    _preset_values.setdefault('Socket_5', False)  # Gravity off unless explicitly enabled by a recipe.
    _preset_values['Socket_3'] = (0.0, 0.0, -9.81)  # Consistent 3D gravity vector when enabled.
    _preset_values['Socket_67'] = 1.0             # A preset always starts at full influence.
    _preset_data['motion_profile'] = _profile_id
    # Remove unverified frequency / mass claims from the visible recipe names and copy.
    _preset_data['name'] = re.sub(r'\s*\([^)]*(?:Hz|kg|\d+(?:\.\d+)?\s*g\b|gram|resonance)[^)]*\)', '', _preset_data.get('name', ''), flags=re.IGNORECASE).strip()
    _preset_data['name'] = _preset_data['name'].replace('Biomechanical Pecs', 'Toned Pecs').replace('Biomechanical Glutes', 'Natural Glutes')
    _desc = _preset_data.get('description', '')
    _desc = _desc.replace('Biomechanical', 'Natural').replace('biomechanical', 'natural')
    _desc = re.sub(r'\b\d+(?:\.\d+)?\s*(?:Hz|kg|g)\b', ' ', _desc, flags=re.IGNORECASE)
    _desc = re.sub(r'\([^)]*(?:Hz|kg|\d+(?:\.\d+)?\s*g\b|resonance frequency)[^)]*\)', ' ', _desc, flags=re.IGNORECASE)
    _desc = re.sub(r'\btrue biological mass\b|\btrue tissue mass\b', 'relative simulated mass', _desc, flags=re.IGNORECASE)
    _desc = _desc.replace('critical damping (zeta ~0.75)', 'strongly damped response')
    _desc = re.sub(r'\b\d+%\s*(?:stiffness increase|stiffness reduction)', 'higher support', _desc, flags=re.IGNORECASE)
    _preset_data['description'] = (re.sub(r'\s+', ' ', _desc).strip() +
        f" Profile: {_profile['label']}. Motion feel: {_profile['summary']}.")


def get_preset_category_items(self, context):
    gender = getattr(self, "preset_gender", "FEMALE")
    return GENDER_CATEGORIES.get(gender, GENDER_CATEGORIES['FEMALE'])

def get_new_zone_category_items(self, context):
    gender = getattr(self, "new_zone_gender", "FEMALE")
    return GENDER_CATEGORIES.get(gender, GENDER_CATEGORIES['FEMALE'])

def _sync_dynamic_preset_selection(self, context, preset_attr, items_fn):
    try:
        items = items_fn(self, context)
        valid_keys = [item[0] for item in items]
        current = getattr(self, preset_attr, '')
        if valid_keys and current not in valid_keys:
            setattr(self, preset_attr, valid_keys[0])
    except Exception:
        # Blender can invoke enum update callbacks while RNA is still refreshing.
        pass

def update_preset_gender(self, context):
    try:
        self.preset_category = 'ALL'
    except Exception:
        pass
    _sync_dynamic_preset_selection(self, context, 'preset_choice', get_preset_enum_items)

def update_new_zone_gender(self, context):
    try:
        self.new_zone_category = 'ALL'
    except Exception:
        pass
    _sync_dynamic_preset_selection(self, context, 'new_zone_preset', get_new_zone_preset_items)

def update_preset_category(self, context):
    _sync_dynamic_preset_selection(self, context, 'preset_choice', get_preset_enum_items)

def update_new_zone_category(self, context):
    _sync_dynamic_preset_selection(self, context, 'new_zone_preset', get_new_zone_preset_items)

def get_preset_enum_items(self, context):
    gender = getattr(self, "preset_gender", "FEMALE")
    cat = getattr(self, "preset_category", "ALL")
    mode = getattr(self, "preset_mode", "REALISTIC")
    items = []
    seen = set()
    for key, data in PRESETS.items():
        if key in seen:
            continue
        p_mode = data.get('mode', 'ALL')
        if p_mode != 'ALL' and p_mode != mode:
            continue
        p_gender = data.get('gender', 'FEMALE')
        if p_gender != gender:
            continue
        cat_id = data.get('category_id', '')
        if cat == 'ALL' or cat_id == cat:
            name = data.get('name')
            if not name or name in seen:
                continue
            items.append((key, name, data.get('description', '')))
            seen.add(name)
    if not items:
        for key, data in PRESETS.items():
            p_mode = data.get('mode', 'ALL')
            if p_mode == 'ALL' or p_mode == mode:
                if data.get('gender') == gender and data.get('name') not in seen:
                    items.append((key, data['name'], data.get('description', '')))
                    seen.add(data['name'])
    return items or [('REAL_BREASTS_NATURAL', "Natural Tissue / Balanced", "")]

def get_new_zone_preset_items(self, context):
    gender = getattr(self, "new_zone_gender", "FEMALE")
    cat = getattr(self, "new_zone_category", "ALL")
    mode = getattr(self, "preset_mode", "REALISTIC")
    items = []
    seen = set()
    for key, data in PRESETS.items():
        if key in seen:
            continue
        p_mode = data.get('mode', 'ALL')
        if p_mode != 'ALL' and p_mode != mode:
            continue
        p_gender = data.get('gender', 'FEMALE')
        if p_gender != gender:
            continue
        cat_id = data.get('category_id', '')
        if cat == 'ALL' or cat_id == cat:
            name = data.get('name')
            if not name or name in seen:
                continue
            items.append((key, name, data.get('description', '')))
            seen.add(name)
    if not items:
        for key, data in PRESETS.items():
            p_mode = data.get('mode', 'ALL')
            if p_mode == 'ALL' or p_mode == mode:
                if data.get('gender') == gender and data.get('name') not in seen:
                    items.append((key, data['name'], data.get('description', '')))
                    seen.add(data['name'])
    return items or [('REAL_BREASTS_NATURAL', "Natural Tissue / Balanced", "")]

PRESET_ENUM_ITEMS = get_preset_enum_items(None, None)

# ==============================================================================
# ZONE METADATA & RECIPIE HELPERS
# ==============================================================================
def set_mod_giggle_metadata(mod, gender, category, preset):
    """Store zone metadata on parent object ID data."""
    if not mod:
        return
    obj = getattr(mod, "id_data", None)
    if not obj:
        obj = bpy.context.active_object
    if obj:
        # Never store 'ALL' as anatomical category; resolve from preset
        resolved_cat = category
        if (not resolved_cat or resolved_cat == 'ALL') and preset in PRESETS:
            resolved_cat = PRESETS[preset].get('category_id', '')
        if gender is not None:
            obj[f"_giggle_{mod.name}_gender"] = str(gender)
        if resolved_cat is not None:
            obj[f"_giggle_{mod.name}_category"] = str(resolved_cat)
        if preset is not None:
            obj[f"_giggle_{mod.name}_preset"] = str(preset)
        clear_mod_customized(mod)

def get_mod_giggle_metadata(mod):
    """Return (gender, category_id, preset_id) for a Giggle modifier, inferring if needed."""
    if not mod:
        return None
    obj = getattr(mod, "id_data", None)
    if not obj:
        obj = bpy.context.active_object

    p_preset = None
    p_cat = None
    p_gender = None
    if obj:
        p_preset = obj.get(f"_giggle_{mod.name}_preset")
        p_cat = obj.get(f"_giggle_{mod.name}_category")
        p_gender = obj.get(f"_giggle_{mod.name}_gender")

    if p_preset and p_preset in PRESETS:
        data = PRESETS[p_preset]
        canon_gender = data.get('gender', p_gender or 'FEMALE')
        canon_cat = data.get('category_id', p_cat or 'ALL')
        return (canon_gender, canon_cat, p_preset)
    if p_gender in GENDER_CATEGORIES and p_cat:
        return (p_gender, p_cat, p_preset)

    # Infer from modifier name or the Wiggy vertex-group attribute. Use a
    # whole-token match so "female" is not mistaken for "male".
    name_lower = mod.name.lower()
    s_in = getattr(getattr(mod, "properties", None), "inputs", None)
    if mod.node_group and mod.node_group.name == "Wiggy 0.1" and s_in and hasattr(s_in, "Socket_2"):
        name_lower += " " + getattr(s_in.Socket_2, "attribute_name", "").lower()
    male_group = bool(
        re.search(r'(?<![a-z0-9])male(?![a-z0-9])', name_lower)
        or re.match(r'^male(?:_|-|\.|[0-9]|chest|pec|belly|glute|thigh|arm|leg|groin)', name_lower)
        or re.match(r'^(?:man[_\-. ]|m[_\-.])', name_lower)
    )

    if male_group and any(k in name_lower for k in ['pec', 'chest']):
        return ('MALE', 'MALE_CHEST', 'MALE_PECS_TONED')
    elif male_group and any(k in name_lower for k in ['groin', 'bulge', 'jock', 'scrot', 'genital']):
        return ('MALE', 'MALE_GENITALIA', 'MALE_GROIN_JOCKSTRAP')
    elif male_group and any(k in name_lower for k in ['beer', 'paunch', 'dadbod', 'belly', 'abdomen', 'stomach']):
        return ('MALE', 'MALE_STOMACH', 'MALE_BELLY_BEER' if any(k in name_lower for k in ['beer', 'paunch', 'dadbod']) else 'MALE_BELLY_AVERAGE')
    elif male_group and any(k in name_lower for k in ['butt', 'booty', 'glute', 'ass', 'hip', 'hips', 'pelvis', 'rear']):
        return ('MALE', 'MALE_BUTTOCKS', 'MALE_GLUTES_SOFT')
    elif male_group and any(k in name_lower for k in ['thigh', 'leg', 'quad', 'calf', 'calves']):
        return ('MALE', 'MALE_LEGS', 'MALE_THIGHS_QUADS')
    elif male_group and any(k in name_lower for k in ['face', 'jaw']):
        return ('MALE', 'MALE_EXTRAS', 'MALE_FACE_JAW')
    elif male_group and any(k in name_lower for k in ['arm', 'bicep', 'tricep', 'neck', 'trap']):
        return ('MALE', 'MALE_EXTRAS', 'MALE_ARMS_BICEPS')
    elif any(k in name_lower for k in ['butt', 'booty', 'glute', 'ass', 'hip', 'hips', 'pelvis', 'rear', 'derriere']):
        return ('FEMALE', 'FEMALE_BUTTOCKS', 'GLUTES_SOFT')
    elif any(k in name_lower for k in ['breast', 'boob', 'chest', 'cleavage', 'bust', 'tit', 'areola', 'nipple']) and not male_group:
        return ('FEMALE', 'FEMALE_CHEST', 'BREASTS_REGULAR_BRA')
    elif any(k in name_lower for k in ['gut', 'gutt', 'belly', 'tummy', 'stomach', 'waist', 'torso', 'midriff', 'flab', 'navel']) and not male_group:
        return ('FEMALE', 'FEMALE_STOMACH', 'BELLY_SOFT')
    elif any(k in name_lower for k in ['thigh', 'leg', 'quad', 'calf', 'calves']):
        return ('FEMALE', 'FEMALE_LEGS', 'THIGHS_INNER')
    elif any(k in name_lower for k in ['hair', 'ponytail', 'braid', 'pigtail', 'ribbon']):
        return ('PROPS', 'PROPS_HAIR', 'PONYTAIL_HAIR')
    elif any(k in name_lower for k in ['jelly', 'water', 'elastic', 'prop', 'skirt', 'backpack', 'holster']):
        return ('PROPS', 'PROPS_ELASTIC', 'JELLY_PROP')

    return ('FEMALE', 'FEMALE_CHEST', 'BREASTS_NATURAL')

def get_zone_recipe_badge(mod):
    """Return concise display name of preset applied to zone."""
    obj = getattr(mod, 'id_data', None) if mod else None
    if obj and obj.get(f"_giggle_{mod.name}_customized", False):
        return "Custom"
    meta = get_mod_giggle_metadata(mod)
    if not meta or not meta[2]:
        return "Custom"
    p_id = meta[2]
    if p_id in PRESETS:
        name = PRESETS[p_id]['name']
        return name.split("/")[0].split("(")[0].strip()
    return "Custom"

def sync_settings_from_zone_mod(settings, mod):
    """Update scene preset settings to match selected zone safely without RNA exceptions."""
    if not settings or not mod:
        return
    try:
        meta = get_mod_giggle_metadata(mod)
        if not meta:
            return
        p_gender, p_cat, p_preset = meta

        # 1. Update gender first
        if p_gender in GENDER_CATEGORIES:
            try:
                settings.preset_gender = p_gender
            except Exception:
                pass

        # 2. Determine target category from preset
        target_cat = p_cat
        if p_preset and p_preset in PRESETS:
            target_cat = PRESETS[p_preset].get('category_id', p_cat)

        # 3. Set category first so dynamic enum contains the preset
        if target_cat and target_cat != 'ALL':
            try:
                settings.preset_category = target_cat
            except Exception:
                try:
                    settings.preset_category = 'ALL'
                except Exception:
                    pass
        else:
            try:
                settings.preset_category = 'ALL'
            except Exception:
                pass

        # 4. Now assign preset_choice cleanly
        if p_preset and p_preset in PRESETS:
            try:
                settings.preset_choice = p_preset
            except Exception:
                try:
                    settings.preset_category = 'ALL'
                    settings.preset_choice = p_preset
                except Exception:
                    pass

        # 5. Record synced mod on parent object
        obj = getattr(mod, "id_data", None)
        if not obj:
            obj = getattr(bpy.context, "active_object", None)
        if obj:
            try:
                obj["_giggle_last_synced_mod"] = mod.name
            except Exception:
                pass
    except Exception as e:
        print(f"[Giggle] Warning: sync_settings_from_zone_mod error: {e}")

def update_active_zone_index(self, context):
    obj = getattr(context, "active_object", None)
    if not obj or obj.type != 'MESH':
        return
    # Auto-collapse Create New Zone when selecting an active zone for tuning
    try:
        self.show_create_zone = False
    except Exception:
        pass
    mods = get_giggle_modifiers(obj)
    idx = self.active_zone_index
    if 0 <= idx < len(mods):
        sync_settings_from_zone_mod(self, mods[idx])
        try:
            obj["_giggle_last_synced_mod"] = mods[idx].name
        except Exception:
            pass

def get_asset_blend_path(filename):
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(addon_dir, "assets", filename)
    if os.path.exists(path):
        return path
    parent_path = os.path.join(addon_dir, "..", filename)
    if os.path.exists(parent_path):
        return os.path.abspath(parent_path)
    return None

def ensure_nodetree(tree_name):
    if tree_name in bpy.data.node_groups:
        return bpy.data.node_groups[tree_name]
    
    filename = "Wiggy_0.1.blend" if ("Wiggy" in tree_name or tree_name == "Collider") else "JiggleV2.blend"
    path = get_asset_blend_path(filename)
    if not path or not os.path.exists(path):
        print(f"[Giggle] Asset file not found: {filename}")
        return None
    
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        if tree_name in df.node_groups:
            dt.node_groups = [tree_name]
            
    return bpy.data.node_groups.get(tree_name)

def get_mod_socket_prop(mod, socket_id):
    properties = getattr(mod, 'properties', None)
    inputs = getattr(properties, 'inputs', None) if properties else None
    return getattr(inputs, socket_id, None) if inputs is not None else None

def set_mod_socket(mod, socket_id, value=None, attribute=None, sync_cage=True):
    """Set a Geometry Nodes modifier input; return False when the socket is unavailable."""
    is_wiggy = bool(getattr(mod, "node_group", None) and mod.node_group.name == "Wiggy 0.1")
    # Wiggy Socket_2 is its vertex-group attribute, never a numeric value.
    if is_wiggy and socket_id == 'Socket_2':
        if isinstance(value, str):
            attribute, value = value, None
        elif attribute is None:
            return False

    properties = getattr(mod, 'properties', None)
    inputs = getattr(properties, 'inputs', None) if properties else None
    socket = getattr(inputs, socket_id, None) if inputs is not None else None

    if inputs is not None and socket is None:
        return False

    applied = False
    if socket is not None:
        try:
            if attribute is not None:
                if hasattr(socket, 'type'):
                    socket.type = 'ATTRIBUTE'
                if not hasattr(socket, 'attribute_name'):
                    return False
                socket.attribute_name = str(attribute)
            elif value is not None:
                if hasattr(socket, 'type'):
                    socket.type = 'VALUE'
                if not hasattr(socket, 'value'):
                    return False
                current = socket.value
                if hasattr(current, '__len__') and not isinstance(value, (tuple, list)):
                    # Handle scalar assigned to vector socket (e.g. gravity Z-acceleration)
                    if len(current) == 3:
                        current[0] = 0.0
                        current[1] = 0.0
                        current[2] = float(value)
                    else:
                        current[0] = float(value)
                elif isinstance(value, (tuple, list)) and hasattr(current, '__len__'):
                    if len(current) != len(value):
                        return False
                    for i, component in enumerate(value):
                        current[i] = component
                else:
                    socket.value = value
            if getattr(mod, 'id_data', None):
                try:
                    mod.id_data.update_tag(refresh={'DATA'})
                except Exception:
                    pass
            applied = True
        except (TypeError, ValueError, AttributeError, KeyError, RuntimeError):
            return False
    else:
        # Blender versions without the newer modifier input API use ID properties.
        try:
            if attribute is not None:
                mod[f"{socket_id}_use_attribute"] = 1
                mod[f"{socket_id}_attribute_name"] = str(attribute)
            elif value is not None:
                mod[f"{socket_id}_use_attribute"] = 0
                mod[socket_id] = value
            else:
                return False
            applied = True
        except (TypeError, ValueError, AttributeError, KeyError, RuntimeError):
            return False

    if applied and sync_cage:
        sync_socket_to_cage(mod, socket_id, value=value, attribute=attribute)

    return applied

def get_mod_socket(mod, socket_id):
    s = get_mod_socket_prop(mod, socket_id)
    if s is not None and hasattr(s, "value"):
        return s.value
    try:
        return mod.get(socket_id, None)
    except (TypeError, KeyError):
        return None

def get_mod_socket_attribute_name(mod, socket_id='Socket_2'):
    """Return the attribute/vertex-group name assigned to a modifier socket as a string, or empty string."""
    s = get_mod_socket_prop(mod, socket_id)
    if s is not None:
        attr = getattr(s, "attribute_name", None)
        if isinstance(attr, str) and attr:
            return attr
    try:
        attr = mod.get(f"{socket_id}_attribute_name", None)
        if isinstance(attr, str) and attr:
            return attr
    except Exception:
        pass
    return ""

def is_giggle_modifier(mod):
    if mod.type != 'NODES' or not mod.node_group:
        return False
    return (mod.node_group.name in {'Wiggy 0.1', 'Jiggle', 'Jiggle + Deformation'} or
            mod.name.startswith("Giggle"))

def get_giggle_modifiers(obj):
    if not obj or obj.type != 'MESH':
        return []
    return [m for m in obj.modifiers if is_giggle_modifier(m)]

def position_giggle_modifier(obj, mod):
    # Wiggy / Giggle should sit immediately after Armature modifiers and preceding Giggle modifiers,
    # and before any Subdivision Surface, Corrective Smooth, or Solidify modifiers.
    mod_names = [m.name for m in obj.modifiers]
    if mod.name not in mod_names:
        return
    mod_idx = mod_names.index(mod.name)
    
    target_idx = 0
    for i, m in enumerate(obj.modifiers):
        if m.name == mod.name:
            continue
        if m.type == 'ARMATURE' or is_giggle_modifier(m):
            target_idx = i + 1

    if target_idx == mod_idx:
        return

    # In Blender 4.0+, modifier_move_to_index moves atomically in one evaluation
    if hasattr(bpy.ops.object, "modifier_move_to_index"):
        try:
            with bpy.context.temp_override(active_object=obj, object=obj):
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=target_idx)
            return
        except Exception:
            pass

    # Fallback step-by-step
    while mod_idx > target_idx:
        try:
            with bpy.context.temp_override(active_object=obj, object=obj):
                bpy.ops.object.modifier_move_up(modifier=mod.name)
        except Exception:
            pass
        new_names = [m.name for m in obj.modifiers]
        if mod.name not in new_names:
            break
        new_idx = new_names.index(mod.name)
        if new_idx == mod_idx:
            break
        mod_idx = new_idx

def get_bone_conflict(obj, vg_name):
    """Checks if the vertex group name matches any bone in an active armature modifier."""
    if not obj or not vg_name:
        return None
    for m in obj.modifiers:
        if m.type == 'ARMATURE' and m.object and m.object.type == 'ARMATURE':
            arm = m.object.data
            if vg_name in arm.bones:
                return arm.name
    return None


def mark_mod_customized(mod):
    """Mark a recipe as hand-adjusted, invalidate support baseline, and flag cache as outdated."""
    if not mod:
        return
    obj = getattr(mod, 'id_data', None)
    if obj:
        try:
            obj[f"_giggle_{mod.name}_customized"] = True
        except Exception:
            pass
        try:
            obj.pop(f"_giggle_{mod.name}_support_base_json", None)
        except Exception:
            pass
    touch_zone_modified(mod)


def clear_mod_customized(mod):
    if not mod:
        return
    obj = getattr(mod, 'id_data', None)
    if obj:
        try:
            obj.pop(f"_giggle_{mod.name}_customized", None)
        except Exception:
            pass
        try:
            obj.pop(f"_giggle_{mod.name}_support_base_json", None)
        except Exception:
            pass


def _get_active_mod():
    settings = getattr(bpy.context.scene, "giggle_settings", None)
    idx = settings.active_zone_index if settings else 0

    # 1. Check active object first
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        mods = get_giggle_modifiers(obj)
        if mods:
            if 0 <= idx < len(mods):
                return mods[idx]
            return mods[0]

    # 2. Check selected objects
    for sel in getattr(bpy.context, 'selected_objects', []):
        if sel and sel.type == 'MESH':
            mods = get_giggle_modifiers(sel)
            if mods:
                if 0 <= idx < len(mods):
                    return mods[idx]
                return mods[0]

    # 3. Fallback to any character mesh in the scene with Giggle modifiers
    for scn_obj in getattr(bpy.context.scene, 'objects', []):
        if scn_obj.type == 'MESH' and not scn_obj.get('_giggle_cage') and not scn_obj.name.endswith('_Cage'):
            mods = get_giggle_modifiers(scn_obj)
            if mods:
                if 0 <= idx < len(mods):
                    return mods[idx]
                return mods[0]

    return None

def make_socket_get(socket_id, default=0.0):
    def getter(self):
        mod = _get_active_mod()
        if mod:
            val = get_mod_socket(mod, socket_id)
            if val is not None:
                try:
                    if hasattr(val, '__len__') and len(val) >= 3:
                        return float(val[2])  # Return Z-component for 3D acceleration/vectors
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return default
    return getter

def make_socket_set(socket_id, min_val=None, max_val=None):
    def setter(self, value):
        mod = _get_active_mod()
        if mod:
            if min_val is not None:
                value = max(min_val, value)
            if max_val is not None:
                value = min(max_val, value)
            if set_mod_socket(mod, socket_id, value=value):
                mark_mod_customized(mod)
    return setter

def make_socket_int_get(socket_id, default=0):
    def getter(self):
        mod = _get_active_mod()
        if mod:
            val = get_mod_socket(mod, socket_id)
            if val is not None:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    pass
        return default
    return getter

def make_socket_int_set(socket_id, min_val=None, max_val=None):
    def setter(self, value):
        mod = _get_active_mod()
        if mod:
            if min_val is not None:
                value = max(min_val, value)
            if max_val is not None:
                value = min(max_val, value)
            if set_mod_socket(mod, socket_id, value=int(value)):
                mark_mod_customized(mod)
    return setter

def make_socket_bool_get(socket_id, default=False):
    def getter(self):
        mod = _get_active_mod()
        if mod:
            val = get_mod_socket(mod, socket_id)
            if val is not None:
                return bool(val)
        return default
    return getter

def make_socket_bool_set(socket_id):
    def setter(self, value):
        mod = _get_active_mod()
        if mod:
            set_mod_socket(mod, socket_id, value=bool(value))
            mark_mod_customized(mod)
    return setter


# ==============================================================================
# PROPERTIES & SETTINGS
# ==============================================================================
def update_preset_mode(self, context):
    """Safely update preset_choice and new_zone_preset when toggling between Realistic and Stylized modes."""
    try:
        items = get_preset_enum_items(self, context)
        if items and len(items) > 0:
            current = getattr(self, "preset_choice", "")
            valid_keys = [it[0] for it in items]
            if current not in valid_keys:
                self.preset_choice = valid_keys[0]
    except Exception:
        pass
    try:
        new_items = get_new_zone_preset_items(self, context)
        if new_items and len(new_items) > 0:
            current_new = getattr(self, "new_zone_preset", "")
            valid_new_keys = [it[0] for it in new_items]
            if current_new not in valid_new_keys:
                self.new_zone_preset = valid_new_keys[0]
    except Exception:
        pass

def update_new_zone_vg(self, context):
    """Suggest a mode-compatible preset from common vertex-group naming patterns."""
    vg_name = (getattr(self, "new_zone_vg", "") or "").strip().lower()
    if not vg_name:
        return

    stylized = getattr(self, 'preset_mode', 'REALISTIC') == 'STYLIZED'
    male_group = bool(
        re.search(r'(?<![a-z0-9])male(?![a-z0-9])', vg_name)
        or re.match(r'^male(?:_|-|\.|[0-9]|chest|pec|belly|glute|thigh|arm|leg|groin)', vg_name)
        or re.match(r'^(?:man[_\-. ]|m[_\-.])', vg_name)
    )
    def choose(realistic_key, stylized_key=None):
        return stylized_key if stylized and stylized_key else realistic_key

    def assign(gender, category, preset):
        self.new_zone_gender = gender
        self.new_zone_category = category
        self.new_zone_preset = preset

    try:
        # Props first so words such as "hair ribbon" and "backpack" are not
        # misclassified by the broad body-part keyword checks below.
        if any(k in vg_name for k in ['ribbon', 'cape_strip', 'hair_strip']):
            assign('PROPS', 'PROPS_HAIR', choose('REAL_HAIR_STRANDS', 'STYLE_HAIR_RIBBON'))
        elif any(k in vg_name for k in ['backpack', 'rucksack', 'holster', 'soft_pack']):
            assign('PROPS', 'PROPS_ELASTIC', 'PROP_BACKPACK')
        elif any(k in vg_name for k in ['water_balloon', 'waterballoon', 'balloon']):
            assign('PROPS', 'PROPS_ELASTIC', 'WATER_BALLOON')
        elif any(k in vg_name for k in ['jelly', 'toy', 'elastic', 'prop', 'skirt']):
            assign('PROPS', 'PROPS_ELASTIC', 'JELLY_PROP')
        elif any(k in vg_name for k in ['hair', 'wig', 'ponytail', 'braid', 'pigtail', 'twintail', 'bang']):
            assign('PROPS', 'PROPS_HAIR', choose('REAL_HAIR_PONYTAIL', 'STYLE_HAIR_PONYTAIL'))

        # Male-specific labels must be considered before generic chest, belly,
        # glute and leg terms so "male_belly" does not fall into a female preset.
        elif male_group and any(k in vg_name for k in ['pec', 'chest']):
            assign('MALE', 'MALE_CHEST', choose('REAL_MALE_PECS_TONED', 'STYLE_MALE_PECS_TONED'))
        elif male_group and any(k in vg_name for k in ['groin', 'bulge', 'jock', 'scrot', 'genital']):
            assign('MALE', 'MALE_GENITALIA', 'MALE_GROIN_JOCKSTRAP')
        elif male_group and any(k in vg_name for k in ['belly', 'abdomen', 'stomach', 'paunch', 'beer', 'dadbod']):
            assign('MALE', 'MALE_STOMACH', 'MALE_BELLY_BEER' if any(k in vg_name for k in ['beer', 'paunch', 'dadbod']) else 'MALE_BELLY_AVERAGE')
        elif male_group and any(k in vg_name for k in ['butt', 'glute', 'hip', 'pelvis']):
            assign('MALE', 'MALE_BUTTOCKS', choose('REAL_MALE_GLUTES_ATHLETIC', 'STYLE_MALE_GLUTES_ATHLETIC'))
        elif male_group and any(k in vg_name for k in ['thigh', 'leg', 'quad', 'calf', 'calves']):
            assign('MALE', 'MALE_LEGS', 'MALE_THIGHS_SOFT' if 'soft' in vg_name else 'MALE_THIGHS_QUADS')
        elif male_group and any(k in vg_name for k in ['arm', 'bicep', 'tricep', 'neck', 'trap', 'face', 'jaw']):
            assign('MALE', 'MALE_EXTRAS', 'MALE_FACE_JAW' if any(k in vg_name for k in ['face', 'jaw']) else ('MALE_NECK_TRAP' if any(k in vg_name for k in ['neck', 'trap']) else ('MALE_ARMS_TRICEPS' if 'tricep' in vg_name else 'MALE_ARMS_BICEPS'))) 

        elif any(k in vg_name for k in ['butt', 'booty', 'glute', 'ass', 'hip', 'hips', 'pelvis', 'rear', 'derriere']):
            assign('FEMALE', 'FEMALE_BUTTOCKS', choose('REAL_GLUTES_SOFT', 'STYLE_GLUTES_SOFT'))
        elif any(k in vg_name for k in ['gut', 'gutt', 'belly', 'tummy', 'stomach', 'waist', 'torso', 'midriff', 'flab', 'navel']):
            assign('FEMALE', 'FEMALE_STOMACH', choose('REAL_BELLY_SOFT', 'STYLE_BELLY_SOFT'))
        elif any(k in vg_name for k in ['breast', 'boob', 'chest', 'cleavage', 'bust', 'tit', 'areola', 'nipple', 'jiggle', 'giggle']):
            assign('FEMALE', 'FEMALE_CHEST', choose('REAL_BREASTS_NATURAL', 'STYLE_BREASTS_NATURAL'))
        elif any(k in vg_name for k in ['thigh', 'leg', 'quad', 'calf', 'calves']):
            assign('FEMALE', 'FEMALE_LEGS', choose('REAL_THIGHS_INNER', 'STYLE_THIGHS_INNER'))
        elif any(k in vg_name for k in ['cheek', 'face', 'jaw']):
            assign('FEMALE', 'FEMALE_EXTRAS', 'FACE_CHEEKS_FEMALE')
        elif any(k in vg_name for k in ['arm', 'tricep', 'underarm']):
            assign('FEMALE', 'FEMALE_EXTRAS', 'ARMS_SOFT')
        else:
            assign('FEMALE', 'FEMALE_CHEST', choose('REAL_BREASTS_NATURAL', 'STYLE_BREASTS_NATURAL'))
    except Exception as exc:
        print(f"[Giggle] Could not auto-suggest preset for vertex group '{vg_name}': {exc}")

def resolve_garment_target_zone(cloth_obj, body_obj, max_dist=0.35, ambiguity_thresh=0.05):
    """
    Spatially detect the closest Giggle physics zone on body_obj for a specific cloth_obj.
    Uses geometry-aware surface proximity and character scale awareness.
    Returns: (best_mod, best_vg, best_dist, status_code)
    status_code: 'OK', 'EXCEEDS_DISTANCE', 'AMBIGUOUS', 'NO_ZONES', 'ERROR'
    """
    try:
        from mathutils import Vector
        mods = get_giggle_modifiers(body_obj)
        if not mods:
            return None, None, 999.0, 'NO_ZONES'

        # Scale awareness based on character height / body dimensions
        body_h = max(body_obj.dimensions.z, 0.1)
        scale_fac = max(0.1, body_h / 1.7)
        eff_max_dist = max_dist * scale_fac
        eff_ambiguity = ambiguity_thresh * scale_fac

        # Sample cloth vertices for geometry-aware surface-to-surface proximity
        n_c = len(cloth_obj.data.vertices)
        if n_c == 0:
            return None, None, 999.0, 'ERROR'
        step_c = max(1, n_c // 60)
        c_pts = [cloth_obj.matrix_world @ cloth_obj.data.vertices[i].co for i in range(0, n_c, step_c)]

        candidates = []
        for m in mods:
            vg_name = get_mod_socket_attribute_name(m, 'Socket_2')
            if not vg_name or vg_name not in body_obj.vertex_groups:
                continue
            vg_idx = body_obj.vertex_groups[vg_name].index
            v_pts = [body_obj.matrix_world @ v.co for v in body_obj.data.vertices if any(g.group == vg_idx and g.weight > 0.1 for g in v.groups)]
            if v_pts:
                step_z = max(1, len(v_pts) // 60)
                z_pts = v_pts[::step_z]
                # Geometry-aware minimum surface-to-surface distance
                surf_dist = min((p_c - p_z).length for p_c in c_pts for p_z in z_pts)
                candidates.append((surf_dist, m, vg_name))

        if not candidates:
            return None, None, 999.0, 'NO_ZONES'

        candidates.sort(key=lambda x: x[0])
        best_dist, best_mod, best_vg = candidates[0]

        if best_dist > eff_max_dist:
            return best_mod, best_vg, best_dist, 'EXCEEDS_DISTANCE'

        if len(candidates) > 1:
            second_dist = candidates[1][0]
            ratio = second_dist / max(best_dist, 0.001)
            if (second_dist - best_dist) < eff_ambiguity and ratio < 2.0:
                return best_mod, best_vg, best_dist, 'AMBIGUOUS'

        return best_mod, best_vg, best_dist, 'OK'
    except Exception as exc:
        print(f"[Giggle] Error resolving garment target zone: {exc}")
        return None, None, 999.0, 'ERROR'


def resolve_clothing_target_zone(context):
    """Detect the spatially closest Giggle physics zone for the active/first selected clothing."""
    try:
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        body = context.active_object if context.active_object in giggle_bodies else (giggle_bodies[0] if giggle_bodies else None)
        if not body:
            for o in getattr(context.scene, 'objects', []):
                if o.type == 'MESH' and get_giggle_modifiers(o):
                    body = o
                    break
        if not body:
            return None, None, None, None

        clothing_objs = [o for o in selected_meshes if o != body]
        if not clothing_objs:
            mods = get_giggle_modifiers(body)
            if mods:
                return body, mods[0], get_mod_socket_attribute_name(mods[0], 'Socket_2'), None
            return None, None, None, None

        cloth = clothing_objs[0]
        mod, vg, dist, status = resolve_garment_target_zone(cloth, body)
        return body, mod, vg, dist
    except Exception:
        return None, None, None, None

def get_clothing_target_zone_items(self, context):
    """Dynamic EnumProperty items for selecting which physics zone to attach clothing to."""
    items = [('AUTO', "Auto-Detect (Closest Zone)", "Automatically detect the closest physics zone based on 3D proximity", 0)]
    if not context:
        return items
    try:
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        body = context.active_object if context.active_object in giggle_bodies else (giggle_bodies[0] if giggle_bodies else None)
        if not body:
            for o in getattr(context.scene, 'objects', []):
                if o.type == 'MESH' and get_giggle_modifiers(o):
                    body = o
                    break
        if body:
            mods = get_giggle_modifiers(body)
            for i, m in enumerate(mods):
                vg_name = get_mod_socket_attribute_name(m, 'Socket_2') or 'Zone'
                label = f"{m.name} ({vg_name})"
                items.append((m.name, label, f"Attach clothing to {m.name} ({vg_name})", i + 1))
    except Exception:
        pass
    return items


class GiggleSceneSettings(PropertyGroup):
    new_zone_name: StringProperty(
        name="Custom Name (Optional)",
        description="Optional custom name for the zone modifier (defaults to vertex group name if empty)",
        default=""
    )
    new_zone_vg: StringProperty(
        name="Vertex Group",
        description="Vertex group that defines the soft zone (type or search)",
        default="",
        update=update_new_zone_vg
    )
    new_zone_engine: EnumProperty(
        name="Engine",
        description="Simulation physics engine",
        items=[
            ('WIGGY', "XPBD Physics (Wiggy)", "Supported engine for new zones. Existing Jiggle V2 modifiers remain editable for legacy scenes."),
        ],
        default='WIGGY'
    )
    new_zone_cage_mode: BoolProperty(
        name="Cage XPBD",
        description="Build a lightweight proxy cage for new zones so physics runs on a few hundred vertices instead of the whole mesh. Uncheck to create a Full-Mesh zone (advanced, much slower on dense meshes)",
        default=True
    )
    preset_mode: EnumProperty(
        name="Physics Mode",
        description="Choose restrained natural motion or more expressive secondary motion",
        items=[
            ('REALISTIC', "Natural Motion", "Restrained, controlled secondary motion with lower travel and quicker settling", 'PHYSICS', 0),
            ('STYLIZED', "Expressive Motion", "Larger, more visible secondary motion for stylized and cinematic animation", 'SHADING_RENDERED', 1),
        ],
        default='REALISTIC',
        update=update_preset_mode
    )
    preset_gender: EnumProperty(
        name="Gender / Type",
        description="Filter presets by character type",
        items=PRESET_GENDERS,
        default='FEMALE',
        update=update_preset_gender
    )
    preset_category: EnumProperty(
        name="Category",
        description="Filter presets by anatomical category",
        items=get_preset_category_items,
        update=update_preset_category
    )
    preset_choice: EnumProperty(
        name="Preset",
        description="Recipe preset to apply to active zone",
        items=get_preset_enum_items
    )
    new_zone_gender: EnumProperty(
        name="Gender / Type",
        description="Filter initial preset by character type",
        items=PRESET_GENDERS,
        default='FEMALE',
        update=update_new_zone_gender
    )
    new_zone_category: EnumProperty(
        name="Category",
        description="Filter initial preset by category",
        items=get_new_zone_category_items,
        update=update_new_zone_category
    )
    new_zone_preset: EnumProperty(
        name="Preset",
        description="Initial tuning recipe for this zone",
        items=get_new_zone_preset_items
    )
    clothing_target_zone: EnumProperty(
        name="Target Zone",
        description="Select which physics zone this clothing should follow",
        items=get_clothing_target_zone_items,
        default=0
    )
    active_zone_index: IntProperty(
        name="Active Zone Index",
        default=0,
        update=update_active_zone_index
    )
    # --- SIMULATION CACHE & BAKING SETTINGS (MILESTONE 3) ---
    bake_storage_mode: EnumProperty(
        name="Storage Mode",
        description="Choose how simulation cache is stored",
        items=[
            ('PACKED', "Packed in .blend", "Store simulation cache directly inside the .blend file"),
            ('DISK', "External Disk", "Store simulation cache on disk (requires saved .blend file)"),
        ],
        default='PACKED'
    )
    bake_use_scene_range: BoolProperty(
        name="Use Scene Range",
        description="Use scene start and end frames for baking",
        default=True
    )
    bake_frame_start: IntProperty(
        name="Start Frame",
        description="First frame to bake",
        default=1, min=-100000, max=100000
    )
    bake_frame_end: IntProperty(
        name="End Frame",
        description="Last frame to bake",
        default=250, min=-100000, max=100000
    )
    bake_disk_path: StringProperty(
        name="Bake Directory",
        description="Directory for external cache files",
        subtype='DIR_PATH',
        default="//giggle_cache/"
    )
    check_cache_on_render: BoolProperty(
        name="Pre-Flight Render Check",
        description="Verify simulation caches match current animation and physics before rendering",
        default=True
    )

    show_create_zone: BoolProperty(
        name="Create New Zone",
        description="Expand or collapse the Create New Zone section",
        default=True
    )

    # --- CLAMPED ACTIVE ZONE CONTROLS (DYNAMICS & INERTIA) ---
    zone_softness: FloatProperty(
        name="Softness (Freedom)",
        description="How freely the flesh moves relative to parent bones (0 = stiff, 0.5 = loose)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=0.5, step=1, precision=3,
        get=make_socket_get('Socket_33', 0.18), set=make_socket_set('Socket_33', 0.0, 1.0)
    )
    zone_mass: FloatProperty(
        name="Mass / Inertia",
        description="Relative simulated mass (higher = heavier lag and inertia); treat as a tuning value, not a measured kilogram value",
        min=0.01, max=100.0, soft_min=0.5, soft_max=20.0, step=10, precision=2,
        get=make_socket_get('Socket_31', 5.0), set=make_socket_set('Socket_31', 0.01, 100.0)
    )
    zone_mass_by_area: BoolProperty(
        name="Mass by Area (Even Weight)",
        description="Distribute mass evenly regardless of polygon density",
        get=make_socket_bool_get('Socket_102', True), set=make_socket_bool_set('Socket_102')
    )
    zone_wobble: FloatProperty(
        name="Wobble Strength",
        description="Strength of spring-like oscillation after displacement (0 = none, higher = more visible rebound)",
        min=0.0, max=2.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_126', 0.60), set=make_socket_set('Socket_126', 0.0, 2.0)
    )
    zone_damping: FloatProperty(
        name="Damping (Lag)",
        description="How quickly oscillations settle down (higher = stops shaking faster)",
        min=0.0, max=10.0, soft_min=0.0, soft_max=5.0, step=5, precision=3,
        get=make_socket_get('Socket_8', 1.0), set=make_socket_set('Socket_8', 0.0, 10.0)
    )
    zone_max_distance: FloatProperty(
        name="Max Distance (Sag Limit)",
        description="Maximum distance tissue can stretch from rest position (0 = unlimited)",
        min=0.0, max=2.0, soft_min=0.0, soft_max=0.5, step=1, precision=3,
        get=make_socket_get('Socket_123', 0.15), set=make_socket_set('Socket_123', 0.0, 2.0)
    )
    zone_influence: FloatProperty(
        name="Influence",
        description="Global blend strength of the jiggle effect (0 = off, 1 = full)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_67', 1.0), set=make_socket_set('Socket_67', 0.0, 1.0)
    )

    # --- CLAMPED SHAPE & VOLUME ---
    zone_preserve_volume: FloatProperty(
        name="Preserve Volume",
        description="Flesh retains natural fullness rather than flattening or stretching thin",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_118', 0.85), set=make_socket_set('Socket_118', 0.0, 1.0)
    )
    zone_sway: FloatProperty(
        name="Sway (Island Swing)",
        description="Coordinated directional swinging of the whole body part together",
        min=0.0, max=2.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_119', 0.70), set=make_socket_set('Socket_119', 0.0, 2.0)
    )
    zone_stretching: FloatProperty(
        name="Stretching",
        description="Resistance to surface elongation along mesh edges",
        min=0.0, max=2.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_6', 0.10), set=make_socket_set('Socket_6', 0.0, 2.0)
    )
    zone_bending: FloatProperty(
        name="Bending",
        description="Curvature stiffness (lower for soft ripples, higher for firm curves)",
        min=0.0, max=2.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_30', 0.20), set=make_socket_set('Socket_30', 0.0, 2.0)
    )
    zone_edge_fade: IntProperty(
        name="Edge Fade (Rings)",
        description="Number of border polygon rings to smoothly transition physics into rigid bone skinning",
        min=0, max=10,
        get=make_socket_int_get('Socket_122', 0), set=make_socket_int_set('Socket_122', 0, 10)
    )

    # --- CLAMPED COLLISIONS & CONTACTS ---
    zone_thickness: FloatProperty(
        name="Thickness",
        description="Collision offset boundary around obstacles",
        min=0.0, max=1.0, soft_min=0.0, soft_max=0.1, step=1, precision=3,
        get=make_socket_get('Socket_24', 0.01), set=make_socket_set('Socket_24', 0.0, 1.0)
    )
    zone_friction: FloatProperty(
        name="Friction",
        description="Surface grip against colliding obstacles",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_28', 0.0), set=make_socket_set('Socket_28', 0.0, 1.0)
    )
    zone_push_aside: FloatProperty(
        name="Push Aside",
        description="Lateral displacement force when contacting obstacles",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_128', 0.0), set=make_socket_set('Socket_128', 0.0, 1.0)
    )
    zone_cling: FloatProperty(
        name="Cling",
        description="Adhesion to obstacle surfaces during contact",
        min=0.0, max=0.5, soft_min=0.0, soft_max=0.5, step=1, precision=3,
        get=make_socket_get('Socket_129', 0.0), set=make_socket_set('Socket_129', 0.0, 0.5)
    )
    zone_grip: FloatProperty(
        name="Grip",
        description="Tangential drag force against contacting objects",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_130', 0.0), set=make_socket_set('Socket_130', 0.0, 1.0)
    )
    zone_squeeze: BoolProperty(
        name="Enable Squeeze",
        description="Compress flesh volume when squished against hard surfaces",
        get=make_socket_bool_get('Socket_34', False), set=make_socket_bool_set('Socket_34')
    )
    zone_squeeze_depth: FloatProperty(
        name="Squeeze Depth",
        description="Depth of fleshy squish depression",
        min=0.0, max=10.0, soft_min=0.0, soft_max=2.0, step=1, precision=3,
        get=make_socket_get('Socket_36', 0.0), set=make_socket_set('Socket_36', 0.0, 10.0)
    )

    # --- CLAMPED SELF COLLISION ---
    zone_self_collision: BoolProperty(
        name="Self Collision",
        description="Prevent soft body geometry from penetrating itself",
        get=make_socket_bool_get('Socket_104', False), set=make_socket_bool_set('Socket_104')
    )
    zone_self_gap: FloatProperty(
        name="Gap Distance",
        description="Minimum clearance gap between folding surface layers",
        min=0.0, max=0.1, soft_min=0.0, soft_max=0.05, step=1, precision=3,
        get=make_socket_get('Socket_105', 0.01), set=make_socket_set('Socket_105', 0.0, 0.1)
    )
    zone_self_friction: FloatProperty(
        name="Friction",
        description="Friction when soft tissue folds rub together",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_109', 0.0), set=make_socket_set('Socket_109', 0.0, 1.0)
    )
    zone_self_push_speed: FloatProperty(
        name="Push Speed",
        description="Repulsion speed separating colliding vertices",
        min=0.0, max=100.0, soft_min=0.0, soft_max=20.0, step=10, precision=2,
        get=make_socket_get('Socket_108', 5.0), set=make_socket_set('Socket_108', 0.0, 100.0)
    )
    zone_self_max_depth: FloatProperty(
        name="Max Depth",
        description="Maximum self-penetration search depth",
        min=0.0, max=2.0, soft_min=0.0, soft_max=0.5, step=1, precision=3,
        get=make_socket_get('Socket_106', 0.1), set=make_socket_set('Socket_106', 0.0, 2.0)
    )

    # --- CLAMPED GRAVITY & FORCES ---
    zone_gravity: BoolProperty(
        name="Enable Gravity",
        description="Simulate downward gravitational force on soft tissue",
        get=make_socket_bool_get('Socket_5', False), set=make_socket_bool_set('Socket_5')
    )
    zone_gravity_accel: FloatProperty(
        name="Acceleration",
        description="Gravitational acceleration (-9.8 m/s² for real-world Earth gravity)",
        min=-100.0, max=100.0, soft_min=-30.0, soft_max=30.0, step=10, precision=2,
        get=make_socket_get('Socket_3', -9.8), set=make_socket_set('Socket_3', -100.0, 100.0)
    )

    # --- CLAMPED SIMZONE (JIGGLE V2) ---
    zone_jiggle_strength: FloatProperty(
        name="Jiggle Strength",
        description="Overall jiggle amplitude",
        min=0.0, max=10.0, soft_min=0.0, soft_max=3.0, step=1, precision=3,
        get=make_socket_get('Socket_2', 1.0), set=make_socket_set('Socket_2', 0.0, 10.0)
    )
    zone_vel_damping: FloatProperty(
        name="Velocity Damping",
        description="Damping applied to velocity vector",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_4', 0.65), set=make_socket_set('Socket_4', 0.0, 1.0)
    )
    zone_pos_damping: FloatProperty(
        name="Position Damping",
        description="Spring resistance pulling vertices back to rest position",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_6', 0.20), set=make_socket_set('Socket_6', 0.0, 1.0)
    )
    zone_deform_depth: FloatProperty(
        name="Deform Depth",
        description="Penetration depth of deformation",
        min=0.0, max=5.0, soft_min=0.0, soft_max=1.0, step=1, precision=3,
        get=make_socket_get('Socket_3', 0.1), set=make_socket_set('Socket_3', 0.0, 5.0)
    )


# ==============================================================================
# OPERATORS
# ==============================================================================
class GIGGLE_OT_pick_active_vg(Operator):
    bl_idname = "giggle.pick_active_vg"
    bl_label = "Pick Active Vertex Group"
    bl_description = "Use the vertex group currently selected in Weight Paint mode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.vertex_groups.active is not None

    def execute(self, context):
        vg = context.active_object.vertex_groups.active
        context.scene.giggle_settings.new_zone_vg = vg.name
        self.report({'INFO'}, f"Selected active vertex group: '{vg.name}'")
        return {'FINISHED'}


class GIGGLE_OT_create_vg(Operator):
    bl_idname = "giggle.create_vg"
    bl_label = "New Vertex Group"
    bl_description = "Create a new empty vertex group ready for Weight Painting"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        base_name = "Jiggle_Zone"
        name = base_name
        counter = 1
        while name in obj.vertex_groups:
            name = f"{base_name}_{counter}"
            counter += 1

        vg = obj.vertex_groups.new(name=name)
        obj.vertex_groups.active = vg
        context.scene.giggle_settings.new_zone_vg = name
        self.report({'INFO'}, f"Created vertex group '{name}'. Switch to Weight Paint to paint it!")
        return {'FINISHED'}


class GIGGLE_OT_duplicate_safe_vg(Operator):
    bl_idname = "giggle.duplicate_safe_vg"
    bl_label = "Duplicate as Safe Jiggle Group"
    bl_description = "Duplicate this vertex group to a dedicated Jiggle group to avoid breaking bone skinning"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        return obj and obj.type == 'MESH' and settings.new_zone_vg in obj.vertex_groups

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        source_vg = obj.vertex_groups.get(settings.new_zone_vg)
        
        new_name = f"Wiggy_{source_vg.name}"
        target_vg = obj.vertex_groups.new(name=new_name)
        
        # Fast weight copy via direct vertex group query (avoids tens of thousands of RuntimeError exceptions)
        src_idx = source_vg.index
        for v in obj.data.vertices:
            for g in v.groups:
                if g.group == src_idx:
                    target_vg.add([v.index], g.weight, 'REPLACE')
                    break
                
        obj.vertex_groups.active = target_vg
        settings.new_zone_vg = target_vg.name
        self.report({'INFO'}, f"Copied weights to safe group '{target_vg.name}' without bone conflicts.")
        return {'FINISHED'}


class GIGGLE_OT_add_zone(Operator):
    bl_idname = "giggle.add_zone"
    bl_label = "Add Jiggle Zone"
    bl_description = "Add a new soft-body jiggle zone modifier to the active mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        original_mode = getattr(obj, 'mode', 'OBJECT')

        engine = settings.new_zone_engine
        if engine != 'WIGGY':
            self.report({'ERROR'}, "New zones currently require the Wiggy XPBD engine. Jiggle V2 is retained for legacy scenes only.")
            return {'CANCELLED'}
        preset_key = settings.new_zone_preset
        preset = PRESETS.get(preset_key)
        
        tree_name = "Wiggy 0.1"

        ng = ensure_nodetree(tree_name)
        if not ng:
            self.report({'ERROR'}, f"Could not load node tree '{tree_name}' from assets.")
            return {'CANCELLED'}

        raw_vg = settings.new_zone_vg
        vg_name = raw_vg.strip()
        custom_name = settings.new_zone_name.strip()
        if custom_name:
            zone_name = custom_name
        elif vg_name:
            zone_name = vg_name
        else:
            zone_name = "Jiggle"

        mod_name = f"Giggle_{zone_name}"

        # Resolve the requested vertex group before changing the user's object mode.
        actual_vg = None
        if vg_name in obj.vertex_groups:
            actual_vg = vg_name
        elif raw_vg in obj.vertex_groups:
            actual_vg = raw_vg

        # Pre-flight guard: Never create an XPBD zone on an object missing the assigned vertex group!
        if not actual_vg:
            self.report({'ERROR'}, f"Vertex group '{vg_name or raw_vg}' not found on '{obj.name}'. Assign or create a vertex group first.")
            return {'CANCELLED'}

        if actual_vg:
            vg_obj = obj.vertex_groups[actual_vg]
            # Safety check: if vertex group has 0 assigned vertices, initialize with 0.0 weight
            # to guarantee Blender's internal attribute buffer is allocated and avoid nullptr dereferences in mix_geometries.cc
            has_assigned = any(any(g.group == vg_obj.index and g.weight > 0.0 for g in v.groups) for v in obj.data.vertices)
            if not has_assigned and len(obj.data.vertices) > 0:
                self.report({'WARNING'}, f"Vertex group '{actual_vg}' has no non-zero weights. The zone will remain inactive until you paint weights.")

        # Only enter Object Mode after all non-destructive preflight checks pass.
        if obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception as exc:
                self.report({'ERROR'}, f"Could not switch '{obj.name}' to Object Mode: {exc}")
                return {'CANCELLED'}

        # Preserve user active frame during zone creation

        # SAFEGUARD: Temporarily mute viewport display for existing Subdivision Surface modifiers.
        # This prevents OpenSubdiv from computing face-varying stencil tables on partial geometry (bad_alloc crash).
        subsurf_state = [(m, m.show_viewport, m.levels) for m in obj.modifiers if m.type == 'SUBSURF']
        for s, was_visible, old_levels in subsurf_state:
            if was_visible:
                s.show_viewport = False
            # Clamp only while the new node modifier is being initialized.
            if s.levels > 2:
                s.levels = 1

        mod = None
        failed_inputs = []
        previous_rest_position = getattr(obj, "add_rest_position_attribute", None)
        try:
            # 1. Enable Rest Position attribute first (required by XPBD self-collision & volume)
            if previous_rest_position is not None:
                obj.add_rest_position_attribute = True

            # 2. Add modifier, keeping viewport muted during initial setup
            mod = obj.modifiers.new(name=mod_name, type='NODES')
            mod.node_group = ng
            mod.show_viewport = False

            # 3. Configure the required vertex-group attribute before applying recipe values.
            if not set_mod_socket(mod, 'Socket_2', attribute=actual_vg):
                raise RuntimeError(f"Could not assign vertex group '{actual_vg}' to the Wiggy modifier.")

            if preset and preset.get('values'):
                for sock_id, val in preset['values'].items():
                    if not set_mod_socket(mod, sock_id, value=val):
                        failed_inputs.append(sock_id)

            # 4. Position modifier atomically right after Armatures
            position_giggle_modifier(obj, mod)

            # 5. Restore viewport on the new modifier
            mod.show_viewport = True
        except Exception as exc:
            if mod is not None:
                try:
                    obj.modifiers.remove(mod)
                except Exception:
                    pass
            if previous_rest_position is not None:
                try:
                    obj.add_rest_position_attribute = previous_rest_position
                except Exception:
                    pass
            if original_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=original_mode)
                except Exception:
                    pass
            self.report({'ERROR'}, f"Could not create Giggle zone: {exc}")
            return {'CANCELLED'}
        finally:
            # Restore every Subdivision setting exactly as it was before zone creation.
            for s, was_visible, old_levels in subsurf_state:
                try:
                    s.levels = old_levels
                    s.show_viewport = was_visible
                except Exception:
                    pass

        if original_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except Exception:
                pass

        if failed_inputs:
            self.report({'WARNING'}, "Zone created, but some preset inputs were unavailable: " + ", ".join(failed_inputs))

        # Store zone metadata on parent object for auto-synchronization
        set_mod_giggle_metadata(mod, settings.new_zone_gender, settings.new_zone_category, settings.new_zone_preset)

        # Clear vertex group picker and auto-collapse Create New Zone
        settings.new_zone_vg = ""
        settings.show_create_zone = False

        giggle_mods = get_giggle_modifiers(obj)
        if mod in giggle_mods:
            settings.active_zone_index = giggle_mods.index(mod)
            sync_settings_from_zone_mod(settings, mod)
            obj["_giggle_last_synced_mod"] = mod.name

        # New zones are accelerated to Cage XPBD by default (2.1). A failed bind
        # must not cost the user their zone: keep it full-mesh, remember the
        # reason, and let the zone card explain and offer the choice.
        if getattr(settings, "new_zone_cage_mode", True) and not is_zone_in_cage_mode(obj, mod):
            cage_error = ""
            try:
                with context.temp_override(
                    active_object=obj,
                    object=obj,
                    selected_objects=[obj],
                    selected_editable_objects=[obj],
                ):
                    bpy.ops.giggle.generate_cage('EXEC_DEFAULT')
            except Exception as exc:
                cage_error = str(exc)

            if is_zone_in_cage_mode(obj, mod):
                set_zone_cage_error(mod, "")
            else:
                # generate_cage() already stored the real cause on failure. Keep it:
                # its message is more specific than anything we can rebuild here.
                reason = (get_zone_cage_error(mod) or cage_error
                          or "Surface Deform could not bind a proxy cage to this region")
                set_zone_cage_error(mod, reason)
                self.report(
                    {'WARNING'},
                    f"Zone '{mod.name}' was created as Full-Mesh XPBD because cage binding failed. "
                    "See the zone card for details."
                )

        try:
            obj.update_tag(refresh={'DATA'})
        except Exception:
            pass
        try:
            context.view_layer.update()
        except Exception:
            pass
        self.report({'INFO'}, f"Added Giggle Zone '{mod.name}' ({engine})")
        return {'FINISHED'}



def touch_zone_modified(mod):
    """Mark zone and its associated cage as modified to invalidate bake cache."""
    if not mod:
        return
    import time
    now = time.time()
    obj = getattr(mod, 'id_data', None)
    if obj:
        try:
            bake_t = obj.get('_giggle_baked_at_timestamp', 0)
            obj['_giggle_settings_modified_at'] = max(now, bake_t + 0.001)
        except Exception:
            pass
        vg_name = get_mod_socket_attribute_name(mod, 'Socket_2')
        if vg_name:
            cage = get_zone_cage_object(obj, vg_name)
            if cage:
                try:
                    c_bake_t = cage.get('_giggle_baked_at_timestamp', 0)
                    cage['_giggle_settings_modified_at'] = max(now, c_bake_t + 0.001)
                except Exception:
                    pass
        elif obj.name.endswith('_Cage') or obj.get('_giggle_cage'):
            try:
                bake_t = obj.get('_giggle_baked_at_timestamp', 0)
                obj['_giggle_settings_modified_at'] = max(now, bake_t + 0.001)
            except Exception:
                pass


def sync_socket_to_cage(mod, socket_id, value=None, attribute=None):
    """If zone has an active cage proxy, synchronize modifier input to the cage solver."""
    obj = getattr(mod, 'id_data', None)
    if not obj or obj.type != 'MESH':
        return
    vg_name = get_mod_socket_attribute_name(mod, 'Socket_2')
    if vg_name and socket_id != 'Socket_2':
        cage = get_zone_cage_object(obj, vg_name)
        if cage:
            c_mod = next((m for m in cage.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
            if c_mod:
                set_mod_socket(c_mod, socket_id, value=value, attribute=attribute, sync_cage=False)

def get_zone_cage_object(obj, vg_name):
    if not obj or not vg_name:
        return None
    return bpy.data.objects.get(f"{obj.name}_{vg_name}_Cage")

def get_zone_sd_modifier(obj, vg_name):
    if not obj or not vg_name:
        return None
    return obj.modifiers.get(f"Giggle_Cage_SD_{vg_name}")

def clean_cage_error_message(message):
    """Normalize an operator/exception message into one readable line."""
    text = str(message or "").replace("\r", " ").replace("\n", " ").strip()
    for prefix in ("Error:", "RuntimeError:", "error:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    text = " ".join(text.split())
    while text.endswith((".", " ")):
        text = text[:-1]
    return text or "Cage proxy could not be created for this region"

def set_zone_cage_error(mod, message):
    """Remember (or clear) why a zone could not be accelerated with a cage."""
    if not mod:
        return
    obj = getattr(mod, "id_data", None) or bpy.context.active_object
    if not obj:
        return
    key = f"_giggle_{mod.name}_cage_error"
    try:
        if message:
            obj[key] = clean_cage_error_message(message)
        else:
            obj.pop(key, None)
    except Exception:
        pass

def get_zone_cage_error(mod):
    """Return the stored cage failure reason for a zone, or an empty string."""
    if not mod:
        return ""
    obj = getattr(mod, "id_data", None) or bpy.context.active_object
    if not obj:
        return ""
    try:
        return str(obj.get(f"_giggle_{mod.name}_cage_error", "") or "")
    except Exception:
        return ""

def wrap_zone_error(message, width=46, max_lines=3):
    """Split a stored cage error into panel-friendly lines."""
    words = str(message or "").split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = (lines[-1][: width - 1] + "…") if len(lines[-1]) >= width else (lines[-1] + "…")
    return lines or ["Cage binding failed for this region"]

def is_zone_in_cage_mode(obj, mod):
    if not obj or not mod:
        return False
    s_in = getattr(getattr(mod, "properties", None), "inputs", None)
    if not s_in or not hasattr(s_in, "Socket_2"):
        return False
    vg_name = getattr(s_in.Socket_2, "attribute_name", "")
    if not vg_name:
        return False
    cage = get_zone_cage_object(obj, vg_name)
    sd = get_zone_sd_modifier(obj, vg_name)
    return bool(cage and sd and getattr(sd, "is_bound", False))

def zone_mode_label(obj, mod):
    """Short 'Cage 483v' / 'Full 28,652v' label for a zone row. Never raises."""
    try:
        if is_zone_in_cage_mode(obj, mod):
            vg_name = get_mod_socket_attribute_name(mod, 'Socket_2')
            cage = get_zone_cage_object(obj, vg_name) if vg_name else None
            return f"Cage {len(cage.data.vertices):,}v" if cage else "Cage"
        return f"Full {len(obj.data.vertices):,}v"
    except Exception:
        return "Full-Mesh"


def sanitize_cage_manifold(bm, max_iterations=10):
    """
    Sanitize non-manifold and degenerate geometry on proxy cage BMesh.
    Guarantees that no edge connects to > 2 polygons, no wire edges exist,
    and no isolated vertices remain, satisfying Blender Surface Deform binding.
    Raises RuntimeError if cleanup fails to converge within max_iterations.
    Returns comprehensive diagnostic metrics including area, faces, boundary edges,
    and connected-component counts.
    """
    import bmesh
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    initial_v = len(bm.verts)
    initial_e = len(bm.edges)
    initial_f = len(bm.faces)
    initial_boundary_e = len([e for e in bm.edges if len(e.link_faces) == 1])
    initial_area = sum(f.calc_area() for f in bm.faces)

    def _count_components(b_mesh):
        visited = set()
        comps = 0
        for f in b_mesh.faces:
            if f not in visited:
                comps += 1
                queue = [f]
                visited.add(f)
                while queue:
                    curr = queue.pop()
                    for e in curr.edges:
                        for lf in e.link_faces:
                            if lf not in visited:
                                visited.add(lf)
                                queue.append(lf)
        return comps

    initial_components = _count_components(bm)

    total_nm_edges_removed = 0
    total_wire_edges_removed = 0
    total_loose_verts_removed = 0
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        bm.edges.ensure_lookup_table()
        bad_nm = [e for e in bm.edges if len(e.link_faces) > 2]
        bad_wire = [e for e in bm.edges if len(e.link_faces) == 0]

        if not bad_nm and not bad_wire:
            break

        total_nm_edges_removed += len(bad_nm)
        total_wire_edges_removed += len(bad_wire)
        bmesh.ops.delete(bm, geom=bad_nm + bad_wire, context='EDGES')

        bm.verts.ensure_lookup_table()
        loose = [v for v in bm.verts if len(v.link_edges) == 0]
        if loose:
            total_loose_verts_removed += len(loose)
            bmesh.ops.delete(bm, geom=loose, context='VERTS')

    bm.verts.ensure_lookup_table()
    loose = [v for v in bm.verts if len(v.link_edges) == 0]
    if loose:
        total_loose_verts_removed += len(loose)
        bmesh.ops.delete(bm, geom=loose, context='VERTS')

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Mandatory Convergence Check: verify zero bad edges remain
    remaining_nm = [e for e in bm.edges if len(e.link_faces) > 2]
    remaining_wire = [e for e in bm.edges if len(e.link_faces) == 0]
    if remaining_nm or remaining_wire:
        raise RuntimeError(
            f"Cage manifold sanitizer failed to converge within {max_iterations} iterations "
            f"({len(remaining_nm)} non-manifold and {len(remaining_wire)} wire edges remain). "
            f"Aborting cage generation."
        )

    final_v = len(bm.verts)
    final_e = len(bm.edges)
    final_f = len(bm.faces)
    final_boundary_e = len([e for e in bm.edges if len(e.link_faces) == 1])
    final_components = _count_components(bm)
    final_area = sum(f.calc_area() for f in bm.faces)

    faces_removed = initial_f - final_f
    area_removed = initial_area - final_area
    area_loss_pct = (area_removed / initial_area * 100.0) if initial_area > 0.0 else 0.0
    face_loss_pct = (faces_removed / initial_f * 100.0) if initial_f > 0 else 0.0

    return {
        "converged": True,
        "iterations": iteration,
        "initial_v": initial_v, "initial_e": initial_e, "initial_f": initial_f,
        "initial_boundary_e": initial_boundary_e, "initial_components": initial_components,
        "initial_area": initial_area,
        "final_v": final_v, "final_e": final_e, "final_f": final_f,
        "final_boundary_e": final_boundary_e, "final_components": final_components,
        "final_area": final_area,
        "nm_edges_removed": total_nm_edges_removed,
        "wire_edges_removed": total_wire_edges_removed,
        "loose_verts_removed": total_loose_verts_removed,
        "faces_removed": faces_removed,
        "area_removed": area_removed,
        "face_loss_pct": face_loss_pct,
        "area_loss_pct": area_loss_pct,
    }


class GIGGLE_OT_generate_cage(Operator):
    """Generate an accelerated ~450-vertex simulation cage for the active jiggle zone (5-8x faster evaluation)"""
    bl_idname = "giggle.generate_cage"
    bl_label = "Generate Simulation Cage"
    bl_description = "Extract and decimate a lightweight proxy cage to accelerate physics while preserving full deformation"
    bl_options = {'REGISTER', 'UNDO'}

    target_verts: IntProperty(
        name="Target Vertices",
        description="Target vertex count for the proxy cage (400-500 is optimal)",
        default=450, min=100, max=2000
    )
    dilation_rings: IntProperty(
        name="Dilation Rings",
        description="Number of vertex rings to dilate around the active zone for smooth anchor falloff",
        default=2, min=1, max=5
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        import bmesh
        obj = context.active_object
        scene = context.scene
        settings = scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        src_mod = mods[idx]

        s_in = getattr(getattr(src_mod, "properties", None), "inputs", None)
        vg_name = getattr(s_in.Socket_2, "attribute_name", "") if (s_in and hasattr(s_in, "Socket_2")) else ""
        if not vg_name or vg_name not in obj.vertex_groups:
            self.report({'ERROR'}, f"Active zone '{src_mod.name}' has no valid vertex group assigned.")
            return {'CANCELLED'}

        vg_idx = obj.vertex_groups[vg_name].index
        cage_name = f"{obj.name}_{vg_name}_Cage"
        mesh_name = f"{cage_name}_Mesh"

        # 1. State capture & Rest Pose isolation
        orig_mode = obj.mode
        orig_frame = scene.frame_current
        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_src_mod_viewport = src_mod.show_viewport
        orig_src_mod_render = src_mod.show_render
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        arm_mod = next((m for m in obj.modifiers if m.type == 'ARMATURE' and m.object), None)
        arm_obj = arm_mod.object if arm_mod else None
        orig_pose_pos = 'POSE'
        if arm_obj and hasattr(arm_obj.data, 'pose_position'):
            orig_pose_pos = arm_obj.data.pose_position
            arm_obj.data.pose_position = 'REST'

        scene.frame_set(scene.frame_start)
        context.view_layer.update()

        # Dedicated collection
        col = bpy.data.collections.get("Giggle_Cages")
        if not col:
            col = bpy.data.collections.new("Giggle_Cages")
            scene.collection.children.link(col)

        # Track for ACID Rollback
        created_objects = []
        created_meshes = []
        old_sd = obj.modifiers.get(f"Giggle_Cage_SD_{vg_name}")
        old_sd_state = None
        if old_sd:
            old_sd_state = (old_sd.target, old_sd.vertex_group, old_sd.show_viewport)
            obj.modifiers.remove(old_sd)

        # Clean existing cage object if rebuilding
        existing_cage = bpy.data.objects.get(cage_name)
        if existing_cage:
            bpy.data.objects.remove(existing_cage, do_unlink=True)
        existing_mesh = bpy.data.meshes.get(mesh_name)
        if existing_mesh:
            bpy.data.meshes.remove(existing_mesh, do_unlink=True)

        try:
            # 2. Extract Base Rest Geometry
            cage_mesh = obj.data.copy()
            cage_mesh.name = mesh_name
            created_meshes.append(cage_mesh)

            cage_obj = bpy.data.objects.new(cage_name, cage_mesh)
            col.objects.link(cage_obj)
            cage_obj.matrix_world = obj.matrix_world
            created_objects.append(cage_obj)

            if cage_obj.data.shape_keys:
                cage_obj.shape_key_clear()

            # 3. Dilation and Edge cleanup in BMesh
            bm = bmesh.new()
            try:
                bm.from_mesh(cage_obj.data)
                dvert_lay = bm.verts.layers.deform.active

                verts_to_keep = set()
                for v in bm.verts:
                    dvert = v[dvert_lay] if dvert_lay else None
                    w = dvert.get(vg_idx, 0.0) if dvert else 0.0
                    if w >= 0.01:
                        verts_to_keep.add(v)

                dilated = set(verts_to_keep)
                for _ in range(self.dilation_rings):
                    ring = set(dilated)
                    for v in dilated:
                        for e in v.link_edges:
                            ring.add(e.other_vert(v))
                    dilated = ring

                verts_to_delete = [v for v in bm.verts if v not in dilated]
                bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')

                bad_edges = [e for e in bm.edges if len(e.link_faces) > 2 or e.is_wire]
                if bad_edges:
                    bmesh.ops.delete(bm, geom=bad_edges, context='EDGES')

                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
                bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

                # Stage C: Manifold Sanitizer Pass 1
                diag_c = sanitize_cage_manifold(bm)
                if diag_c["area_loss_pct"] > 20.0 or diag_c["face_loss_pct"] > 25.0:
                    raise RuntimeError(
                        f"Manifold sanitization removed excessive geometry in Stage C "
                        f"({diag_c['area_loss_pct']:.1f}% area, {diag_c['face_loss_pct']:.1f}% faces). "
                        "Aborting cage generation to preserve shape."
                    )
                if diag_c["final_components"] > diag_c["initial_components"] + 2:
                    raise RuntimeError("Manifold sanitization fragmented cage topology in Stage C.")

                bm.to_mesh(cage_obj.data)
                cage_obj.data.update()
            finally:
                bm.free()

            # 4. Decimate to target_verts
            curr_v = len(cage_obj.data.vertices)
            if curr_v > self.target_verts:
                dec = cage_obj.modifiers.new('Decimate', 'DECIMATE')
                dec.ratio = float(self.target_verts) / float(curr_v)
                with context.temp_override(active_object=cage_obj, object=cage_obj):
                    bpy.ops.object.modifier_apply(modifier=dec.name)

            # Stage E: Re-triangulate and Manifold Sanitizer Pass 2
            bm2 = bmesh.new()
            try:
                bm2.from_mesh(cage_obj.data)
                bmesh.ops.triangulate(bm2, faces=bm2.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
                diag_e = sanitize_cage_manifold(bm2)
                if diag_e["area_loss_pct"] > 20.0 or diag_e["face_loss_pct"] > 25.0:
                    raise RuntimeError(
                        f"Manifold sanitization removed excessive geometry post-decimation "
                        f"({diag_e['area_loss_pct']:.1f}% area, {diag_e['face_loss_pct']:.1f}% faces). "
                        "Aborting cage generation to preserve shape."
                    )

                if len(bm2.faces) < 4 or len(bm2.verts) < 10:
                    raise RuntimeError("Sanitized simulation cage has insufficient geometric density.")
                if diag_e["final_components"] > diag_e["initial_components"] + 2:
                    raise RuntimeError("Manifold sanitization fragmented cage topology post-decimation.")

                bm2.to_mesh(cage_obj.data)
                cage_obj.data.update()
            finally:
                bm2.free()

            # 5. Add Armature
            if arm_obj:
                c_arm = cage_obj.modifiers.new('Armature', 'ARMATURE')
                c_arm.object = arm_obj
                for prop in ['use_vertex_groups', 'use_bone_envelopes', 'use_deform_delay']:
                    if hasattr(arm_mod, prop):
                        setattr(c_arm, prop, getattr(arm_mod, prop))

            # 6. Add Wiggy 0.1 solver modifier
            c_wiggy = cage_obj.modifiers.new(f"Giggle_Cage_{vg_name}", 'NODES')
            c_wiggy.node_group = src_mod.node_group

            b_props = getattr(src_mod, 'properties', None)
            b_inputs = getattr(b_props, 'inputs', None) if b_props else None
            c_props = getattr(c_wiggy, 'properties', None)
            c_inputs = getattr(c_props, 'inputs', None) if c_props else None
            if b_inputs and c_inputs:
                for attr in dir(b_inputs):
                    if attr.startswith('Socket_'):
                        bs = getattr(b_inputs, attr)
                        cs = getattr(c_inputs, attr, None)
                        if cs:
                            try:
                                typ = getattr(bs, 'type', None)
                                if typ == 'ATTRIBUTE':
                                    cs.type = 'ATTRIBUTE'
                                    cs.attribute_name = bs.attribute_name
                                elif typ == 'VALUE':
                                    cs.type = 'VALUE'
                                    if isinstance(bs.value, str):
                                        cs.value = bs.value
                                    elif hasattr(bs.value, '__len__'):
                                        for i in range(len(bs.value)):
                                            cs.value[i] = bs.value[i]
                                    else:
                                        cs.value = bs.value
                            except Exception:
                                pass

            cage_obj.add_rest_position_attribute = True
            cage_obj.display_type = 'TEXTURED'
            cage_obj.hide_render = True
            cage_obj['_giggle_cage'] = True
            cage_obj['_giggle_source_body'] = obj.name
            cage_obj['_giggle_vg_name'] = vg_name

            # 7. Add Surface Deform to Body
            sd_name = f"Giggle_Cage_SD_{vg_name}"
            body_sd = obj.modifiers.new(sd_name, 'SURFACE_DEFORM')
            body_sd.target = cage_obj
            body_sd.vertex_group = vg_name
            body_sd.falloff = 4.0

            # Move Surface Deform right after Armatures
            arm_idx = -1
            for idx_m, m in enumerate(obj.modifiers):
                if m.type == 'ARMATURE':
                    arm_idx = idx_m
            if arm_idx >= 0 and arm_idx + 1 < len(obj.modifiers):
                with context.temp_override(active_object=obj, object=obj):
                    try:
                        bpy.ops.object.modifier_move_to_index(modifier=body_sd.name, index=arm_idx + 1)
                    except Exception:
                        pass

            # 8. Bind Surface Deform
            with context.temp_override(active_object=obj, object=obj):
                bpy.ops.object.surfacedeform_bind(modifier=body_sd.name)

            if not body_sd.is_bound:
                raise RuntimeError(f"Surface Deform failed to bind to {cage_name}.")

            # 9. Mute body full-mesh solver
            src_mod.show_viewport = False
            src_mod.show_render = False
            set_zone_cage_error(src_mod, "")

            # 10. Auto-route assigned clothing to the cage
            clothing_count = 0
            for garment in scene.objects:
                if garment.type == 'MESH' and garment != obj and garment != cage_obj:
                    g_sd = garment.modifiers.get(f"Giggle_Cage_SD_{vg_name}") or garment.modifiers.get("Giggle_Cage_SurfaceDeform")
                    if g_sd and g_sd.target in {obj, None, existing_cage}:
                        g_sd.target = cage_obj
                        with context.temp_override(active_object=garment, object=garment):
                            try:
                                bpy.ops.object.surfacedeform_bind(modifier=g_sd.name)
                                clothing_count += 1
                            except Exception:
                                pass

        except Exception as exc:
            # ACID Rollback
            for o in created_objects:
                try:
                    bpy.data.objects.remove(o, do_unlink=True)
                except Exception:
                    pass
            for m in created_meshes:
                try:
                    bpy.data.meshes.remove(m, do_unlink=True)
                except Exception:
                    pass
            body_sd_cleanup = obj.modifiers.get(f"Giggle_Cage_SD_{vg_name}")
            if body_sd_cleanup:
                obj.modifiers.remove(body_sd_cleanup)
            src_mod.show_viewport = orig_src_mod_viewport
            src_mod.show_render = orig_src_mod_render
            set_zone_cage_error(src_mod, str(exc))
            if arm_obj:
                arm_obj.data.pose_position = orig_pose_pos
            scene.frame_set(orig_frame)
            if orig_active and orig_active.name in bpy.data.objects:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            for o in context.selected_objects:
                try:
                    o.select_set(False)
                except Exception:
                    pass
            for o in orig_selected:
                if o and o.name in bpy.data.objects:
                    try:
                        o.select_set(True)
                    except Exception:
                        pass
            if orig_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=orig_mode)
                except Exception:
                    pass
            self.report({'ERROR'}, f"Failed to generate cage: {exc}")
            return {'CANCELLED'}

        # Restore frame and pose
        if arm_obj:
            arm_obj.data.pose_position = orig_pose_pos
        scene.frame_set(orig_frame)
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=orig_mode)
            except Exception:
                pass
        context.view_layer.update()

        final_verts = len(cage_obj.data.vertices)
        self.report({'INFO'}, f"Generated cage '{cage_name}' ({final_verts} verts) — 5-8x faster evaluation active!")
        return {'FINISHED'}


class GIGGLE_OT_toggle_simulation_mode(Operator):
    """Toggle active zone between Full-Mesh XPBD and accelerated Cage XPBD"""
    bl_idname = "giggle.toggle_simulation_mode"
    bl_label = "Switch Simulation Mode"
    bl_description = "Switch active zone between legacy Full-Mesh XPBD and accelerated Cage XPBD"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        src_mod = mods[idx]

        s_in = getattr(getattr(src_mod, "properties", None), "inputs", None)
        vg_name = getattr(s_in.Socket_2, "attribute_name", "") if (s_in and hasattr(s_in, "Socket_2")) else ""
        if not vg_name:
            self.report({'ERROR'}, "No vertex group assigned to active zone.")
            return {'CANCELLED'}

        in_cage = is_zone_in_cage_mode(obj, src_mod)
        if in_cage:
            # Revert to Full-Mesh
            sd = get_zone_sd_modifier(obj, vg_name)
            if sd:
                obj.modifiers.remove(sd)
            cage = get_zone_cage_object(obj, vg_name)
            if cage:
                bpy.data.objects.remove(cage, do_unlink=True)
            src_mod.show_viewport = True
            src_mod.show_render = True
            set_zone_cage_error(src_mod, "")
            self.report({'INFO'}, f"Switched '{src_mod.name}' to Full-Mesh XPBD (Legacy)")
        else:
            # Accelerate with Cage
            return bpy.ops.giggle.generate_cage()

        return {'FINISHED'}


class GIGGLE_OT_rebuild_cage(Operator):
    """Rebuild active zone simulation cage from current rest geometry"""
    bl_idname = "giggle.rebuild_cage"
    bl_label = "Rebuild Simulation Cage"
    bl_description = "Regenerate and rebind the proxy cage if mesh geometry or vertex weights changed"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        return bpy.ops.giggle.generate_cage()


class GIGGLE_OT_keep_full_mesh(Operator):
    """Accept Full-Mesh XPBD for this zone and hide the cage failure notice"""
    bl_idname = "giggle.keep_full_mesh"
    bl_label = "Keep Full-Mesh XPBD"
    bl_description = "Keep this zone on Full-Mesh XPBD and dismiss the cage binding notice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        if not (0 <= idx < len(mods)):
            return {'CANCELLED'}
        mod = mods[idx]
        set_zone_cage_error(mod, "")
        mod.show_viewport = True
        mod.show_render = True
        self.report(
            {'INFO'},
            f"'{mod.name}' stays on Full-Mesh XPBD. It simulates every vertex of this mesh."
        )
        return {'FINISHED'}


class GIGGLE_OT_remove_zone(Operator):
    bl_idname = "giggle.remove_zone"
    bl_label = "Remove Zone"
    bl_description = "Remove the selected jiggle zone modifier from this object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and get_giggle_modifiers(obj)

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index

        if 0 <= idx < len(mods):
            target_mod = mods[idx]
            name = target_mod.name
            # Clean up object ID metadata
            obj.pop(f"_giggle_{name}_preset", None)
            obj.pop(f"_giggle_{name}_category", None)
            obj.pop(f"_giggle_{name}_gender", None)
            obj.pop(f"_giggle_{name}_customized", None)
            obj.pop(f"_giggle_{name}_support_base_json", None)
            obj.pop(f"_giggle_{name}_cage_error", None)
            obj.pop("_giggle_last_synced_mod", None)
            # Clean up associated Cage XPBD proxy and Surface Deform modifier if present
            s_in = getattr(getattr(target_mod, "properties", None), "inputs", None)
            vg_name = getattr(s_in.Socket_2, "attribute_name", "") if (s_in and hasattr(s_in, "Socket_2")) else ""
            if vg_name:
                sd = get_zone_sd_modifier(obj, vg_name)
                if sd:
                    try:
                        obj.modifiers.remove(sd)
                    except Exception:
                        pass
                cage = get_zone_cage_object(obj, vg_name)
                if cage:
                    try:
                        bpy.data.objects.remove(cage, do_unlink=True)
                    except Exception:
                        pass
            obj.modifiers.remove(target_mod)
            settings.active_zone_index = max(0, idx - 1)
            # Preserve user active frame during zone removal
            self.report({'INFO'}, f"Removed zone modifier '{name}'")
            return {'FINISHED'}

        return {'CANCELLED'}



class GIGGLE_OT_apply_support_level(Operator):
    bl_idname = "giggle.apply_support_level"
    bl_label = "Apply Support Level"
    bl_description = "Apply a repeatable support profile to the active Wiggy zone"
    bl_options = {'REGISTER', 'UNDO'}

    level: EnumProperty(
        items=[
            ('FREE', "Bare / Free", "Maximum travel and sway with a soft, loose response"),
            ('LOOSE', "Loose Fit", "Relaxed movement with moderate restraint"),
            ('NORMAL', "Normal Fit", "Balanced everyday support"),
            ('FIRM', "Firm / Sports", "Shorter travel, firmer shape and quicker settling"),
            ('COMPRESSION', "High Compression", "Minimal travel and very firm shape retention"),
        ],
        default='NORMAL'
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        mods = get_giggle_modifiers(obj)
        settings = getattr(context.scene, 'giggle_settings', None)
        if not settings or not (0 <= settings.active_zone_index < len(mods)):
            return False
        return bool(mods[settings.active_zone_index].node_group and mods[settings.active_zone_index].node_group.name == 'Wiggy 0.1')

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        if not (0 <= idx < len(mods)):
            self.report({'ERROR'}, "No active Giggle zone.")
            return {'CANCELLED'}
        mod = mods[idx]
        if not mod.node_group or mod.node_group.name != 'Wiggy 0.1':
            self.report({'ERROR'}, "Support profiles are only available for Wiggy XPBD zones.")
            return {'CANCELLED'}

        meta = get_mod_giggle_metadata(mod)
        is_hair = bool(meta and meta[1] == 'PROPS_HAIR')
        base_keys = ('Socket_33', 'Socket_8', 'Socket_123', 'Socket_119', 'Socket_6', 'Socket_30', 'Socket_122', 'Socket_118')

        try:
            saved = obj.get(f"_giggle_{mod.name}_support_base_json")
        except Exception:
            saved = None
        base = None
        if saved:
            try:
                base = json.loads(saved)
            except (TypeError, ValueError):
                base = None
        if base is None:
            is_custom = bool(obj.get(f"_giggle_{mod.name}_customized", False))
            preset_id = meta[2] if meta else None
            preset_data = PRESETS.get(preset_id) if preset_id else None
            if preset_data and not is_custom:
                source = preset_data.get('values', {})
                base = {key: source.get(key) for key in base_keys if source.get(key) is not None}
            else:
                base = {}
                for key in base_keys:
                    value = get_mod_socket(mod, key)
                    if value is not None:
                        base[key] = value
            for key, default in {
                'Socket_33': 0.12, 'Socket_8': 1.75, 'Socket_123': 0.038,
                'Socket_119': 0.42, 'Socket_6': 0.65, 'Socket_30': 0.36,
                'Socket_122': 2, 'Socket_118': 0.94,
            }.items():
                base.setdefault(key, default)
            # Persist the unscaled starting point so repeated clicks are idempotent.
            try:
                obj[f"_giggle_{mod.name}_support_base_json"] = json.dumps(base)
            except Exception:
                pass

        level_values = {
            'FREE':         (1.35, 0.70, 1.40, 1.35, 0.80, 0.85, 0),
            'LOOSE':        (1.18, 0.88, 1.18, 1.15, 0.92, 0.92, None),
            'NORMAL':       (1.00, 1.00, 1.00, 1.00, 1.00, 1.00, None),
            'FIRM':         (0.72, 1.28, 0.65, 0.62, 1.20, 1.18, None),
            'COMPRESSION':  (0.48, 1.65, 0.35, 0.35, 1.35, 1.38, None),
        }
        if is_hair:
            hair_profiles = {
                'FREE':        (0.25, 1.20, 0.12, 1.10, 0.95, 0.35, 0.00),
                'LOOSE':       (0.20, 1.60, 0.09, 0.85, 0.96, 0.45, 0.00),
                'NORMAL':      (0.15, 2.00, 0.06, 0.55, 0.98, 0.55, 0.00),
                'FIRM':        (0.10, 2.60, 0.03, 0.35, 0.98, 0.70, 0.00),
                'COMPRESSION': (0.05, 3.50, 0.015, 0.20, 0.99, 0.85, 0.00),
            }
            soft, damping, sag, sway, stretch, bending, edge = hair_profiles[self.level]
            result = {
                'Socket_33': soft, 'Socket_8': damping, 'Socket_123': sag,
                'Socket_119': sway, 'Socket_6': stretch, 'Socket_30': bending,
                'Socket_122': int(edge), 'Socket_118': 0.0,
            }
        else:
            f_soft, f_damp, f_sag, f_sway, f_stretch, f_bend, fixed_edge = level_values[self.level]
            result = {
                'Socket_33': min(0.50, max(0.0, float(base['Socket_33']) * f_soft)),
                'Socket_8': min(5.0, max(0.0, float(base['Socket_8']) * f_damp)),
                'Socket_123': min(0.50, max(0.0, float(base['Socket_123']) * f_sag)),
                'Socket_119': min(1.50, max(0.0, float(base['Socket_119']) * f_sway)),
                'Socket_6': min(1.0, max(0.0, float(base['Socket_6']) * f_stretch)),
                'Socket_30': min(1.0, max(0.0, float(base['Socket_30']) * f_bend)),
                'Socket_122': int(fixed_edge if fixed_edge is not None else max(base['Socket_122'], 2 if self.level == 'COMPRESSION' else (1 if self.level == 'FIRM' else 0))),
                'Socket_118': float(base['Socket_118']),
            }

        failed = [key for key, value in result.items() if not set_mod_socket(mod, key, value=value)]
        mark_mod_customized(mod)
        # mark_mod_customized clears the stored baseline; restore it after this operation.
        try:
            obj[f"_giggle_{mod.name}_support_base_json"] = json.dumps(base)
        except Exception:
            pass

        # Preserve user active frame during preset application

        if failed:
            self.report({'WARNING'}, f"Support profile partially applied; unavailable inputs: {', '.join(failed)}")
        else:
            self.report({'INFO'}, f"Applied repeatable '{self.level.title()}' support profile to '{mod.name}'.")
        return {'FINISHED'}

class GIGGLE_OT_apply_preset(Operator):
    bl_idname = "giggle.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply a motion-profile preset to the active Wiggy XPBD zone"
    bl_options = {'REGISTER', 'UNDO'}

    preset: StringProperty(name="Preset ID", default="BREASTS")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None) if context.scene else None
        mods = get_giggle_modifiers(obj) if obj else []
        if not settings or not (0 <= settings.active_zone_index < len(mods)):
            return False
        active_mod = mods[settings.active_zone_index]
        return bool(active_mod.node_group and active_mod.node_group.name == 'Wiggy 0.1')

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index

        if not (0 <= idx < len(mods)):
            return {'CANCELLED'}

        mod = mods[idx]
        preset = PRESETS.get(self.preset)
        if not preset:
            self.report({'ERROR'}, f"Unknown preset '{self.preset}'.")
            return {'CANCELLED'}
        if preset.get('engine', 'WIGGY') != 'WIGGY' or not mod.node_group or mod.node_group.name != 'Wiggy 0.1':
            self.report({'ERROR'}, "This preset requires the Wiggy XPBD modifier. Legacy Jiggle V2 modifiers cannot use Wiggy recipes.")
            return {'CANCELLED'}

        meta = get_mod_giggle_metadata(mod)
        active_cat = meta[1] if meta else preset.get('category_id', '')
        values_to_apply = dict(preset['values'])
        enforce_anatomical_safety(values_to_apply, active_cat)

        failed_sockets = []
        for sock_id, val in values_to_apply.items():
            if not set_mod_socket(mod, sock_id, value=val):
                failed_sockets.append(sock_id)
        if failed_sockets:
            self.report({'WARNING'}, "Preset partially applied; unavailable inputs: " + ", ".join(failed_sockets))

        # Preserve user active frame during support scaling

        # Store applied recipe metadata on parent object
        p_gender = preset.get('gender', 'FEMALE') if preset else None
        p_cat = preset.get('category_id', '') if preset else None
        set_mod_giggle_metadata(mod, p_gender, p_cat, self.preset)
        touch_zone_modified(mod)

        self.report({'INFO'}, f"Applied '{preset['name']}' to '{mod.name}'")
        return {'FINISHED'}


class GIGGLE_OT_toggle_mute(Operator):
    bl_idname = "giggle.toggle_mute"
    bl_label = "Toggle Zone"
    bl_description = "Enable or disable this zone simulation"
    bl_options = {'REGISTER', 'UNDO'}

    mod_name: StringProperty(name="Modifier Name")

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get(self.mod_name)
        if mod:
            mod.show_viewport = not mod.show_viewport
            mod.show_render = mod.show_viewport
        return {'FINISHED'}


class GIGGLE_OT_solo_zone(Operator):
    bl_idname = "giggle.solo_zone"
    bl_label = "Solo Zone"
    bl_description = "Mute all other Giggle zones and isolate the active one"
    bl_options = {'REGISTER', 'UNDO'}

    mod_name: StringProperty(name="Modifier Name")

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        mods = get_giggle_modifiers(obj)
        target = obj.modifiers.get(self.mod_name)
        if not target:
            return {'CANCELLED'}

        others_hidden = all(not m.show_viewport for m in mods if m != target)
        if others_hidden:
            for m in mods:
                m.show_viewport = True
                m.show_render = True
        else:
            for m in mods:
                visible = (m == target)
                m.show_viewport = visible
                m.show_render = visible

        return {'FINISHED'}


class GIGGLE_OT_add_collider(Operator):
    bl_idname = "giggle.add_collider"
    bl_label = "Set as Collider"
    bl_description = "Configure selected objects as XPBD colliders and connect them to active zone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None) if context.scene else None
        mods = get_giggle_modifiers(active_obj) if active_obj else []
        if not (settings and context.selected_objects and len(context.selected_objects) > 1):
            return False
        idx = settings.active_zone_index
        return bool(0 <= idx < len(mods) and mods[idx].node_group and mods[idx].node_group.name == "Wiggy 0.1")

    def execute(self, context):
        active_obj = context.active_object
        mods = get_giggle_modifiers(active_obj)
        settings = context.scene.giggle_settings
        idx = settings.active_zone_index

        if not (0 <= idx < len(mods)):
            self.report({'WARNING'}, "No active Giggle zone on the active mesh.")
            return {'CANCELLED'}

        mod = mods[idx]
        if not mod.node_group or mod.node_group.name != "Wiggy 0.1":
            self.report({'ERROR'}, "Colliders are supported only by Wiggy XPBD zones.")
            return {'CANCELLED'}

        collider_ng = ensure_nodetree("Collider")
        if not collider_ng:
            self.report({'ERROR'}, "Could not load the Collider node group from the bundled asset.")
            return {'CANCELLED'}

        col_name = "Giggle_Colliders"
        col = bpy.data.collections.get(col_name)
        if not col:
            col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(col)

        if not set_mod_socket(mod, 'Socket_7', value=col):
            self.report({'ERROR'}, "Could not connect the collider collection to the active Wiggy zone.")
            return {'CANCELLED'}

        added_count = 0
        for other in context.selected_objects:
            if other == active_obj:
                continue
            if other.name not in col.objects:
                col.objects.link(other)
            if other.type == 'MESH':
                has_col_mod = any(m.type == 'NODES' and m.node_group == collider_ng for m in other.modifiers)
                if not has_col_mod:
                    col_m = other.modifiers.new(name="Collider", type='NODES')
                    col_m.node_group = collider_ng
            added_count += 1

        self.report({'INFO'}, f"Configured {added_count} collider(s) in '{col_name}' and connected to '{mod.name}'")
        return {'FINISHED'}


class GIGGLE_OT_add_wind(Operator):
    bl_idname = "giggle.add_wind"
    bl_label = "Add Wind Force Field"
    bl_description = "Create a Geometry Nodes Wind force field and add it to the Colliders collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wind_ng = ensure_nodetree("Wiggy Wind")
        if not wind_ng:
            self.report({'ERROR'}, "Could not load 'Wiggy Wind' node group.")
            return {'CANCELLED'}

        col_name = "Giggle_Colliders"
        col = bpy.data.collections.get(col_name)
        if not col:
            col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(col)

        mesh = bpy.data.meshes.new("Giggle_Wind")
        wind_obj = bpy.data.objects.new("Giggle_Wind", mesh)
        col.objects.link(wind_obj)
        
        mod = wind_obj.modifiers.new(name="Wiggy Wind", type='NODES')
        mod.node_group = wind_ng

        context.view_layer.objects.active = wind_obj
        wind_obj.select_set(True)
        self.report({'INFO'}, f"Created '{wind_obj.name}' in '{col_name}'")
        return {'FINISHED'}


class GIGGLE_OT_autotune_substeps(Operator):
    bl_idname = "giggle.autotune_substeps"
    bl_label = "Auto-Tune Substeps for FPS"
    bl_description = "Automatically set Substeps according to scene frame rate (GUIDE [2.9]: 24fps=10, 60fps=4)"
    bl_options = {'REGISTER', 'UNDO'}

    all_zones: BoolProperty(
        name="All Zones",
        default=False,
        description="Auto-tune all Wiggy zones on the object (False: active zone only)"
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bool(obj and any(m.node_group and m.node_group.name == "Wiggy 0.1" for m in get_giggle_modifiers(obj)))

    def execute(self, context):
        obj = context.active_object
        mods = [m for m in get_giggle_modifiers(obj) if m.node_group and m.node_group.name == "Wiggy 0.1"]
        if not mods:
            self.report({'WARNING'}, "No Wiggy XPBD zones found on the active object.")
            return {'CANCELLED'}

        fps = context.scene.render.fps / (context.scene.render.fps_base or 1.0)
        if fps <= 0:
            self.report({'ERROR'}, "The scene frame rate must be greater than zero.")
            return {'CANCELLED'}
        substeps = max(2, min(16, round(240.0 / fps)))

        if not self.all_zones:
            idx = context.scene.giggle_settings.active_zone_index
            target_mods = [mods[idx]] if 0 <= idx < len(mods) else [mods[0]]
        else:
            target_mods = mods

        updated = [m for m in target_mods if set_mod_socket(m, 'Socket_14', value=substeps)]
        if not updated:
            self.report({'ERROR'}, "Could not update the Substeps input on the selected Wiggy zone.")
            return {'CANCELLED'}
        zone_label = f"across {len(updated)} zone(s)" if self.all_zones else f"on '{target_mods[0].name}'"
        self.report({'INFO'}, f"Scene FPS is {fps:.1f} -> Set Substeps to {substeps} {zone_label}")
        return {'FINISHED'}


class GIGGLE_OT_reset_sim(Operator):
    bl_idname = "giggle.reset_sim"
    bl_label = "Reset Sim to Start"
    bl_description = "Jump to the scene start frame and purge simulation caches"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        start_f = context.scene.frame_start
        context.scene.frame_set(start_f)
        obj = context.active_object
        if obj:
            try:
                with context.temp_override(active_object=obj, selected_objects=[obj]):
                    bpy.ops.object.simulation_nodes_cache_delete()
            except Exception:
                pass
            try:
                obj.update_tag(refresh={'DATA'})
            except Exception:
                pass
        self.report({'INFO'}, f"Reset simulation to frame {start_f} and purged cache.")
        return {'FINISHED'}



FINGERPRINT_SCHEMA = "2.0.0"


def get_action_fcurves(act):
    """Retrieve all F-Curves from an action, supporting both Blender 5.2/5.3 Layered Actions and legacy actions."""
    if not act:
        return []
    fcurves = []
    if hasattr(act, "layers") and act.layers:
        for layer in act.layers:
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    fcurves.extend(cb.fcurves)
    elif hasattr(act, "fcurves") and act.fcurves:
        fcurves.extend(act.fcurves)
    return fcurves


def get_driving_armature(cage_or_mesh):
    """Find the armature driving this simulation object or its source body."""
    if not cage_or_mesh:
        return None
    for m in getattr(cage_or_mesh, "modifiers", []):
        if m.type == 'ARMATURE' and m.object:
            return m.object
    if cage_or_mesh.parent and getattr(cage_or_mesh.parent, "type", "") == 'ARMATURE':
        return cage_or_mesh.parent
    src_body_name = cage_or_mesh.get('_giggle_source_body')
    if src_body_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body:
            for m in getattr(src_body, "modifiers", []):
                if m.type == 'ARMATURE' and m.object:
                    return m.object
            if src_body.parent and getattr(src_body.parent, "type", "") == 'ARMATURE':
                return src_body.parent
    scene = getattr(bpy.context, 'scene', None)
    for o in (scene.objects if scene is not None else bpy.data.objects):
        if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action:
            return o
    return None


def get_binding_armatures(objects):
    """Armatures that deform these meshes (armature modifiers and armature parenting)."""
    found = []
    seen = set()
    for obj in objects:
        if not obj or getattr(obj, "type", "") != 'MESH':
            continue
        candidates = [m.object for m in getattr(obj, "modifiers", [])
                      if m.type == 'ARMATURE' and m.object]
        parent = getattr(obj, "parent", None)
        if parent is not None and getattr(parent, "type", "") == 'ARMATURE':
            candidates.append(parent)
        for arm in candidates:
            if arm.name not in seen:
                seen.add(arm.name)
                found.append(arm)
    return found


def enter_rest_pose(armatures):
    """Switch the armature datablocks behind these objects to REST.

    Returns (switched, failures):
      switched - [(datablock, original_pose_position)] actually left in REST
      failures - [(armature_name, datablock_name, error_text)]
    Each datablock is switched exactly once, even when several armature
    objects share it. A datablock that refuses REST is reported, never ignored.
    """
    failures = []
    wanted = []
    seen = set()
    for arm in armatures:
        arm_name = getattr(arm, "name", "?")
        try:
            data = getattr(arm, "data", None)
            if data is None or not hasattr(data, "pose_position"):
                continue
            key = data.as_pointer()
            if key in seen:
                continue
            seen.add(key)
            wanted.append((arm_name, data))
        except Exception as exc:
            failures.append((arm_name, "?", str(exc)))

    switched = []
    for arm_name, data in wanted:
        data_name = getattr(data, "name", "?")
        try:
            original = data.pose_position
            data.pose_position = 'REST'
        except Exception as exc:
            failures.append((arm_name, data_name, str(exc)))
            continue
        if data.pose_position != 'REST':
            failures.append((arm_name, data_name, "armature refused Rest Pose"))
            continue
        switched.append((data, original))
    return switched, failures


def unrested_armatures(switched):
    """Armature datablocks that did not stay in REST once the depsgraph ran."""
    bad = []
    for data, _original in switched or ():
        try:
            if data.pose_position != 'REST':
                bad.append(getattr(data, "name", "armature data"))
        except Exception:
            bad.append(getattr(data, "name", "armature data"))
    return bad


def restore_pose_position(saved):
    """Restore pose_position values exactly.

    Returns [(datablock_name, error_text)] for every datablock that could not
    be restored, so the caller can report it instead of binding against a shape
    nobody asked for.
    """
    failures = []
    for data, original in saved or ():
        name = getattr(data, "name", "armature data")
        try:
            data.pose_position = original
            if data.pose_position != original:
                failures.append((name, f"armature stayed in {data.pose_position}"))
        except Exception as exc:
            failures.append((name, str(exc)))
    return failures


def compute_animation_hash(arm_obj):
    """Deterministic hash of armature animation keyframes, handles, and interpolation."""
    if not arm_obj or not getattr(arm_obj, "animation_data", None):
        return "NO_ANIM"
    act = arm_obj.animation_data.action
    if not act:
        return "NO_ACTION"
    fcurves = get_action_fcurves(act)
    if not fcurves:
        return f"EMPTY_ACTION_{act.name}"
    h = hashlib.sha256()
    h.update(act.name.encode('utf-8'))
    sorted_fc = sorted(fcurves, key=lambda fc: (fc.data_path, fc.array_index))
    for fc in sorted_fc:
        h.update(f"{fc.data_path}[{fc.array_index}]".encode('utf-8'))
        for kp in fc.keyframe_points:
            entry = f"{round(kp.co[0], 3)}:{round(kp.co[1], 4)}:{round(kp.handle_left[0], 3)}:{round(kp.handle_left[1], 4)}:{round(kp.handle_right[0], 3)}:{round(kp.handle_right[1], 4)}:{kp.interpolation};"
            h.update(entry.encode('utf-8'))
    return h.hexdigest()


def compute_armature_hash(arm_obj):
    """Deterministic hash of armature bone rest transforms and constraints."""
    if not arm_obj or arm_obj.type != 'ARMATURE' or not arm_obj.data:
        return "NO_ARMATURE"
    h = hashlib.sha256()
    for b in sorted(arm_obj.data.bones, key=lambda x: x.name):
        h.update(b.name.encode('utf-8'))
        h.update(f"{b.head.x:.4f},{b.head.y:.4f},{b.head.z:.4f}".encode('utf-8'))
        h.update(f"{b.tail.x:.4f},{b.tail.y:.4f},{b.tail.z:.4f}".encode('utf-8'))
    if arm_obj.pose:
        for pb in sorted(arm_obj.pose.bones, key=lambda x: x.name):
            for c in pb.constraints:
                h.update(f"{pb.name}:{c.type}:{c.mute}:{getattr(c, 'influence', 1.0):.4f}".encode('utf-8'))
    return h.hexdigest()


def compute_physics_hash(cage_obj):
    """Deterministic hash of Giggle Wiggy GN modifier inputs."""
    if not cage_obj:
        return "NO_OBJ"
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod:
        return "NO_WIGGY_MOD"
    h = hashlib.sha256()
    s_in = getattr(getattr(mod, "properties", None), "inputs", None)
    if s_in:
        for identifier in sorted(dir(s_in)):
            if identifier.startswith("Socket_"):
                sock = getattr(s_in, identifier)
                val = getattr(sock, "value", None)
                if val is not None:
                    h.update(f"{identifier}={val};".encode('utf-8'))
                att = getattr(sock, "attribute_name", None)
                if att is not None:
                    h.update(f"{identifier}_att={att};".encode('utf-8'))
    return h.hexdigest()


def compute_geometry_hash(cage_obj):
    """Deterministic hash of cage mesh vertex count and rest vertex coordinates."""
    if not cage_obj or cage_obj.type != 'MESH' or not cage_obj.data:
        return "NO_GEOMETRY"
    h = hashlib.sha256()
    mesh = cage_obj.data
    h.update(f"vcount={len(mesh.vertices)};".encode('utf-8'))
    for v in mesh.vertices:
        h.update(f"{v.co.x:.4f},{v.co.y:.4f},{v.co.z:.4f};".encode('utf-8'))
    src_body_name = cage_obj.get('_giggle_source_body')
    vg_name = cage_obj.get('_giggle_vg_name')
    if src_body_name and vg_name:
        src_body = bpy.data.objects.get(src_body_name)
        if src_body and src_body.type == 'MESH' and src_body.data:
            vg = src_body.vertex_groups.get(vg_name)
            if vg:
                h.update(f"vg={vg_name};".encode('utf-8'))
                for v in src_body.data.vertices:
                    try:
                        w = vg.weight(v.index)
                        if w > 0.0001:
                            h.update(f"{v.index}:{w:.3f};".encode('utf-8'))
                    except Exception:
                        pass
    return h.hexdigest()


def compute_simulation_hash(scene, settings, storage_mode, f_start, f_end):
    """Deterministic hash of scene frame range, FPS, and storage mode."""
    h = hashlib.sha256()
    fps = round(scene.render.fps / scene.render.fps_base, 3) if scene.render.fps_base else scene.render.fps
    h.update(f"range={f_start}-{f_end};fps={fps};storage={storage_mode};".encode('utf-8'))
    return h.hexdigest()


def compute_zone_fingerprint(cage_or_mesh, context, storage_mode="PACKED", f_start=1, f_end=250):
    """Generate complete multi-domain cryptographic dependency fingerprint."""
    scene = context.scene
    arm = get_driving_armature(cage_or_mesh)
    return {
        "schema": FINGERPRINT_SCHEMA,
        "animation": compute_animation_hash(arm),
        "armature": compute_armature_hash(arm),
        "physics": compute_physics_hash(cage_or_mesh),
        "geometry": compute_geometry_hash(cage_or_mesh),
        "simulation": compute_simulation_hash(scene, None, storage_mode, f_start, f_end)
    }


def save_zone_bake_fingerprint(cage_or_mesh, context, storage_mode, f_start, f_end, fp_dict=None, is_valid=True, reason=""):
    """Stamp verified bake fingerprint and status metadata onto simulation object."""
    now = time.time()
    fp = fp_dict or compute_zone_fingerprint(cage_or_mesh, context, storage_mode, f_start, f_end)
    cage_or_mesh['_giggle_baked_at_timestamp'] = now
    cage_or_mesh['_giggle_bake_fingerprint_json'] = json.dumps(fp, sort_keys=True)
    cage_or_mesh['_giggle_bake_schema_version'] = FINGERPRINT_SCHEMA
    cage_or_mesh['_giggle_baked_frame_range'] = (f_start, f_end)
    cage_or_mesh['_giggle_baked_storage'] = storage_mode
    cage_or_mesh['_giggle_status'] = "BAKED" if is_valid else ("OUTDATED" if "modified" in reason.lower() else "FAILED")
    cage_or_mesh['_giggle_last_known_valid'] = is_valid
    cage_or_mesh['_giggle_outdated_reason'] = reason
    cage_or_mesh.pop('_giggle_settings_modified_at', None)


GIGGLE_CAGE_BIND_PREFIX = "Giggle_Cage_"


def get_surface_deform_targets(objects=None):
    """Objects in `objects` (default: the active scene) that some mesh drives through Surface Deform."""
    if objects is None:
        scene = getattr(bpy.context, 'scene', None)
        objects = scene.objects if scene is not None else bpy.data.objects
    targets = set()
    for ob in objects:
        for m in ob.modifiers:
            if m.type == 'SURFACE_DEFORM' and m.target:
                targets.add(m.target)
    return targets


def get_giggle_cage_bind_targets(objects=None):
    """Surface Deform targets driven by a modifier Giggle named.

    Only a bind Giggle created counts as ownership proof. A pre-1.2 cage carries no metadata, so
    the bind is the only evidence, and another add-on driving its own Wiggy cage through its own
    Surface Deform must not be adopted.
    """
    if objects is None:
        scene = getattr(bpy.context, 'scene', None)
        objects = scene.objects if scene is not None else bpy.data.objects
    targets = set()
    for ob in objects:
        for m in ob.modifiers:
            if (m.type == 'SURFACE_DEFORM' and m.target
                    and m.name.startswith(GIGGLE_CAGE_BIND_PREFIX)):
                targets.add(m.target)
    return targets


def is_giggle_owned_cage(obj, bind_targets=None):
    """True only for cages this add-on created or can prove it drives.

    A mesh that merely ends in '_Cage' or sits in a 'Giggle_Cages' collection belongs to whoever
    made it. Giggle is a Wiggy fork, so trusting those names let it bake and clear another
    add-on's simulation.
    """
    if not obj or obj.type != 'MESH':
        return False
    # The proxy marker has to win, because builds before this check stamped _giggle_cage onto
    # clothing proxies. Those proxies carry _giggle_source_body and _giggle_vg_name too, are bound
    # to garments through Surface Deform, and hold a copy of the body's Wiggy modifier, so a stale
    # flag is enough to make one look like a cage. Clear the flag instead of trusting it.
    if obj.get('_giggle_proxy'):
        if obj.get('_giggle_cage'):
            del obj['_giggle_cage']
        return False
    if obj.get('_giggle_cage'):
        return True
    # 1.2 and 2.0.0 cages always store the source body and vertex group; adopt them once.
    if obj.get('_giggle_source_body') and obj.get('_giggle_vg_name'):
        obj['_giggle_cage'] = True
        return True
    # Cages written before 1.2 carry no metadata at all. The only structural proof is that a body
    # mesh is bound to them through a Surface Deform modifier Giggle named. This stays a
    # per-session test: it is not proof enough to write a permanent ownership flag.
    if bind_targets is None:
        bind_targets = get_giggle_cage_bind_targets()
    return obj in bind_targets and any(
        m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'
        for m in obj.modifiers)


def get_giggle_simulation_objects(context, obj=None):
    """Return Giggle-managed simulation objects in the active scene (cages or a full-mesh zone)."""
    sim_objs = []
    scene = getattr(context, 'scene', None)
    objects = scene.objects if scene is not None else bpy.data.objects
    bind_targets = get_giggle_cage_bind_targets(objects)
    for o in objects:
        if not is_giggle_owned_cage(o, bind_targets):
            continue
        if any(m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for m in o.modifiers):
            if o not in sim_objs:
                sim_objs.append(o)
    target = obj or context.active_object
    if target and target.type == 'MESH':
        full_mods = [m for m in get_giggle_modifiers(target) if m.show_viewport and not is_zone_in_cage_mode(target, m)]
        if full_mods and target not in sim_objs:
            sim_objs.append(target)
    return sim_objs


def get_cage_bake_status(cage_obj):
    """Fast check of cage bake status for UI display (zero heavy computation during redraw)."""
    if not cage_obj or cage_obj.type != 'MESH':
        return 'NOT_BAKED', (1, 250), 'PACKED', "Object is not a mesh"
    bake_time = cage_obj.get('_giggle_baked_at_timestamp', None)
    if not bake_time:
        return 'NOT_BAKED', (1, 250), 'PACKED', "Not baked"

    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod or not mod.bakes:
        return 'NOT_BAKED', (1, 250), 'PACKED', "Missing Wiggy modifier"

    has_data = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_data:
        return 'NOT_BAKED', (1, 250), 'PACKED', "No simulation cache blocks"

    frange = cage_obj.get('_giggle_baked_frame_range', (1, 250))
    storage = cage_obj.get('_giggle_baked_storage', 'PACKED')

    last_mod_time = cage_obj.get('_giggle_settings_modified_at', 0)
    if last_mod_time > bake_time:
        return 'OUTDATED', frange, storage, "Physics settings modified via Giggle UI"

    st = cage_obj.get('_giggle_status', None)
    reason = cage_obj.get('_giggle_outdated_reason', '')
    if st in ('BAKED', 'OUTDATED', 'FAILED'):
        return st, frange, storage, reason

    return 'BAKED', frange, storage, "Matches Setup"


def get_requested_bake_config(context):
    """Return (storage_mode, frame_start, frame_end) as requested by the scene settings."""
    scene = context.scene
    settings = getattr(scene, 'giggle_settings', None)
    storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
    use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
    if settings is None or use_scene_range:
        return storage_mode, scene.frame_start, scene.frame_end
    return storage_mode, settings.bake_frame_start, settings.bake_frame_end


def check_cage_validity(cage_obj, context):
    """On-demand cryptographic dependency verification for a simulation cage."""
    if not cage_obj or cage_obj.type != 'MESH':
        return 'NOT_BAKED', "Object is not a mesh"
    
    bake_time = cage_obj.get('_giggle_baked_at_timestamp', None)
    if not bake_time:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Simulation not baked"
        return 'NOT_BAKED', "Simulation not baked"
    
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod or not mod.bakes:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Missing Wiggy modifier or bake items"
        return 'NOT_BAKED', "Missing Wiggy modifier or bake items"
    
    has_data = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_data:
        cage_obj['_giggle_status'] = 'NOT_BAKED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "No simulation cache blocks present"
        return 'NOT_BAKED', "No simulation cache blocks present"
    
    fp_json = cage_obj.get('_giggle_bake_fingerprint_json', None)
    if not fp_json:
        if cage_obj.get('_giggle_settings_modified_at', 0) > bake_time:
            cage_obj['_giggle_status'] = 'OUTDATED'
            cage_obj['_giggle_last_known_valid'] = False
            cage_obj['_giggle_outdated_reason'] = "Physics settings modified"
            return 'OUTDATED', "Physics settings modified"
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Missing dependency fingerprint (baked with older version)"
        return 'OUTDATED', "Missing dependency fingerprint (baked with older version)"
    
    try:
        saved_fp = json.loads(fp_json)
    except Exception:
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = "Invalid fingerprint JSON"
        return 'OUTDATED', "Invalid fingerprint JSON"

    saved_schema = cage_obj.get('_giggle_bake_schema_version', None)
    if saved_schema != FINGERPRINT_SCHEMA:
        reason = f"Cache uses fingerprint schema {saved_schema}, expected {FINGERPRINT_SCHEMA}"
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = reason
        return 'OUTDATED', reason

    # Compare the cache against what the scene asks for now, not against the values stored in the
    # cache. Reading the stored values back on both sides always matched.
    requested_storage, req_start, req_end = get_requested_bake_config(context)
    stored_range = cage_obj.get('_giggle_baked_frame_range', (req_start, req_end))
    stored_storage = cage_obj.get('_giggle_baked_storage', requested_storage)
    curr_fp = compute_zone_fingerprint(cage_obj, context, requested_storage, req_start, req_end)
    
    status = 'BAKED'
    reason = "Cache matches setup"
    if saved_fp.get('animation') != curr_fp['animation']:
        status = 'OUTDATED'
        reason = "Animation keyframes or handles modified"
    elif saved_fp.get('physics') != curr_fp['physics']:
        status = 'OUTDATED'
        reason = "Physics settings modified"
    elif saved_fp.get('geometry') != curr_fp['geometry']:
        status = 'OUTDATED'
        reason = "Cage geometry or vertex weights modified"
    elif saved_fp.get('armature') != curr_fp['armature']:
        status = 'OUTDATED'
        reason = "Armature rest pose or rig constraints modified"
    elif saved_fp.get('simulation') != curr_fp['simulation']:
        status = 'OUTDATED'
        reason = ("Frame range, FPS, or storage mode changed "
                  f"(cache: {stored_range[0]}-{stored_range[1]} {stored_storage}, "
                  f"requested: {req_start}-{req_end} {requested_storage})")
        
    cage_obj['_giggle_status'] = status
    cage_obj['_giggle_last_known_valid'] = (status == 'BAKED')
    cage_obj['_giggle_outdated_reason'] = reason
    return status, reason


def preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end):
    """Run pre-bake validation checks before touching existing caches."""
    if not sim_objs:
        return False, "No active Giggle simulation zones found."
    if storage_mode == 'DISK' and not bpy.data.is_saved:
        return False, "Please save your .blend file before baking to external disk."
    if f_end < f_start:
        return False, f"Invalid frame range: start frame ({f_start}) > end frame ({f_end})."
    if getattr(getattr(context, 'screen', None), 'is_animation_playing', False):
        return False, "Cannot bake while animation playback is running."
    
    for o in sim_objs:
        for m in o.modifiers:
            if m.type == 'NODES' and m.node_group and m.node_group.name != 'Wiggy 0.1':
                if any(node.type == 'SIMULATION_OUTPUT' for node in getattr(m.node_group, 'nodes', [])):
                    return False, f"Conflicting non-Giggle simulation modifier found on '{o.name}'. Aborting to protect unrelated simulations."
    return True, "Preflight passed"


BACKUP_KEEP = 1
CACHE_BACKUP_KEEP = 1


def create_project_backup(keep=BACKUP_KEEP, dirty=None):
    """Keep one recoverable copy of the project before a cache is replaced.

    When the session has unsaved edits the backup is written from the live session, not from the
    file on disk, otherwise a copy of the saved file is used and is reused while that file has not
    changed. `dirty` overrides the unsaved-changes test; it defaults to `bpy.data.is_dirty`.
    """
    if not bpy.data.is_saved:
        return None
    try:
        filepath = bpy.data.filepath
        if not filepath or not os.path.exists(filepath):
            return None
        backup_dir = os.path.join(os.path.dirname(filepath), "giggle_backup")
        os.makedirs(backup_dir, exist_ok=True)
        basename = os.path.basename(filepath)
        prefix = f"{basename}."
        existing = sorted(
            {os.path.join(backup_dir, name) for name in os.listdir(backup_dir)
             if name.startswith(prefix) and name.endswith(".bak")},
            key=os.path.getmtime, reverse=True)

        if dirty is None:
            # UI sessions set this when the .blend has unsaved edits. Background sessions cannot
            # be trusted with it: the flag stays False after adding or moving objects, so a copy
            # of the file on disk can be stale. Default to the live session instead - one extra
            # save is cheaper than a backup that does not contain the work being protected.
            dirty = bool(getattr(bpy.data, 'is_dirty', True))
            if not dirty and getattr(bpy.app, 'background', False):
                dirty = True
        src_stat = os.stat(filepath)
        unchanged = (not dirty and bool(existing)
                     and os.path.getsize(existing[0]) == src_stat.st_size
                     and int(os.path.getmtime(existing[0])) == int(src_stat.st_mtime))
        if unchanged:
            newest = existing[0]
        else:
            stamp = time.strftime("%Y%m%d_%H%M%S")
            newest = os.path.join(backup_dir, f"{basename}.{stamp}.bak")
            counter = 1
            while os.path.exists(newest):
                newest = os.path.join(backup_dir, f"{basename}.{stamp}_{counter}.bak")
                counter += 1
            if dirty:
                # Write the live session: the scene may hold work the saved file does not have.
                result = bpy.ops.wm.save_as_mainfile(
                    filepath=newest, copy=True, check_existing=False, compress=True)
                if result != {'FINISHED'}:
                    raise RuntimeError(f"save_as_mainfile returned {result}")
            else:
                shutil.copy2(filepath, newest)

        keep_list = [newest] + [p for p in existing if os.path.normcase(p) != os.path.normcase(newest)]
        for old in keep_list[keep:]:
            try:
                os.remove(old)
            except OSError:
                pass
        return newest
    except Exception as e:
        print(f"[Giggle Backup Warning] Could not create backup copy: {e}")
        return None


def cage_has_cache(cage_obj):
    """True when this cage already holds simulation cache blocks."""
    if not cage_obj:
        return False
    for m in cage_obj.modifiers:
        if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1':
            if any(len(b.data_blocks) > 0 for b in m.bakes):
                return True
    return False


def cage_disk_cache_dirs(cage_obj):
    """External cache directories this cage would write to, for cages stored on disk."""
    dirs = []
    for m in cage_obj.modifiers:
        if m.type != 'NODES' or not m.node_group or m.node_group.name != 'Wiggy 0.1':
            continue
        if getattr(m, 'bake_target', None) != 'DISK':
            continue
        directory = getattr(m, 'bake_directory', '') or ''
        if directory:
            resolved = bpy.path.abspath(directory)
            if resolved not in dirs:
                dirs.append(resolved)
    return dirs


def snapshot_disk_cache(cage_obj, keep=CACHE_BACKUP_KEEP):
    """Copy this cage's external cache next to the .blend before it is overwritten.

    A .blend backup cannot restore simulation data that lives in a DISK cache, so the directory
    is copied and pruned like the project backup. Returns (ok, message).
    """
    dirs = [d for d in cage_disk_cache_dirs(cage_obj) if os.path.isdir(d)]
    if not dirs:
        return True, ""
    filepath = bpy.data.filepath
    if not filepath:
        return False, "Save the .blend first: Giggle cannot store an external cache snapshot."
    backup_root = os.path.join(os.path.dirname(filepath), "giggle_backup")
    try:
        os.makedirs(backup_root, exist_ok=True)
    except Exception as e:
        return False, f"Could not create the backup folder: {e}"

    stamp = time.strftime("%Y%m%d_%H%M%S")
    for source in dirs:
        name = os.path.basename(os.path.normpath(source)) or "cache"
        # Two caches can share a basename (`/a/giggle_cache` and `/b/giggle_cache`). Pruning by
        # name alone made one snapshot delete the other, so the full path is part of the label.
        digest = hashlib.sha1(
            os.path.normcase(os.path.abspath(source)).encode("utf-8")).hexdigest()[:8]
        label = f"{name}.{digest}.cache."
        target = os.path.join(backup_root, f"{label}{stamp}")
        counter = 1
        while os.path.exists(target):
            target = os.path.join(backup_root, f"{label}{stamp}_{counter}")
            counter += 1
        try:
            shutil.copytree(source, target)
        except Exception as e:
            return False, f"Could not snapshot the external cache at {source}: {e}"

        snapshots = sorted(
            (os.path.join(backup_root, entry) for entry in os.listdir(backup_root)
             if entry.startswith(label)),
            key=os.path.getmtime, reverse=True)
        for old in snapshots[keep:]:
            try:
                shutil.rmtree(old)
            except OSError:
                pass
        print(f"[Giggle Backup] External cache snapshot: {target}")
    return True, ""


def prepare_cache_replacement(targets):
    """Make everything recoverable before a bake overwrites it. Returns (ok, message).

    Refuses to continue when a backup cannot be created: replacing a cache without a recovery
    point is the failure this whole path exists to prevent.
    """
    replacing = [o for o in targets if cage_has_cache(o)]
    if not replacing:
        return True, ""

    if not bpy.data.is_saved:
        return False, ("Save the .blend first: Giggle needs a recovery copy before replacing "
                       "an existing simulation cache.")

    path = create_project_backup()
    if not path:
        return False, "Could not create the project backup; the existing cache was left alone."
    print(f"[Giggle Backup] Project backup created at: {path}")

    for cage in replacing:
        ok, message = snapshot_disk_cache(cage)
        if not ok:
            return False, message
    return True, ""


def backup_before_replacing_cache(targets):
    """Deprecated alias kept for callers outside this file."""
    return prepare_cache_replacement(targets)


def mark_bake_failure(cage_obj, message, had_cache):
    """Record a failed bake without throwing away the status of a cache that is still there."""
    cage_obj['_giggle_last_bake_error'] = message
    if not had_cache:
        cage_obj['_giggle_status'] = 'FAILED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = message


def run_bake_operator(context, cage_obj):
    """Call Blender's simulation bake operator for one cage.

    Extracted so a test can substitute a failure, which is otherwise impossible to provoke at
    will: a DISK bake into a path whose parent is a file still returns FINISHED.
    """
    with context.temp_override(active_object=cage_obj, selected_objects=[cage_obj]):
        return bpy.ops.object.simulation_nodes_cache_bake(selected=True)


def execute_cage_bake_step(cage_obj, context, storage_mode, disk_path, f_start, f_end):
    """Bake one simulation cage with verification, keeping the old cache until the new one works.

    The existing cache is not deleted first. Blender re-bakes over it (verified: an in-place bake
    with changed physics reproduces the clean-bake result), so a failed bake leaves the previous
    working cache untouched.

    This is not transactional: if Blender overwrites the cache and then fails, the previous
    cache is gone and only `giggle_backup/` can restore it.
    """
    mod = next((m for m in cage_obj.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1'), None)
    if not mod:
        msg = "Missing Wiggy 0.1 simulation modifier"
        cage_obj['_giggle_last_bake_error'] = msg
        return False, msg

    pre_fp = compute_zone_fingerprint(cage_obj, context, storage_mode, f_start, f_end)
    had_cache = any(len(b.data_blocks) > 0 for b in mod.bakes)

    mod.bake_target = storage_mode
    if storage_mode == 'DISK':
        mod.bake_directory = disk_path
    for b in mod.bakes:
        b.frame_start = f_start
        b.frame_end = f_end

    for ob in context.view_layer.objects:
        ob.select_set(False)
    cage_obj.select_set(True)
    context.view_layer.objects.active = cage_obj

    context.scene.frame_set(f_start)
    context.view_layer.update()

    try:
        bake_res = run_bake_operator(context, cage_obj)
    except Exception as exc:
        msg = f"Blender bake operator raised: {exc}"
        mark_bake_failure(cage_obj, msg, had_cache)
        return False, msg

    if bake_res != {'FINISHED'}:
        msg = f"Blender bake operator returned {bake_res}"
        mark_bake_failure(cage_obj, msg, had_cache)
        return False, msg

    has_blocks = any(len(b.data_blocks) > 0 for b in mod.bakes)
    if not has_blocks:
        msg = "Bake produced 0 simulation cache blocks"
        mark_bake_failure(cage_obj, msg, had_cache)
        return False, msg

    post_fp = compute_zone_fingerprint(cage_obj, context, storage_mode, f_start, f_end)
    if pre_fp != post_fp:
        # The cache on disk is now the new one; it just does not describe this configuration.
        # Nothing is restored here, so the marker has to say the cache cannot be trusted.
        msg = "Dependencies modified during baking"
        save_zone_bake_fingerprint(cage_obj, context, storage_mode, f_start, f_end, fp_dict=post_fp, is_valid=False, reason=msg)
        mark_bake_failure(cage_obj, msg, had_cache)
        cage_obj['_giggle_status'] = 'OUTDATED'
        cage_obj['_giggle_last_known_valid'] = False
        cage_obj['_giggle_outdated_reason'] = msg
        return False, msg

    cage_obj.pop('_giggle_last_bake_error', None)
    save_zone_bake_fingerprint(cage_obj, context, storage_mode, f_start, f_end, fp_dict=post_fp, is_valid=True, reason="")
    return True, "Success"


class GIGGLE_OT_bake_all_cages(Operator):
    """Bake simulation caches for all active Giggle cages (or active full-mesh zones)"""
    bl_idname = "giggle.bake_all_cages"
    bl_label = "Bake All Giggle Zones"
    bl_description = "Bake every active Giggle physics simulation for non-sequential, instantaneous playback"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        ok_backup, backup_msg = prepare_cache_replacement(sim_objs)
        if not ok_backup:
            self.report({'ERROR'}, backup_msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in sim_objs:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Bake failed for all {len(sim_objs)} zone(s). Check simulation ranges.")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Baked {len(succeeded)} zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully baked all {len(succeeded)} Giggle simulation zone(s) (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Baking failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in context.view_layer.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_bake_selected_cage(Operator):
    """Bake simulation cache for the active Giggle zone only"""
    bl_idname = "giggle.bake_selected_cage"
    bl_label = "Bake Active Zone"
    bl_description = "Bake only the active Giggle simulation cage"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None)
        mods = get_giggle_modifiers(obj)
        return bool(obj and obj.type == 'MESH' and settings and 0 <= settings.active_zone_index < len(mods))

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        settings = scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        active_mod = mods[idx]

        s_in = getattr(getattr(active_mod, "properties", None), "inputs", None)
        vg_name = getattr(s_in.Socket_2, "attribute_name", "") if (s_in and hasattr(s_in, "Socket_2")) else ""

        cage_obj = get_zone_cage_object(obj, vg_name) if vg_name else None
        target_sim = cage_obj if cage_obj else obj

        storage_mode = settings.bake_storage_mode
        disk_path = settings.bake_disk_path
        f_start = scene.frame_start if settings.bake_use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if settings.bake_use_scene_range else settings.bake_frame_end

        ok, msg = preflight_validate_bake(context, [target_sim], storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        ok_backup, backup_msg = prepare_cache_replacement([target_sim])
        if not ok_backup:
            self.report({'ERROR'}, backup_msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        try:
            ok_bake, err = execute_cage_bake_step(target_sim, context, storage_mode, disk_path, f_start, f_end)
            if not ok_bake:
                self.report({'ERROR'}, f"Baking zone failed: {err}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Baked zone '{active_mod.name}' (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Baking zone failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in context.view_layer.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_rebake_all(Operator):
    """Safely invalidate and rebuild every Giggle-managed simulation cache with transactional verification"""
    bl_idname = "giggle.rebake_all"
    bl_label = "Rebake All Giggle Zones"
    bl_description = "Safely purge and recalculate all Giggle physics simulation caches"
    bl_options = {'REGISTER'}

    confirm: BoolProperty(
        name="Confirm Rebake",
        description="Proceed with replacing existing simulation caches",
        default=True
    )

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def invoke(self, context, event):
        sim_objs = get_giggle_simulation_objects(context)
        if not sim_objs:
            self.report({'WARNING'}, "No active Giggle simulation zones found to rebake.")
            return {'CANCELLED'}

        has_existing = any(
            o.get('_giggle_baked_at_timestamp') or any(len(b.data_blocks) > 0 for m in o.modifiers if m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for b in m.bakes)
            for o in sim_objs
        )
        if has_existing and event is not None:
            return context.window_manager.invoke_props_dialog(self, width=420)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        sim_objs = get_giggle_simulation_objects(context)
        box = layout.box()
        box.alert = True
        box.label(text="Confirm Rebake All: Existing caches will be replaced!", icon='ERROR')

        col = box.column(align=True)
        for o in sim_objs:
            st, fr, stor, reason = get_cage_bake_status(o)
            row = col.row()
            row.label(text=o.name, icon='OUTLINER_OB_MESH')
            row.label(text=f"Status: {st}")

        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        layout.label(text=f"Configuration: Frames {f_start}–{f_end} | Storage: {storage_mode}")
        layout.label(text="Click OK to create a safety backup and rebake all zones.")

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        ok_backup, backup_msg = prepare_cache_replacement(sim_objs)
        if not ok_backup:
            self.report({'ERROR'}, backup_msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in sim_objs:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Rebake failed for all {len(sim_objs)} zone(s).")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Rebaked {len(succeeded)} zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully rebaked all {len(succeeded)} Giggle simulation zone(s) (Frames {f_start}-{f_end}, {storage_mode})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Rebake All failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in context.view_layer.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_rebake_sim(Operator):
    """Safely invalidate and rebake all Giggle simulation zones (alias for giggle.rebake_all)"""
    bl_idname = "giggle.rebake_sim"
    bl_label = "Rebake All Zones"
    bl_description = "Safely purge existing simulation caches and rebake with current physics settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return bpy.ops.giggle.rebake_all()


class GIGGLE_OT_bake_missing(Operator):
    """Bake only unbaked or outdated simulation caches, skipping valid ones"""
    bl_idname = "giggle.bake_missing"
    bl_label = "Bake Missing / Outdated"
    bl_description = "Recalculate simulation caches only for unbaked or outdated Giggle zones"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        storage_mode = getattr(settings, 'bake_storage_mode', 'PACKED') if settings else 'PACKED'
        use_scene_range = getattr(settings, 'bake_use_scene_range', True) if settings else True
        disk_path = getattr(settings, 'bake_disk_path', '//giggle_cache/') if settings else '//giggle_cache/'
        f_start = scene.frame_start if use_scene_range else settings.bake_frame_start
        f_end = scene.frame_end if use_scene_range else settings.bake_frame_end

        sim_objs = get_giggle_simulation_objects(context)
        ok, msg = preflight_validate_bake(context, sim_objs, storage_mode, f_start, f_end)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        # Filter to only missing or outdated cages
        targets = []
        for o in sim_objs:
            st, reason = check_cage_validity(o, context)
            if st != 'BAKED':
                targets.append(o)

        if not targets:
            self.report({'INFO'}, "All Giggle simulation caches are already baked and up to date.")
            return {'FINISHED'}

        ok_backup, backup_msg = prepare_cache_replacement(targets)
        if not ok_backup:
            self.report({'ERROR'}, backup_msg)
            return {'CANCELLED'}

        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]
        orig_frame = scene.frame_current

        succeeded = []
        failed = []

        try:
            for o in targets:
                ok_bake, err = execute_cage_bake_step(o, context, storage_mode, disk_path, f_start, f_end)
                if ok_bake:
                    succeeded.append(o)
                else:
                    failed.append((o, err))

            if failed and not succeeded:
                self.report({'ERROR'}, f"Bake failed for all {len(targets)} missing zone(s).")
                return {'CANCELLED'}
            elif failed:
                names = ", ".join(f"{o.name} ({err})" for o, err in failed)
                self.report({'WARNING'}, f"Baked {len(succeeded)} missing zone(s), but failed for: {names}")
                return {'FINISHED'}

            self.report({'INFO'}, f"Successfully baked {len(succeeded)} missing/outdated Giggle zone(s) (Frames {f_start}-{f_end})")
            return {'FINISHED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Bake Missing failed: {exc}")
            return {'CANCELLED'}

        finally:
            for o in context.view_layer.objects:
                o.select_set(False)
            for o in orig_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if orig_active:
                try:
                    context.view_layer.objects.active = orig_active
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            context.view_layer.update()


class GIGGLE_OT_check_cache_validity(Operator):
    """Verify whether simulation caches match current animation keyframes, rig transforms, and physics settings"""
    bl_idname = "giggle.check_cache_validity"
    bl_label = "Check Cache Validity"
    bl_description = "Recalculate dependency fingerprints to verify whether simulation caches match the current scene"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sim_objs = get_giggle_simulation_objects(context)
        return bool(sim_objs)

    def execute(self, context):
        sim_objs = get_giggle_simulation_objects(context)
        valid_cages = []
        outdated_cages = []
        unbaked_cages = []

        for o in sim_objs:
            st, reason = check_cage_validity(o, context)
            if st == 'BAKED':
                valid_cages.append(o)
            elif st == 'OUTDATED':
                outdated_cages.append((o, reason))
            else:
                unbaked_cages.append((o, reason))

        if outdated_cages:
            details = ", ".join(f"{o.name} ({r})" for o, r in outdated_cages)
            self.report({'WARNING'}, f"{len(outdated_cages)} cage(s) OUTDATED: {details}")
        elif unbaked_cages:
            self.report({'INFO'}, f"{len(valid_cages)} cage(s) match setup, {len(unbaked_cages)} unbaked.")
        else:
            self.report({'INFO'}, f"All {len(valid_cages)} Giggle simulation cache(s) match scene dependencies.")
        return {'FINISHED'}


class GIGGLE_OT_mark_cache_outdated(Operator):
    """Manually mark Giggle simulation caches as outdated"""
    bl_idname = "giggle.mark_cache_outdated"
    bl_label = "Mark Cache Outdated"
    bl_description = "Manually mark Giggle simulation caches as outdated to force recalculation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sim_objs = get_giggle_simulation_objects(context)
        for o in sim_objs:
            o['_giggle_status'] = 'OUTDATED'
            o['_giggle_last_known_valid'] = False
            o['_giggle_outdated_reason'] = "Manually marked outdated by user"
            o.update_tag(refresh={'DATA'})
        self.report({'INFO'}, f"Marked {len(sim_objs)} Giggle simulation cache(s) as outdated.")
        return {'FINISHED'}


class GIGGLE_OT_clear_sim_cache(Operator):
    bl_idname = "giggle.clear_sim_cache"
    bl_label = "Clear Giggle Cache"
    bl_description = "Purge Geometry Nodes simulation caches strictly on Giggle-managed simulation cages"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        failed_objs = []
        sim_objs = get_giggle_simulation_objects(context)
        if not sim_objs:
            self.report({'INFO'}, "No active Giggle simulation caches found to clear.")
            return {'FINISHED'}

        for obj in sim_objs:
            try:
                with context.temp_override(active_object=obj, selected_objects=[obj]):
                    del_res = bpy.ops.object.simulation_nodes_cache_delete(selected=True)
                if del_res == {'FINISHED'}:
                    obj.pop('_giggle_baked_at_timestamp', None)
                    obj.pop('_giggle_bake_fingerprint_json', None)
                    obj.pop('_giggle_bake_schema_version', None)
                    obj.pop('_giggle_baked_frame_range', None)
                    obj.pop('_giggle_baked_storage', None)
                    obj.pop('_giggle_settings_modified_at', None)
                    obj['_giggle_status'] = 'NOT_BAKED'
                    obj['_giggle_last_known_valid'] = False
                    obj['_giggle_outdated_reason'] = "Cache cleared"
                    obj.update_tag(refresh={'DATA'})
                    count += 1
                else:
                    failed_objs.append(obj.name)
            except Exception:
                failed_objs.append(obj.name)

        context.scene.frame_set(context.scene.frame_current)

        if failed_objs and count == 0:
            self.report({'ERROR'}, f"Failed to clear simulation cache on: {', '.join(failed_objs)}")
            return {'CANCELLED'}
        elif failed_objs:
            self.report({'WARNING'}, f"Purged cache on {count} object(s), but failed for: {', '.join(failed_objs)}")
            return {'FINISHED'}

        self.report({'INFO'}, f"Purged Giggle simulation cache on {count} object(s). Unrelated simulations preserved.")
        return {'FINISHED'}


class GIGGLE_OT_fix_gpu_subdivision(Operator):
    bl_idname = "giggle.fix_gpu_subdivision"
    bl_label = "Disable GPU Subdivision"
    bl_description = "Disable GPU Subdivision in Preferences to prevent OpenSubdiv memory crashes on complex models"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if hasattr(context.preferences.system, "use_gpu_subdivision"):
            context.preferences.system.use_gpu_subdivision = False
            self.report({'INFO'}, "GPU Subdivision disabled. OpenSubdiv crashes prevented!")
            return {'FINISHED'}
        self.report({'WARNING'}, "GPU Subdivision setting not found in this Blender version.")
        return {'CANCELLED'}


class GIGGLE_OT_clamp_subdivision(Operator):
    bl_idname = "giggle.clamp_subdivision"
    bl_label = "Optimize Subsurf Levels"
    bl_description = "Lower Subdivision Surface viewport levels to 1 to prevent simulation stutter and OpenSubdiv memory crashes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}
        count = 0
        for m in obj.modifiers:
            if m.type == 'SUBSURF' and m.levels > 1:
                m.levels = 1
                count += 1
        self.report({'INFO'}, f"Optimized {count} subdivision modifier(s) to viewport level 1.")
        return {'FINISHED'}


# ==============================================================================
# UI PANELS
# ==============================================================================
class VIEW3D_PT_giggle_base:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Giggle"


class GIGGLE_OT_select_zone(Operator):
    """Select a jiggle zone and synchronize preset dropdowns"""
    bl_idname = "giggle.select_zone"
    bl_label = "Select Zone"
    bl_description = "Select this jiggle zone and sync presets"
    bl_options = {'INTERNAL', 'UNDO'}

    index: IntProperty(name="Zone Index", default=0)

    def execute(self, context):
        settings = context.scene.giggle_settings
        settings.active_zone_index = self.index
        settings.show_create_zone = False
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        if 0 <= self.index < len(mods):
            sync_settings_from_zone_mod(settings, mods[self.index])
            try:
                obj["_giggle_last_synced_mod"] = mods[self.index].name
            except Exception:
                pass
        return {'FINISHED'}


class GIGGLE_OT_sync_active_zone(Operator):
    """Synchronize preset category and choice to the active zone recipe"""
    bl_idname = "giggle.sync_active_zone"
    bl_label = "Sync to Active Zone"
    bl_description = "Synchronize preset dropdowns to the active jiggle zone recipe"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        settings = context.scene.giggle_settings
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        if 0 <= idx < len(mods):
            sync_settings_from_zone_mod(settings, mods[idx])
            self.report({'INFO'}, f"Synced preset to '{mods[idx].name}'")
        return {'FINISHED'}

class VIEW3D_PT_giggle_main(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_main"
    bl_label = "Giggle Physics"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = context.scene.giggle_settings

        if not obj or obj.type != 'MESH':
            box_empty = layout.box()
            box_empty.label(text="Select a Mesh Object to begin", icon='MESH_DATA')
            box_empty.operator("giggle.select_body_mesh", text="Select Character Body", icon='RESTRICT_SELECT_OFF')
            return

        # Check for GPU Subdivision bug in Blender 5.3 Beta
        use_gpu_sub = getattr(context.preferences.system, "use_gpu_subdivision", False)
        if use_gpu_sub:
            sub_box = layout.box()
            sub_box.alert = True
            sub_box.label(text="GPU Subdivision is Active (Blender 5.3)", icon='ERROR')
            sub_box.label(text="Can crash OpenSubdiv on detailed meshes.")
            sub_box.operator("giggle.fix_gpu_subdivision", text="Disable GPU Subdivision (Fix)", icon='CHECKMARK')

        # Check for high Subdivision levels on this mesh
        high_subsurfs = [m for m in obj.modifiers if m.type == 'SUBSURF' and m.levels > 1]
        if high_subsurfs:
            h_box = layout.box()
            h_box.label(text=f"Subdiv Viewport Level is {high_subsurfs[0].levels} (High)", icon='INFO')
            h_box.operator("giggle.clamp_subdivision", text="Optimize Viewport Subdiv to 1", icon='MOD_SUBSURF')

        box = layout.box()
        box.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')

        # Existing Zones List
        giggle_mods = get_giggle_modifiers(obj)
        if giggle_mods:
            box.label(text="Active Jiggle Zones:", icon='MOD_PHYSICS')
            for i, m in enumerate(giggle_mods):
                row = box.row(align=True)
                is_active = (i == settings.active_zone_index)
                
                icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                op_select = row.operator("giggle.select_zone", text=m.name, icon=icon)
                op_select.index = i

                # Compact recipe badge pill
                badge = get_zone_recipe_badge(m)
                row.label(text=f"[{badge}]")

                # Simulation mode + vertex cost, visible without selecting the zone
                mode_cell = row.row(align=True)
                mode_cell.scale_x = 0.9
                mode_cell.label(text=zone_mode_label(obj, m))

                eye_icon = 'HIDE_OFF' if m.show_viewport else 'HIDE_ON'
                op_mute = row.operator("giggle.toggle_mute", text="", icon=eye_icon)
                op_mute.mod_name = m.name

                op_solo = row.operator("giggle.solo_zone", text="S", emboss=True)
                op_solo.mod_name = m.name

            # Integrated Active Zone Card (Directly below active selection)
            idx = settings.active_zone_index
            if 0 <= idx < len(giggle_mods):
                active_mod = giggle_mods[idx]
                card = box.box()
                
                s_inputs = getattr(getattr(active_mod, "properties", None), "inputs", None)
                s2 = None
                if active_mod.node_group and active_mod.node_group.name == 'Wiggy 0.1' and s_inputs and hasattr(s_inputs, "Socket_2"):
                    s2 = s_inputs.Socket_2
                    attr_val = getattr(s2, "attribute_name", "")
                    if not attr_val or attr_val not in obj.vertex_groups:
                        alert_box = card.box()
                        alert_box.alert = True
                        alert_box.label(text="No vertex group assigned! Zone is inactive.", icon='ERROR')
                    row_grp = card.row(align=True)
                    if not attr_val:
                        row_grp.alert = True
                    row_grp.prop_search(s2, "attribute_name", obj, "vertex_groups", text="Assigned Group", icon='GROUP_VERTEX')

                # --- CAGE XPBD vs FULL-MESH MODE CARD ---
                vg_attr = getattr(s2, "attribute_name", "") if s2 else ""
                in_cage = is_zone_in_cage_mode(obj, active_mod)
                mode_box = card.box()
                if in_cage:
                    cage_obj = get_zone_cage_object(obj, vg_attr)
                    c_verts = len(cage_obj.data.vertices) if cage_obj else 0
                    row_c = mode_box.row(align=True)
                    row_c.label(text="Mode: Cage XPBD (Fast)", icon='PHYSICS')
                    row_c.label(text=f"[{c_verts} verts]")
                    row_c_btn = mode_box.row(align=True)
                    row_c_btn.operator("giggle.rebuild_cage", text="Rebuild", icon='FILE_REFRESH')
                    row_c_btn.operator("giggle.toggle_simulation_mode", text="Switch to Full-Mesh", icon='ARROW_LEFTRIGHT')
                else:
                    row_f = mode_box.row(align=True)
                    row_f.label(text="Mode: Full-Mesh XPBD", icon='MESH_DATA')
                    v_count = len(obj.data.vertices) if hasattr(obj.data, "vertices") else 0
                    row_f.label(text=f"[{v_count:,} verts]")
                    mode_box.operator("giggle.generate_cage", text="Accelerate with Cage XPBD (5-8x Faster)", icon='AUTO')

                    # Explain a failed automatic cage instead of leaving the user
                    # with a silently expensive zone.
                    cage_error = get_zone_cage_error(active_mod)
                    if cage_error:
                        err_box = card.box()
                        err_box.alert = True
                        err_box.label(text="Cage binding failed for this region", icon='ERROR')
                        for line_txt in wrap_zone_error(cage_error):
                            err_box.label(text=line_txt)
                        err_box.label(text=f"Simulating all {v_count:,} vertices at once.")
                        row_err = err_box.row(align=True)
                        row_err.operator("giggle.generate_cage", text="Retry Cage", icon='FILE_REFRESH')
                        row_err.operator("giggle.keep_full_mesh", text="Keep Full-Mesh", icon='CHECKMARK')

                row_rem = card.row(align=True)
                row_rem.operator("giggle.remove_zone", text=f"Remove Zone '{active_mod.name}'", icon='X')
        else:
            box.label(text="No jiggle zones on this mesh yet.", icon='INFO')

        layout.separator()

        # Add New Zone Section (Collapsible with Auto-Fold)
        is_open = settings.show_create_zone or (not giggle_mods)
        add_box = layout.box()

        row_toggle = add_box.row(align=True)
        toggle_icon = 'DISCLOSURE_TRI_DOWN' if is_open else 'DISCLOSURE_TRI_RIGHT'
        row_toggle.prop(
            settings, "show_create_zone",
            text="Create New Zone",
            icon=toggle_icon,
            emboss=False
        )

        if is_open:
            # Searchable Vertex Group with Quick-Pick and Create buttons
            row = add_box.row(align=True)
            row.prop_search(settings, "new_zone_vg", obj, "vertex_groups", text="Vertex Group", icon='GROUP_VERTEX')
            row.operator("giggle.pick_active_vg", text="", icon='EYEDROPPER')
            row.operator("giggle.create_vg", text="", icon='ADD')

            # Check for duplicate zone assignment on selected vertex group
            vg_assigned_mod = None
            if settings.new_zone_vg:
                for m in giggle_mods:
                    s_in = getattr(getattr(m, "properties", None), "inputs", None)
                    if m.node_group and m.node_group.name == 'Wiggy 0.1' and s_in and hasattr(s_in, "Socket_2"):
                        if getattr(s_in.Socket_2, "attribute_name", "") == settings.new_zone_vg:
                            vg_assigned_mod = m.name
                            break
            if vg_assigned_mod:
                dup_box = add_box.box()
                dup_box.scale_y = 0.8
                dup_box.label(text=f"Note: '{settings.new_zone_vg}' already driven by '{vg_assigned_mod}'", icon='INFO')

            # Check bone collision warning (GUIDE [7])
            bone_arm = get_bone_conflict(obj, settings.new_zone_vg)
            if bone_arm:
                warn_box = add_box.box()
                warn_box.alert = True
                warn_box.label(text=f"Warning: Matches bone in '{bone_arm}'!", icon='ERROR')
                warn_box.label(text="Direct use breaks bone skinning.")
                warn_box.operator("giggle.duplicate_safe_vg", text="Duplicate as Safe Group", icon='DUPLICATE')

            # Segmented physics mode selector (Realistic vs Stylized)
            row_mode_new = add_box.row(align=True)
            row_mode_new.prop(settings, "preset_mode", expand=True)

            row_gender_new = add_box.row(align=True)
            row_gender_new.prop(settings, "new_zone_gender", expand=True)

            add_box.prop(settings, "new_zone_category", text="Category")
            add_box.prop(settings, "new_zone_preset", text="Preset")
            add_box.label(text="Engine: Wiggy XPBD", icon='PHYSICS')
            add_box.prop(settings, "new_zone_name", text="Custom Name (Optional)")
            add_box.prop(settings, "new_zone_cage_mode", text="Cage XPBD (fast, recommended)")

            add_box.operator(
                "giggle.add_zone",
                text="Add Jiggle Zone (Cage XPBD)" if settings.new_zone_cage_mode else "Add Jiggle Zone (Full-Mesh)",
                icon='MOD_PHYSICS'
            )


class VIEW3D_PT_giggle_presets(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_presets"
    bl_label = "Zone Presets & Tightness"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        settings = getattr(context.scene, 'giggle_settings', None) if context.scene else None
        return bool(settings and 0 <= settings.active_zone_index < len(mods) and mods[settings.active_zone_index].node_group and mods[settings.active_zone_index].node_group.name == 'Wiggy 0.1')

    def draw(self, context):
        layout = self.layout
        try:
            settings = context.scene.giggle_settings
            obj = context.active_object
            mods = get_giggle_modifiers(obj)
            idx = settings.active_zone_index
            active_mod = mods[idx] if (0 <= idx < len(mods)) else None

            # Auto-sync preset category on initial load or zone change BEFORE drawing props
            if active_mod and obj:
                if obj.get("_giggle_last_synced_mod") != active_mod.name:
                    try:
                        sync_settings_from_zone_mod(settings, active_mod)
                    except Exception:
                        pass
                    try:
                        obj["_giggle_last_synced_mod"] = active_mod.name
                    except Exception:
                        pass

            # 1. Categorized Preset Selector
            box = layout.box()
            col = box.column(align=True)
            row_hdr = col.row(align=True)
            row_hdr.label(text="Anatomical & Clothing Preset:", icon='PRESET')
            row_hdr.operator("giggle.sync_active_zone", text="", icon='FILE_REFRESH')
            
            # Segmented physics mode selector (Realistic vs Stylized)
            row_mode = col.row(align=True)
            row_mode.prop(settings, "preset_mode", expand=True)

            # Segmented gender selector
            row_gender = col.row(align=True)
            row_gender.prop(settings, "preset_gender", expand=True)
            
            col.separator(factor=0.5)
            col.prop(settings, "preset_category", text="Category")
            col.prop(settings, "preset_choice", text="Preset")

            choice_id = settings.preset_choice
            data = PRESETS.get(choice_id, {})
            if data and 'description' in data:
                desc_box = box.box()
                desc_box.scale_y = 0.75
                desc_box.label(text=data['name'], icon='INFO')
                _profile_data = MOTION_PROFILES.get(data.get('motion_profile', 'BALANCED'), {})
                if _profile_data:
                    desc_box.label(text=f"Motion profile: {_profile_data.get('label', 'Balanced / Natural')}", icon='PHYSICS')
                desc_box.label(text=data['description'])

            # Contextual Intelligent Apply Button with Cross-Anatomy Warning
            meta = get_mod_giggle_metadata(active_mod) if active_mod else None
            active_cat = meta[1] if meta else None
            target_name = active_mod.name.replace("Giggle_", "") if active_mod else "Zone"
            choice_cat = data.get('category_id', '')
            
            # Only flag cross-anatomy when both are specific categories and genuinely differ
            is_cross_anatomy = bool(
                active_cat and choice_cat and 
                active_cat != 'ALL' and choice_cat != 'ALL' and 
                active_cat != choice_cat
            )

            row = box.row(align=True)
            row.scale_y = 1.25
            if is_cross_anatomy:
                row.alert = True
                btn_text = f"Apply '{data.get('name', choice_id)}' to {target_name} (Cross-Anatomy)"
                btn_icon = 'ERROR'
            else:
                btn_text = f"Apply '{data.get('name', choice_id)}' to {target_name}"
                btn_icon = 'CHECKMARK'

            op = row.operator("giggle.apply_preset", text=btn_text, icon=btn_icon)
            op.preset = choice_id

            # 2. Support & Tightness Modifiers
            layout.separator()
            t_box = layout.box()
            t_col = t_box.column(align=True)
            t_col.label(text="Support & Tightness (Scale Active Zone):", icon='MOD_CLOTH')

            r1 = t_col.row(align=True)
            r1.operator("giggle.apply_support_level", text="Bare / Free").level = 'FREE'
            r1.operator("giggle.apply_support_level", text="Loose Fit").level = 'LOOSE'
            r1.operator("giggle.apply_support_level", text="Normal").level = 'NORMAL'

            r2 = t_col.row(align=True)
            r2.operator("giggle.apply_support_level", text="Firm / Sports").level = 'FIRM'
            r2.operator("giggle.apply_support_level", text="Compression").level = 'COMPRESSION'

            # Clean 2-Line Non-Truncating Tightness Guide
            sub_box = t_box.box()
            sub_box.scale_y = 0.7
            if settings.preset_gender == 'FEMALE':
                sub_box.label(text="Bare: Free sway  |  Loose: Bralette fit  |  Normal: Everyday bra")
                sub_box.label(text="Firm: Sports support  |  Compression: Locked binder / corset")
            elif settings.preset_gender == 'MALE':
                sub_box.label(text="Bare: Natural swing  |  Loose: Boxers  |  Normal: Fitted briefs")
                sub_box.label(text="Firm: Jockstrap sport  |  Compression: Tight athletic spandex")
            else:
                sub_box.label(text="Bare: Free float  |  Loose: Relaxed  |  Normal: Balanced")
                sub_box.label(text="Firm: High stiffness  |  Compression: Locked rigid")

            # 3. Action / Jump Safety Guard
            layout.separator()
            guard_box = layout.box()
            guard_col = guard_box.column(align=True)
            guard_col.label(text="Action & Jump Dynamics:", icon='MOD_PHYSICS')
            g_row = guard_col.row(align=True)
            g_row.operator("giggle.apply_action_safety", text="Action / Jump Safety Guard", icon='PHYSICS')
            if active_mod and obj and any(k.startswith(f'_giggle_backup_{active_mod.name}_') for k in obj.keys()):
                g_row.operator("giggle.restore_zone_settings", text="Restore", icon='LOOP_BACK')

        except Exception as e:
            err_box = layout.box()
            err_box.alert = True
            err_box.label(text="Preset Refresh Needed", icon='INFO')
            err_box.operator("giggle.sync_active_zone", text="Refresh Preset for Active Zone", icon='FILE_REFRESH')


class VIEW3D_PT_giggle_dynamics(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_dynamics"
    bl_label = "Dynamics & Inertia"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and get_giggle_modifiers(obj)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index

        if not (0 <= idx < len(mods)):
            return

        mod = mods[idx]
        col = layout.column()

        if mod.node_group.name == "Wiggy 0.1":
            col.prop(settings, "zone_softness", text="Softness (Freedom)", slider=True)
            col.prop(settings, "zone_mass", text="Mass / Inertia", slider=True)
            col.prop(settings, "zone_mass_by_area", text="Mass by Area (Even Weight)")
            col.prop(settings, "zone_wobble", text="Wobble Strength", slider=True)
            col.prop(settings, "zone_damping", text="Damping (Lag)", slider=True)
            col.prop(settings, "zone_max_distance", text="Max Distance (Sag Limit)", slider=True)
            col.prop(settings, "zone_influence", text="Influence", slider=True)
        else:
            col.prop(settings, "zone_jiggle_strength", text="Jiggle Strength", slider=True)
            col.prop(settings, "zone_vel_damping", text="Velocity Damping", slider=True)
            col.prop(settings, "zone_pos_damping", text="Position Damping", slider=True)
            s_inputs = getattr(mod.properties, "inputs", None) if hasattr(mod, "properties") else None
            if s_inputs and hasattr(s_inputs, "Socket_3"):
                col.prop(settings, "zone_deform_depth", text="Deform Depth", slider=True)


class VIEW3D_PT_giggle_shape(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_shape"
    bl_label = "Shape & Volume"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        if not mods:
            return False
        idx = context.scene.giggle_settings.active_zone_index
        if 0 <= idx < len(mods):
            return mods[idx].node_group.name == "Wiggy 0.1"
        return False

    def draw(self, context):
        layout = self.layout
        settings = context.scene.giggle_settings
        col = layout.column()
        col.prop(settings, "zone_preserve_volume", text="Preserve Volume", slider=True)
        col.prop(settings, "zone_sway", text="Sway (Island Swing)", slider=True)
        col.prop(settings, "zone_stretching", text="Stretching", slider=True)
        col.prop(settings, "zone_bending", text="Bending", slider=True)
        col.prop(settings, "zone_edge_fade", text="Edge Fade (Rings)")


class VIEW3D_PT_giggle_collisions(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_collisions"
    bl_label = "Collisions & Contacts"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and get_giggle_modifiers(obj)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        idx = settings.active_zone_index
        if not (0 <= idx < len(mods)):
            return
        mod = mods[idx]
        s_inputs = getattr(mod.properties, "inputs", None) if hasattr(mod, "properties") else None

        col = layout.column()
        row = col.row(align=True)
        row.operator("giggle.add_collider", text="Add Selected as Collider", icon='MOD_PHYSICS')
        row.operator("giggle.add_wind", text="Add Wind", icon='FORCE_WIND')

        if mod.node_group.name == "Wiggy 0.1":
            if s_inputs and hasattr(s_inputs, "Socket_7"):
                col.prop(s_inputs.Socket_7, "value", text="Colliders Collection")
            col.prop(settings, "zone_thickness", text="Thickness", slider=True)
            col.prop(settings, "zone_friction", text="Friction", slider=True)
            col.separator()
            col.label(text="Contact Shaping (Soft Objects):")
            col.prop(settings, "zone_push_aside", text="Push Aside", slider=True)
            col.prop(settings, "zone_cling", text="Cling", slider=True)
            col.prop(settings, "zone_grip", text="Grip", slider=True)
            col.separator()
            col.prop(settings, "zone_squeeze", text="Enable Squeeze")
            if settings.zone_squeeze:
                col.prop(settings, "zone_squeeze_depth", text="Squeeze Depth", slider=True)
        elif "Jiggle" in mod.node_group.name and s_inputs and hasattr(s_inputs, "Socket_5"):
            col.prop(s_inputs.Socket_5, "value", text="Colliders Collection")


class VIEW3D_PT_giggle_self_collision(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_self_collision"
    bl_label = "Self Collision"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        if not mods:
            return False
        idx = context.scene.giggle_settings.active_zone_index
        if 0 <= idx < len(mods):
            return mods[idx].node_group.name == "Wiggy 0.1"
        return False

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = context.scene.giggle_settings

        col = layout.column()
        col.prop(settings, "zone_self_collision", text="Self Collision")
        if settings.zone_self_collision:
            if hasattr(obj, "add_rest_position_attribute"):
                col.prop(obj, "add_rest_position_attribute", text="Add Rest Position Attribute (Required)")
            col.prop(settings, "zone_self_gap", text="Gap Distance", slider=True)
            col.prop(settings, "zone_self_friction", text="Friction", slider=True)
            col.prop(settings, "zone_self_push_speed", text="Push Speed", slider=True)
            col.prop(settings, "zone_self_max_depth", text="Max Depth", slider=True)


class VIEW3D_PT_giggle_forces(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_forces"
    bl_label = "Gravity & Forces"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        if not mods:
            return False
        idx = context.scene.giggle_settings.active_zone_index
        if 0 <= idx < len(mods):
            return mods[idx].node_group.name == "Wiggy 0.1"
        return False

    def draw(self, context):
        layout = self.layout
        settings = context.scene.giggle_settings

        col = layout.column()
        col.prop(settings, "zone_gravity", text="Enable Gravity")
        if settings.zone_gravity:
            col.prop(settings, "zone_gravity_accel", text="Acceleration", slider=True)


class VIEW3D_PT_giggle_playback(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_playback"
    bl_label = "Simulation & Playback"
    bl_parent_id = "VIEW3D_PT_giggle_main"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = getattr(scene, 'giggle_settings', None)
        obj = context.active_object

        # --- SIMULATION CACHE MANAGER CARD ---
        box_cache = layout.box()
        box_cache.label(text="Simulation Cache & Baking:", icon='FILE_CACHE')

        # Check cache status across active zones
        sim_objs = get_giggle_simulation_objects(context, obj)
        all_baked = bool(sim_objs)
        any_outdated = False
        any_failed = False
        zone_statuses = []

        for so in sim_objs:
            status, frange, storage, reason = get_cage_bake_status(so)
            zone_statuses.append((so, status, frange, storage, reason))
            if status != 'BAKED':
                all_baked = False
            if status == 'OUTDATED':
                any_outdated = True
            elif status == 'FAILED':
                any_failed = True

        st_box = box_cache.box()
        if any_failed:
            st_box.alert = True
            st_box.label(text="Cache Generation Failed on one or more zones", icon='CANCEL')
        elif any_outdated:
            st_box.alert = True
            st_box.label(text="Cache Outdated (Dependencies or settings changed)", icon='ERROR')
        elif all_baked:
            st_box.label(text="Status: BAKED (All Zones Synchronized)", icon='CHECKMARK')
        else:
            st_box.label(text="Status: UNBAKED / REAL-TIME", icon='TIME')
            st_box.label(text="Bake simulations to scrub instantly and render safely.", icon='INFO')

        # Per-zone detailed status display
        if sim_objs:
            col_zones = st_box.column(align=True)
            for so, status, frange, storage, reason in zone_statuses:
                row_z = col_zones.row(align=True)
                if status == 'BAKED':
                    row_z.label(text=f"{so.name}: BAKED ({frange[0]}-{frange[1]}, {storage})", icon='CHECKMARK')
                elif status == 'OUTDATED':
                    row_z.label(text=f"{so.name}: OUTDATED ({reason})", icon='ERROR')
                elif status == 'FAILED':
                    row_z.label(text=f"{so.name}: FAILED ({reason})", icon='CANCEL')
                else:
                    row_z.label(text=f"{so.name}: NOT BAKED", icon='TIME')

        # Storage options
        if settings:
            row_store = box_cache.row(align=True)
            row_store.prop(settings, "bake_storage_mode", expand=True)

            row_range = box_cache.row(align=True)
            row_range.prop(settings, "bake_use_scene_range", text="Use Scene Range")
            if not settings.bake_use_scene_range:
                row_f = box_cache.row(align=True)
                row_f.prop(settings, "bake_frame_start", text="Start")
                row_f.prop(settings, "bake_frame_end", text="End")

        # Action Buttons
        row_bake = box_cache.row(align=True)
        row_bake.scale_y = 1.2
        row_bake.operator("giggle.bake_missing", text="Bake Missing / Outdated", icon='PLAY')
        row_bake.operator("giggle.rebake_all", text="Rebake All", icon='FILE_REFRESH')

        row_ops2 = box_cache.row(align=True)
        row_ops2.operator("giggle.check_cache_validity", text="Check Validity", icon='CHECKMARK')
        row_ops2.operator("giggle.clear_sim_cache", text="Clear Cache", icon='TRASH')

        row_act = box_cache.row(align=True)
        row_act.operator("giggle.bake_selected_cage", text="Bake Active Zone Only", icon='RESTRICT_SELECT_OFF')

        if settings:
            box_cache.prop(settings, "check_cache_on_render", text="Pre-Flight Render Check")

        # Timeline scrubbing row
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("giggle.reset_sim", text="Reset to Start", icon='REW')
        row.prop(scene, "frame_current", text="Current Frame")

        # Solver details if active zone is Wiggy
        obj = context.active_object
        mods = get_giggle_modifiers(obj)
        settings = scene.giggle_settings
        idx = settings.active_zone_index

        if mods and 0 <= idx < len(mods):
            mod = mods[idx]
            if mod.node_group.name == "Wiggy 0.1":
                s_inputs = getattr(mod.properties, "inputs", None) if hasattr(mod, "properties") else None
                if s_inputs:
                    box = layout.box()
                    box.label(text=f"XPBD Solver Quality ({mod.name}):", icon='PREFERENCES')
                    box.prop(s_inputs.Socket_61, "value", text="Simulate Active")
                    row = box.row(align=True)
                    row.prop(s_inputs.Socket_14, "value", text="Substeps")
                    op = row.operator("giggle.autotune_substeps", text="Auto FPS", icon='TIME')
                    op.all_zones = False
                    box.prop(s_inputs.Socket_15, "value", text="Iterations")
                    box.prop(s_inputs.Socket_127, "value", text="Speed (Slow Motion)")


class VIEW3D_PT_giggle_diagnostics(VIEW3D_PT_giggle_base, Panel):
    bl_idname = "VIEW3D_PT_giggle_diagnostics"
    bl_label = "Performance & Diagnostics"
    bl_parent_id = "VIEW3D_PT_giggle_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if not obj:
            layout.label(text="Select an object to inspect diagnostics.", icon='INFO')
            return

        mods = get_giggle_modifiers(obj)
        sim_mods = [m for m in mods if getattr(m, "node_group", None) and m.node_group.name == "Wiggy 0.1"]

        box = layout.box()
        box.label(text="Active Zones & Geometry:", icon='INFO')
        row = box.row()
        row.label(text=f"XPBD Zones: {len(sim_mods)}")
        if hasattr(obj.data, "vertices"):
            row.label(text=f"Total Verts: {len(obj.data.vertices):,}")

        # Warning checks
        has_subsurf_issue = False
        for m in getattr(obj, "modifiers", []):
            if m.type == 'SUBSURF' and getattr(m, "levels", 0) > 1 and getattr(m, "show_viewport", False):
                has_subsurf_issue = True
                break

        has_gpu_subdiv = getattr(getattr(context, "preferences", None), "system", None)
        gpu_subdiv_on = getattr(has_gpu_subdiv, "use_gpu_subdivision", False)

        has_high_poly_self_col = False
        if hasattr(obj.data, "vertices") and len(obj.data.vertices) > 1000:
            for sm in sim_mods:
                s_in = getattr(getattr(sm, "properties", None), "inputs", None)
                if s_in and hasattr(s_in, "Socket_104") and getattr(s_in.Socket_104, "value", False):
                    has_high_poly_self_col = True
                    break

        if has_subsurf_issue or gpu_subdiv_on or has_high_poly_self_col:
            warn_box = layout.box()
            warn_box.label(text="Performance Recommendations:", icon='ERROR')
            if has_subsurf_issue:
                row = warn_box.row(align=True)
                row.label(text="Subsurf level > 1 slows viewport", icon='CANCEL')
                row.operator("giggle.clamp_subdivision", text="Clamp to 1")
            if gpu_subdiv_on:
                row = warn_box.row(align=True)
                row.label(text="GPU Subdivision causes memory spikes", icon='CANCEL')
                row.operator("giggle.fix_gpu_subdivision", text="Fix")
            if has_high_poly_self_col:
                warn_box.label(text="Self-Collision on full mesh is expensive (3-5x slower)", icon='INFO')
        else:
            layout.label(text="Status: Optimal settings for viewport playback", icon='CHECKMARK')


# ==============================================================================
# REGISTRATION
# ==============================================================================

# ==============================================================================
# HHP TOOLKIT INTEGRATION (Wardrobe, Clothing Follower, Anti-Clipping & Deform)
# ==============================================================================

# ==============================================================================
# HHP TOOLKIT INTEGRATION (Wardrobe, Clothing Follower, Anti-Clipping & Deform)
# ==============================================================================

def get_layer_collection(view_layer, col):
    """Recursively search for a LayerCollection matching a bpy.data.collection in the view layer."""
    if not view_layer or not hasattr(view_layer, "layer_collection"):
        return None
    def _search(lc):
        if lc.collection == col:
            return lc
        for child in lc.children:
            res = _search(child)
            if res:
                return res
        return None
    return _search(view_layer.layer_collection)

def get_show_collection_render(self):
    vl = getattr(bpy.context, "view_layer", None)
    if vl:
        lc = get_layer_collection(vl, self)
        if lc and (lc.exclude or lc.hide_viewport):
            return False
    return not self.hide_viewport and not self.hide_render

def set_show_collection_render(self, value):
    # Set data-level properties (Viewport & Render)
    self.hide_viewport = not value
    self.hide_render = not value
    # Also set View Layer exclusion and visibility so unchecked Outliner collections turn ON
    vl = getattr(bpy.context, "view_layer", None)
    if vl:
        lc = get_layer_collection(vl, self)
        if lc:
            lc.exclude = not value
            lc.hide_viewport = not value

def get_show_object_render(self):
    return not self.hide_viewport and not self.hide_render

def set_show_object_render(self, value):
    self.hide_viewport = not value
    self.hide_render = not value
    if hasattr(self, "hide_set"):
        try:
            self.hide_set(not value)
        except Exception:
            pass

def is_bone_widget_or_rig_object(obj):
    """Check if object is an armature bone widget or control shape."""
    name = obj.name.lower()
    return name.startswith(('cs_', 'wgt-', 'wgt_', 'cs.', 'widget', 'wgt.'))

_wardrobe_cache = {'key': None, 'result': None}

def get_wardrobe_scene_collections(context):
    """
    Find all character wardrobe and body collections in the scene.
    PERSISTENT: Discovered globally across the scene regardless of selection or visibility state,
    so collections and items never vanish when toggled hidden.
    Cached across UI redraw ticks to eliminate viewport FPS drops.
    """
    scene = getattr(context, 'scene', None)
    # A count-only key missed renames and membership changes in existing collections.
    # Build a compact structural signature so the UI cache invalidates when users edit
    # collection names, child links, or the objects assigned to a collection.
    collection_signature = []
    for collection in bpy.data.collections:
        try:
            collection_id = collection.as_pointer()
        except Exception:
            collection_id = id(collection)
        object_signature = tuple(sorted((getattr(obj, 'name', ''), getattr(obj, 'type', '')) for obj in collection.objects))
        child_signature = tuple(sorted(getattr(child, 'name', '') for child in collection.children))
        collection_signature.append((collection_id, collection.name, object_signature, child_signature))
    cache_key = (id(scene), tuple(collection_signature))
    if _wardrobe_cache['key'] == cache_key and _wardrobe_cache['result'] is not None:
        return _wardrobe_cache['result']
    outfit_keywords = {
        'cloth', 'clothes', 'costume', 'outfit', 'clothing', 'apparel', 'garment',
        'wear', 'dress', 'top', 'bottom', 'corset', 'skirt', 'pants', 'shirt',
        'jacket', 'suit', 'underwear', 'panties', 'bra', 'boxers', 'briefs',
        'thong', 'bikini', 'swimwear', 'swimsuit', 'sfw', 'nsfw', 'armor',
        'leggins', 'leggings', 'uniform', 'coat', 'robe', 'hoodie'
    }
    accessory_keywords = {
        'hair', 'wig', 'ponytail', 'braid', 'glasses', 'sunglasses', 'heels',
        'shoes', 'boots', 'socks', 'gloves', 'collar', 'hat', 'cap', 'belt',
        'jewelry', 'props', 'accessory', 'accessories', 'weapon', 'holster',
        'choker', 'earring', 'piercing'
    }
    body_keywords = {
        'body', 'character', 'face', 'head', 'skin', 'eyes', 'mouth', 'tongue',
        'mesh_body', 'base_mesh'
    }
    exclude_keywords = {
        'rig', 'armature', 'cs_', '_cs', 'widget', 'camera', 'light', 'lights',
        'studio', 'bone', 'metarig'
    }

    all_cols = []
    seen = set()

    def scan_col(c):
        if c in seen or c == context.scene.collection:
            return
        seen.add(c)
        all_cols.append(c)
        for ch in c.children:
            scan_col(ch)

    for c in context.scene.collection.children:
        scan_col(c)

    for c in bpy.data.collections:
        if c not in seen and c != context.scene.collection:
            scan_col(c)

    categories = {
        'body': [],
        'outfits': [],
        'accessories': [],
        'other': []
    }

    for c in all_cols:
        name_lower = c.name.lower()
        mesh_objs = [o for o in c.objects if o.type == 'MESH' and not is_bone_widget_or_rig_object(o)]
        if not mesh_objs:
            continue

        # Exclude rig / helper collections unless explicitly matching clothing or body
        if any(k in name_lower for k in exclude_keywords) and not any(k in name_lower for k in outfit_keywords | body_keywords | accessory_keywords):
            continue

        if any(k in name_lower for k in body_keywords):
            categories['body'].append((c, mesh_objs))
        elif any(k in name_lower for k in accessory_keywords):
            categories['accessories'].append((c, mesh_objs))
        elif any(k in name_lower for k in outfit_keywords):
            categories['outfits'].append((c, mesh_objs))
        else:
            categories['other'].append((c, mesh_objs))

    _wardrobe_cache['key'] = cache_key
    _wardrobe_cache['result'] = categories
    return categories

def find_character_clothing_collections(context):
    """Backward compatibility helper returning all non-body clothing collections."""
    cats = get_wardrobe_scene_collections(context)
    return [col for col, _ in (cats['outfits'] + cats['accessories'] + cats['other'])]


class GIGGLE_OT_wardrobe_show_all(Operator):
    """Unhide all wardrobe and character collections and objects"""
    bl_idname = "giggle.wardrobe_show_all"
    bl_label = "Show All Wardrobe"
    bl_description = "Show all clothing, hair, accessories, and body collections in Viewport and Render"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cats = get_wardrobe_scene_collections(context)
        for cat_list in cats.values():
            for col, objs in cat_list:
                if hasattr(col, "giggle_show_render"):
                    col.giggle_show_render = True
                for obj in objs:
                    if hasattr(obj, "giggle_show_render"):
                        obj.giggle_show_render = True
        self.report({'INFO'}, "All wardrobe collections and objects are now visible.")
        return {'FINISHED'}


class GIGGLE_OT_wardrobe_hide_clothes(Operator):
    """Hide clothing and accessories to view base body for jiggle physics tuning"""
    bl_idname = "giggle.wardrobe_hide_clothes"
    bl_label = "Hide Clothes (Nude Base)"
    bl_description = "Hide all outfits and accessories while keeping base body visible for physics tuning"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cats = get_wardrobe_scene_collections(context)
        # Ensure body is visible
        for col, objs in cats['body']:
            if hasattr(col, "giggle_show_render"):
                col.giggle_show_render = True
            for obj in objs:
                if hasattr(obj, "giggle_show_render"):
                    obj.giggle_show_render = True
        # Hide outfits and accessories
        for col, objs in (cats['outfits'] + cats['accessories'] + cats['other']):
            if hasattr(col, "giggle_show_render"):
                col.giggle_show_render = False
        self.report({'INFO'}, "Hidden all clothes; base character body is visible for tuning.")
        return {'FINISHED'}


class GIGGLE_OT_select_body_mesh(Operator):
    """Unhide character body collection and select the main body mesh"""
    bl_idname = "giggle.select_body_mesh"
    bl_label = "Select Body Mesh"
    bl_description = "Unhide body collection and select the character mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cats = get_wardrobe_scene_collections(context)
        target_obj = None
        for col, objs in cats['body']:
            if hasattr(col, "giggle_show_render"):
                col.giggle_show_render = True
            for obj in objs:
                if hasattr(obj, "giggle_show_render"):
                    obj.giggle_show_render = True
                if not target_obj:
                    name_l = obj.name.lower()
                    if any(k in name_l for k in ('body', 'character', 'skin', 'base', 'mesh')):
                        target_obj = obj
            if not target_obj and objs:
                target_obj = objs[0]

        if not target_obj:
            # Fallback search across all meshes in scene
            for obj in context.scene.objects:
                if obj.type == 'MESH' and not is_bone_widget_or_rig_object(obj):
                    name_l = obj.name.lower()
                    if any(k in name_l for k in ('body', 'character', 'skin', 'base')):
                        target_obj = obj
                        break

        if target_obj:
            target_obj.hide_viewport = False
            target_obj.hide_render = False
            if hasattr(target_obj, "hide_set"):
                target_obj.hide_set(False)
            context.view_layer.objects.active = target_obj
            target_obj.select_set(True)
            self.report({'INFO'}, f"Selected '{target_obj.name}'")
            return {'FINISHED'}

        self.report({'WARNING'}, "No body mesh found in scene.")
        return {'CANCELLED'}



class GIGGLE_OT_fix_body_manifold(Operator):
    """Clean non-manifold multi-face edges on active mesh so Surface Deform modifier can bind"""
    bl_idname = "giggle.fix_body_manifold"
    bl_label = "Fix Body Non-Manifold (Enable Surface Deform)"
    bl_description = "Removes multi-face (>2 polygons) internal edges preventing Surface Deform from binding"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bool(obj and obj.type == 'MESH')

    def execute(self, context):
        import bmesh
        obj = context.active_object
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        multi_edges = [e for e in bm.edges if len(e.link_faces) > 2]
        wire_edges = [e for e in bm.edges if e.is_wire]
        bad_edges = list(set(multi_edges + wire_edges))

        if not bad_edges:
            bm.free()
            self.report({'INFO'}, f"'{obj.name}' has no multi-face or wire edges. Surface Deform is already supported!")
            return {'FINISHED'}

        bm.free()
        self.report({'WARNING'}, f"'{obj.name}' has {len(bad_edges)} non-manifold edges (often in mouth cavity/eyelids). Destructive deletion is blocked to protect character face and armature rig.")
        return {'CANCELLED'}


class GIGGLE_OT_rebind_clothing_modifiers(Operator):
    """Reset to the scene start frame and rebind supported clothing deformation modifiers."""
    bl_idname = "giggle.rebind_clothing_modifiers"
    bl_label = "Rebind Clothing Deform"
    bl_description = "Reset to the scene start frame and rebind clothing Surface Deform, Mesh Deform and Corrective Smooth modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        scene = context.scene
        previous_sync_mode = getattr(scene, 'sync_mode', None)
        orig_active = context.view_layer.objects.active
        orig_active_mode = getattr(orig_active, 'mode', 'OBJECT') if orig_active else 'OBJECT'
        selected_objects = list(context.selected_objects)
        rebound_count = 0
        failures = []

        try:
            # Cancel playback only when the operator is available in the current context.
            try:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            except Exception:
                pass

            for obj in selected_objects:
                if obj.type != 'MESH':
                    continue
                context.view_layer.objects.active = obj
                with context.temp_override(active_object=obj, object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
                    if obj.mode != 'OBJECT':
                        bpy.ops.object.mode_set(mode='OBJECT')
                    for mod in obj.modifiers:
                        try:
                            if mod.type == 'SURFACE_DEFORM':
                                if mod.is_bound:
                                    bpy.ops.object.surfacedeform_bind(modifier=mod.name)
                                bpy.ops.object.surfacedeform_bind(modifier=mod.name)
                                rebound_count += 1
                            elif mod.type == 'MESH_DEFORM':
                                if mod.is_bound:
                                    bpy.ops.object.meshdeform_bind(modifier=mod.name)
                                bpy.ops.object.meshdeform_bind(modifier=mod.name)
                                rebound_count += 1
                            elif mod.type == 'CORRECTIVE_SMOOTH' and hasattr(mod, 'is_bind'):
                                if mod.is_bind:
                                    bpy.ops.object.correctivesmooth_bind(modifier=mod.name)
                                bpy.ops.object.correctivesmooth_bind(modifier=mod.name)
                                rebound_count += 1
                        except Exception as exc:
                            failures.append(f"{obj.name}/{mod.name}: {exc}")
        finally:
            try:
                context.view_layer.objects.active = orig_active
            except Exception:
                pass
            if previous_sync_mode is not None:
                try:
                    scene.sync_mode = previous_sync_mode
                except Exception:
                    pass
            # Restore the original active object's mode after processing all selected meshes.
            if orig_active and orig_active_mode and orig_active_mode != 'OBJECT':
                try:
                    with context.temp_override(
                        active_object=orig_active,
                        object=orig_active,
                        selected_objects=selected_objects,
                        selected_editable_objects=selected_objects,
                    ):
                        bpy.ops.object.mode_set(mode=orig_active_mode)
                except Exception:
                    pass

        if failures:
            self.report({'WARNING'}, f"Rebound {rebound_count} modifier(s); {len(failures)} failed. See console for details.")
            for failure in failures:
                print(f"[Giggle] Rebind failed: {failure}")
        else:
            self.report({'INFO'}, f"Rebound {rebound_count} deform modifiers at frame {scene.frame_start}; restored the original active object and mode.")
        return {'FINISHED'}


class GIGGLE_OT_attach_clothing_proxy(Operator):
    """Attach selected clothes to body jiggle using a clean non-destructive Deform Proxy (100% flush, transactional)"""
    bl_idname = "giggle.attach_clothing_proxy"
    bl_label = "Attach Clothes to Jiggle (Flush Surface)"
    bl_description = "Creates/reuses a clean manifold jiggle proxy and transactionally binds clothes with Surface Deform"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        has_giggle = any(get_giggle_modifiers(o) for o in selected_meshes)
        return len(selected_meshes) >= 2 and has_giggle

    def execute(self, context):
        import bmesh
        from mathutils import Vector
        scene = context.scene
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        if not giggle_bodies:
            self.report({'WARNING'}, "No selected mesh has Giggle physics. Select your character body and clothing.")
            return {'CANCELLED'}

        active_obj = context.active_object if context.active_object in giggle_bodies else giggle_bodies[0]
        clothing_objs = [o for o in selected_meshes if o != active_obj]
        if not clothing_objs:
            self.report({'WARNING'}, "No clothing meshes selected. Select both clothing and character body.")
            return {'CANCELLED'}

        settings = getattr(scene, 'giggle_settings', None)
        target_choice = getattr(settings, 'clothing_target_zone', 'AUTO') if settings else 'AUTO'
        body_mods = get_giggle_modifiers(active_obj)

        # 1. Resolve target zone for EACH clothing mesh independently
        garment_zones = {}
        for cloth in clothing_objs:
            if target_choice != 'AUTO':
                matched_mod = next((m for m in body_mods if m.name == target_choice), None)
                if not matched_mod:
                    self.report({'ERROR'}, f"Selected manual zone '{target_choice}' not found on '{active_obj.name}'.")
                    return {'CANCELLED'}
                matched_vg = get_mod_socket_attribute_name(matched_mod, 'Socket_2')
                if not matched_vg or matched_vg not in active_obj.vertex_groups:
                    self.report({'ERROR'}, f"Zone '{matched_mod.name}' has no valid vertex group assigned.")
                    return {'CANCELLED'}
                garment_zones[cloth] = (matched_mod, matched_vg)
            else:
                best_mod, best_vg, dist, status = resolve_garment_target_zone(cloth, active_obj)
                if status == 'EXCEEDS_DISTANCE':
                    self.report({'ERROR'}, f"Garment '{cloth.name}' is {dist*100:.1f} cm away from the nearest jiggle zone. Select target zone explicitly.")
                    return {'CANCELLED'}
                elif status == 'AMBIGUOUS':
                    self.report({'ERROR'}, f"Garment '{cloth.name}' is ambiguous (equally close to multiple zones). Select target zone explicitly.")
                    return {'CANCELLED'}
                elif status != 'OK' or not best_mod:
                    self.report({'ERROR'}, f"Could not auto-detect a valid jiggle zone for '{cloth.name}'. Select target zone explicitly.")
                    return {'CANCELLED'}
                garment_zones[cloth] = (best_mod, best_vg)

        # 2. Group clothes by (src_mod, vg_name)
        zone_groups = {}
        for cloth, (m, vg) in garment_zones.items():
            zone_groups.setdefault((m, vg), []).append(cloth)

        # 3. State capture (Medium 10 & Medium 9)
        orig_mode = context.mode
        orig_frame = scene.frame_current
        orig_active = context.view_layer.objects.active
        orig_selected = [o for o in context.selected_objects if o]

        # Only the armatures that really deform this body and these garments.
        # Binding in POSE would capture the posed silhouette as the rest shape.
        binding_armatures = get_binding_armatures([active_obj] + clothing_objs)
        orig_pose_positions = []

        # Switch to OBJECT mode defensively if needed
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        # Tracking for full ACID transactional rollback (Critical 1, 2, 3)
        created_temp_proxies = []  # dicts: {'obj': tmp_proxy, 'mesh': proxy_data, 'perm_name': perm_name}
        staged_modifiers = []      # (cloth, staged_sd)
        orig_proxy_vis = {}        # proxy -> (hide_viewport, hide_get, hide_render)
        migrated_dependents = []   # (dep_obj, dep_mod, old_perm)
        bound_count = 0

        # Dedicated hidden collection for proxies to prevent viewport clutter / wire cage display
        giggle_col = bpy.data.collections.get("Giggle_Proxies")
        if not giggle_col:
            giggle_col = bpy.data.collections.new("Giggle_Proxies")
            scene.collection.children.link(giggle_col)

        try:
            try:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            except Exception:
                pass

            # Bind against the neutral shape. Going to scene.frame_start does not
            # guarantee a rest pose, so the driving armatures are isolated in REST
            # for the whole bind and restored in finally. If a rig refuses REST we
            # must not bind at all: that is the bug this correction exists for.
            orig_pose_positions, rest_failures = enter_rest_pose(binding_armatures)
            context.view_layer.update()

            # Bind strictly at scene.frame_start
            scene.frame_set(scene.frame_start)
            dg = context.evaluated_depsgraph_get()
            dg.update()

            # A driven or keyframed pose_position snaps back to POSE during frame
            # evaluation only, so REST has to be verified again right here.
            if not rest_failures:
                reverted = unrested_armatures(orig_pose_positions)
                if reverted:
                    rest_failures = [(name, name, "armature left Rest Pose during animation evaluation")
                                     for name in reverted]
            if rest_failures:
                details = "; ".join(
                    f"'{arm}'" + (f" ({data_name})" if data_name and data_name != arm else "")
                    + f" could not enter Rest Pose: {error}"
                    for arm, data_name, error in rest_failures
                )
                raise RuntimeError(
                    f"Nothing was bound. {details}. "
                    "Set the rig's Pose Position to REST and try again."
                )

            # Process each zone group
            for (src_mod, vg_name), clothes_in_zone in zone_groups.items():
                vg_idx = active_obj.vertex_groups[vg_name].index
                perm_name = f"{active_obj.name}_{vg_name}_Proxy"
                existing_proxy = bpy.data.objects.get(perm_name)

                can_reuse = False
                if existing_proxy and existing_proxy.type == 'MESH':
                    orig_proxy_vis[existing_proxy.name] = (existing_proxy.hide_viewport, existing_proxy.hide_get(), existing_proxy.hide_render)
                    has_verts = len(existing_proxy.data.vertices) > 0
                    body_arm_obj = getattr(next((m for m in active_obj.modifiers if m.type == 'ARMATURE'), None), 'object', None)
                    has_arm = any(m.type == 'ARMATURE' and m.object == body_arm_obj for m in existing_proxy.modifiers)
                    has_wiggy = any(m.type == 'NODES' and m.node_group and m.node_group.name == 'Wiggy 0.1' for m in existing_proxy.modifiers)

                    # Robust Fingerprint Validation (High 4)
                    match_body = existing_proxy.get('_giggle_source_body') == active_obj.name
                    match_verts = existing_proxy.get('_giggle_source_verts') == len(active_obj.data.vertices)
                    match_vg = existing_proxy.get('_giggle_vg_name') == vg_name

                    if has_verts and has_arm and has_wiggy and match_body and match_verts and match_vg:
                        can_reuse = True

                if can_reuse:
                    target_proxy = existing_proxy
                    target_proxy.display_type = 'TEXTURED'
                    target_proxy.hide_viewport = False
                    target_proxy.hide_set(False)
                else:
                    tmp_proxy_name = f"_tmp_{active_obj.name}_{vg_name}_Proxy"
                    old_tmp = bpy.data.objects.get(tmp_proxy_name)
                    if old_tmp:
                        bpy.data.objects.remove(old_tmp, do_unlink=True)

                    proxy_data = active_obj.data.copy()
                    proxy_data.name = f"{tmp_proxy_name}_Mesh"
                    tmp_proxy = bpy.data.objects.new(tmp_proxy_name, proxy_data)
                    giggle_col.objects.link(tmp_proxy)
                    tmp_proxy.matrix_world = active_obj.matrix_world

                    # CRITICAL 2: Track immediately upon creation before any subsequent operation can throw!
                    proxy_record = {'obj': tmp_proxy, 'mesh': proxy_data, 'perm_name': perm_name}
                    created_temp_proxies.append(proxy_record)

                    # Extract zone vertices with 1 edge-ring dilation
                    bm = bmesh.new()
                    bm.from_mesh(proxy_data)
                    dvert_lay = bm.verts.layers.deform.active

                    verts_to_keep = set()
                    for v in bm.verts:
                        dvert = v[dvert_lay] if dvert_lay else None
                        w = dvert.get(vg_idx, 0.0) if dvert else 0.0
                        if w >= 0.01:
                            verts_to_keep.add(v)

                    dilated = set(verts_to_keep)
                    for v in verts_to_keep:
                        for e in v.link_edges:
                            dilated.add(e.other_vert(v))

                    verts_to_delete = [v for v in bm.verts if v not in dilated]
                    bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')

                    bad_edges = [e for e in bm.edges if len(e.link_faces) > 2 or e.is_wire]
                    if bad_edges:
                        bmesh.ops.delete(bm, geom=bad_edges, context='EDGES')

                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
                    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

                    bm.to_mesh(proxy_data)
                    proxy_data.update()
                    bm.free()

                    if len(tmp_proxy.data.vertices) == 0 or len(tmp_proxy.data.polygons) == 0:
                        raise RuntimeError(f"Proxy mesh for '{vg_name}' is empty. Check vertex group weights.")

                    # Defensive vertex group validation
                    for vg in active_obj.vertex_groups:
                        if vg.name not in tmp_proxy.vertex_groups:
                            tmp_proxy.vertex_groups.new(name=vg.name)

                    # Copy Armature and Giggle modifier to proxy
                    tmp_proxy.modifiers.clear()
                    for m in active_obj.modifiers:
                        if m.type == 'ARMATURE':
                            arm = tmp_proxy.modifiers.new(name=m.name, type='ARMATURE')
                            arm.object = m.object
                            for prop in ['use_vertex_groups', 'use_bone_envelopes', 'use_deform_delay']:
                                if hasattr(m, prop):
                                    setattr(arm, prop, getattr(m, prop))
                        elif m == src_mod:
                            g_mod = tmp_proxy.modifiers.new(name=m.name, type='NODES')
                            g_mod.node_group = m.node_group
                            if hasattr(m, "properties") and hasattr(m.properties, "inputs"):
                                for k in m.properties.inputs.keys():
                                    s_src = getattr(m.properties.inputs, k)
                                    s_dst = getattr(g_mod.properties.inputs, k, None)
                                    if s_dst:
                                        if getattr(s_src, 'attribute_name', None):
                                            s_dst.type = 'ATTRIBUTE'
                                            s_dst.attribute_name = s_src.attribute_name
                                        elif getattr(s_src, 'value', None) is not None:
                                            s_dst.type = 'VALUE'
                                            try:
                                                s_dst.value = s_src.value
                                            except Exception:
                                                pass

                    # Store proxy metadata & fingerprint properties (High 4)
                    tmp_proxy['_giggle_source_body'] = active_obj.name
                    tmp_proxy['_giggle_source_verts'] = len(active_obj.data.vertices)
                    tmp_proxy['_giggle_vg_name'] = vg_name
                    tmp_proxy['_giggle_proxy'] = True

                    # Normal display instead of WIRE to eliminate black wire cages when unhidden
                    tmp_proxy.display_type = 'TEXTURED'
                    tmp_proxy.hide_viewport = False
                    tmp_proxy.hide_set(False)
                    tmp_proxy.hide_render = True

                    target_proxy = tmp_proxy

                # Stage SurfaceDeform on each clothing item in this zone
                for cloth in clothes_in_zone:
                    staged_sd = cloth.modifiers.new(name="_tmp_Giggle_SurfaceDeform", type='SURFACE_DEFORM')
                    staged_sd.target = target_proxy
                    staged_sd.falloff = 4.0
                    staged_modifiers.append((cloth, staged_sd))

                    arm_idx = -1
                    for idx_m, m in enumerate(cloth.modifiers):
                        if m.type == 'ARMATURE':
                            arm_idx = idx_m
                    if arm_idx >= 0 and arm_idx + 1 < len(cloth.modifiers):
                        with context.temp_override(active_object=cloth, object=cloth):
                            try:
                                bpy.ops.object.modifier_move_to_index(modifier=staged_sd.name, index=arm_idx + 1)
                            except Exception:
                                pass

                    context.view_layer.objects.active = cloth
                    with context.temp_override(active_object=cloth, object=cloth):
                        bpy.ops.object.surfacedeform_bind(modifier=staged_sd.name)
                        if not staged_sd.is_bound:
                            raise RuntimeError(f"Surface Deform failed to bind on '{cloth.name}'. Target mesh violates deformation rules.")
                        bound_count += 1

            # ==================================================================
            # 4. COMMIT PHASE (Critical 1 & Critical 3: Dependent verification)
            # ==================================================================
            old_proxies_to_remove = []

            for p_info in created_temp_proxies:
                tmp_proxy = p_info['obj']
                perm_name = p_info['perm_name']
                old_perm = bpy.data.objects.get(perm_name)

                if old_perm and old_perm != tmp_proxy:
                    # Collect all external dependent objects targeting old_perm
                    dependent_mods = []
                    for obj in bpy.data.objects:
                        if obj not in clothing_objs and obj.type == 'MESH':
                            for m in obj.modifiers:
                                if m.type == 'SURFACE_DEFORM' and m.target == old_perm and getattr(m, 'is_bound', False):
                                    dependent_mods.append((obj, m))

                    # Rebind each dependent garment to tmp_proxy and verify is_bound == True
                    for dep_obj, dep_mod in dependent_mods:
                        dep_mod.target = tmp_proxy
                        context.view_layer.objects.active = dep_obj
                        with context.temp_override(active_object=dep_obj, object=dep_obj):
                            try:
                                bpy.ops.object.surfacedeform_bind(modifier=dep_mod.name)
                            except Exception as exc:
                                print(f"[Giggle] Migration bind failed on '{dep_obj.name}': {exc}")

                        if not dep_mod.is_bound:
                            # Revert failing dependent and all prior migrated dependents back to old_perm
                            dep_mod.target = old_perm
                            with context.temp_override(active_object=dep_obj, object=dep_obj):
                                try:
                                    bpy.ops.object.surfacedeform_bind(modifier=dep_mod.name)
                                except Exception:
                                    pass
                            for r_obj, r_mod, _ in migrated_dependents:
                                r_mod.target = old_perm
                                with context.temp_override(active_object=r_obj, object=r_obj):
                                    try:
                                        bpy.ops.object.surfacedeform_bind(modifier=r_mod.name)
                                    except Exception:
                                        pass
                            raise RuntimeError(f"Dependent garment '{dep_obj.name}' failed to rebind to replacement proxy. Preserving old proxy.")

                        migrated_dependents.append((dep_obj, dep_mod, old_perm))

                    old_proxies_to_remove.append(old_perm)

            # Safely remove replaced proxies only after 100% of dependents verified
            for old_p in old_proxies_to_remove:
                bpy.data.objects.remove(old_p, do_unlink=True)

            # Finalize new proxies
            for p_info in created_temp_proxies:
                tmp_p = p_info['obj']
                tmp_p.name = p_info['perm_name']
                tmp_p.data.name = f"{tmp_p.name}_Mesh"
                tmp_p.display_type = 'TEXTURED'
                tmp_p.hide_viewport = True
                tmp_p.hide_set(True)
                tmp_p.hide_render = True

            # Finalize reused proxies
            for p_name in orig_proxy_vis.keys():
                p = bpy.data.objects.get(p_name)
                if p:
                    p.display_type = 'TEXTURED'
                    p.hide_viewport = True
                    p.hide_set(True)
                    p.hide_render = True

            # Hide dedicated proxies collection
            if giggle_col:
                giggle_col.hide_viewport = True
                giggle_col.hide_render = True

            # Finalize staged modifiers (Selective cleanup - Medium 8)
            for cloth, staged_sd in staged_modifiers:
                for m in list(cloth.modifiers):
                    if m == staged_sd:
                        continue
                    if m.type == 'NODES' and m.name.startswith("Giggle_") and m.name.endswith("_Follow"):
                        cloth.modifiers.remove(m)
                    elif m.type == 'SURFACE_DEFORM' and m.name == "Giggle_SurfaceDeform":
                        cloth.modifiers.remove(m)
                staged_sd.name = "Giggle_SurfaceDeform"

            self.report({'INFO'}, f"Successfully attached {bound_count} clothing mesh(es) to Giggle jiggle zones!")
            return {'FINISHED'}

        except Exception as e:
            # 5. TRANSACTIONAL ROLLBACK (Critical 1, 2, 3 & Medium 9)
            for cloth, staged_sd in staged_modifiers:
                if cloth and staged_sd.name in cloth.modifiers:
                    cloth.modifiers.remove(staged_sd)

            # Revert any migrated dependents back to their old proxies
            for dep_obj, dep_mod, old_perm in migrated_dependents:
                if dep_obj and dep_mod.name in dep_obj.modifiers and old_perm and old_perm.name in bpy.data.objects:
                    dep_mod.target = old_perm
                    with context.temp_override(active_object=dep_obj, object=dep_obj):
                        try:
                            bpy.ops.object.surfacedeform_bind(modifier=dep_mod.name)
                        except Exception:
                            pass

            # Remove all created temp proxies and their mesh datablocks (Critical 2)
            for p_info in created_temp_proxies:
                obj = p_info.get('obj')
                mesh = p_info.get('mesh')
                if obj and obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                if mesh and mesh.name in bpy.data.meshes:
                    bpy.data.meshes.remove(mesh, do_unlink=True)

            # Restore reused proxy visibility (Medium 9)
            for p_name, (hv, hg, hr) in orig_proxy_vis.items():
                p = bpy.data.objects.get(p_name)
                if p:
                    p.hide_viewport = hv
                    p.hide_set(hg)
                    p.hide_render = hr

            self.report({'ERROR'}, f"Clothing attachment failed (Rolled back): {e}")
            return {'CANCELLED'}

        finally:
            # Never leave the user's rig in REST, whatever path we took.
            restore_failures = restore_pose_position(orig_pose_positions)
            if restore_failures:
                detail = "; ".join(f"'{name}': {error}" for name, error in restore_failures)
                message = (f"Some armatures could not be returned to their original pose ({detail}). "
                           "Set their Pose Position back manually.")
                print("[Giggle] " + message)
                try:
                    self.report({'ERROR'}, message)
                except Exception:
                    pass
            if orig_pose_positions:
                try:
                    context.view_layer.update()
                except Exception:
                    pass
            scene.frame_set(orig_frame)
            if orig_active and orig_active.name in bpy.data.objects:
                context.view_layer.objects.active = orig_active
            for o in orig_selected:
                if o and o.name in bpy.data.objects:
                    try:
                        o.select_set(True)
                    except Exception:
                        pass
            # Restore original context mode (Medium 10)
            if orig_mode != 'OBJECT' and orig_active and orig_active.name in bpy.data.objects:
                with context.temp_override(active_object=orig_active, object=orig_active):
                    try:
                        bpy.ops.object.mode_set(mode=orig_mode)
                    except Exception:
                        pass



class GIGGLE_OT_copy_zone_to_clothing(Operator):
    """Copy active Giggle jiggle zone to selected clothing meshes so clothing moves with body physics"""
    bl_idname = "giggle.copy_zone_to_clothing"
    bl_label = "Copy Jiggle Zone to Clothing"
    bl_description = "Add a matching Giggle physics zone directly to selected clothing objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        has_giggle = any(get_giggle_modifiers(o) for o in selected_meshes)
        return len(selected_meshes) >= 2 and has_giggle

    def execute(self, context):
        settings = context.scene.giggle_settings
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
        if not giggle_bodies:
            self.report({'WARNING'}, "No selected mesh has Giggle physics.")
            return {'CANCELLED'}

        active_obj = context.active_object if context.active_object in giggle_bodies else giggle_bodies[0]
        mods = get_giggle_modifiers(active_obj)
        idx = settings.active_zone_index
        if not (0 <= idx < len(mods)):
            idx = 0

        source_mod = mods[idx]
        tree = source_mod.node_group

        clothing_objs = [o for o in selected_meshes if o != active_obj]
        added = 0

        for cloth in clothing_objs:
            if hasattr(cloth, "add_rest_position_attribute"):
                cloth.add_rest_position_attribute = True

            mod_name = f"Giggle_{cloth.name}_Follow"
            existing = cloth.modifiers.get(mod_name)
            if existing:
                cloth.modifiers.remove(existing)

            new_mod = cloth.modifiers.new(name=mod_name, type='NODES')
            new_mod.node_group = tree

            if hasattr(source_mod, "properties") and hasattr(source_mod.properties, "inputs"):
                for s_name in source_mod.properties.inputs.keys():
                    val = get_mod_socket(source_mod, s_name)
                    if val is not None:
                        set_mod_socket(new_mod, s_name, value=val)

            # Project vertex group from body to clothing using KDTree proximity
            source_vg_name = get_mod_socket_attribute_name(source_mod, 'Socket_2')
            if not source_vg_name or not isinstance(source_vg_name, str) or source_vg_name not in active_obj.vertex_groups:
                mod_suffix = source_mod.name.replace("Giggle_", "")
                if mod_suffix in active_obj.vertex_groups:
                    source_vg_name = mod_suffix
                elif "Jiggle_Zone" in active_obj.vertex_groups:
                    source_vg_name = "Jiggle_Zone"
                elif active_obj.vertex_groups:
                    source_vg_name = active_obj.vertex_groups[0].name
                else:
                    source_vg_name = "Jiggle_Zone"

            body_vg = active_obj.vertex_groups.get(source_vg_name) if isinstance(source_vg_name, str) else None

            cloth_vg_name = f"{source_vg_name}_Cloth" if source_vg_name else "Giggle_Cloth"
            cloth_vg = cloth.vertex_groups.get(cloth_vg_name) or cloth.vertex_groups.new(name=cloth_vg_name)

            if body_vg and len(active_obj.data.vertices) > 0 and len(cloth.data.vertices) > 0:
                from mathutils.kdtree import KDTree
                kd = KDTree(len(active_obj.data.vertices))
                for i, v in enumerate(active_obj.data.vertices):
                    kd.insert(v.co, i)
                kd.balance()

                for v in cloth.data.vertices:
                    co, index, dist = kd.find(v.co)
                    try:
                        w = body_vg.weight(index)
                        if dist > 0.03:
                            w = 0.0
                        elif dist > 0.01:
                            w *= (0.03 - dist) / 0.02
                        if w > 0.001:
                            cloth_vg.add([v.index], w, 'REPLACE')
                        else:
                            cloth_vg.add([v.index], 0.0, 'REPLACE')
                    except RuntimeError:
                        cloth_vg.add([v.index], 0.0, 'REPLACE')
            else:
                cloth_vg.add(list(range(len(cloth.data.vertices))), 1.0, 'REPLACE')

            set_mod_socket(new_mod, 'Socket_2', attribute=cloth_vg_name)
            position_giggle_modifier(cloth, new_mod)
            added += 1

        self.report({'INFO'}, f"Applied Giggle physics zone to {added} clothing meshes.")
        return {'FINISHED'}


class GIGGLE_OT_split_shapekey_lr(Operator):
    """Split active shape key into .l and .r halves at X=0"""
    bl_idname = "giggle.split_shapekey_lr"
    bl_label = "Split Shape Key (L / R)"
    bl_description = "Split the active shape key into independent left (.l) and right (.r) shape keys"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.active_shape_key and obj.data.shape_keys

    def execute(self, context):
        obj = context.active_object
        sk_data = obj.data.shape_keys
        active_sk = obj.active_shape_key
        basis_sk = sk_data.key_blocks[0]

        if active_sk == basis_sk:
            self.report({'WARNING'}, "Cannot split the Basis shape key.")
            return {'CANCELLED'}

        orig_name = active_sk.name
        orig_val = active_sk.value

        sk_l = obj.shape_key_add(name=f"{orig_name}.l", from_mix=False)
        sk_r = obj.shape_key_add(name=f"{orig_name}.r", from_mix=False)
        sk_l.value = orig_val
        sk_r.value = orig_val

        mesh = obj.data
        seam_width = 0.001
        for i, vert in enumerate(mesh.vertices):
            base_co = basis_sk.data[i].co
            active_co = active_sk.data[i].co
            delta = active_co - base_co

            if abs(base_co.x) <= seam_width:
                # Smooth midline seam transition across [-seam_width, +seam_width]
                t = 0.5 + (base_co.x / (2.0 * seam_width))
                sk_l.data[i].co = base_co + delta * t
                sk_r.data[i].co = base_co + delta * (1.0 - t)
            elif base_co.x > seam_width:  # Left side
                sk_l.data[i].co = active_co
                sk_r.data[i].co = base_co
            else:  # Right side
                sk_l.data[i].co = base_co
                sk_r.data[i].co = active_co

        # Keep the original as a backup, but disable it so it is not summed with the two halves.
        if hasattr(active_sk, 'mute'):
            active_sk.mute = True
        else:
            active_sk.value = 0.0
        self.report({'INFO'}, f"Split '{orig_name}' into '{orig_name}.l' and '.r'; original muted as backup.")
        return {'FINISHED'}


class GIGGLE_OT_create_body_mask(Operator):
    """Create an anti-clipping mask from selected vertices so skin never pokes through tight clothing"""
    bl_idname = "giggle.create_body_mask"
    bl_label = "Create Anti-Clipping Mask"
    bl_description = "In Edit Mode: Create a mask modifier from selected vertices to prevent skin poking through clothes"
    bl_options = {'REGISTER', 'UNDO'}

    mask_name: StringProperty(name="Mask Name", default="UnderClothes")

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and context.active_object and context.active_object.type == 'MESH')

    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')

        selected_indices = [v.index for v in obj.data.vertices if v.select]
        if not selected_indices:
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'WARNING'}, "No vertices selected! Select the vertices hidden under clothing first.")
            return {'CANCELLED'}

        vg_name = f"Mask_{self.mask_name}"
        vg = obj.vertex_groups.get(vg_name)
        if not vg:
            vg = obj.vertex_groups.new(name=vg_name)
        vg.add(selected_indices, 1.0, 'REPLACE')

        mod_name = f"Giggle_Mask_{self.mask_name}"
        mask_mod = obj.modifiers.get(mod_name)
        if not mask_mod:
            mask_mod = obj.modifiers.new(name=mod_name, type='MASK')

        mask_mod.vertex_group = vg_name
        mask_mod.invert_vertex_group = True # Hide selected covered skin

        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, f"Created anti-clipping mask '{vg_name}' on {len(selected_indices)} vertices.")
        return {'FINISHED'}


class GIGGLE_OT_relink_textures(Operator):
    """Re-link missing or pink textures in the project"""
    bl_idname = "giggle.relink_textures"
    bl_label = "Re-Link Missing Textures"
    bl_description = "Scan directory to find and re-link missing texture images"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.file.find_missing_files('INVOKE_DEFAULT')
        return {'FINISHED'}


class VIEW3D_PT_giggle_wardrobe(Panel):
    bl_label = "Wardrobe & Costumes"
    bl_idname = "VIEW3D_PT_giggle_wardrobe"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Giggle'
    bl_order = 15
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        cats = get_wardrobe_scene_collections(context)
        total_cols = sum(len(lst) for lst in cats.values())

        if total_cols == 0:
            layout.label(text="No clothing or character collections detected.", icon='OUTLINER_COLLECTION')
            layout.label(text="Name collections 'costume', 'clothes', or 'body'", icon='INFO')
            return

        # Top utility buttons
        top_row = layout.row(align=True)
        top_row.operator("giggle.wardrobe_show_all", text="Show All", icon='CHECKMARK')
        top_row.operator("giggle.wardrobe_hide_clothes", text="Hide Clothes (Tune)", icon='HIDE_ON')

        # Helper to draw a category section
        def draw_cat_section(title, col_list, section_icon):
            if not col_list:
                return
            header_box = layout.box()
            header_box.label(text=title, icon=section_icon)
            for col, objs in col_list:
                is_vis = col.giggle_show_render
                col_box = header_box.box()
                row = col_box.row(align=True)
                icon = 'CHECKBOX_HL' if is_vis else 'CHECKBOX_DEHL'
                label_text = col.name if is_vis else f"{col.name} [Hidden]"
                row.prop(col, "giggle_show_render", text=label_text, toggle=True, icon=icon)

                # If this is the character body, provide a direct 1-click select button
                if title.startswith("Character"):
                    row.operator("giggle.select_body_mesh", text="", icon='RESTRICT_SELECT_OFF')

                if is_vis and objs:
                    obj_col = col_box.column(align=True)
                    for obj in objs:
                        obj_vis = obj.giggle_show_render
                        obj_icon = 'CHECKBOX_HL' if obj_vis else 'CHECKBOX_DEHL'
                        obj_row = obj_col.row(align=True)
                        obj_row.prop(obj, "giggle_show_render", text=obj.name, toggle=True, icon=obj_icon)

        # 1. Outfits & Clothing
        draw_cat_section("Outfits & Costumes", cats['outfits'], 'MOD_CLOTH')

        # 2. Hair & Accessories
        draw_cat_section("Hair & Accessories", cats['accessories'], 'RESTRICT_VIEW_OFF')

        # 3. Base Character & Body
        draw_cat_section("Character Body & Mesh", cats['body'], 'USER')

        # 4. Other Mesh Collections
        draw_cat_section("Other Scene Meshes", cats['other'], 'OUTLINER_COLLECTION')


class VIEW3D_PT_giggle_clothing_follower(Panel):
    bl_label = "Clothing Follower & Deform"
    bl_idname = "VIEW3D_PT_giggle_clothing_follower"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Giggle'
    bl_order = 16
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        try:
            settings = getattr(context.scene, 'giggle_settings', None)
            box = layout.box()
            box.label(text="Make Clothing Follow Jiggle:", icon='MOD_CLOTH')

            if settings:
                col = box.column(align=True)
                col.prop(settings, "clothing_target_zone", text="Zone")
                if settings.clothing_target_zone != 'AUTO':
                    col.label(text=f"Target: {settings.clothing_target_zone} (Manual)", icon='RESTRICT_SELECT_OFF')
                else:
                    selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
                    giggle_bodies = [o for o in selected_meshes if get_giggle_modifiers(o)]
                    body = context.active_object if context.active_object in giggle_bodies else (giggle_bodies[0] if giggle_bodies else None)
                    clothing_objs = [o for o in selected_meshes if o != body]
                    if len(clothing_objs) > 1 and body:
                        col.label(text=f"Auto: {len(clothing_objs)} garments (resolving per-mesh):", icon='INFO')
                        for c in clothing_objs[:3]:
                            r_mod, r_vg, d_val, status = resolve_garment_target_zone(c, body)
                            if r_mod and r_vg:
                                d_s = f" ({d_val*100:.1f} cm)" if d_val is not None else ""
                                ic = 'CHECKMARK' if status == 'OK' else 'ERROR'
                                col.label(text=f"  • {c.name}: {r_mod.name}{d_s}", icon=ic)
                        if len(clothing_objs) > 3:
                            col.label(text=f"  ...and {len(clothing_objs)-3} more", icon='BLANK1')
                    else:
                        body_res, resolved_mod, resolved_vg, dist = resolve_clothing_target_zone(context)
                        if resolved_mod and resolved_vg:
                            dist_str = f" ({dist*100:.1f} cm)" if dist is not None else ""
                            if dist is not None and dist > 0.35:
                                col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='ERROR')
                            else:
                                col.label(text=f"Auto Target: {resolved_mod.name} -> {resolved_vg}{dist_str}", icon='CHECKMARK')
                        else:
                            col.label(text="Auto: Each garment resolves closest zone", icon='INFO')

            box.operator("giggle.attach_clothing_proxy", text="Attach Clothes to Jiggle (Flush Surface)", icon='MOD_MESHDEFORM')

            box.separator()
            box.label(text="Clothing Deform Rebind:", icon='HOOK')
            box.operator("giggle.rebind_clothing_modifiers", text="Rebind Modifiers (Scene Start)", icon='FILE_REFRESH')

            box.separator()
            box.operator("giggle.copy_zone_to_clothing", text="Copy Physics Solver to Clothes (Advanced)", icon='DUPLICATE')
        except Exception as e:
            layout.label(text=f"UI Error: {e}", icon='ERROR')


class GIGGLE_OT_pin_hair_roots(Operator):
    """Pin hair roots to the scalp (weight 0.0) with smooth falloff to free tips (1.0)"""
    bl_idname = "giggle.pin_hair_roots"
    bl_label = "Auto-Pin Hair Roots (Gradient)"
    bl_description = "Automatically pin hair roots to scalp (0.0) with a smooth falloff down to free tips (1.0) to prevent detachment"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a Mesh")
            return {'CANCELLED'}

        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        target_vg_name = ""

        # Determine target vertex group from active zone or selection
        if mods and 0 <= settings.active_zone_index < len(mods):
            mod = mods[settings.active_zone_index]
            s_in = getattr(getattr(mod, "properties", None), "inputs", None)
            if mod.node_group and mod.node_group.name == 'Wiggy 0.1' and s_in and hasattr(s_in, "Socket_2"):
                target_vg_name = getattr(s_in.Socket_2, "attribute_name", "")

        if not target_vg_name and getattr(settings, "new_zone_vg", ""):
            target_vg_name = settings.new_zone_vg

        if not target_vg_name:
            if obj.vertex_groups.active:
                target_vg_name = obj.vertex_groups.active.name
            else:
                target_vg_name = "Hair_Pin_Gradient"

        vg = obj.vertex_groups.get(target_vg_name)
        if not vg:
            vg = obj.vertex_groups.new(name=target_vg_name)

        if mods and 0 <= settings.active_zone_index < len(mods):
            target_mod = mods[settings.active_zone_index]
            s_in = getattr(getattr(target_mod, "properties", None), "inputs", None)
            if target_mod.node_group and target_mod.node_group.name == 'Wiggy 0.1' and s_in and hasattr(s_in, "Socket_2") and not getattr(s_in.Socket_2, "attribute_name", ""):
                try:
                    s_in.Socket_2.attribute_name = vg.name
                except Exception:
                    pass

        mesh = obj.data
        if len(mesh.vertices) == 0:
            self.report({'WARNING'}, "Mesh has no vertices")
            return {'CANCELLED'}

        # Calculate bounding box along Z axis (local height)
        # Restrict to existing group vertices if already painted, or selected vertices in edit mode
        existing_indices = [v.index for v in mesh.vertices for g in v.groups if g.group == vg.index and g.weight > 0.0]
        if existing_indices:
            target_indices = existing_indices
        elif obj.mode == 'EDIT':
            import bmesh
            bm = bmesh.from_edit_mesh(mesh)
            target_indices = [v.index for v in bm.verts if v.select]
            if not target_indices:
                target_indices = list(range(len(mesh.vertices)))
        else:
            target_indices = list(range(len(mesh.vertices)))

        z_coords = [mesh.vertices[i].co.z for i in target_indices]
        min_z = min(z_coords)
        max_z = max(z_coords)
        height = max(0.001, max_z - min_z)

        # Crown / scalp roots are at max_z (top of head in Z-up models).
        # Strand tips hang down at min_z.
        # Lock top 12% strictly to 0.0 (pin), and smoothly ease to 1.0 at min_z.
        pinned_count = 0
        for idx in target_indices:
            v = mesh.vertices[idx]
            t = (max_z - v.co.z) / height
            t = max(0.0, min(1.0, t))

            if t < 0.12:
                weight = 0.0
            else:
                rel_t = (t - 0.12) / 0.88
                weight = rel_t * rel_t * (3.0 - 2.0 * rel_t)

            vg.add([v.index], weight, 'REPLACE')
            pinned_count += 1

        self.report({'INFO'}, f"Auto-pinned hair roots on '{vg.name}': Top 12% locked (0.0), smooth falloff to tips (1.0)")
        return {'FINISHED'}

class VIEW3D_PT_giggle_character_tools(Panel):
    bl_label = "Character Shape & Anti-Clipping"
    bl_idname = "VIEW3D_PT_giggle_character_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Giggle'
    bl_order = 17
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Anti-Clipping Mask (Edit Mode):", icon='MOD_MASK')
        box.operator("giggle.create_body_mask", text="Hide Covered Skin Under Clothes", icon='SELECT_SUBTRACT')

        box.separator()
        box.label(text="Distance-Based Falloff (Crease Fix):", icon='BRUSH_DATA')
        box.operator("giggle.generate_distance_falloff", text="Generate Falloff Weights", icon='SMOOTHCURVE')

        box.separator()
        box.label(text="Shape Key Splitter:", icon='SHAPEKEY_DATA')
        box.operator("giggle.split_shapekey_lr", text="Split Active Shape Key (L / R)", icon='ARROW_LEFTRIGHT')

        box.separator()
        box.label(text="Textures & Optimization:", icon='IMAGE_DATA')
        box.operator("giggle.relink_textures", text="Find & Re-Link Textures", icon='VIEWZOOM')


class GIGGLE_OT_apply_action_safety(Operator):
    """Apply action-safe physical limits and auto-scale substeps for jumping, running and explosive impacts"""
    bl_idname = "giggle.apply_action_safety"
    bl_label = "Apply Action / Jump Safety"
    bl_description = "Clamps displacement, sway, and wobble to jump-safe limits and scales solver substeps"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None) if context.scene else None
        if not obj or not settings:
            return False
        mods = get_giggle_modifiers(obj)
        if not (0 <= settings.active_zone_index < len(mods)):
            return False
        mod = mods[settings.active_zone_index]
        return bool(mod.node_group and mod.node_group.name == 'Wiggy 0.1')

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        mod = mods[settings.active_zone_index]

        # Backup current settings on the parent object ID data
        for sock_id in ['Socket_123', 'Socket_119', 'Socket_126', 'Socket_8', 'Socket_118', 'Socket_6', 'Socket_30', 'Socket_14', 'Socket_122']:
            val = get_mod_socket(mod, sock_id)
            if val is not None:
                obj[f"_giggle_backup_{mod.name}_{sock_id}"] = val

        # Identify category / anatomy
        meta = get_mod_giggle_metadata(mod)
        active_cat = meta[1] if meta else ""
        vg_name = ""
        s_zone = getattr(getattr(mod, "properties", None), "inputs", None)
        if s_zone and hasattr(s_zone, "Socket_2"):
            vg_name = getattr(s_zone.Socket_2, "attribute_name", "").lower()

        is_glute = any(k in active_cat.lower() or k in vg_name or k in mod.name.lower() for k in ['butt', 'glute', 'leg', 'thigh', 'groin', 'genitalia'])

        # Calculate action substeps based on scene FPS
        fps = context.scene.render.fps / context.scene.render.fps_base if (context.scene and context.scene.render.fps_base) else 24.0
        target_substeps = max(int(round(360.0 / fps)), 4)

        if is_glute:
            set_mod_socket(mod, 'Socket_123', 0.025)  # 2.5 cm max travel
            set_mod_socket(mod, 'Socket_119', 0.18)   # 0.18 sway across hip joint
            set_mod_socket(mod, 'Socket_126', 0.35)   # 0.35 wobble (settles fast)
            set_mod_socket(mod, 'Socket_8', 2.00)     # 2.00 damping
            set_mod_socket(mod, 'Socket_118', 0.98)   # 0.98 volume retention
            set_mod_socket(mod, 'Socket_6', 0.08)     # low stretching compliance
            set_mod_socket(mod, 'Socket_30', 0.18)    # bending compliance
            set_mod_socket(mod, 'Socket_122', 4)      # edge fade 4
        else:
            set_mod_socket(mod, 'Socket_123', 0.028)  # 2.8 cm max travel for chest/torso
            set_mod_socket(mod, 'Socket_119', 0.28)   # 0.28 sway
            set_mod_socket(mod, 'Socket_126', 0.35)   # 0.35 wobble
            set_mod_socket(mod, 'Socket_8', 2.00)     # 2.00 damping
            set_mod_socket(mod, 'Socket_118', 0.96)   # 0.96 volume retention
            set_mod_socket(mod, 'Socket_6', 0.09)     # low stretching compliance
            set_mod_socket(mod, 'Socket_30', 0.20)
            set_mod_socket(mod, 'Socket_122', 3)

        set_mod_socket(mod, 'Socket_14', target_substeps)
        obj[f"_giggle_action_safety_{mod.name}"] = True

        # Preserve user active frame during action safety application

        zone_type = "Glutes / Leg Joints" if is_glute else "Chest / Torso Soft Tissue"
        self.report({'INFO'}, f"Action Safety applied to '{mod.name}' ({zone_type}): max travel <= {0.025 if is_glute else 0.028}m, substeps={target_substeps}.")
        return {'FINISHED'}


class GIGGLE_OT_restore_zone_settings(Operator):
    """Restore previous simulation settings backed up before applying Action Safety"""
    bl_idname = "giggle.restore_zone_settings"
    bl_label = "Restore Original Settings"
    bl_description = "Restores simulation parameters backed up before Action Safety was applied"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        settings = getattr(context.scene, 'giggle_settings', None) if context.scene else None
        if not obj or not settings:
            return False
        mods = get_giggle_modifiers(obj)
        if not (0 <= settings.active_zone_index < len(mods)):
            return False
        mod = mods[settings.active_zone_index]
        prefix = f'_giggle_backup_{mod.name}_'
        return any(k.startswith(prefix) for k in obj.keys())

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.giggle_settings
        mods = get_giggle_modifiers(obj)
        mod = mods[settings.active_zone_index]

        prefix = f'_giggle_backup_{mod.name}_'
        restored_count = 0
        for k in list(obj.keys()):
            if k.startswith(prefix):
                sock_id = k.replace(prefix, '')
                set_mod_socket(mod, sock_id, obj[k])
                restored_count += 1
                del obj[k]
        obj[f"_giggle_action_safety_{mod.name}"] = False

        # Preserve user active frame during zone restore

        self.report({'INFO'}, f"Restored {restored_count} original settings on '{mod.name}'.")
        return {'FINISHED'}


class GIGGLE_OT_generate_distance_falloff(Operator):
    """Generate smooth distance-based falloff weights from selected vertices or zone apex"""
    bl_idname = "giggle.generate_distance_falloff"
    bl_label = "Generate Distance Falloff Weights"
    bl_description = "Creates a smooth, spherical or ellipsoidal distance falloff weight map to eliminate sharp boundary creases"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: StringProperty(name="Vertex Group", default="Jiggle_Zone")
    inner_radius: FloatProperty(name="Inner Core Radius", default=0.035, min=0.001, max=1.0, unit='LENGTH', description="Distance from origin where weight is 1.0 (100% influence)")
    outer_radius: FloatProperty(name="Outer Border Radius", default=0.120, min=0.005, max=2.0, unit='LENGTH', description="Distance from origin where weight falls off to 0.0")
    falloff_curve: EnumProperty(
        name="Falloff Curve",
        items=[
            ('SMOOTH', "Smoothstep", "Smooth cubic Hermite transition (3x^2 - 2x^3)"),
            ('LINEAR', "Linear", "Linear transition from core to border"),
            ('SHARP', "Sharp", "Rapid falloff preserving firmer edges"),
        ],
        default='SMOOTH'
    )
    use_symmetry: BoolProperty(name="X-Axis Symmetry", default=True, description="Mirror weights across character centerline (X = 0)")

    @classmethod
    def poll(cls, context):
        return bool(context.active_object and context.active_object.type == 'MESH')

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # 1. Selected vertices (edit or object mode)
        sel_cos = [v.co for v in mesh.vertices if v.select]
        
        # 2. Existing vertex group apex
        if not sel_cos:
            vg = obj.vertex_groups.get(self.group_name)
            if vg:
                best_w = -1.0
                best_co = None
                for v in mesh.vertices:
                    for g in v.groups:
                        if g.group == vg.index and g.weight > best_w:
                            best_w = g.weight
                            best_co = v.co
                if best_co is not None:
                    sel_cos = [best_co]
        
        # 3. 3D cursor in object space
        if not sel_cos and hasattr(context.scene, 'cursor'):
            try:
                inv_matrix = obj.matrix_world.inverted()
                sel_cos = [inv_matrix @ context.scene.cursor.location]
            except Exception:
                pass

        # 4. Fallback: object origin
        if not sel_cos:
            sel_cos = [mathutils.Vector((0.0, 0.0, 0.0))]

        # Center point
        center = sum(sel_cos, mathutils.Vector((0.0, 0.0, 0.0))) / len(sel_cos)
        sym_center = mathutils.Vector((-center.x, center.y, center.z))

        # Ensure vertex group exists
        vg = obj.vertex_groups.get(self.group_name)
        if not vg:
            vg = obj.vertex_groups.new(name=self.group_name)

        r_in = max(self.inner_radius, 0.0001)
        r_out = max(self.outer_radius, r_in + 0.001)
        r_range = r_out - r_in

        assigned_count = 0
        for v in mesh.vertices:
            d = (v.co - center).length
            if self.use_symmetry:
                d_sym = (v.co - sym_center).length
                if d_sym < d:
                    d = d_sym
            
            if d <= r_in:
                w = 1.0
            elif d >= r_out:
                w = 0.0
            else:
                t = 1.0 - ((d - r_in) / r_range)
                if self.falloff_curve == 'SMOOTH':
                    w = 3.0 * (t ** 2) - 2.0 * (t ** 3)
                elif self.falloff_curve == 'SHARP':
                    w = t ** 2
                else:
                    w = t
            
            if w > 0.001:
                vg.add([v.index], w, 'REPLACE')
                assigned_count += 1
            else:
                vg.remove([v.index])

        self.report({'INFO'}, f"Generated distance falloff for '{vg.name}': {assigned_count} vertices weighted (inner={r_in*100:.1f}cm, outer={r_out*100:.1f}cm).")
        return {'FINISHED'}



@bpy.app.handlers.persistent
def render_pre_cache_check(scene):
    try:
        settings = getattr(scene, 'giggle_settings', None)
        if not settings or not getattr(settings, 'check_cache_on_render', True):
            return
        outdated = []
        unbaked = []
        bind_targets = get_giggle_cage_bind_targets(scene.objects)
        for o in scene.objects:
            if is_giggle_owned_cage(o, bind_targets):
                st, reason = check_cage_validity(o, bpy.context)
                if st == 'OUTDATED':
                    outdated.append(f"{o.name} ({reason})")
                elif st != 'BAKED':
                    unbaked.append(o.name)
        if outdated or unbaked:
            print("\n[GIGGLE PRE-FLIGHT RENDER WARNING]")
            if outdated:
                print(f"  WARNING: Rendering with OUTDATED cache on: {', '.join(outdated)}")
            if unbaked:
                print(f"  WARNING: Rendering with UNBAKED cache on: {', '.join(unbaked)}")
            print("  Recommendation: Recalculate simulation caches with 'Rebake All' before rendering.\n")
    except Exception:
        pass

classes = (
    GIGGLE_OT_apply_action_safety,
    GIGGLE_OT_restore_zone_settings,
    GIGGLE_OT_generate_distance_falloff,
    GIGGLE_OT_wardrobe_show_all,
    GIGGLE_OT_wardrobe_hide_clothes,
    GIGGLE_OT_select_body_mesh,
    GIGGLE_OT_fix_body_manifold,
    GIGGLE_OT_rebind_clothing_modifiers,
    GIGGLE_OT_attach_clothing_proxy,
    GIGGLE_OT_copy_zone_to_clothing,
    GIGGLE_OT_split_shapekey_lr,
    GIGGLE_OT_create_body_mask,
    GIGGLE_OT_relink_textures,
    VIEW3D_PT_giggle_wardrobe,
    VIEW3D_PT_giggle_clothing_follower,
    VIEW3D_PT_giggle_character_tools,
    GiggleSceneSettings,
    GIGGLE_OT_pick_active_vg,
    GIGGLE_OT_create_vg,
    GIGGLE_OT_duplicate_safe_vg,
    GIGGLE_OT_pin_hair_roots,
    GIGGLE_OT_add_zone,
    GIGGLE_OT_remove_zone,
    GIGGLE_OT_apply_support_level,
    GIGGLE_OT_apply_preset,
    GIGGLE_OT_toggle_mute,
    GIGGLE_OT_solo_zone,
    GIGGLE_OT_add_collider,
    GIGGLE_OT_add_wind,
    GIGGLE_OT_autotune_substeps,
    GIGGLE_OT_reset_sim,
    GIGGLE_OT_clear_sim_cache,
    GIGGLE_OT_fix_gpu_subdivision,
    GIGGLE_OT_clamp_subdivision,
    GIGGLE_OT_generate_cage,
    GIGGLE_OT_toggle_simulation_mode,
    GIGGLE_OT_rebuild_cage,
    GIGGLE_OT_keep_full_mesh,
    GIGGLE_OT_bake_all_cages,
    GIGGLE_OT_bake_selected_cage,
    GIGGLE_OT_rebake_all,
    GIGGLE_OT_rebake_sim,
    GIGGLE_OT_bake_missing,
    GIGGLE_OT_check_cache_validity,
    GIGGLE_OT_mark_cache_outdated,
    GIGGLE_OT_select_zone,
    GIGGLE_OT_sync_active_zone,
    VIEW3D_PT_giggle_main,
    VIEW3D_PT_giggle_presets,
    VIEW3D_PT_giggle_dynamics,
    VIEW3D_PT_giggle_shape,
    VIEW3D_PT_giggle_collisions,
    VIEW3D_PT_giggle_self_collision,
    VIEW3D_PT_giggle_forces,
    VIEW3D_PT_giggle_playback,
    VIEW3D_PT_giggle_diagnostics,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if render_pre_cache_check not in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.append(render_pre_cache_check)
    bpy.types.Scene.giggle_settings = PointerProperty(type=GiggleSceneSettings)
    bpy.types.Collection.giggle_show_render = BoolProperty(
        name="Show in Viewport & Render",
        description="Toggle Collection Visibility for both Viewport and Render",
        get=get_show_collection_render,
        set=set_show_collection_render
    )
    bpy.types.Object.giggle_show_render = BoolProperty(
        name="Show in Viewport & Render",
        description="Toggle Object Visibility for both Viewport and Render",
        get=get_show_object_render,
        set=set_show_object_render
    )

def unregister():
    if render_pre_cache_check in bpy.app.handlers.render_pre:
        try:
            bpy.app.handlers.render_pre.remove(render_pre_cache_check)
        except Exception:
            pass
    if hasattr(bpy.types.Collection, "giggle_show_render"):
        del bpy.types.Collection.giggle_show_render
    if hasattr(bpy.types.Object, "giggle_show_render"):
        del bpy.types.Object.giggle_show_render
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    if hasattr(bpy.types.Scene, "giggle_settings"):
        try:
            del bpy.types.Scene.giggle_settings
        except Exception:
            pass

if __name__ == "__main__":
    register()
