# type: ignore

from PIL import Image, ImageDraw, ImageFont

# Function to convert ASCII string to image
size_multiple = (580, 240)
size_single = (580, 112)


def text_to_image(text, image_size=(580, 240)):
    margin = 5
    font_size = 12
    font_path = "scripts/CascadiaMono.ttf"
    background_color = "#2a2e36"
    text_color = "white"
    text_arr = text.split("\n")

    text_width = len(text_arr[0]) * font_size
    text_height = len(text_arr) * font_size

    img_width = text_width + 2 * margin
    img_height = text_height + 2 * margin
    # image_size = (img_width, img_height)
    image = Image.new("RGB", image_size, background_color)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(font_path, font_size)
    text_width = draw.textlength(text_arr[0], font)
    text_height = len(text_arr) * font_size
    text_x = (image_size[0] - text_width) // 2
    text_y = (image_size[1] - text_height) // 2

    # Draw the text on the image
    draw.text((5, 0), text, font=font, fill=text_color)

    return image


# Example usage
multiple = """┌──────┬───────────────────────────┬───────────────┬──────────────┬─────────────┐
│ rank ┆ member                    ┆ num_questions ┆ pct_answered ┆ avg_replies │
│ ---  ┆ ---                       ┆ ---           ┆ ---          ┆ ---         │
│ u32  ┆ str                       ┆ u32           ┆ str          ┆ i64         │
╞══════╪═══════════════════════════╪═══════════════╪══════════════╪═════════════╡
│ 1    ┆ Craig Potts               ┆ 1             ┆ 100.0%       ┆ 1           │
│ 2    ┆ Janet Miller              ┆ 2             ┆ 0.0%         ┆ 1           │
│ 3    ┆ Anthony Jackson           ┆ 1             ┆ 100.0%       ┆ 2           │
│ 4    ┆ Natalie Ramirez           ┆ 4             ┆ 25.0%        ┆ 2           │
│ …    ┆ …                         ┆ …             ┆ …            ┆ …           │
│ 47   ┆ Jill Campbell             ┆ 1             ┆ 0.0%         ┆ 8           │
│ 48   ┆ Michelle Reed             ┆ 1             ┆ 0.0%         ┆ 8           │
│ 49   ┆ Sean Spencer              ┆ 2             ┆ 50.0%        ┆ 9           │
│ 50   ┆ Christopher Sherman       ┆ 1             ┆ 0.0%         ┆ 10          │
└──────┴───────────────────────────┴───────────────┴──────────────┴─────────────┘"""

single = """┌──────┬───────────────────────────┬───────────────┬──────────────┬─────────────┐
│ rank ┆ member                    ┆ num_questions ┆ pct_answered ┆ avg_replies │
│ ---  ┆ ---                       ┆ ---           ┆ ---          ┆ ---         │
│ u32  ┆ str                       ┆ u32           ┆ str          ┆ i64         │
╞══════╪═══════════════════════════╪═══════════════╪══════════════╪═════════════╡
│ 23   ┆ Bruce Glover              ┆ 4             ┆ 50.0%        ┆ 5           │
└──────┴───────────────────────────┴───────────────┴──────────────┴─────────────┘"""
image_multiple = text_to_image(multiple, size_multiple)
image_single = text_to_image(single, size_single)

# Save the image to a file
image_multiple.save("output_image_multiple.png")
image_single.save("output_image_single.png")
