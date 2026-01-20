from PIL import Image, ImageDraw
import os

def create_feather_icon(path):
    # Ensure assets dir exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Create a 256x256 image with transparency
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Color: generic Tk blue-ish
    color = (30, 144, 255, 255) # DodgerBlue
    
    # Draw a feather shape (curved spine + vanes)
    # Spine: quadratic curve? We'll approximate with points
    spine_points = []
    for t in range(0, 101):
        # t goes 0 to 100
        # Start bottom-left, end top-right
        x = 50 + t * 1.5      # 50 -> 200
        y = 200 - t * 1.5     # 200 -> 50
        # Add curve
        offset = (50 - abs(t - 50)) * 0.2
        x += offset
        y -= offset
        spine_points.append((x, y))
    
    draw.line(spine_points, fill=color, width=8)

    # Vanes
    for x, y in spine_points[10:-10:2]:
        # Left/Bottom vane
        draw.line([(x, y), (x - 20, y + 25)], fill=color, width=2)
        # Right/Top vane
        draw.line([(x, y), (x + 25, y - 20)], fill=color, width=2)
        
    # Save as ICO with multiple sizes
    img.save(path, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])

if __name__ == "__main__":
    create_feather_icon("assets/feather.ico")
    print("Created assets/feather.ico")
