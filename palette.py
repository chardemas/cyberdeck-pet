"""Every color in the world art, 3 to 4 tones per surface.

The outline and wood browns are sampled from the Onfe horse so the props sit
in the same style as the horse: dark brown outlines, warm shading, light from
the top-left.
"""

# Sampled from Horse_fullcolor_brown.png.
OUTLINE = (25, 13, 6)          # the horse's darkest outline
HORSE_SHADE = (68, 37, 22)
HORSE_MID = (94, 52, 32)
HORSE_BASE = (128, 71, 44)

# Grass.
GRASS = (92, 164, 76)
GRASS_DARK = (70, 136, 60)
GRASS_DEEP = (56, 112, 50)
GRASS_LIGHT = (124, 188, 92)

# Worn dirt.
DIRT_LIGHT = (172, 138, 94)
DIRT = (150, 118, 78)
DIRT_DARK = (124, 96, 62)

# Wood (fence, trough, jump poles), warmed toward the horse's browns.
WOOD_LIGHT = (188, 140, 86)
WOOD = (150, 104, 60)
WOOD_DARK = (102, 68, 38)
WOOD_DEEP = HORSE_SHADE

# Painted jump rail.
RAIL_WHITE = (244, 240, 228)
RAIL_RED = (210, 72, 64)
RAIL_RED_DARK = (160, 48, 46)

# Water.
WATER_LIGHT = (156, 214, 240)
WATER = (92, 168, 220)
WATER_DARK = (60, 124, 184)
WATER_DEEP = (44, 92, 150)

# Hay and straw.
HAY_LIGHT = (246, 222, 128)
HAY = (226, 190, 86)
HAY_DARK = (186, 146, 58)
HAY_TWINE = (160, 60, 50)

# Produce.
CARROT_LIGHT = (252, 168, 72)
CARROT = (236, 128, 40)
CARROT_DARK = (190, 90, 30)
APPLE_LIGHT = (246, 110, 100)
APPLE = (214, 58, 56)
APPLE_DARK = (156, 36, 40)
LEAF_LIGHT = (128, 196, 80)
LEAF = (78, 150, 56)
LEAF_DARK = (52, 108, 44)

# Metal bucket.
METAL_LIGHT = (196, 208, 214)
METAL = (150, 164, 174)
METAL_DARK = (102, 114, 126)

# Trees and bushes.
CANOPY_LIGHT = (104, 176, 84)
CANOPY = (66, 136, 64)
CANOPY_DARK = (44, 100, 54)
CANOPY_DEEP = (32, 74, 46)
BARK = HORSE_MID
BARK_DARK = HORSE_SHADE

# Effects.
HEART = (244, 92, 132)
HEART_LIGHT = (255, 170, 196)
SPARKLE = (255, 246, 190)
SPARKLE_CORE = (255, 255, 255)
DUST = (196, 170, 128)
DUST_LIGHT = (222, 202, 162)

# Big flowers: (petal, petal shade) pairs, plus a shared yellow middle.
BIG_PETALS = [
    ((250, 168, 196), (218, 116, 156)),  # pink
    ((252, 248, 240), (208, 202, 200)),  # white
    ((200, 168, 240), (152, 120, 200)),  # lavender
    ((156, 204, 248), (108, 152, 212)),  # sky blue
    ((252, 196, 150), (224, 146, 100)),  # peach
]
FLOWER_MIDDLE = (252, 216, 84)
FLOWER_MIDDLE_DARK = (220, 160, 48)
SMALL_FLOWERS = [(244, 240, 228), (248, 214, 84), (232, 128, 160)]
