from PIL import Image

img = Image.open("res/anki_ico.png").convert("RGBA")  # mets ton PNG source ici
img.save(
    "res/anki_ico.ico",
    sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
)
