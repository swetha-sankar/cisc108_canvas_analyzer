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

__version__ = 7


# 1) main
def main(user_id:str):
    print_user_info(canvas_requests.get_user(user_id))
    courses = filter_available_courses(canvas_requests.get_courses(user_id))
    print_courses(courses)
    summarize_points(canvas_requests.get_submissions(user_id, choose_course((get_course_ids(courses)))))
    summarize_groups(canvas_requests.get_submissions(user_id, choose_course(get_course_ids(courses))))
    plot_scores(canvas_requests.get_submissions(user_id, choose_course((get_course_ids(courses)))))


# 2) print_user_info
def print_user_info(user_id: dict):
    print("Name: " + user_id["name"])
    print("Title: " + user_id["title"])
    print("Primary Email: " + user_id["primary_email"])
    print("Bio: " + user_id["bio"])


# 3) filter_available_courses
def filter_available_courses(courses: [dict]) -> [dict]:
    available = []
    for course in courses:
        if course["workflow_state"] == "available":
            available.append(course)
    return available


# 4) print_courses
def print_courses(courses: [dict]):
    for course in courses:
        print(course["id"], ":", course["name"])


# 5) get_course_ids
def get_course_ids(courses:[dict]) -> [int]:
    ids = []
    for course in courses:
        ids.append(course["id"])
    return ids


# 6) choose_course
def choose_course(course_ids: list) -> int:
    chosen = int(input("Enter a valid course ID: "))
    while chosen not in course_ids:
        chosen = int(input("Enter a valid course ID: "))
    return chosen


# 7) summarize_points
def summarize_points(submissions: [dict]):
    submissions_score = 0
    points_possible = 0
    for submission in submissions:
        if submission["score"] is not None:
            submissions_score = submission["score"] + submissions_score
            points_possible = submission["assignment"]["points_possible"] + points_possible
            points_obtained = submissions_score * (submission["assignment"]["group"]["group_weight"])
        points_possible_so_far = points_possible * (submission["assignment"]["group"]["group_weight"])
        current_grade = round(100 * (points_obtained / points_possible_so_far))
    print("Points possible so far: " + str(points_possible_so_far))
    print("Points obtained: " + str(points_obtained))
    print("Current grade: " + str(current_grade))


# summarize_groups
def summarize_groups(submissions: [dict]):
    print("* Class Activities : ")
    print("* Discussion Forums : ")
    print("* Learning Quizzes : ")
    print("* Programming Problems : ")


# 9) plot_scores
def plot_scores(submissions: [dict]):
    for submission in submissions:
        if submission["score"] and submission["assignment"]["points_possible"] is not None:
            grade = (submission["score"]*100)/submission["assignment"]["points_possible"]
        plt.hist(grade)
    plt.title("Distribution of Grades")
    plt.xlabel("Grades")
    plt.ylabel("Number of Assignments")
    plt.show()


# 10) plot_grade_trends
def plot_grade_trends(submissions:[dict]):
    running_high_sum = 0
    running_high_sums = []
    running_low_sum = 0
    running_low_sums = []
    for submission in submissions:
        for item in submission:
            pass


# Keep any function tests inside this IF statement to ensure
# that your `test_my_solution.py` does not execute it.
if __name__ == "__main__":
    main('hermione')
    # main('ron')
    # main('harry')
    
    # https://community.canvaslms.com/docs/DOC-10806-4214724194
    # main('YOUR OWN CANVAS TOKEN (You know, if you want)')