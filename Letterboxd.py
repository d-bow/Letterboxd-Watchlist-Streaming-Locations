#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 19:27:02 2018

@author: Drew Bowman
"""

import urllib.request
import tqdm
import re
from datetime import datetime


# Get HTML from webpage
def getPage(url):
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
        response = urllib.request.urlopen(request).read().decode('utf-8')
        return response
    except urllib.error.HTTPError as err:
        return
    except:
        return
    
# Get stream information from Decider.com
def getStreamsDecider(htmlData):
    streaming_options = []
    pattern = 'target="_blank" class="(.*?)">\n\t*<picture>\n\t*<source ' + \
              'srcset="https:\/\/images.gowatchit.com\/providers\/original\/(.*?)" media'
    stream_data = re.findall(pattern, htmlData)
    for stream in stream_data:
        if stream[0] == "Amazon" and stream[1] == "pf_16_dark_logo.png" and include_Prime:
            streaming_options.append("Amazon Prime")
        elif stream[0] == "Netflix" and include_Netflix:
            streaming_options.append(stream[0])
        elif stream[0] == "Hulu" and include_Hulu:
            streaming_options.append(stream[0])
        
    return streaming_options

# Get movies from Letterboxd page
def getMovies(htmlData):
    movies = []
    moviePattern = 'data-film-slug="\/film\/(.*?)\/"(.*?)alt="(.*?)"\/><span ' + \
                   'class="frame"><span class="frame-title"><\/span><\/span> <\/div>'
    
    movie_data = re.findall(moviePattern, htmlData)
    for movie in movie_data:
        cleaned_title = movie[0]
        nice_title = movie[2]
        both = [cleaned_title, nice_title]
        movies.append(both)
    
    return movies

# Get list of all Letterboxd watchlist URLs for a given account
def getWatchlistURLS(watchlistURL):
    urls = []
    count = 0
    nextPagePattern = 'Next(.*?)<\/div>'
    
    next_exists = True
    while next_exists:
        count += 1
        url = watchlistURL + "/page/" + str(count) + "/"
        urls.append(url)
        
        htmlData = getPage(url)
        page_data = re.findall(nextPagePattern, htmlData)
        if page_data[0] == "</span>":
            next_exists = False
    return urls

# Reverse the list so movies are sorted by oldest additions first
def reverseList(list_to_reverse):
    new_list = []
    for item in list_to_reverse:
        new_list = [item] + new_list
    return new_list

# Get the length of the longest movie title
def getMaxTitle(list_of_movies):
    max_length = 0
    for movie in list_of_movies:
        mov_len = len(movie[1])
        if mov_len > max_length:
            max_length = mov_len
    return max_length

# Pad the string to be max_length characters long
def padTitle(title, max_length):
    padded = title
    while len(padded) < max_length:
        padded += " "
    return padded

def punctuate_list(list_to_punct, or_and):
    output = ""
    
    if len(list_to_punct) == 1:
        output = str(list_to_punct[0])
    elif len(list_to_punct) == 2:
        output = str(list_to_punct[0]) + " " + or_and + " " + str(list_to_punct[1])
    else:
        for item in list_to_punct:
            if item != list_to_punct[0]:
                output += ", "
            if item == list_to_punct[-1]:
                output += or_and + " "
            output += str(item)
    return output
        

# Get prime videos through Letterboxd
#watchlistPrimeOnlyURL = watchlistURL + "/on/amazon-primevideo"
#Prime_urls = getWatchlistURLS(watchlistPrimeOnlyURL)
#list_of_Prime_movies = []
#for url in Prime_urls:
#    page = getPage(url)
#    list_of_Prime_movies += getMovies(page)
            
#==============================================================================
# Settings
    
username = "ilikecandy" # Change account name here

include_Prime = True
include_Netflix = True
include_Hulu = False

#==============================================================================
# Body of the program

print("Collecting data from " + username + "'s watchlist...")

# Initialize counters
provider_counters = {}
if include_Prime:
    provider_counters["Amazon Prime"] = 0
if include_Netflix:
    provider_counters["Netflix"] = 0
if include_Hulu:
    provider_counters["Hulu"] = 0
    
provider_text = punctuate_list(list(provider_counters.keys()), "or")

num_available = 0
num_found = 0

# Grab URLs for watchlist
watchlistURL = "https://letterboxd.com/" + username + "/watchlist"
urls = getWatchlistURLS(watchlistURL)

# Grab movies from URLs
list_of_movies = []
for url in urls:
    page = getPage(url)
    list_of_movies += getMovies(page)

# Reverse the movie list to sort by last added
reversed_list = reverseList(list_of_movies)


long_message = ""

# Open file to save output
filename = username + "'s_Watchlist.txt"
file = open(filename, "w")

# Loop through movies
progress_bar = tqdm.trange(len(reversed_list), desc = "Collecting Streaming Info...", leave=True)
max_movie_title = getMaxTitle(reversed_list)

for movie in progress_bar:
    # \x1B[23m does italics. I don't know how and it doesn't matter – it just works.
    title = '\x1B[3m' + reversed_list[movie][1] + '\x1B[23m'
    progress_bar.set_description('Checking ' + padTitle(title, max_movie_title))
    progress_bar.refresh() # to show immediately the update
    is_available = False
    streams = None

    message = reversed_list[movie][1] + " –"
        
    decider_url = 'https://decider.com/movie/'
    decider_tv = 'https://decider.com/show/'
    
    year = reversed_list[movie][0][-4:]
    if not year.isnumeric():
        year = reversed_list[movie][0][-6:-2]
        if year.isnumeric():
            reversed_list[movie][0] = reversed_list[movie][0][:-6] + year

    movie_url = decider_url + reversed_list[movie][0]
    movie_page = getPage(movie_url)

    # If the page can't be found, guess a bunch of other possible URLs
    if movie_page:
        streams = getStreamsDecider(movie_page)
    elif year.isnumeric():
        movie_url = decider_url + reversed_list[movie][0][:-4] + str(int(year) - 1)
        movie_page = getPage(movie_url)
        if movie_page:
            streams = getStreamsDecider(movie_page)
        else:
            movie_url = decider_url + reversed_list[movie][0][:-4] + str(int(year) + 1)
            movie_page = getPage(movie_url)
            
            if movie_page:
                streams = getStreamsDecider(movie_page)
            else:
                movie_url = decider_url + reversed_list[movie][0][:-4]
                movie_page = getPage(movie_url)
                if movie_page:
                    streams = getStreamsDecider(movie_page)
                else:
                    tv_url = decider_tv + reversed_list[movie][0]
                    tv_page = getPage(tv_url)
                    if tv_page:
                        streams = getStreamsDecider(tv_page)
                    else:
                        # Give up
                        streams = ["???"]
        
    # Summarize streaming info for each movie
    if streams:
        providers = []
        for stream in sorted(streams):
            if stream in provider_counters:
                provider_counters[stream] += 1
                is_available = True
                providers.append(stream)
            else:
                is_available = "?"
                message += " ???"
        if len(providers) > 0:
            message += " " + punctuate_list(providers, "and")
    else:
        message += " Not on " + provider_text + " :("
        
    # Make output super easy to read
    if is_available == True:
        message = "✅ " + message 
        num_available += 1
        num_found += 1
    elif is_available == "?":
        message = "❓ " + message
    else:
        message = "❌ " + message
        num_found += 1
        
    long_message += message + "\n"
    
# Find some stats
total_num_movies = len(reversed_list)
percent_located = str(int(round((num_found / total_num_movies) * 100, 0)))

# Get current date and time
current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")

# Write results to file
file.write(username + " has " + str(total_num_movies) + " movies on their watchlist, " + 
           str(num_available) + " of which you can stream right now!\n")

for provider in provider_counters:
    file.write("* You can stream " + str(provider_counters[provider]) + 
               " movies through " + provider + ".\n")

file.write("\nThis script located " + str(num_found) + " out of " + str(total_num_movies) + 
           " movies (" + percent_located + "%).\n")
file.write("You'll have to research the remaining " + 
           str(total_num_movies - num_found) + " yourself.\n\n")
file.write("Results updated on " + current_datetime + ".\n\n")
file.write(long_message)

file.close()

print("\nOutput saved to " + filename)




