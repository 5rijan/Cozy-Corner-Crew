import os
import time
import json
import re
import random
import numpy as np
import execjs
import logging
from PIL import Image
from collections import Counter
from urllib.parse import urlparse
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager





def ensure_directory_exists(dir_path):
    """Ensure that a directory exists."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        logging.info(f"Directory ensured: {dir_path}")
    except Exception as e:
        logging.error(f"Error creating directory {dir_path}: {e}")
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
            logging.warning("No elements found on the page for font extraction.")
            return []

        logging.info(f"Total elements found for font extraction: {total_elements}")

        for idx, element in enumerate(elements, start=1):
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
                logging.debug(f"Error extracting font from element {idx}: {e}")
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
        logging.error(f"Error during font metadata extraction: {e}")
        return []
    

def render_font_in_center(driver, font_name, image_size=(800, 600), padding=20):
    """Render the specified font in the center of the page and capture a screenshot."""
    try:
        # Clear the page and inject a div with the font
        js_inject_center = f"""
        document.body.innerHTML = '';  // Clear the page
        var divElement = document.createElement("div");
        divElement.style.fontFamily = "{font_name}";
        divElement.style.fontSize = "60px";
        divElement.style.lineHeight = "1";  // Add sufficient space between lines 
        divElement.style.position = "fixed";
        divElement.style.top = "50%";
        divElement.style.left = "50%";
        divElement.style.transform = "translate(-50%, -50%)";  // Centering the div
        divElement.style.color = "black";
        divElement.style.background = "white";
        divElement.style.padding = "20px";
        divElement.style.textAlign = "center";
        divElement.style.maxWidth = "90%";
        divElement.style.wordWrap = "break-word";
        divElement.style.boxSizing = "border-box";
        divElement.innerHTML = "{font_name} <br><br> A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9";
        document.body.style.backgroundColor = "white";  // Set whole page background to white
        document.body.appendChild(divElement);
        return divElement;
        """
        driver.execute_script(js_inject_center)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "div"))
        )
        div = driver.find_element(By.TAG_NAME, "div")

        # Adjust font size to fit within image dimensions, with proportional scaling
        max_width, max_height = image_size
        font_size = 48  

        while True:
            js_update_font_size = f"arguments[0].style.fontSize = '{font_size}px';"
            driver.execute_script(js_update_font_size, div)
            time.sleep(0.5)  
            bounding_rect = driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {width: rect.width, height: rect.height};
            """, div)

            current_width = bounding_rect['width'] + 2 * padding
            current_height = bounding_rect['height'] + 2 * padding
            if current_width > max_width or current_height > max_height:
                scale_factor = min(max_width / current_width, max_height / current_height)
                font_size = int(font_size * scale_factor)
            else:
                break
            if font_size <= 10:
                logging.warning(f"Could not fit the text for font '{font_name}' without squishing.")
                break
        screenshot_path = "./temp_font_image.png"
        div.screenshot(screenshot_path)

        if not os.path.exists(screenshot_path):
            logging.error(f"Failed to capture screenshot for font '{font_name}'.")
            return None
        img = Image.open(screenshot_path)
        img = crop_image_to_content(img)

        os.remove(screenshot_path)
        return img

    except TimeoutException:
        logging.error(f"Timeout while rendering font '{font_name}'.")
        return None
    except NoSuchElementException:
        logging.error(f"Div element for font '{font_name}' not found.")
        return None
    except Exception as e:
        logging.error(f"Error rendering font '{font_name}': {e}")
        return None

def crop_image_to_content(img, threshold=250):
    """
    Crop the image to the content by removing white borders.
    :param img: PIL Image object
    :param threshold: Pixel value above which a pixel is considered white
    :return: Cropped PIL Image object
    """
    try:
        grayscale = img.convert("L")
        bw = grayscale.point(lambda x: 0 if x < threshold else 1, "1")
        bbox = bw.getbbox()
        if bbox:
            return img.crop(bbox)
        else:
            return img  # Return original if no content detected
    except Exception as e:
        logging.error(f"Error cropping image: {e}")
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
                new_data.append((255, 255, 255, 0)) 
            else:
                new_data.append(item)

        img.putdata(new_data)
        output_path = os.path.join(save_dir, f"{font_name.replace(' ', '_')}.png")
        img.save(output_path, format="PNG")

        logging.info(
            f"Enhanced and transparent PNG saved for font '{font_name}' at: {output_path}"
        )
    except Exception as e:
        logging.error(f"Error enhancing/saving image for font '{font_name}': {e}")


def extract_fonts(driver, fonts_dir):
    """Extract fonts, render them, and save images."""
    sorted_fonts = extract_font_metadata(driver)
    if not sorted_fonts:
        logging.warning("No fonts extracted.")
        return

    logging.info("\nFont Usage Percentages:")
    for font_name, percentage in sorted_fonts:
        logging.info(f"{font_name}: {percentage:.2f}%")
        try:
            cropped_img = render_font_in_center(driver, font_name)
            if cropped_img:
                enhance_and_save_image(cropped_img, font_name, fonts_dir)
            else:
                logging.warning(f"Skipping saving image for font '{font_name}' due to previous errors.")
        except Exception as e:
            logging.error(f"Error processing font '{font_name}': {e}")

