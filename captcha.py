# utils/captcha.py
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

def generate_captcha():
    # Generate random text
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Create image
    width, height = 200, 80
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Add noise
    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=2)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Draw each character with random position and rotation
    x = 10
    for char in captcha_text:
        # Random rotation between -30 and 30 degrees
        angle = random.randint(-30, 30)
        # Create a new image for the character
        char_img = Image.new('RGBA', (40, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((0, 0), char, font=font, fill=(0, 0, 0))
        # Rotate the character
        rotated_char = char_img.rotate(angle, expand=1)
        # Paste the character onto the main image
        image.paste(rotated_char, (x, 10), rotated_char)
        x += 30 + random.randint(-5, 5)
    
    # Save to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_data = buffer.getvalue()
    
    return captcha_text, image_data