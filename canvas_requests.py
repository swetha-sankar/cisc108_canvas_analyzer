"""
Canvas Module for accessing the Canvas API.
Provides a simple interface over Requests, and equipped with a simple cache
for testing and development purposes.

You should not modify this file, because the instructor will be using their
own local version anyway.

@author: acbart
"""
__version__ = 7
import requests
import os
import json
import sqlite3
import sys 
import re

def get_user(user_id):
    return get("users/self/profile", user_id)

def get_courses(user_id):
    return get("courses", user_id)

def get_submissions(user_id, course_id):
    submissions = get("courses/{}/students/submissions".format(course_id), user_id)
    groups = get("courses/{}/assignment_groups".format(course_id), user_id)
    group_map = {g['id']: g for g in groups}
    for submission in submissions:
        assignment_group_id = submission['assignment']['assignment_group_id']
        submission['assignment']['group'] = group_map[assignment_group_id].copy()
    return submissions

# Make sure we are using the right Python version.
if not sys.version_info >= (3, 0):
    raise Exception("This code is expected to be run in Python 3.x")

# Special Exception class for checking purposes
class CanvasException(Exception):
    pass

# Change for different institution
BASE_URL = 'https://vt.instructure.com/api/v1/'

# Connect to local SQLite database (the cache)
DATABASE_NAME = 'sample_canvas_data.db'
if not os.access(DATABASE_NAME, os.F_OK):
    raise CanvasException(('Error! Could not find a "{0}" file. '
                           'Make sure that there is a \"{0}\" in the same '
                           'directory as "{1}.py"! Spelling is very '
                           'important here.').format(DATABASE_NAME, __file__))
if not os.access(DATABASE_NAME, os.R_OK):
    raise CanvasException(('Error! Could not read the "{0}" file. '
                          'Make sure that it readable by changing its '
                          'permissions. You may need to get help from '
                          'your instructor.').format(DATABASE_NAME, __file__))
DATABASE = sqlite3.connect(DATABASE_NAME)

# Preload the list of available users in the cache
USERS = DATABASE.execute("""SELECT name FROM users""")
USERS = [u.lower() for u, in USERS]

# Responses are in the database as JSON data
DATABASE.text_factory = lambda x: json.loads(x.decode('utf-8'))

def get(url, user):
    '''
    Accesses the Canvas API to return data, or from the local cache.
    
    Params:
        url (str): The URL endpoint to access
        user (str): The User (e.g., 'hermione') or API token
    Returns:
        dict or list: Depending on what URL is accessed, will return
                      a list of all the results or just a single dictionary
    '''
    # Confirm types
    if not isinstance(url, str):
        raise TypeError("The URL must be a string.")
    if not isinstance(user, str):
        raise TypeError("The user token must be a string.")
    # If a special user, then return the cached result
    rows = _get_via_cache(url, user)
    if rows:
        return rows[0]
    # Otherwise, get via the requests module
    return _get_via_requests(url, user)

def _normalize_url(url):
    '''
    Normalizes a URL to remove extra trailing slashes, and converts to
    lowercase
    
    Params:
        url (str): The URL endpoint to normalize
    Returns:
        str: The normalized URL endpoint
    '''
    if url.endswith('/'):
        url = url[:-1]
    return url.lower()

def _get_via_cache(url, user):
    '''
    Retrieves the given user's result for that URL from the local cache.
    
    Params:
        url (str): The URL endpoint to look up in the cache
        user (str): One of the users in the cache
    Returns:
        dict or list: Depending on what URL is accessed, will return
                      a list of all the results or just a single dictionary
    '''
    # Normalize URL and user to find them in the cache
    normalized_user = user.lower()
    normalized_url = _normalize_url(url)
    if user.lower() in USERS:
        # Perform the query selection
        rows = DATABASE.execute("""SELECT response FROM responses
                                 WHERE url=? AND user=?""",
                                 (normalized_url, normalized_user))
        return [r for r, in rows]
    return False

def _get_via_requests(url, token):
    # Provide token and increase number of results returned to maximum
    full_url = BASE_URL + url
    parameters = {}
    parameters['access_token'] = token
    parameters['per_page'] = 100
    if re.match("courses/(\d\d+)/students/submissions", url):
        parameters["include[]"] = "assignment"
    final_result = []
    # Loop until we get every page of results
    while True:
        # Make the actual request
        response = requests.get(full_url, parameters)
        if response.status_code == 404:
            exception = ("Canvas URL not found for URL '{}'").format(url)
            raise CanvasException(exception)
        json_data = response.json()
        # Inspect the results, return any dictionaries directly
        if isinstance(json_data, dict):
            if 'errors' in json_data:
                errors = json_data['errors']
                if errors:
                    error_message = errors[0]['message']
                    if error_message == 'Invalid access token.':
                        exception= ("Invalid access token '{}' for "
                                    "URL '{}'. Did you spell the name right?").format(token, url)
                    else:
                        exception= ("Canvas error '{}' for "
                                    "URL '{}'").format(error_message, url)
                else:
                    exception = ("General canvas error for "
                                 "URL '{}'").format(url)
                raise CanvasException(exception)
            return json_data
        # Otherwise, start building up our list
        final_result.extend(json_data)
        # Check if there's another page of data
        if 'next' in response.links:
            # Now we'll go onto the next page
            full_url = response.links['next']['url']
        else:
            # No more pages, stop here
            return final_result