def load_ntc_js():
    """Load and compile the ntc.js script."""
    with open('ntc.js', 'r') as file:
        ntc_js_code = file.read()
    return execjs.compile(ntc_js_code)

def get_color_name(ntc_context, hex_color):
    """Get color name from ntc.js using ExecJS."""
    name_result = ntc_context.call('ntc.name', hex_color)
    return name_result[1]  

def get_top_10(image_array):
    """Get the top 10 most frequent colors in the image, with pixel skipping for speed."""
    # Skip every 3rd pixel for faster processing
    reshaped_array = image_array[::4, ::4].reshape(-1, image_array.shape[-1])
    hex_colors = ["#{:02x}{:02x}{:02x}".format(*color) for color in reshaped_array]
    hex_frequency = Counter(hex_colors)
    top_colors = hex_frequency.most_common(10)
    colors = [color for color, count in top_colors]
    
    return colors


def analyze_image_colors(screenshot_path, color_dir):
    """Analyze colors from the screenshot by finding the top 10 frequent colors."""
    try:
        if not os.path.exists(screenshot_path):
            logging.error(f"Screenshot not found at {screenshot_path}. Cannot perform image color analysis.")
            return

        img = Image.open(screenshot_path)
        img = img.convert("RGB")  
        image_array = np.array(img)  
        ntc_context = load_ntc_js()
        top_colors = get_top_10(image_array)
        image_color_data = []
        if top_colors:
            for hex_color in top_colors:
                color_name = get_color_name(ntc_context, hex_color)
                image_color_data.append({
                    "hex": hex_color,
                    "name": color_name
                })
        image_output_file_path = os.path.join(color_dir, "image_analysis.json")
        with open(image_output_file_path, "w") as json_file:
            json.dump(image_color_data, json_file, indent=2)

        logging.info(f"Image color analysis completed. Overview saved to: {image_output_file_path}")

    except Exception as e:
        logging.error(f"Error during image color analysis: {e}")


def save_fullpage_screenshot(driver, save_path):
    """Save a full-page screenshot of the webpage."""
    try:
        total_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, document.body.offsetWidth, document.documentElement.offsetWidth, document.body.clientWidth, document.documentElement.clientWidth);")
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, document.body.offsetHeight, document.documentElement.offsetHeight, document.body.clientHeight, document.documentElement.clientHeight);")
        driver.set_window_size(total_width, total_height)
        time.sleep(5)  
        driver.save_screenshot(save_path)
        logging.info(f"Full-page screenshot saved at: {save_path}")

    except WebDriverException as e:
        logging.error(f"WebDriverException during screenshot capture: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during screenshot capture: {e}")

def features(url):
    """Main function to extract fonts and analyze colors."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = "http://" + url
        parsed_url = urlparse(url)
    folder_name = (
        parsed_url.netloc.replace(".", "_") + parsed_url.path.replace("/", "_")
    )
    folder_name = folder_name.strip("_")  
    logging.info(f"Folder Name: {folder_name}")

    # Define main save directory inside static/database
    site_dir = os.path.join(os.getcwd(), "static", "database", folder_name)
    try:
        ensure_directory_exists(site_dir)
    except Exception as e:
        logging.error(f"Failed to create main directory '{site_dir}': {e}")
        return None
    logging.info(f"Save Directory: {site_dir}")

    # Define subdirectories
    fonts_dir = os.path.join(site_dir, "fonts")
    color_dir = os.path.join(site_dir, "color")
    try:
        ensure_directory_exists(fonts_dir)
        ensure_directory_exists(color_dir)
    except Exception as e:
        logging.error(f"Failed to create subdirectories: {e}")
        return None
    screenshot_path = os.path.join(site_dir, "screenshot.png")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )
        logging.info("Chrome WebDriver initialized successfully.")
    except WebDriverException as e:
        logging.error(f"Error initializing Chrome WebDriver: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error initializing WebDriver: {e}")
        return None

    try:
        driver.set_page_load_timeout(30)  
        driver.get(url)
        logging.info(f"Page loaded successfully: {url}")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except TimeoutException:
        logging.error(f"Page load timed out for URL: {url}")
        driver.quit()
        return None
    except WebDriverException as e:
        logging.error(f"WebDriverException during page load: {e}")
        driver.quit()
        return None
    except Exception as e:
        logging.error(f"Unexpected error during page load: {e}")
        driver.quit()
        return None

    try:
        save_fullpage_screenshot(driver, screenshot_path)

        extract_fonts(driver, fonts_dir)

    except Exception as e:
        logging.error(f"An error occurred during feature extraction: {e}")

    finally:
        try:
            driver.quit()
            logging.info("WebDriver closed successfully.")
        except Exception as e:
            logging.error(f"Error closing WebDriver: {e}")

    try:
        analyze_image_colors(screenshot_path, color_dir)
    except Exception as e:
        logging.error(f"An error occurred during image color analysis: {e}")

    return site_dir

def load_features(url):
    return features(url)
