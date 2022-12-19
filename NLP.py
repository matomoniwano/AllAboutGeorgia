import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter # to plot word count graph for EDA later
import nltk # for NLP tasks
nltk.download('stopwords')
nltk.download('wordnet')
import nltk
nltk.download('omw-1.4')
from nltk.corpus import stopwords # for pre-processing of text to remove common words
stopwords = stopwords.words('english')
from nltk.stem import WordNetLemmatizer # for pre-processing of text (lemmatize text, i.e. converting a word to its base form)
from sklearn.feature_extraction.text import TfidfVectorizer # for pre-processing of text
from sklearn.model_selection import train_test_split 
from sklearn.svm import LinearSVC # chosen model to train
from sklearn import metrics # for measuring accuracy
import pickle # to store model 

df_raw = pd.read_csv("ag.csv")
df_raw.head()
df = df_raw[['Category', 'Text']]

# df = df.drop( df.query(" `Category`=='WELLNESS' ").index)
# df = df.drop( df.query(" `Category`=='TEAVEL' ").index)
# df = df.drop( df.query(" `Category`=='STYLE & BEAUTY' ").index)
# df = df.drop( df.query(" `Category`=='PARENTING' ").index)
# df = df.drop( df.query(" `Category`=='FOOD & DRINK' ").index)
# df = df.drop( df.query(" `Category`=='WORLD NEWS' ").index)

categories = df['Category'].unique()
print(categories)
df['Category'].value_counts()

RE_stopwords = r'\b(?:{})\b'.format('|'.join(stopwords)) # stopwords variable was defined at the import section earlier
df['Text'] = df['Text'].str.lower().replace([r'\|', RE_stopwords], ['',''], regex=True) # remove stopwords
df['Text'] = df['Text'].str.replace(r'[^\w\s]+', '').replace('_', '') # remove punctuation
df['Text'] = df['Text'].str.replace('_', '') # remove underscores
df['Text'] = df['Text'].str.replace(r"[0-9]+", "", regex=True)  # remove digits
df['Text'] = df['Text'].str.replace("Georgia", "")
df['Text'] = df['Text'].str.replace("Georgian", "")
df['Text'] = df['Text'].str.replace("Tbilisi", "")
df['Text'] = df['Text'].str.replace(r'\b[a-zA-Z]\b', '', regex=True) 

w_tokenizer = nltk.tokenize.WhitespaceTokenizer()
lemmatizer = nltk.stem.WordNetLemmatizer()

def lemmatize_text(text):
    return [lemmatizer.lemmatize(w) for w in w_tokenizer.tokenize(text)]

df['Text'] = df['Text'].apply(lemmatize_text).str.join(" ")



top_N = 10

for category in categories:
    words = df[df['Category']==category]['Text'].str.cat(sep=' ').split()

    # generate DF out of Counter
    rslt = pd.DataFrame(Counter(words).most_common(top_N),
                        columns=['Word', 'Frequency']).set_index('Word')
    # plot
    rslt.plot.bar(rot=45, width=0.8)
    plt.ylabel('Frequency')
    plt.title(category)
    plt.show()


X = df["Text"]
y = df["Category"]
print(X.head())
print(y.head())

# Create training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, stratify = y)

# Initialize a TfidfVectorizer object: tfidf_vectorizer
tfidf_vectorizer = TfidfVectorizer(sublinear_tf=False, min_df=1, norm='l2', encoding='latin-1', ngram_range=(1,2), stop_words=stopwords)

# Transform the training data: tfidf_train 
tfidf_train = tfidf_vectorizer.fit_transform(X_train)

# Transform the test data: tfidf_test 
tfidf_test = tfidf_vectorizer.transform(X_test)

# Print the last 20 features, notice that they are made up of single words and also phrases of 2 words
features = tfidf_vectorizer.get_feature_names_out()[-20:]
features.sort()
features

svc_classifier = LinearSVC()

# Fit the classifier to the training data
svc_classifier.fit(tfidf_train,y_train)

# Create the predicted categories
pred = svc_classifier.predict(tfidf_test)

# Calculate the accuracy score: score
score = metrics.accuracy_score(y_test, pred)
print(score)

with open('class.pkl', 'wb') as file:
    pickle.dump(svc_classifier, file)
    
with open('vector.pkl', 'wb') as file:
    pickle.dump(tfidf_vectorizer, file)
