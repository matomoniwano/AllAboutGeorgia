## All About Georgia Auto Publisher
This script automates the process of publishing articles from a Georgian news website, agenda.ge, to a Japanese website, 00.ge. The script follows the following flow:

- Accesses agenda.ge to detect all the news articles published on the current date.
- Selects the top 5 articles based on the number of texts in the article.
- Logs in to the wordpress admin page for 00.ge.
- Publishes each selected article on the Japanese website every day at 11pm in Georgian time.

### Requirements
The script makes use of various libraries including selenium, beautifulsoup, and GoogleTranslator. It also utilizes pickle to load in pre-trained machine learning models for natural language processing and article categorization.

### Note
Some lines of code are commented out and may not be necessary for the functioning of the script.
