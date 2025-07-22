import os
import json
import time
import logging
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
import sys

# Setup
input_dir = "backend/website"
output_dir = "backend/json"
log_dir = "backend/logs"
parsed_log_path = "backend/parsed.log"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# Log file names by date
today = datetime.now().strftime("%Y-%m-%d")
info_log_file = os.path.join(log_dir, f"info_{today}.log")
error_log_file = os.path.join(log_dir, f"error_{today}.log")

# Configure logging
logging.basicConfig(level=logging.INFO)
info_logger = logging.getLogger("info_logger")
error_logger = logging.getLogger("error_logger")

info_handler = logging.FileHandler(info_log_file)
error_handler = logging.FileHandler(error_log_file)

info_formatter = logging.Formatter('%(asctime)s INFO %(message)s')
error_formatter = logging.Formatter('%(asctime)s ERROR %(message)s')

info_handler.setFormatter(info_formatter)
error_handler.setFormatter(error_formatter)

info_logger.addHandler(info_handler)
error_logger.addHandler(error_handler)

start_time = time.time()
info_logger.info("Started parsing process.")

exit_code = 0

# Read already parsed
parsed_files = set()
if os.path.exists(parsed_log_path):
    with open(parsed_log_path, "r", encoding="utf-8") as f:
        parsed_files = set(line.strip() for line in f if line.strip())

try:
    for filename in os.listdir(input_dir):
        if not filename.endswith(".html"):
            continue
        if filename in parsed_files:
            continue

        filepath = os.path.join(input_dir, filename)
        try:
            file_start = time.time()

            with open(filepath, "r", encoding="utf-8") as f:
                html = f.read()

            soup = BeautifulSoup(html, "html.parser")

            # Title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # Price
            price_tag = soup.select_one("dl.ClassifiedDetailSummary-priceRow dd.ClassifiedDetailSummary-priceDomestic")
            price = price_tag.get_text(strip=True) if price_tag else None

            # Description
            desc_tag = soup.find("div", class_="ClassifiedDetailDescription-text")
            description = desc_tag.get_text(" ", strip=True).replace("\n", " ") if desc_tag else None

            # Listing date
            listing_date_tag = soup.select_one("dd.ClassifiedDetailSystemDetails-listData")
            listing_date = listing_date_tag.get_text(strip=True) if listing_date_tag else None

            # Contact info
            email_tag = soup.select_one("a[href^=mailto]")
            email = email_tag.get_text(strip=True) if email_tag else None

            phone_tag = soup.find("p", class_="UserPhoneNumber-phoneText")
            phone = phone_tag.get_text(strip=True) if phone_tag else None

            # Basic Info
            basic_info = {}
            for dt, dd in zip(
                soup.select(".ClassifiedDetailBasicDetails-listTerm"),
                soup.select(".ClassifiedDetailBasicDetails-listDefinition")
            ):
                key = dt.get_text(strip=True)
                value = dd.get_text(" ", strip=True).replace("\n", " ")
                basic_info[key] = value

            location = basic_info.get("Lokacija")
            size_m2 = basic_info.get("Stambena površina")
            num_rooms = basic_info.get("Broj soba")
            property_type = basic_info.get("Tip stana")

            # Property features
            features = []
            feature_sections = soup.select("section.ClassifiedDetailPropertyGroups-group ul.ClassifiedDetailPropertyGroups-groupList")
            for ul in feature_sections:
                for li in ul.select("li"):
                    features.append(li.get_text(strip=True))

            # Image URLs
            image_tags = soup.select("li[data-media-type='image']")
            image_urls = [tag.get("data-large-image-url") for tag in image_tags if tag.get("data-large-image-url")]

            # Data object
            data = {
                "filename": filename,
                "title": title,
                "price": price,
                "location": location,
                "size_m2": size_m2,
                "num_rooms": num_rooms,
                "property_type": property_type,
                "description": description,
                "listing_date": listing_date,
                "email": email,
                "phone": phone,
                "property_features": features,
                "images": image_urls,
            }

            # Save JSON
            json_filename = os.path.splitext(filename)[0] + ".json"
            json_path = os.path.join(output_dir, json_filename)

            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(data, jf, ensure_ascii=False, indent=2)

            # Update parsed log
            with open(parsed_log_path, "a", encoding="utf-8") as pf:
                pf.write(filename + "\n")

            duration = int((time.time() - file_start) * 1000)
            info_logger.info(f"PARSE {filename} SUCCESS {duration}ms")

        except Exception as e:
            duration = int((time.time() - file_start) * 1000)
            snippet = html[:1000].replace("\n", " ") if 'html' in locals() else "[no HTML loaded]"
            error_logger.error(f"PARSE {filename} FAILED {duration}ms\n{traceback.format_exc()}\nHTML SNIPPET:\n{snippet}")
            exit_code = 3
            raise e

except FileNotFoundError as e:
    error_logger.error(f"Configuration error: {str(e)}\n{traceback.format_exc()}")
    exit_code = 1
except Exception as e:
    error_logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
    if exit_code == 0:
        exit_code = 4
finally:
    elapsed = int((time.time() - start_time) * 1000)
    info_logger.info(f"Finished parsing process in {elapsed}ms.")
    sys.exit(exit_code)
