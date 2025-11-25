UNITS = [
    "g", "kg", "ml", "l", "Stück",
    "TL (flüssig)", "EL (flüssig)",
    "TL (fest)", "EL (fest)"
]

CONVERSION = {
    "TL (flüssig)": ("ml", 5),
    "EL (flüssig)": ("ml", 15),
    "TL (fest)": ("g", 5),
    "EL (fest)": ("g", 12),  # Annäherung
    "kg": ("g", 1000),
    "l":  ("ml", 1000),
}
