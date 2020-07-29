#!/usr/bin/env python2
import facebook
import twitter
import nltk 
import string
from nltk.corpus import stopwords
from nltk import BigramAssocMeasures
from collections import Counter
from prettytable import PrettyTable
from vaderSentiment.vaderSentiment import sentiment as vaderSentiment

import requests
from bs4 import BeautifulSoup
import russell as ru

nltk.download("stopwords")
stopwordset = set(stopwords.words('english'))

# use a file so don't forget to remove for submissions
fid = open("TwitterCreds.txt")
CONSUMER_KEY = fid.readline().rstrip('\n')
CONSUMER_SECRET = fid.readline().rstrip('\n')
OATHU_TOKEN = fid.readline().rstrip('\n')
OATHU_TOKEN_SECRET = fid.readline().rstrip('\n')

auth = twitter.oauth.OAuth(OATHU_TOKEN, OATHU_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
tw = twitter.Twitter(auth=auth)

fid = open("FacebookCreds.txt",'r')
ACCESS_TOKEN = fid.readline().rstrip("\n")

# remove the unicode from text
def removeUnicode(text):
    asciiText = ""
    for char in text:
        if ord(char) < 128:
            asciiText = asciiText + char

    return asciiText

############# TWITTER FUNCTIONS ######################
# retrieve the tweets base off a given hashtag
def getTweets(hashtag):
    tweets = tw.search.tweets(q=hashtag, count=25, lang='en')
    nextSet = tweets['search_metadata']['next_results']
    next_maxID = nextSet.split('max_id=')[1].split('&')[0]
    nextTweets = tw.search.tweets(q=hashtag, count=25, lang='en', max_id=next_maxID)
    return tweets['statuses'] + nextTweets['statuses']


# lexical_diversity(message) takes the message of a tweet and return the lexical
# diversity calculated as the length of the set of all unique words divided by
# the length of the set of all words
def lexical_diversity(message):
    all_words = [word for word in message if word not in stopwordset]
    return float(len(set(all_words))) / len(all_words)


# print_statistics(tweets) takes an array of tweets (statueses), and prints out
# various statistics for each tweet; specificallt, the actual message, the
# favorite count, the retweet_count, the lexical_diversity, and the sentiment
# analysis
def print_statistics(tweets):
    for item in tweets:
        print "======================"
        print item["text"]
        print "Favorite Count: ", item["favorite_count"]
        print "Retweets: ", item["retweet_count"]
        print "Lexical Diversity", lexical_diversity(item["text"])
        print "Sentiment Analysis:", vaderSentiment(item["text"].encode('utf-8'))['compound']

        # not 100% sure this'll work
        if item["user"]:
            print "Username: ", item["user"]["screen_name"].encode('utf-8')
            print "Description: ", item["user"]["description"].encode('utf-8')
            print "Location: ", item["user"]["location"].encode('utf-8')
            
# pretty_table(tweets) takes in an array of tweets (statuses), and returns a
# table that contains word counts of all tweets in the corpus
# Stop words are removed, and sparse words (only used once) are removed from
# the table
def pretty_table(tweets):
    all_words = []
    for item in tweets:
        for word in item["text"].split():
            if word.lower() not in stopwordset:
                 all_words.append(word.lower())

    pt = PrettyTable(field_names=["Word", "Count"])
    count = Counter(all_words)
    sort_count = sorted(count.items(), key=lambda pair: pair[1], reverse=True)
    for row in sort_count:
        if row[1] > 1:
            pt.add_row(row)
    return pt
############## END TWITTER FUNCTIONS ######################


############### WEBPAGE FUNCTIONS ###################
# get the text from a website using the 'p' tags
def getWebpageText(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.text,'html5lib')
    paras = soup.find_all('p')
    # maybe search other tags?
    data = ""
    for para in paras:
        data = data + para.text
    return data


def sentenceSummary(data):
    # Three sentence summary (#3 of grading rubric)
    summary = ru.summarize(data)
    print "----- Three sentence summary of the article -----"
    for sent in summary['top_n_summary']:
        print removeUnicode(sent)

# return n bigrams from the input text
def bigrams(text, n):
    removeUnicode(text)
    bigWords = nltk.tokenize.word_tokenize(text)
    search = nltk.BigramCollocationFinder.from_words(bigWords)
    search.apply_freq_filter(2)
    return search.nbest(BigramAssocMeasures.jaccard, n)

# return a modified version of text with all punctuation removed
def removePunctuation(text):
    full_text = ""
    for char in text:
        if char not in string.punctuation:
            full_text += char
        elif char != "'":
            full_text += " "
    return full_text

# return a string that contains stopwords removed from the input string text
def removeStopWords(text):
    return ' '.join(word.lower() for word in text.split() if not word.lower() in stopwordset)

############### END WEBPAGE FUNCTION ################################

# Main Report Functions
# Run a twitter report
def twitterReport(hashtag):
    tweets = getTweets(hashtag)
    print_statistics(tweets)

# Run a facebook report
def facebookReport(id):
    fb = facebook.GraphAPI(ACCESS_TOKEN)
    d_posts = fb.get_connections(id, 'posts')
    for i in range(10):
        post = d_posts['data'][i]
        postText = post['message']
        vs = vaderSentiment(postText.encode('utf-8'))
        words = postText.split()
        lexicalDiversity = len(set(words))*1.0/len(words)
        print 'Post Text:', removeUnicode(postText)
        print 'Lexical Diversity:', lexicalDiversity
        print 'Sentiment:', vs['compound']
        print '================================================\n'
        
# run a webpage report
def webpageReport(url):
    text = removeStopWords(getWebpageText(url))
    for bigram in bigrams(removePunctuation(text), 5):
        print str(bigram[0]).encode('utf-8'), " ", str(bigram[1]).encode('utf-8')
    print sentenceSummary(text)
    
def main():
    print "\n\n*************************TWITTER***************************"
    twitterReport("@TeslaMotors")

    print "\n\n**************************FACEBOOK*********************************"
    facebookReport('tesla')

    print "\n\n**************************WEBPAGE*********************************"
    webpageReport("https://www.tesla.com/about")
    print
    webpageReport("https://www.tesla.com/blog")

main()
