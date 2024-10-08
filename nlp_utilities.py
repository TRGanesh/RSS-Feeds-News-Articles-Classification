import re
import nltk
from nltk import ngrams
from nltk.corpus import stopwords

# Download NLTK stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))


# Function to load keywords from file
def load_keywords(file_path):
    """Loading keywords from a file, converting them to lowercase, and returning a set of terms."""
    with open(file_path, 'r') as file:
        keywords = file.read().splitlines()
    
    keywords = [keyword.lower() for keyword in keywords]
    return set(keywords)


# Loading keyword sets
natural_disaster_terms = load_keywords('Corpus/natural disaster terms.txt')
natural_disaster_unique_terms = load_keywords('Corpus/natural disaster unique terms.txt')
positive_terms = load_keywords('Corpus/positive terms.txt')
positive_unique_terms = load_keywords('Corpus/positive unique terms.txt')
protest_terms = load_keywords('Corpus/protest terms.txt')
protest_unique_terms = load_keywords('Corpus/protest unique terms.txt')
terrorism_terms = load_keywords('Corpus/Terrorism terms.txt')
terrorism_unique_terms = load_keywords('Corpus/Terrorism unique terms.txt')


def preprocess_text(text):
    # Check if the input is a string
    if not isinstance(text, str):
        return []  # Return an empty list if input is not a string
    
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Removing punctuation and numbers
    
    text = text.lower()
    tokens = text.split()
    
    tokens = [token for token in tokens if token not in stop_words]

    return tokens


# Function to get N-Grams (Bi-Gram && Tri-Gram)
def get_ngrams(tokens, n=2):
    return list(ngrams(tokens, n))

# Classification function based on Keyword Matching, N-Grams, and Normalized Scoring
def classify_article(text, threshold=0.0003):
    """
    Classifying an article into a category based on normalized keyword matching.
    """
    # Check if text is None or empty
    if not text:
        return 'NA'
    
    tokens = preprocess_text(text)
    
    # Initializing scores for each category
    scores = {
        'Terrorism': 0,
        'Protest': 0,
        'Natural Disasters': 0,
        'Positive/Uplifting': 0,
    }

    # Counting total keywords for Normalization
    total_keywords = {
        'Terrorism': len(terrorism_terms) + len(terrorism_unique_terms),
        'Protest': len(protest_terms) + len(protest_unique_terms),
        'Natural Disasters': len(natural_disaster_terms) + len(natural_disaster_unique_terms),
        'Positive/Uplifting': len(positive_terms) + len(positive_unique_terms),
    }

    # Counting keyword matches for each category
    scores['Terrorism'] += sum(1 for token in tokens if token in terrorism_terms or token in terrorism_unique_terms)
    scores['Protest'] += sum(1 for token in tokens if token in protest_terms or token in protest_unique_terms)
    scores['Natural Disasters'] += sum(1 for token in tokens if token in natural_disaster_terms or token in natural_disaster_unique_terms)
    scores['Positive/Uplifting'] += sum(1 for token in tokens if token in positive_terms or token in positive_unique_terms)

    # Use Bi-Gram and Tri-Gram matching to improve classification
    bigrams = get_ngrams(tokens, 2)
    trigrams = get_ngrams(tokens, 3)

    scores['Terrorism'] += sum(1 for bigram in bigrams if ' '.join(bigram) in terrorism_terms or ' '.join(bigram) in terrorism_unique_terms)
    scores['Protest'] += sum(1 for bigram in bigrams if ' '.join(bigram) in protest_terms or ' '.join(bigram) in protest_unique_terms)
    scores['Natural Disasters'] += sum(1 for bigram in bigrams if ' '.join(bigram) in natural_disaster_terms or ' '.join(bigram) in natural_disaster_unique_terms)
    scores['Positive/Uplifting'] += sum(1 for bigram in bigrams if ' '.join(bigram) in positive_terms or ' '.join(bigram) in positive_unique_terms)

    scores['Terrorism'] += sum(1 for trigram in trigrams if ' '.join(trigram) in terrorism_terms or ' '.join(trigram) in terrorism_unique_terms)
    scores['Protest'] += sum(1 for trigram in trigrams if ' '.join(trigram) in protest_terms or ' '.join(trigram) in protest_unique_terms)
    scores['Natural Disasters'] += sum(1 for trigram in trigrams if ' '.join(trigram) in natural_disaster_terms or ' '.join(trigram) in natural_disaster_unique_terms)
    scores['Positive/Uplifting'] += sum(1 for trigram in trigrams if ' '.join(trigram) in positive_terms or ' '.join(trigram) in positive_unique_terms)
    
    # Print exact scores for each category
    # print("Exact Category Scores:")
    # for category, score in scores.items():
        # print(f"{category}: {score:.2f}")
    
    # Normalizing the Scores,, by dividing with total_keywords of that category
    normalized_scores = {category: (score / total_keywords[category]) for category, score in scores.items()}
    
    # Print exact normalized scores for each category
    # print("Normalized Category Scores:")
    # for category, score in normalized_scores.items():
        # print(f"{category}: {score:.5f}")

    # Classifying as "Others" based on Normalized Scores
    max_normalized_score = max(normalized_scores.values())

    if max_normalized_score < threshold:
        # print("All normalized scores are below the threshold, classifying as 'Others'")
        return 'Others'

    if len([score for score in normalized_scores.values() if score >= threshold]) == 0:
        # print("No category meets the minimum normalized score threshold, classifying as 'Others'")
        return 'Others'

    # Prioritize categories if there's a tie: Terrorism > Protest > Natural Disasters > Positive/Uplifting
    priority = ['Terrorism', 'Protest', 'Natural Disasters', 'Positive/Uplifting']
    top_score = max(normalized_scores.values())
    top_categories = [category for category, score in normalized_scores.items() if score == top_score]

    for category in priority:
        if category in top_categories:
            if category == 'Terrorism' or category == 'Protest':
                return "Terrorism/Protest/Politicalunrest/Riot"
            return category