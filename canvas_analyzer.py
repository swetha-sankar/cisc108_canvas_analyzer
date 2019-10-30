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
    :param
    user_id: str
    :return:
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
    :param user_id: dictionary
    '''
    print("Name: " + user_id["name"])
    print("Title: " + user_id["title"])
    print("Primary Email: " + user_id["primary_email"])
    print("Bio: " + user_id["bio"])


# 3) filter_available_courses
def filter_available_courses(courses: [dict]) -> [dict]:
    '''
    :param courses:
    :return:
    '''
    available = []
    for course in courses:
        if course["workflow_state"] == "available":
            available.append(course)
    return available


# 4) print_courses
def print_courses(courses: [dict]):
    '''
    :param courses:
    :return:
    '''
    for course in courses:
        print(course["id"], ":", course["name"])


# 5) get_course_ids
def get_course_ids(courses:[dict]) -> [int]:
    '''
    :param courses:
    :return:
    '''
    ids = []
    for course in courses:
        ids.append(course["id"])
    return ids


# 6) choose_course
def choose_course(course_ids: list) -> int:
    '''
    :param course_ids:
    :return:
    '''
    chosen = int(input("Enter a valid course ID: "))
    while chosen not in course_ids:
        chosen = int(input("Enter a valid course ID: "))
    return chosen


# 7) summarize_points
def summarize_points(submissions: [dict]):
    '''
    :param submissions:
    :return:
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


# summarize_groups
def summarize_groups(submissions: [dict]):
    '''
    :param submissions: list of submission dictionaries
    Consumes a list of Submission dictionaries and prints out the group name and unweighted grade for each group.
    The unweighted grade is the total score for the group's submissions divided by the total points_possible for
    the group's submissions, multiplied by 100 and rounded. Like the summarize_points function, you should ignore the
    submission without a score (i.e. the submission's score is None). You are recommended to apply the Dictionary
    Summing Pattern to implement this function.
    '''
    a = []
    for submission in submissions:
        b = submission["assignment"]["group"]["name"]
        a.append(b)
        if submission["score"] is not None:
            unweighted = submission



# 9) plot_scores
def plot_scores(submissions: [dict]):
    '''
    :param submissions:
    :return:
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
    :param submissions:
    :return:
    '''
    running_high_sum = 0
    running_high_sums = []
    running_low_sum = 0
    running_low_sums = []
    maximum = 0
    maximums = []
    dates = []
    for submission in submissions:
        a_string_date = submission["assignment"]["due_at"]
        dates.append(datetime.datetime.strptime(a_string_date, "%Y-%m-%dT%H:%M:%SZ"))
        maximum = maximum + submission["assignment"]["points_possible"]
        maximums.append(maximum)
        if submission["score"] is None:
            points_possible = submission["assignment"]["points_possible"] * submission["assignment"]["group"]["group_weight"]
            running_high_sum = points_possible + running_high_sum
            running_high_sums.append(running_high_sum)
            running_low_sum = running_low_sum + 0
            running_low_sums.append(running_low_sum)
        else:
            score = submission["score"] * submission["assignment"]["group"]["group_weight"]
            running_high_sum = running_high_sum + score
            running_high_sums.append(running_high_sum)
            running_low_sum = running_low_sum + score
            running_low_sums.append(running_low_sum)
    plt.plot(dates, running_high_sums, label="Highest")
    plt.plot(dates, running_low_sums, label="Lowest")
    plt.plot(dates, maximums, label="Maximum")
    plt.legend()
    plt.xlabel("Due Date")
    plt.ylabel("Points possible")
    plt.show()


# Keep any function tests inside this IF statement to ensure
# that your `test_my_solution.py` does not execute it.
if __name__ == "__main__":
    main('hermione')
    # main('ron')
    # main('harry')
    
    # https://community.canvaslms.com/docs/DOC-10806-4214724194
    # main('YOUR OWN CANVAS TOKEN (You know, if you want)')