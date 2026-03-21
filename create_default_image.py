from PIL import Image, ImageDraw, ImageFont
import os

def create_contact_image():
    # Create a new image with a white background
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a circle for the head
    draw.ellipse((50, 20, 150, 120), fill='lightgray')
    
    # Draw a body
    draw.rectangle((75, 120, 125, 180), fill='lightgray')
    
    # Save the image
    os.makedirs('static/images', exist_ok=True)
    img.save('static/images/contact.png')

if __name__ == '__main__':
    create_contact_image() 