import os
import re
import json
import pandas as pd

from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from textblob import TextBlob

from google.cloud import bigquery
from google.oauth2 import service_account

service_account_info = {
    "type": "service_account",
    "project_id": "feisty-pottery-284800",
    "private_key_id": os.environ.get('PRIVATE_KEY_ID'),
    "private_key": os.environ.get('PRIVATE_KEY').replace('\\n','\n'),
    "client_email": os.environ.get('CLIENT_EMAIL'),
    "client_id": os.environ.get('CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get('CLIENT_X509_CERT_URL'),
    "universe_domain": "googleapis.com"
}

def open_driver():
    """Open the Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

def close_driver(driver):
    """Close the Chrome WebDriver."""
    driver.quit()

def upload_dataframe_to_bigquery(dataframe, project_id, dataset_id, table_id, credentials_path):
    """
    Deletes all data from a table in BigQuery and then uploads a pandas DataFrame.

    Args:
        dataframe: The pandas DataFrame with the data to upload
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        credentials_path: Path to the credentials.json file
    """

    # Configure credentials
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    # Initialize BigQuery client
    client = bigquery.Client(credentials=credentials, project=project_id)

    # Specify the full table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    print(f"Processing table: {table_ref}")

    # Delete all data from the table
    query = f"DELETE FROM {table_ref} WHERE 1=1"
    print("Deleting existing data...")
    query_job = client.query(query)
    query_job.result()  # Wait for the operation to complete
    dataframe["Date"] = pd.to_datetime(dataframe["Date"])
    print("Data deleted successfully")

    # Convert dictionary columns to bytes if necessary
    for column in dataframe.columns:
        if dataframe[column].apply(lambda x: isinstance(x, dict)).any():
            dataframe[column] = dataframe[column].apply(lambda x: json.dumps(x).encode('utf-8'))

    # Convert list columns to bytes if necessary
    for column in dataframe.columns:
        if dataframe[column].apply(lambda x: isinstance(x, list)).any():
            dataframe[column] = dataframe[column].apply(lambda x: json.dumps(x).encode('utf-8'))

    # Verify the conversion to bytes
    for column in dataframe.columns:
        print(f"Column: {column}")
        print(dataframe[column].head())

    # Upload the DataFrame data
    print("Loading new data...")
    job_config = bigquery.LoadJobConfig(
        # Load options: whether the table should be created, replaced, etc.
        write_disposition="WRITE_APPEND",
    )

    # Perform the load
    job = client.load_table_from_dataframe(
        dataframe, table_ref, job_config=job_config
    )
    job.result()  # Wait for the load to complete

    # Verify results
    table = client.get_table(table_ref)
    print(f"Load completed. The table {table_ref} now has {table.num_rows} rows.")

def remove_date(text):
    """Remove date from the Title text."""
    return ' '.join(text.split()[1:])

def extract_news_details(base_url, max_pages):
    """Extract news details from the given base URL up to the specified number of pages."""

    driver = open_driver()

    page_url = base_url

    # Initialize lists to store the details
    titles, kickers, images, links, dates = [], [], [], [], []

    # Initialize page counter
    page_counter = 0

    while max_pages is None or page_counter < max_pages:
        # Open the URL
        driver.get(page_url)

        # Wait for the elements to be present
        items = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'item_noticias')))

        # Iterate over each element and extract the necessary details
        for item in items:
            try:
                title = item.find_element(By.CLASS_NAME, 'fuente_roboto_slab').text
            except:
                title = None

            try:
                kicker = item.find_element(By.TAG_NAME, 'a').get_attribute('title')
            except:
                kicker = None

            try:
                image = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
            except:
                image = None

            try:
                link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except:
                link = None

            try:
                date = item.find_element(By.CLASS_NAME, 'fecha_item_listado_noticias').text
            except:
                date = None

            if title and kicker and image and link and date:
                titles.append(title)
                kickers.append(kicker)
                images.append(image)
                links.append(link)
                dates.append(date)

        # Check if there is a "Next" button to go to the next page
        try:
            next_button = WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.CLASS_NAME, 'boton_paginador.siguiente')))
            next_button.click()
            page_counter += 1

            # If max_pages is set and reached, break the loop
            if max_pages is not None and page_counter >= max_pages:
                break
        except:
            break
        
    # Close the WebDriver
    driver.quit()
    
    # Create a DataFrame to store the details
    data = {
        'Date': dates,
        'Title': titles,
        'Kicker': kickers,
        'Image': images,
        'Link': links
    }
    df = pd.DataFrame(data)

    return df

def get_category_links():
    """Get category links from the main page."""

    driver = open_driver()

    url = "https://www.yogonet.com/international/"

    # Open the URL
    driver.get(url)

    # Move cursor over the "Categories" tab
    categories_tab = driver.find_element(By.CSS_SELECTOR, '.item_menu.transition_02.tiene_hijos.categorias')
    ActionChains(driver).move_to_element(categories_tab).perform()

    # Select all elements with the class "item_menu hijo"
    items = driver.find_elements(By.CSS_SELECTOR, '.contenedor_items_hijos .item_menu.hijo')

    # Initialize list to store the links
    links = [item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') for item in items]

    close_driver(driver)
    # Return only the links for 15 categories
    return links[:16]

def extract_keywords(text, num_keywords):
    """Extract the most frequent keywords from a given text."""
    combined_text = re.sub(r'[^\w\s]', '', text).lower()

    words = combined_text.split()

    word_counts = Counter(words)

    common_keywords = word_counts.most_common(num_keywords)

    return [keyword for keyword, count in common_keywords]

def post_process_data(df):
    """Perform post-processing on the scraped data."""

    def calculate_readability(text):
        """Calculate readability score using Flesch-Kincaid readability tests."""
        words = text.split()
        num_words = len(words)
        num_sentences = text.count('.') + text.count('!') + text.count('?')
        num_syllables = sum([len(re.findall(r'[aeiouy]+', word.lower())) for word in words])

        if num_words == 0 or num_sentences == 0:
            return 0

        flesch_kincaid_score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
        return flesch_kincaid_score

    def calculate_complexity(text):
        """Calculate title complexity based on average word length and sentence length."""
        words = text.split()
        num_words = len(words)

        if num_words == 0:
            return 0

        avg_word_length = sum(len(word) for word in words) / num_words
        return avg_word_length

    def sentiment_analysis(text):
        """Perform sentiment analysis on the text."""
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    # Extract keywords from all titles (maximum 10)
    keywords_to_check_title = extract_keywords(' '.join(df['Title']), num_keywords=10)
    keywords_to_check_kicker = extract_keywords(' '.join(df['Kicker']), num_keywords=10)

    def keyword_frequency(text, keywords):
        """Count frequency of specific keywords in the text."""
        word_list = text.lower().split()
        keyword_count = {keyword: word_list.count(keyword) for keyword in keywords}
        return keyword_count

    # Word count in Title
    df['Word_Count_Title'] = df['Title'].apply(lambda x: len(x.split()))

    # Word count in Kicker
    df['Word_Count_Kicker'] = df['Kicker'].apply(lambda x: len(x.split()))

    # Character count in Title
    df['Character_Count_Title'] = df['Title'].apply(lambda x: len(x))

    # Character count in Kicker
    df['Character_Count_Kicker'] = df['Kicker'].apply(lambda x: len(x))

    # List of words that start with a capital letter in Kicker
    df['Capital_Words_Kicker'] = df['Kicker'].apply(lambda x: [word for word in x.split() if word.istitle()])

    # Sentiment analysis on Title
    df['Sentiment_Title'] = df['Title'].apply(sentiment_analysis)

    # Sentiment analysis on Kicker
    df['Sentiment_Kicker'] = df['Kicker'].apply(sentiment_analysis)

    # Keyword frequency count in Title
    df['Keyword_Frequency_Title'] = df['Title'].apply(lambda x: keyword_frequency(x, keywords_to_check_title))

    # Keyword frequency count in Kicker
    df['Keyword_Frequency_Kicker'] = df['Kicker'].apply(lambda x: keyword_frequency(x, keywords_to_check_kicker))

    # Readability Score of Title
    df['Readability_Score_Title'] = df['Title'].apply(calculate_readability)

    # Readability Score of Kicker
    df['Readability_Score_Kicker'] = df['Kicker'].apply(calculate_readability)

    # Title complexity based on average word length and sentence length
    df['Title_Complexity'] = df['Title'].apply(calculate_complexity)

    return df

def main():
    """Main function to run the pipeline."""
    # Call the function and display the list of URLs
    urls = get_category_links()

    # # Initialize an empty DataFrame to store combined results
    combined_df = pd.DataFrame() 

    for url in urls:
        df = extract_news_details(url,2)  # Reduce max_pages to 2 for optimization
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    combined_df = post_process_data(combined_df)
    
    # Upload the DataFrame to BigQuery
    upload_dataframe_to_bigquery(combined_df, "feisty-pottery-284800", "news", "news_yogonet", "credentials.json")

if __name__ == "__main__":
    main()