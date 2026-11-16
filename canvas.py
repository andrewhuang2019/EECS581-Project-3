import os
from canvasapi import Canvas

API_URL = "https://canvas.ku.edu"

class CanvasAPI:
    # the string passed in needs to be an API token 
    # which can be obtained from the canvas website 
    def __init__(self, api_string: str):
        self.canvas = Canvas(API_URL, api_string)

    def get_courses(self):
        self.courses = []
        for course in self.canvas.get_courses(enrollment_state="active"):
            self.courses.append(course)
        return self.courses

    def update_current_course(self, course_num: int):
        self.current_course = self.canvas.get_course(course_num)

    def get_todo(self):
        self.todo = []
        for item in self.canvas.get_todo_items():
            self.todo.append(item)
        return self.todo

    #the two below use the current course for assignments/modules
    def get_assignments(self):
        self.assignments = []
        for assignment in self.current_course.get_assignments():
            self.assignments.append(assignment)
        return self.assignments

    def get_modules(self):
        self.modules = []
        for module in self.current_course.get_modules():
            self.modules.append(module)
        return self.modules

