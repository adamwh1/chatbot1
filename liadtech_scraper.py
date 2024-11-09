import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


# Function to extract all subpages from liadtech.com website
def extract_all_subpages(url, domain):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all anchor tags with href attributes
        links = set() # using a set to ignore duplicates

        for a in soup.find_all('a', href=True):
            link = urljoin(url, a['href'])  # Convert relative URLs to absolute
            if urlparse(link).netloc == domain:  # Check if the link belongs to the same domain
                links.add(link)
        return links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set()
    except Exception as e:
        print(f"Unexpected error while processing {url}: {e}")
        return set()

# Function to scrape text from a URL and return it as a string
def scrape_page(url):
    try:
        # Get the content of the URL and ensure it is encoded in utf-8 for special characters
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the text
        page_text = soup.get_text(separator='\n', strip=True)

        # Return the scraped text and the URL for saving later
        return url, page_text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return url, None
    except Exception as e:
        print(f"Unexpected error scraping {url}: {e}")
        return url, None

# Function to save scraped text to a file
def save_text_to_file(url, text, save_directory):
    if text is None:
        return

    # Create file name from the URL
    file_name = url.replace('https://', '').replace('/', '_').replace('.', '_')[:50] + '.txt'  # Changed .md to .txt
    file_path = os.path.join(save_directory, file_name)

    try:
        # Save the extracted text to a .txt file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"Text successfully saved to {file_path}")
    except OSError as e:
        print(f"Error writing file {file_path}: {e}")

# Function to scrape the website concurrently
def scrape_website_parallel(url, save_directory, max_workers=5):
    # Ensure the save directory exists
    try:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
    except OSError as e:
        print(f"Error creating directory {save_directory}: {e}")
        return

    try:
        # Get the domain to use it in the extraction process
        domain = urlparse(url).netloc

        # Get all subpages
        subpages = extract_all_subpages(url, domain)
        if not subpages:
            print(f"No subpages found or an error occurred while extracting links from {url}")
            return

        print(f"Found {len(subpages)} subpages.")

        # Use a thread pool to scrape subpages concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            scraped_texts = {executor.submit(scrape_page, link): link for link in subpages}

            for future in as_completed(scraped_texts):
                url, page_text = future.result()
                save_text_to_file(url, page_text, save_directory)

    except Exception as e:
        print(f"Unexpected error during website scraping: {e}")


# Run the scraper ...........
if __name__ == "__main__":

    url = 'https://liadtech.com'
    save_directory = 'data'
    scrape_website_parallel(url, save_directory, max_workers=16)





