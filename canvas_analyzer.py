"""
Project 4C
Canvas Analyzer
CISC108 Honors
Fall 2019

Access the Canvas Learning Management System and process learning analytics.

Edit this file to implement the project.
To test your current solution, run the `test_my_solution.py` file.
Refer to the instructions on Canvas for more information.

"I have neither given nor received help on this assignment."
author: SWETHA SANKAR
"""
import canvas_requests
import matplotlib.pyplot as plt
import datetime

__version__ = 7


# 1) main
def main(user_id: str):
    '''
    This function  a string representing the user token and calls all the other functions.
    :Args:
        user_id (str): User token
    '''
    print_user_info(canvas_requests.get_user(user_id))
    courses = filter_available_courses(canvas_requests.get_courses(user_id))
    print_courses(courses)
    summarize_points(canvas_requests.get_submissions(user_id, choose_course((get_course_ids(courses)))))
    summarize_groups(canvas_requests.get_submissions(user_id, choose_course(get_course_ids(courses))))
    plot_scores(canvas_requests.get_submissions(user_id, choose_course((get_course_ids(courses)))))
    plot_grade_trends(canvas_requests.get_submissions(user_id, choose_course((get_course_ids(courses)))))


# 2) print_user_info
def print_user_info(user_id: dict):
    '''
    This function prints the user's name, title, primary email, and bio.
    :Args:
        user_id (dict): User dictionary
    '''
    print("Name: " + user_id["name"])
    print("Title: " + user_id["title"])
    print("Primary Email: " + user_id["primary_email"])
    print("Bio: " + user_id["bio"])


# 3) filter_available_courses
def filter_available_courses(courses: [dict]) -> [dict]:
    '''
    This function consumes a list of Course dictionaries and returns a list of Course dictionaries where the
    workflow_state key's value is 'available'
    :Args:
        courses ([dict]): List of all course dictionaries
    :return:
        available ([dict]): List of available course dictionaries
    '''
    available = []
    for course in courses:
        if course["workflow_state"] == "available":
            available.append(course)
    return available


# 4) print_courses
def print_courses(courses: [dict]):
    '''
    This function consumes a list of course dictionaries and prints out the ID and name of each course on separate lines.
    :Args:
        courses([dict]): List of available course dictionaries
    '''
    for course in courses:
        print(course["id"], ":", course["name"])


# 5) get_course_ids
def get_course_ids(courses:[dict]) -> [int]:
    '''
    This function consumes a list of course dictionaries and returns a list of integers representing course IDs.
    :Args:
        courses ([dict]): List of available course dictionaries
    :return:
        [int]: List of integers representing course IDs
    '''
    ids = []
    for course in courses:
        ids.append(course["id"])
    return ids


# 6) choose_course
def choose_course(course_ids: list) -> int:
    '''
    This function consumes a list of integers representing course IDs, prompts the user to enter a valid ID, and then
    returns an integer representing the user's chosen course ID.
    If the user does not enter a valid ID, the function repeatedly loops until they type in a valid ID.
    :param
        course_ids(list): List of integers representing course IDs
    :return:
        int: Chosen course ID
    '''
    chosen = int(input("Enter a valid course ID: "))
    while chosen not in course_ids:
        chosen = int(input("Enter a valid course ID: "))
    return chosen


# 7) summarize_points
def summarize_points(submissions: [dict]):
    '''
    This function consumes a list of submission dictionaries and prints
    the user's points possible so far (sum of the assignments' points_possible multiplied by the group_weight),
    points obtained (sum of the submissions' score multiplied by the assignment's group_weight),
    and current grade for a class (points obtained divided by points possible so far)
    :Args:
        submissions ([dict]): List of submission dictionaries from canvas_requests.get_submissions
    '''
    points_obtained = 0
    points_possible_so_far = 0
    for submission in submissions:
        if submission["score"] is not None:
            score = submission["score"] * submission["assignment"]["group"]["group_weight"]
            points_obtained = score + points_obtained
            points = submission["assignment"]["points_possible"] * submission["assignment"]["group"]["group_weight"]
            points_possible_so_far = points + points_possible_so_far
            current_grade = round(100 * (points_obtained / points_possible_so_far))
    print("Points possible so far: " + str(points_possible_so_far))
    print("Points obtained: " + str(points_obtained))
    print("Current grade: " + str(current_grade))


