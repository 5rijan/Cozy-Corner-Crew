import os
import time
import json
import re
from urllib.parse import urlparse

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from webdriver_manager.chrome import ChromeDriverManager
from colorthief import ColorThief


def ensure_directory_exists(dir_path):
    """Ensure that a directory exists."""
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {dir_path}: {e}")
        raise


def rgba_to_hex(rgba):
    """Convert RGBA color to HEX format."""
    match = re.search(
        r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+(?:\.\d+)?)\)', rgba
    )
    if match:
        r, g, b, a = match.groups()
        r, g, b = map(int, [r, g, b])
        # Convert alpha to integer (0-255)
        a = int(float(a) * 255)
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)  # Ignore alpha
    return rgba  # Return original if no match


def extract_font_metadata(driver):
    """Extract font usage metadata from the webpage."""
    font_usage_count = {}
    js_script = (
        "return window.getComputedStyle(arguments[0], null).getPropertyValue('font-family');"
    )

    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "*")
        total_elements = len(elements)
        if total_elements == 0:
            print("No elements found on the page for font extraction.")
            return []

        for element in elements:
            try:
                font_family = driver.execute_script(js_script, element)
                if font_family:
                    # Clean and extract the primary font
                    clean_font_family = font_family.strip().strip('"').split(",")[0].strip().strip(
                        '"'
                    ).strip("'")
                    if clean_font_family in font_usage_count:
                        font_usage_count[clean_font_family] += 1
                    else:
                        font_usage_count[clean_font_family] = 1
            except Exception as e:
                print(f"Error extracting font from element: {e}")
                continue

        font_usage_percentage = {
            font: (count / total_elements) * 100
            for font, count in font_usage_count.items()
        }
        sorted_fonts = sorted(
            font_usage_percentage.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_fonts

    except Exception as e:
        print(f"Error during font metadata extraction: {e}")
        return []


def render_font_in_center(driver, font_name):
    """Render the specified font in the center of the page and capture a screenshot."""
    js_inject_center = f"""
    document.body.innerHTML = '';  // Clear the page
    var divElement = document.createElement("div");
    divElement.style.fontFamily = "{font_name}";
    divElement.style.fontSize = "48px";
    divElement.style.position = "fixed";
    divElement.style.top = "50%";
    divElement.style.left = "50%";
    divElement.style.transform = "translate(-50%, -50%)";  // Centering the div
    divElement.style.color = "black";
    divElement.style.background = "white";
    divElement.style.padding = "20px";
    divElement.innerHTML = "{font_name} <br><br> A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9";
    document.body.style.backgroundColor = "white";  // Set whole page background to white
    document.body.appendChild(divElement);
    return divElement;
    """
    try:
        # Inject the div and get a reference to it
        driver.execute_script(js_inject_center)
        time.sleep(1)  # Wait for the page to render

        # Locate the div element
        div = driver.find_element(By.TAG_NAME, "div")

        # Capture screenshot of the div element only
        screenshot_path = "./temp_font_image.png"
        div.screenshot(screenshot_path)

        if not os.path.exists(screenshot_path):
            print(f"Failed to capture screenshot for font '{font_name}'.")
            return None

        # Open the screenshot and optionally crop it if necessary
        img = Image.open(screenshot_path)

        # Crop the image to remove extra whitespace
        img = crop_image_to_content(img)

        os.remove(screenshot_path)
        return img

    except Exception as e:
        print(f"Error rendering font '{font_name}': {e}")
        return None


def crop_image_to_content(img, threshold=250):
    """
    Crop the image to the content by removing white borders.
    :param img: PIL Image object
    :param threshold: Pixel value above which a pixel is considered white
    :return: Cropped PIL Image object
    """
    try:
        # Convert image to grayscale
        grayscale = img.convert("L")
        # Create a binary image where white pixels are 1 and others are 0
        bw = grayscale.point(lambda x: 0 if x < threshold else 1, "1")
        # Get bounding box
        bbox = bw.getbbox()
        if bbox:
            return img.crop(bbox)
        else:
            return img  # Return original if no content detected
    except Exception as e:
        print(f"Error cropping image: {e}")
        return img  # Return original if cropping fails


def enhance_and_save_image(img, font_name, save_dir):
    """Enhance the image by making white pixels transparent and save it."""
    try:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        data = img.getdata()
        new_data = []
        white_threshold = 200
        for item in data:
            if (
                item[0] > white_threshold
                and item[1] > white_threshold
                and item[2] > white_threshold
            ):
                new_data.append((255, 255, 255, 0))  # Make white pixels transparent
            else:
                new_data.append(item)

        img.putdata(new_data)
        output_path = os.path.join(save_dir, f"{font_name.replace(' ', '_')}.png")
        img.save(output_path, format="PNG")

        print(
            f"Enhanced and transparent PNG saved for font '{font_name}' at: {output_path}"
        )
    except Exception as e:
        print(f"Error enhancing/saving image for font '{font_name}': {e}")


def extract_fonts(driver, fonts_dir):
    """Extract fonts, render them, and save images."""
    sorted_fonts = extract_font_metadata(driver)
    if not sorted_fonts:
        print("No fonts extracted.")
        return

    print("\nFont Usage Percentages:")
    for font_name, percentage in sorted_fonts:
        print(f"{font_name}: {percentage:.2f}%")
        try:
            cropped_img = render_font_in_center(driver, font_name)
            if cropped_img:
                enhance_and_save_image(cropped_img, font_name, fonts_dir)
            else:
                print(f"Skipping saving image for font '{font_name}' due to previous errors.")
        except Exception as e:
            print(f"Error processing font '{font_name}': {e}")


def analyze_image_colors(screenshot_path, color_dir):
    """Analyze colors from the screenshot using ColorThief and save the analysis."""
    try:
        if not os.path.exists(screenshot_path):
            print(f"Screenshot not found at {screenshot_path}. Cannot perform image color analysis.")
            return

        color_thief = ColorThief(screenshot_path)

        # Get the dominant color
        dominant_color = color_thief.get_color(quality=1)

        # Get a color palette of the top 10 colors
        palette = color_thief.get_palette(color_count=10, quality=1)

        # Convert dominant color and palette to hex format
        dominant_color_hex = "#{:02x}{:02x}{:02x}".format(*dominant_color)
        palette_hex = ["#{:02x}{:02x}{:02x}".format(*color) for color in palette]

        # Prepare color data for saving
        image_color_data = {
            "dominant_color": dominant_color_hex,
            "palette": palette_hex,
        }

        # Save the image color analysis to a JSON file
        image_output_file_path = os.path.join(color_dir, "image_analysis.json")
        with open(image_output_file_path, "w") as json_file:
            json.dump(image_color_data, json_file, indent=2)

        print(
            f"Image color analysis completed. Overview saved to: {image_output_file_path}"
        )

    except Exception as e:
        print(f"Error during image color analysis: {e}")


def save_fullpage_screenshot(driver, save_path):
    """Save a full-page screenshot of the webpage."""
    try:
        # Calculate total width and height
        total_width = driver.execute_script("return document.body.scrollWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(total_width, total_height)
        time.sleep(2)  # Wait for the window to resize

        driver.save_screenshot(save_path)
        print(f"Full-page screenshot saved at: {save_path}")

    except WebDriverException as e:
        print(f"WebDriverException during screenshot capture: {e}")
    except Exception as e:
        print(f"Unexpected error during screenshot capture: {e}")


def features(url):
    """Main function to extract fonts and analyze colors."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = "http://" + url
        parsed_url = urlparse(url)

    # Create a safe folder name
    folder_name = (
        parsed_url.netloc.replace(".", "_") + parsed_url.path.replace("/", "_")
    )
    folder_name = folder_name.strip("_")  # Remove leading/trailing underscores
    print("Folder Name:", folder_name)

    # Define main save directory inside static/database
    site_dir = os.path.join(os.getcwd(), "static", "database", folder_name)
    try:
        ensure_directory_exists(site_dir)
    except Exception as e:
        print(f"Failed to create main directory '{site_dir}': {e}")
        return None
    print("Save Directory:", site_dir)

    # Define subdirectories
    fonts_dir = os.path.join(site_dir, "fonts")
    color_dir = os.path.join(site_dir, "color")
    try:
        ensure_directory_exists(fonts_dir)
        ensure_directory_exists(color_dir)
    except Exception as e:
        print(f"Failed to create subdirectories: {e}")
        return None

    # Define screenshot path
    screenshot_path = os.path.join(site_dir, "screenshot.png")

    # Set up Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )
    except WebDriverException as e:
        print(f"Error initializing Chrome WebDriver: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error initializing WebDriver: {e}")
        return None

    try:
        driver.set_page_load_timeout(10)  # Set timeout for page load
        driver.get(url)
        driver.implicitly_wait(5)  # Wait for the page to load

    except TimeoutException:
        print(f"Page load timed out for URL: {url}")
        driver.quit()
        return None
    except WebDriverException as e:
        print(f"WebDriverException during page load: {e}")
        driver.quit()
        return None
    except Exception as e:
        print(f"Unexpected error during page load: {e}")
        driver.quit()
        return None

    try:
        # 1. Capture full-page screenshot
        save_fullpage_screenshot(driver, screenshot_path)

        # 2. Extract fonts and save images
        extract_fonts(driver, fonts_dir)

    except Exception as e:
        print(f"An error occurred during feature extraction: {e}")

    finally:
        try:
            driver.quit()
            print("WebDriver closed successfully.")
        except Exception as e:
            print(f"Error closing WebDriver: {e}")

    try:
        # 3. Perform image color analysis
        analyze_image_colors(screenshot_path, color_dir)
    except Exception as e:
        print(f"An error occurred during image color analysis: {e}")

    return site_dir


def load_features(url):
    return features(url)

