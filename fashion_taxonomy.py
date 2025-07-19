import google.generativeai as genai
import json
import enum
import typing
from PIL import Image
from datetime import datetime

# =============================================================================
# FASHION TAXONOMY DEFINITIONS
# =============================================================================

class ApparelCategory(enum.Enum):
    DRESS = "Dress"
    TOP = "Top"
    KNIT_TOP = "Knit or Sweater Top"
    SHIRT = "Shirt"
    PANTS = "Pants"
    SHORTS = "Shorts"
    SKIRT = "Skirt"
    SHOES = "Shoes"
    OUTERWEAR = "Outerwear"
    UNDERGARMENTS = "Undergarments"
    BAG = "Bag"
    ACCESSORY = "Accessory"

class Waist(enum.Enum):
    RIB_CAGE = "Rib cage"
    HIGH_WAISTED = "High Waisted"
    NATURAL_WAIST = "Natural Waist"
    MIDRISE = "Midrise"
    LOWRISE = "Lowrise"
    HIP_HUGGER = "Hip Hugger"

class PantsType(enum.Enum):
    JEANS = "Jeans"
    CHINOS = "Chinos"
    JOGGERS = "Joggers"
    FORMAL = "Formal"
    CARGO = "Cargo"

class PantsLength(enum.Enum):
    FULL_LENGTH = "Full Length"
    ANKLE = "Ankle"
    CROPPED = "Cropped"
    SHORTS = "Shorts"

class ShirtStyle(enum.Enum):
    BUTTON_DOWN = "Button Down"
    POLO = "Polo"
    TEE = "T-shirt"
    LONG_SLEEVE = "Long Sleeve"
    SHORT_SLEEVE = "Short Sleeve"

class ShoeType(enum.Enum):
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    FORMAL_SHOES = "Formal Shoes"
    SLIPPERS = "Slippers"

class WatchType(enum.Enum):
    ANALOG = "Analog"
    DIGITAL = "Digital"
    SMARTWATCH = "Smartwatch"

class FabricDetails(typing.TypedDict):
    material: str
    texture: str

class ClothingItem(typing.TypedDict):
    category: ApparelCategory
    colors: list[str]
    fabric: str
    fabric_details: list[FabricDetails]
    specific_type: str
    additional_attributes: dict

class Pants(ClothingItem):
    additional_attributes: dict

class Dress(ClothingItem):
    additional_attributes: dict

class Top(ClothingItem):
    additional_attributes: dict

class KnitTop(ClothingItem):
    additional_attributes: dict

class Shirt(ClothingItem):
    additional_attributes: dict

class Shorts(ClothingItem):
    additional_attributes: dict

class Skirt(ClothingItem):
    additional_attributes: dict

class Shoes(ClothingItem):
    additional_attributes: dict

class Outerwear(ClothingItem):
    additional_attributes: dict

class Undergarments(ClothingItem):
    additional_attributes: dict

class Bag(ClothingItem):
    additional_attributes: dict

class Accessory(ClothingItem):
    additional_attributes: dict
