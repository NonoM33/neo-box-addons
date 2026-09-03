"""La police de l'ecran, chargee une fois par taille.

Pillow embarque une police vectorielle par defaut (Aileron) : deterministe tant que la
version de Pillow est figee, ce qui evite de dependre d'une police systeme absente
de l'image Alpine de l'add-on.
"""

from functools import cache

from PIL import ImageFont


@cache
def font(size: int) -> ImageFont.FreeTypeFont:
    """La police a la taille demandee (en pixels)."""
    loaded = ImageFont.load_default(size=size)
    if not isinstance(loaded, ImageFont.FreeTypeFont):
        msg = "Pillow sans FreeType : impossible de charger une police redimensionnable"
        raise TypeError(msg)
    return loaded
