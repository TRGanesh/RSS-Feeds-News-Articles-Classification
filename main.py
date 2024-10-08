# Imports
import logging
import feedparser
import configparser
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, String, Text, DateTime, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from nlp_utilities import classify_article


# Set up Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"), 
        logging.StreamHandler() 
    ]
)

def main():
    # Get Credentials from "config.yaml" file using configparser
    config = configparser.ConfigParser()
    config.read('config.yaml')
    logging.info("Configuration file readed")

    DB_USER = config['database']['user']
    DB_PASSWORD = config['database']['password']
    DB_NAME = config['database']['name']

    # MySQL Database configuration
    DATABASE_URI = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}'

    # Initialize SQLAlchemy Base and Session
    Base = declarative_base()
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Define the NewsArticle Model (Table Schema)
    class NewsArticle(Base):
        __tablename__ = 'news_articles'
        
        id = Column(String(255), primary_key=True) # Consider Link as Primary Key
        title = Column(String(255))
        link = Column(String(255), unique=True) 
        description = Column(Text)
        published_date = Column(DateTime)
        category = Column(String(255))

    # Create the table if it doesn't exist
    Base.metadata.create_all(engine)

    # List of Feed URLs
    feed_urls = [
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://qz.com/feed",
        "http://feeds.foxnews.com/foxnews/politics",
        "http://feeds.reuters.com/reuters/businessNews",
        "http://feeds.feedburner.com/NewshourWorld",
        "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml"
    ]

    # Function to clean HTML Content and Extract Plain Text
    def clean_html(text):
        if text:  # Handle NA values
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text()
        return text

    # Function to format the Published Date in Feed,, according to the MySQL DB
    def convert_to_datetime(date_string):
        try:
            pub_date = pd.to_datetime(date_string, errors='coerce')
            
            if pd.notnull(pub_date):
                return pub_date.to_pydatetime()
            else:
                return None 
        except Exception as e:
            logging.error(f"Error converting date: {date_string}, Error: {e}")
            return None
            

    # Function to parse feeds and save into MySQL database
    def parse_feeds(feed_urls):
        # Iterate through each feed URL
        for feed_url in feed_urls:
            try:
                feed = feedparser.parse(feed_url)
                
                # Check if the feed was parsed successfully
                if feed.bozo:
                    logging.warning(f"Parsing error in feed: {feed_url}, bozo_exception: {feed.bozo_exception}")

                    continue
                
                # Iterate over each Entry (article) in the feed
                for entry in feed.entries:
                    title = entry.get("title", "N/A")
                    link = entry.get("link", "N/A")
                    description = entry.get("description", "N/A")
                    pub_date = entry.get("published", "N/A")

                    # Clean HTML Content from the description
                    cleaned_description = clean_html(description)
                    
                    # ****** Have to pass to the classify_article function ******
                    category = classify_article(cleaned_description)
                    
                    # Format 'Published Date' 
                    formatted_pub_date = convert_to_datetime(pub_date)

                    # Check for Duplicates by Link (Since link is Unique)
                    existing_article = session.query(NewsArticle).filter_by(link=link).first()
                    
                    if not existing_article:
                        # Create a new NewsArticle object
                        new_article = NewsArticle(
                            id=link,  # Use link as a Unique Identifier
                            title=title,
                            link=link,
                            description=cleaned_description,
                            published_date=formatted_pub_date,
                            category=category
                        )
                        
                        # Add the new article to the session
                        session.add(new_article)
                        logging.info(f"New article added: {title} from {feed_url}")
                    else:
                        logging.info(f"Duplicate entry found for link: {link}")
                
                # Commit the session to save changes to the database
                try:
                    session.commit()
                    logging.info(f"Data from {feed_url} committed successfully.")

                except exc.SQLAlchemyError as e:
                    logging.error(f"Error during commit: {e}")
                    session.rollback()

            # Handle feed parsing errors
            except ValueError as ve:
                logging.error(f"Feed parsing error: {ve}")
            # Catch any other unforeseen errors
            except Exception as e:
                logging.critical(f"An unexpected error occurred: {e}")

        logging.info("Data from feeds recorded successfully in the database")


    # Call the function with feed URLs
    parse_feeds(feed_urls)

if __name__ == "__main__":
    main()