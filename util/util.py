from PIL import Image
from django.core.files import File
from io import BytesIO

def resize_img(image, w=400, h=300):
    """resize image using PIL

    Args:
        image (ImageField): ImageField instance
        w (int, optional): width. Defaults to 400.
        h (int, optional): height. Defaults to 300.

    Returns:
        File: django-friendly Files object
    """
    try:
        with Image.open(image) as img:
            size = (w, h)
            if img.width > size[0] or img.height > size[1]:
                img.convert('RGB')
                img.thumbnail(size)
                # create a BytesIO object
                img_io = BytesIO()
                # save image to BytesIO object
                img.save(img_io, img.format)
                img_io.seek(0)
                # create a django-friendly Files object
                return File(img_io, name=image.name)
    except Exception as er:
        print("img resizing er: ", er)
        return image
        