# 8) summarize_groups
def summarize_groups(submissions: [dict]):
    '''
    This function consumes a list of Submission dictionaries and prints out the group name and unweighted grade for each group.
    The unweighted grade is the total score for the group's submissions divided by the total points_possible for
    the group's submissions, multiplied by 100 and rounded.
    :Args:
        submissions ([dict]): List of submission dictionaries from canvas_requests.get_submissions
    '''
    groups = {}
    points_possible = 0
    score = 0
    for submission in submissions:
        if submission["assignment"]["group"]["name"] in groups and submission["score"] is not None:
            groups[submission["assignment"]["group"]["name"]] += 1
        else:
            groups[submission["assignment"]["group"]["name"]] = 1
    for key, value in groups.items():
        for submission in submissions:
            if key == submission["assignment"]["group"]["name"] and submission["score"] is not None:
                score = submission["score"] + score
                points_possible = submission["assignment"]["points_possible"] + points_possible
        grade = round((score*value)/(points_possible*value)*100)
        print("*", key, ":", grade)


# 9) plot_scores
def plot_scores(submissions: [dict]):
    '''
    This function consumes a list of Submission dictionaries and plots each submissions' grade as a histogram
    :Args:
        submissions ([dict]): List of submission dictionaries from canvas_requests.get_submissions
    '''
    a = []
    for submission in submissions:
        if submission["score"] is not None and submission["assignment"]["points_possible"] > 0:
            grade = (100*submission["score"])/(submission["assignment"]["points_possible"])
            a.append(grade)
    plt.hist(a)
    plt.title("Distribution of Grades")
    plt.xlabel("Grades")
    plt.ylabel("Number of Assignments")
    plt.show()


# 10) plot_grade_trends
def plot_grade_trends(submissions:[dict]):
    '''
    This function consumes a list of Submission dictionaries and plots the grade trend of the submissions as a line plot
    It plots the running sum of graded submission scores followed by the running sum of points still possible from
    ungraded assignments (Highest), the running sum of graded submission scores followed by the running sum if you scored
    0 on all ungraded assignments (Lowest), and the running sum of the points possible on all assignments in the course
    (Maximum).
    :Args:
        submissions ([dict]): List of submission dictionaries from canvas_requests.get_submissions
    '''
    running_high_sum = 0
    running_high_sums = []
    running_low_sum = 0
    running_low_sums = []
    maximum = 0
    maximums = []
    dates = []
    total_points = 0
    for submission in submissions:
        total_points = submission["assignment"]["points_possible"] * submission["assignment"]["group"]["group_weight"] + total_points
        a_string_date = submission["assignment"]["due_at"]
        dates.append(datetime.datetime.strptime(a_string_date, "%Y-%m-%dT%H:%M:%SZ"))
        maximum = 100 * submission["assignment"]["points_possible"] * submission["assignment"]["group"]["group_weight"] + maximum
        maximums.append(maximum)
        if submission["score"] is None:
            running_high_sum = 100 * submission["assignment"]["points_possible"] * submission["assignment"]["group"]["group_weight"] + running_high_sum
            running_high_sums.append(running_high_sum)
            running_low_sum = running_low_sum + 0
            running_low_sums.append(running_low_sum)
        else:
            running_high_sum = 100 * submission["score"] * submission["assignment"]["group"]["group_weight"] + running_high_sum
            running_high_sums.append(running_high_sum)
            running_low_sum = 100 * submission["score"] * submission["assignment"]["group"]["group_weight"] + running_low_sum
            running_low_sums.append(running_low_sum)
    final_high_sums = []
    for hnum in running_high_sums:
        finalh = hnum/total_points
        final_high_sums.append(finalh)
    final_low_sums = []
    for lnum in running_low_sums:
        finall = lnum/total_points
        final_low_sums.append(finall)
    final_max = []
    for mnum in maximums:
        finalm = mnum/total_points
        final_max.append(finalm)
    plt.plot(dates, final_high_sums, label="Highest")
    plt.plot(dates, final_low_sums, label="Lowest")
    plt.plot(dates, final_max, label="Maximum")
    plt.legend()
    plt.title("Grade Trend")
    plt.ylabel("Grade")
    plt.show()

# Keep any function tests inside this IF statement to ensure
# that your `test_my_solution.py` does not execute it.
if __name__ == "__main__":
    main('hermione')
    # main('ron')
    # main('harry')
    
    # https://community.canvaslms.com/docs/DOC-10806-4214724194
    # main('YOUR OWN CANVAS TOKEN (You know, if you want)')