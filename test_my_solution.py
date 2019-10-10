'''
This file is used to test your implementation of `canvas_analyzer.py` for
project 6 (Canvas Analyzer).

You should not modify this file, because the instructor will be running
your code against the original version anyway.

@author: acbart
'''
#%% Imports
__version__ = 7
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
import io
import bisect
import string
import textwrap
import traceback
import pprint
from hashlib import md5
import inspect
import re
import ast
import copy
from datetime import datetime, timedelta
import types

#%% Top-level constants

# Settings
FINAL_MODE = False
FULL_TRACE = False
STRICT_VERSIONS = True

# Value checking tolerance
TOLERANCE = 2
TIME_TOLERANCE = timedelta(seconds=31)

# Display options
MAXIMUM_VALUE_LENGTH = 120

# File validation
STUDENT_FILENAME = "canvas_analyzer.py"
SAMPLE_OUTPUT_FILENAME = "sample_output.txt"
SAMPLE_OUTPUT_HASH = "197688191079b4fca95b00091886d4df"
CANVAS_PY_HASH = "7099e31181b55d2a789e8a4dbab1a2de"

CONGRATULATIONS = """CONGRATULATIONS!
Your solution passes all the unit tests.
Clean and organize your code, so that it looks nice.
Check the style guide for recommendations on organization.
Then, submit on Web-CAT.
Outstanding work on writing all that code :)
"""
#%% Mocks
class MockPlt:
    '''
    Mock MatPlotLib library that can be used to capture plot data.
    '''
    def __init__(self):
        self._reset_plots()
    def show(self, **kwargs):
        self.plots.append(self.active_plot)
        self._reset_plot()
    def unshown_plots(self):
        return self.active_plot['data']
    def __repr__(self):
        return repr(self.plots)
    def __str__(self):
        return str(self.plots)
    def _reset_plots(self):
        self.plots = []
        self._reset_plot()
    def _reset_plot(self):
        self.active_plot = {'data': [], 
                            'xlabel': None, 'ylabel': None, 
                            'title': None, 'legend': False}
    def hist(self, data, **kwargs):
        label = kwargs.get('label', None)
        self.active_plot['data'].append({'type': 'Histogram', 'values': data, 'label': label})
    def plot(self, xs, ys=None, **kwargs):
        label = kwargs.get('label', None)
        if ys == None:
            self.active_plot['data'].append({'type': 'Line', 
                                            'x': range(len(xs)), 'y': xs, 'label': label})
        else:
            self.active_plot['data'].append({'type': 'Line', 'x': xs, 'y': ys, 'label': label})
    def scatter(self, xs, ys, **kwargs):
        label = kwargs.get('label', None)
        self.active_plot['data'].append({'type': 'Scatter', 'x': xs, 'y': ys, 'label': label})
    def xlabel(self, label, **kwargs):
        self.active_plot['xlabel'] = label
    def title(self, label, **kwargs):
        self.active_plot['title'] = label
    def ylabel(self, label, **kwargs):
        self.active_plot['ylabel'] = label
    def legend(self, **kwargs):
        self.active_plot['legend'] = True
    def _add_to_module(self, module):
        for name, value in self._generate_patches().items():
            setattr(module, name, value)
    def _generate_patches(self):
        def dummy(**kwargs):
            pass
        return dict(hist=self.hist, plot=self.plot, 
                    scatter=self.scatter, show=self.show,
                    xlabel=self.xlabel, ylabel=self.ylabel, 
                    title=self.title, legend=self.legend,
                    xticks=dummy, yticks=dummy,
                    autoscale=dummy, axhline=dummy,
                    axhspan=dummy, axvline=dummy,
                    axvspan=dummy, clf=dummy,
                    cla=dummy, close=dummy,
                    figlegend=dummy, figimage=dummy,
                    suptitle=dummy, text=dummy,
                    tick_params=dummy, ticklabel_format=dummy,
                    tight_layout=dummy, xkcd=dummy,
                    xlim=dummy, ylim=dummy,
                    xscale=dummy, yscale=dummy)

fake_module = types.ModuleType('matplotlib')
fake_module.pyplot = types.ModuleType('pyplot')
MOCKED_MODULES = {
        'matplotlib': fake_module,
        'matplotlib.pyplot': fake_module.pyplot,
        }
mock_plt = MockPlt()
mock_plt._add_to_module(fake_module.pyplot)

#%% Helper Functions
def call_safely(a_function, *args, prompter=None, matplotlib=False, 
                example=None, **kwargs):
    '''
    Call a given function, but patch all the dangerous built-ins.
    
    Params:
        a_function (function): The function to call.
        prompter (generator): A generator to supply 
    Returns:
        function: The wrapped function, ready to be called (without parameters)
    '''
    if prompter is None:
        def prompter(prompt=''):
            return ''
    parameters = copy.deepcopy(kwargs)
    mock_plt._reset_plots()
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('builtins.input', prompter)
    @patch('time.sleep', return_value=None)
    @patch('builtins.open', mock_open())
    @patch('requests.get', side_effect=_requests_not_usable)
    @patch.dict(sys.modules, MOCKED_MODULES)
    def wrapped_function(r, sleep, stdout):
        input_failed = False
        try:
            result = a_function(*args, **kwargs)
        except StopIteration:
            input_failed = True
            result= None
        except Exception as e:
            if example is None:
                code = _demonstrate_call(a_function, parameters)
            else:
                code = example
            _raise_improved_error(e, code)
        if matplotlib:
            return result, stdout.getvalue(), input_failed, mock_plt
        else:
            return result, stdout.getvalue(), input_failed
    return wrapped_function()

def _append_to_error(e, message):
    e.args = (e.args[0]+message,)
    return e

def _demonstrate_complex_call(call, conditions):
    code = ".\n\nThe error above occurred when I ran:\n"
    code += indent4(call)
    code += "\nWhere:\n"
    defs = ''
    for key, value in conditions.items():
        value = pprint.pformat(value, indent=2, compact=True)
        if len(value) >= MAXIMUM_VALUE_LENGTH:
            value = value[:MAXIMUM_VALUE_LENGTH-3] + "..."
        defs += "{} is {}\n".format(key, value)
    code += indent4(defs)
    return code

def indent4(a_string):
    return textwrap.indent(a_string, ' '*4)

def _run_example(*lines, **format_values):
    code = ".\n\nThe error above occurred when I ran:\n"
    code += indent4('\n'.join(lines))
    return code.format(**format_values)

class FormatPrinter(pprint.PrettyPrinter):
    def __init__(self, formats):
        if FINAL_MODE:
            super(FormatPrinter, self).__init__()
        else:
            super(FormatPrinter, self).__init__(compact=True)
        self.formats = formats

    def format(self, obj, ctx, maxlvl, lvl):
        if type(obj) in self.formats:
            return self.formats[type(obj)](obj), 1, 0
        return pprint.PrettyPrinter.format(self, obj, ctx, maxlvl, lvl)
fp = FormatPrinter({float: lambda f: "{:0.2f}".format(f).rstrip('0').rstrip('.'), 
                    int: "{:d}".format})

def _demonstrate_call(a_function, parameters):
    if not isinstance(a_function, str):
        a_function = a_function.__name__
    defs = ""
    for key, value in parameters.items():
        value = pprint.pformat(value, indent=2, compact=True)
        if len(value) >= MAXIMUM_VALUE_LENGTH:
            value = value[:MAXIMUM_VALUE_LENGTH-3] + "..."
        defs += "{} = {}\n".format(key, value)
    arguments = ", ".join(parameters.keys())
    code = "{defs}{name}({arguments})".format(name=a_function, defs=defs, 
                                              arguments=arguments)
    code = code.replace("{", "{{").replace("}", "}}")
    code = indent4(code)
    code = ".\n\nThe error above occurred when I ran:\n"+code
    return code

def _raise_improved_error(e, code):
    if isinstance(e, KeyError):
        raise _copy_key_error(e, code) from None
    else:
        raise _append_to_error(e, code)

def _copy_key_error(e, code):
    new_args = (repr(e.args[0])+code,)
    new_except = _KeyError(*new_args)
    new_except.__cause__ = e.__cause__
    new_except.__traceback__ = e.__traceback__
    new_except.__context__  = e.__context__ 
    return new_except

def _make_inputs(*input_list, repeat=None):
    '''
    Helper function for creating mock user input.
    
    Params:
        input_list (list of str): The list of inputs to be returned
    Returns:
        function (str=>str): The mock input function that is returned, which
                             will return the next element of input_list each
                             time it is called.
    '''
    generator = iter(input_list)
    def mock_input(prompt=''):
        print(prompt)
        try:
            return next(generator)
        except StopIteration as SI:
            if repeat is None:
                raise SI
            else:
                return repeat
    return mock_input

#: A basic identify function that returns the given argument unchanged
IDENTITY_FUNCTION = lambda x: x

def _skip_unless_callable(module, function_name):
    '''
    Helper function to test if the student has defined the relevant function.
    This is meant to be used as a decorator.
    
    Params:
        function_name (str): The name of the function to test in student_main.
    Returns:
        function (x=>x): Either the identity function (unchanged), or a
                         unittest.skip function to let you skip over the
                         function's tests.
    '''
    if FINAL_MODE:
        return IDENTITY_FUNCTION
    msg = ("You have not defined `{0}` in {1} as a function."
           ).format(function_name, STUDENT_FILENAME)
    if hasattr(module, function_name):
        if callable(getattr(module, function_name)):
            return IDENTITY_FUNCTION
        return unittest.skip(msg)
    return unittest.skip(msg)

# Prevent certain code constructs
class ProjectRulesViolation(Exception):
    pass

# No cheap built-ins
def no_builtins_exception(name):
    def f(*args, **kwargs):
        raise ProjectRulesViolation('Error! You seem to have used a builtin function.')
    return f

def _human_type(a_value):
    return {list: 'List', dict: 'Dictionary',
            int: 'Integer', str: 'String',
            float: 'Float', bool: 'Boolean'
            }.get(type(a_value), type(a_value))

def _clean_output(output):
    output = output.replace("{", "{{").replace( "}", "}}")
    return textwrap.indent(output, ' |  ')

punctuation_table = str.maketrans(string.punctuation, ' '*len(string.punctuation))
def _normalize_string(a_string, numeric_endings=False):
    # Lower case
    a_string = a_string.lower()
    # Remove trailing decimals (TODO: How awful!)
    if numeric_endings:
        a_string = re.sub(r"(\s*[0-9]+)\.[0-9]+(\s*)", r"\1\2", a_string)
    # Remove punctuation
    a_string = a_string.translate(punctuation_table)
    # Split lines
    lines = a_string.split("\n")
    normalized = [[piece
                   for piece in line.split()]
                  for line in lines]
    normalized = [[piece for piece in line if piece]
                  for line in normalized
                  if line]
    return sorted(normalized)

_OUTPUT_DIFF_EXPLANATION = """\nI recommend you check the Output Diff above.
Check each line above for these symbols:
  + means a line you need to REMOVE
  - means a line you need to ADD
  ? means a line you need to CHANGE
  ^ means a character you need to CHANGE"""

class TestBase(unittest.TestCase):
    maxDiff = None
    
    def __init__(self, methodName='runTest'):
        super(TestBase, self).__init__(methodName)
        self.example = None
        
    def tearDown(self):
        self.example = None
    
    def make_feedback(self, msg, _call=None, **format_args):
        msg = msg.format(function=self.shortDescription(), **format_args)
        msg = "\n\nFeedback:\n"+ textwrap.indent(msg, '  ')
        if self.example is not None:
            msg = self.example + msg
        elif _call is not None:
            _call = _demonstrate_call(self.shortDescription(), _call)
            msg = _call.format()+msg
        return msg 
    
    def call_safely(self, a_function, *args, prompter=None, matplotlib=False, **kwargs):
        '''
        Wrapper around `call_safey` to automatically include the example parameter
        '''
        return call_safely(a_function, *args, prompter=prompter,
                           matplotlib=matplotlib, example=self.example, **kwargs)

    def assertSimilarStrings(self, first, second, msg):
        if _normalize_string(first) != _normalize_string(second):
            return self.assertEqual(first, second, msg)
            #msg = self._formatMessage(msg, '%s == %s' % (safe_repr(first),
            #                          safe_repr(second)))
            #return self.failureException(msg)

class _KeyError(KeyError):
    def __str__(self):
        return BaseException.__str__(self)
    
class TestSuccessHolder(unittest.TextTestResult):
    '''
    Improved TextTestResult that records successes and removes errors
    that are not directly related to the students' code.
    '''
    def __init__(self, stream, descriptions, verbosity):
        '''
        Initialize the successes list
        '''
        super(TestSuccessHolder, self).__init__(stream, descriptions, verbosity)
        self.successes = []
    
    def addSuccess(self, test):
        '''
        Add this passing test to the successes list
        '''
        super(TestSuccessHolder, self).addSuccess(test)
        self.successes.append(test)
    
    def _is_relevant_tb_level(self, tb):
        '''
        Determines if the give part of the traceback is relevant to the user.
        
        Returns:
            boolean: True means it is NOT relevant
        '''
        # Are in verbose mode?
        if FULL_TRACE:
            return False
        filename, _, _, _ = traceback.extract_tb(tb, limit=1)[0]
        # Is the error in this test file?
        if filename == __file__:
            return True
        # Is the error related to a file in this directory?
        current_directory = os.path.dirname(os.path.realpath(__file__))
        if filename.startswith(current_directory):
            return False
        # Is the error in a local file?
        if filename.startswith('.'):
            return False
        # Is the error in an absolute path?
        if not os.path.isabs(filename):
            return False
        # Okay, it's not a student related file
        return True

#: Mapping TextTestResult's attributes to messages
UNIT_TEST_MESSAGES = [('successes', 'Success!'), 
                      ('skipped', 'Skipped (function not defined)'), 
                      ('failures', 'Test failed'), 
                      ('errors', 'Test error (your code has an error!)'),
                      ('unexpectedSuccesses', 'Unexpected success'), 
                      ('expectedFailures', 'Expected failure')]

def _run_unit_tests(phases):
    runner = unittest.TextTestRunner(resultclass=TestSuccessHolder)
    success = True
    total_cases = 0
    for number, (name, phase) in enumerate(phases):
        if not FINAL_MODE:
            print("#"*70)
            print("Testing Phase {}: {}".format(number, name))
            print("Summary: ", end="")
        sys.stderr.flush()
        sys.stdout.flush()
        phase_suite = unittest.TestSuite()
        phase_suite.addTest(unittest.makeSuite(phase))
        total_cases += phase_suite.countTestCases()
        result = runner.run(phase_suite)
        for UNIT_TEST_TYPE, MESSAGE in UNIT_TEST_MESSAGES:
            for case in getattr(result, UNIT_TEST_TYPE):
                if isinstance(case, tuple):
                    case = case[0]
                print("\t", case.shortDescription()+":", MESSAGE)
        success = success and (result.wasSuccessful() and not result.skipped)
        if not FINAL_MODE and not success:
            break
    sys.stderr.flush()
    sys.stdout.flush()
    if success:
        print("")
        print(CONGRATULATIONS)
        
def _requests_not_usable():
    raise Exception("Requests is not available on Web-CAT. "
                   "Your code attempted to access the actual Canvas site."
                   "You should not do that on here.")

def _validate_python_file(a_filename):
    # Dummy prompter avoids the most common student error
    # TODO: Extract this, make it more elegant.
    dummy_prompter = _make_inputs('52', '', repeat='')
    try:
        return call_safely(__import__, a_filename[:-3], 
                           prompter=dummy_prompter, matplotlib=True)
    except ImportError as e:
        if e.name == a_filename:
            message = ('Error! Could not find a "{1}" file. '
                       'Make sure that there is a "{1}" in the same '
                       'directory as "{0}"! Spelling is very '
                       'important here.').format(__file__, a_filename)
            raise Exception(message)
        else:
            raise e
    except Exception as e:
        message = ("\n\nWhile importing your {0} file, I encountered an error."
                   "\nTry running the file directly and debug the error."
                   "\nMake sure you are not calling input() or a function that"
                   "\n    uses input() at the top-level."
                   ).format(a_filename)
        raise _append_to_error(e, message)
def _hash_file(a_filename):
    with open(a_filename, 'rb') as output_file:
        hashed= md5(output_file.read()).hexdigest()
    return hashed

def group_by_value(ds, ys):
    result = {}
    for d, y in zip(ds, ys):
        if d not in result:
            result[d] = []
        bisect.insort(result[d], y)
    return result

#%% Check Python Version
if sys.version_info <= (3, 0):
    raise Exception("This code is expected to be run in Python 3.x")
    
#%% Student main file was created
student_main, _, _, _ = _validate_python_file(STUDENT_FILENAME)

#%% Student has not modified canvas.py inappropriately
canvas_requests, _, _, _ = _validate_python_file("canvas_requests.py")
if STRICT_VERSIONS and canvas_requests.__version__ != __version__:
    raise Exception(('The canvas module is not at the same version ({}) '
                     'as the version of this unit test file ({}). Make sure '
                     'you download the correct versions.'
                     ).format(canvas_requests.__version__, __version__))
#if CANVAS_PY_HASH and CANVAS_PY_HASH != _hash_file("canvas_requests.py"):
#    raise Exception(('Error! Hash mismatch. '
#                     'Make sure that you did not modify your "canvas_requests.py" file.'
#                     'You may want to redownload the file.'))
#%% Student has not modified sample_output.txt
if not os.access(SAMPLE_OUTPUT_FILENAME, os.F_OK):
    raise Exception(('Error! Could not find a "{0}" file. '
                     'Make sure that there is a \"{0}\" in the same '
                     'directory as "{1}.py"! Spelling is very '
                     'important here.').format(SAMPLE_OUTPUT_FILENAME, __file__))
if not os.access(SAMPLE_OUTPUT_FILENAME, os.R_OK):
    raise Exception(('Error! Could not read the "{0}" file. '
                     'Make sure that it readable by changing its '
                     'permissions. You may need to get help from '
                     'your instructor.').format(SAMPLE_OUTPUT_FILENAME, __file__))
#if SAMPLE_OUTPUT_HASH and SAMPLE_OUTPUT_HASH != _hash_file(SAMPLE_OUTPUT_FILENAME):
#    raise Exception(('Error! Hash mismatch. '
#                     'Make sure that you did not modify your "{0}" file.'
#                     'You may want to redownload the file.')
#                    .format(SAMPLE_OUTPUT_FILENAME))
#%% Load sample_output.txt
with open(SAMPLE_OUTPUT_FILENAME) as output_file:
    output = output_file.read()
C = "#"
sections = output.split(C*32)
output_version = sections[0].split("\n", maxsplit=1)[0].split()[-1]
if STRICT_VERSIONS and str(__version__) != output_version:
    raise Exception(('Your "{0}" is at a different version '
                     'than these unit tests. You should make sure you are '
                     'using the latest version of all these files ({1}).')
                    .format(SAMPLE_OUTPUT_FILENAME, __version__))
reference = {}
for section in sections[1:]:
    a_ref = {}
    user, course = section.split("\n")[1:3]
    rest = section.split("\n")[3:]
    user = user.rsplit()[-1]
    course = course.rsplit()[-1]
    for line in rest:
        if line.startswith(C):
            key = line[2:]
            a_ref[key] = []
        else:
            a_ref[key].append(textwrap.dedent(line))
    reference[(user, course)] = a_ref
#%% Assignment-Specific Unit Tests
#: List of (String phase name, TestBase) pairs
class TestFunctions(TestBase):
    
    @_skip_unless_callable(student_main, 'print_user_info')
    def test_print_user_info(self):
        "print_user_info"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("user = canvas_requests.get_user({user_id}!r)",
                                        "print_user_info(user)",
                                        user_id=user_id)
            user = canvas_requests.get_user(user_id)
            _, output, _ = self.call_safely(student_main.print_user_info, user)
            # Did they print?
            msg = self.make_feedback("{function} did not print anything.")
            self.assertNotEqual(output, "", msg=msg)
            # Did they print the essential components?
            msg = self.make_feedback("{function} did not print the correct value")
            expected = reference[(user_id, course_id)]["print_user_info"]
            expected_joined = '\n'.join(expected)
            msg = self.make_feedback("{function} did not print the correct value\n"
                                     "Expected to see the following lines:\n"
                                     "{expected}\n"
                                     "Instead only found:\n"
                                     "{output}\n",
                                     expected=indent4(expected_joined),
                                     output=indent4(output))
            output = _normalize_string(output)
            for line in _normalize_string(expected_joined):
                self.assertIn(line, output, msg=msg)
    
    @_skip_unless_callable(student_main, 'filter_available_courses')
    def test_filter_available_courses(self):
        "filter_available_courses"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("courses = canvas_requests.get_courses({user_id!r})",
                                        "filter_available_courses(courses)",
                                        user_id=user_id)
            courses = canvas_requests.get_courses(user_id)
            result, _, _ = call_safely(student_main.filter_available_courses, courses)
            # Did they return something?
            msg = self.make_feedback("{function} returned nothing (None).")
            self.assertIsNotNone(result, msg=msg)
            # Did they return a list?
            msg = self.make_feedback("{function} must return a List.\n"
                                 "Instead it has returned a {t}",
                                 t=_human_type(result))
            self.assertIsInstance(result, list, msg=msg)
            # Was it empty?
            msg = self.make_feedback("{function} must return a non-empty List.\n"
                                 "Instead the list was empty")
            self.assertTrue(result, msg=msg)
            # Did they return a list of dictionaries?
            msg = self.make_feedback("{function} must return a List of Dictionaries.\n"
                                 "Instead it returned a List of {t}.",
                                 t=_human_type(result[0]))
            msgContains = self.make_feedback("{function} must return a list of Course dictionaries.\n"
                                             "But the course dictionaries were missing the 'id' field.")
            for index, item in enumerate(result):
                self.assertIsInstance(item, dict, msg=msg)
                self.assertIn("id", item, msg=msgContains)
            # Was the list correct?
            expected = reference[(user_id, course_id)]["filter_available_courses"][0]
            expected = ast.literal_eval(expected)
            expected.sort(key=lambda c: c['id'])
            result.sort(key=lambda c: c['id'])
            msg = self.make_feedback("{function} did not return the right list.")
            self.assertSequenceEqual(expected, result, msg=msg)
            
class TestCourseHandling(TestBase):
    
    @_skip_unless_callable(student_main, 'print_courses')
    def test_print_courses(self):
        "print_courses"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("courses = canvas_requests.get_courses({user_id!r})",
                                        "courses = filter_available_courses(courses)",
                                        "print_courses(courses)",
                                        user_id=user_id)
            courses = canvas_requests.get_courses(user_id)
            courses, _, _ = call_safely(student_main.filter_available_courses, courses)
            _, output, _ = call_safely(student_main.print_courses, courses)
            # Did they print?
            msg = self.make_feedback("{function} did not print anything.")
            self.assertNotEqual(output, "", msg=msg)
            # Did they print the essential components?
            msg = self.make_feedback("{function} did not print the correct value",
                                     user=user)
            expected = reference[(user_id, course_id)]["print_courses"]
            expected_joined = '\n'.join(expected)
            msg = self.make_feedback("{function} did not print the correct value\n"
                                     "Expected to see the following lines:\n"
                                     "{expected}\n"
                                     "Instead only found:\n"
                                     "{output}\n",
                                     expected=indent4(expected_joined),
                                     output=indent4(output))
            output = _normalize_string(output)
            for line in _normalize_string(expected_joined):
                self.assertIn(line, output, msg=msg)
            
    @_skip_unless_callable(student_main, 'get_course_ids')
    def test_get_course_ids(self):
        "get_course_ids"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("courses = canvas_requests.get_courses({user_id!r})",
                                        "courses = filter_available_courses(courses)",
                                        "get_course_ids(courses)",
                                        user_id=user_id)
            courses = canvas_requests.get_courses(user_id)
            courses, _, _ = call_safely(student_main.filter_available_courses, courses)
            result, _, _ = call_safely(student_main.get_course_ids, courses)
            # Did they return something?
            msg = self.make_feedback("{function} returned nothing (None).")
            self.assertIsNotNone(result, msg=msg)
            # Did they return a list?
            msg = self.make_feedback("{function} must return a List.\n"
                                 "Instead it has returned a {t}",
                                 t=_human_type(result))
            self.assertIsInstance(result, list, msg=msg)
            # Was it empty?
            msg = self.make_feedback("{function} must return a non-empty List.\n"
                                 "Instead the list was empty")
            self.assertTrue(result, msg=msg)
            # Did they return a list of dictionaries?
            msg = self.make_feedback("{function} must return a List of Integers.\n"
                                 "Instead it returned a List of {t}.",
                                 t=_human_type(result[0]))
            for index, item in enumerate(result):
                self.assertIsInstance(item, int, msg=msg)
            # Was the list correct?
            expected = reference[(user_id, course_id)]["get_course_ids"][0]
            expected = ast.literal_eval(expected)
            expected.sort()
            result.sort()
            msg = self.make_feedback("{function} did not return the right list.")
            self.assertSequenceEqual(expected, result, msg=msg)

class TestCourseInput(TestBase):
    @_skip_unless_callable(student_main, 'choose_course')
    def test_choose_course(self):
        "choose_course"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("courses = canvas_requests.get_courses({user_id!r})",
                                        "courses = filter_available_courses(courses)",
                                        "course_ids = get_course_ids(courses)",
                                        "# User intends to type in 10000, -1, and {course_id}",
                                        "choose_course(courses)",
                                        user_id=user_id,
                                        course_id=course_id)
            courses = canvas_requests.get_courses(user_id)
            courses, _, _ = call_safely(student_main.filter_available_courses, courses)
            course_ids, _, _ = call_safely(student_main.get_course_ids, courses)
            # TODO: Hard mode, include a non-integer
            input_values= ["10000", "-1", course_id]
            inputs = _make_inputs(*input_values)
            result, _, input_failed = call_safely(student_main.choose_course, course_ids, prompter=inputs)
            # Did the input fail?
            msg = self.make_feedback("{function} did not stop accepting valid inputs.\n"
                                     "Maybe an infinite loop happened?")
            self.assertFalse(input_failed, msg=msg)
            # Did they return something?
            msg = self.make_feedback("{function} returned nothing (None).")
            self.assertIsNotNone(result, msg=msg)
            # Did they return an integer?
            msg = self.make_feedback("{function} must return an Integer.\n"
                                 "Instead it has returned a {t}",
                                 t=_human_type(result))
            self.assertIsInstance(result, int, msg=msg)
            # Did they return the RIGHT integer?
            expected = reference[(user_id, course_id)]["choose_course"][0]
            expected = ast.literal_eval(expected)
            msg = self.make_feedback("{function} did not return the right value\n"
                                     " when I entered the inputs {inputs}.\n"
                                     "It should have returned {expected}.\n"
                                     "Instead it returned {actual}.",
                                     inputs=', '.join(input_values),
                                     expected=expected,
                                     actual=result)
            self.assertEqual(expected, result, msg=msg)
            
class TestSubmissions(TestBase):
    @_skip_unless_callable(student_main, 'summarize_points')
    def test_summarize_points(self):
        "summarize_points"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("submissions = canvas_requests.get_submissions({user_id!r}, {course_id!r})",
                                        "summarize_points(submissions)",
                                        user_id=user_id,
                                        course_id=course_id)
            submissions = canvas_requests.get_submissions(user_id, course_id)
            _, output, _ = call_safely(student_main.summarize_points, submissions)
            # Did they print?
            msg = self.make_feedback("{function} did not print anything")
            self.assertNotEqual(output, "", msg=msg)
            # Did they print the essential components?
            expected = reference[(user_id, course_id)]["summarize_points"]
            expected_joined = '\n'.join(expected)
            msg = self.make_feedback("{function} did not print the correct value\n"
                                     "Expected to see the following lines:\n"
                                     "{expected}\n"
                                     "Instead only found:\n"
                                     "{output}\n",
                                     expected=indent4(expected_joined),
                                     output=indent4(output))
            output = _normalize_string(output, numeric_endings=True)
            for line in _normalize_string('\n'.join(expected), numeric_endings=True):
                self.assertIn(line, output, msg=msg)
    
    @_skip_unless_callable(student_main, 'summarize_groups')
    def test_summarize_groups(self):
        "summarize_groups"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("submissions = canvas_requests.get_submissions({user_id!r}, {course_id!r})",
                                        "summarize_groups(submissions)",
                                        user_id=user_id,
                                        course_id=course_id)
            submissions = canvas_requests.get_submissions(user_id, course_id)
            _, output, _ = call_safely(student_main.summarize_groups, submissions)
            # Did they print?
            msg = self.make_feedback("{function} did not print anything\n")
            self.assertNotEqual(output, "", msg=msg)
            # Did they print the essential components?
            expected = reference[(user_id, course_id)]["summarize_groups"]
            expected_joined = '\n'.join(expected)
            msg = self.make_feedback("{function} did not print the correct value\n"
                                     "Expected to see the following:\n"
                                     "{expected}\n"
                                     "Instead only found:\n"
                                     "{output}\n"
                                     "Order does not matter, but the words and numbers do.\n"
                                     "It's okay to include categories without any graded submissions.",
                                     expected=indent4(expected_joined),
                                     output=indent4(output))
            output = _normalize_string(output, numeric_endings=True)
            for line in _normalize_string(expected_joined, numeric_endings=True):
                self.assertIn(line, output, msg=msg)
            
    @_skip_unless_callable(student_main, 'plot_scores')
    def test_plot_scores(self):
        "plot_scores"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("submissions = canvas_requests.get_submissions({user_id!r}, {course_id!r})",
                                        "plot_scores(submissions)",
                                        user_id=user_id,
                                        course_id=course_id)
            submissions = canvas_requests.get_submissions(user_id, course_id)
            _, output, _, mpl = call_safely(student_main.plot_scores, 
                                            submissions, matplotlib=True)
            # Did they forget to plot something?
            msg = self.make_feedback("{function} has an unshown plot\n"
                                     "Make sure you call plt.show().")
            self.assertFalse(mpl.unshown_plots(), msg=msg)
            # Do they have no plots?
            msg = self.make_feedback("{function} is not plotting anything\n")
            self.assertTrue(mpl.plots, msg=msg)
            # Do they have too many plots?
            msg = self.make_feedback("{function} has more than one plot\n")
            self.assertEqual(len(mpl.plots), 1, msg=msg)
            # Do they have any data?
            plot = mpl.plots[0]
            plot_data = plot['data']
            msg = self.make_feedback("{function} is not plotting any data\n")
            self.assertTrue(plot_data, msg=msg)
            # Do they have too much data?
            msg = self.make_feedback("{function} is plotting too many things\n")
            self.assertEqual(len(plot_data), 1, msg=msg)
            # Did they make the right kind of plot?
            histogram = plot_data[0]
            msg = self.make_feedback("{function} did not produce a Histogram\n")
            self.assertEqual(histogram['type'], 'Histogram', msg=msg)
            # Did they plot the right amount of data?
            expected = reference[(user_id, course_id)]["plot_scores"][0]
            expected = ast.literal_eval(expected)
            msg = self.make_feedback("{function} did not plot the right number of things\n"
                                     +"You should only plot assignments with points possible\n"
                                     +"and with a score that is not None.")
            self.assertEqual(len(histogram['values']), len(expected), msg=msg)
            # Did they plot the actual right data
            actual = sorted(histogram['values'])
            expected.sort()
            msg = self.make_feedback("{function} did not plot the right data\n"
                                     +" Expected: "+fp.pformat(expected)
                                     +"\n Actual: "+fp.pformat(actual))
            for i, (student, correct) in enumerate(zip(actual, expected)):
                self.assertAlmostEqual(student, correct, TOLERANCE, msg=msg)
            # Did they have titles?
            msg = self.make_feedback('{function} did not have the right title ("Distribution of Grades")\n')
            self.assertIsNotNone(plot['title'], msg=msg)
            self.assertSimilarStrings(plot['title'], "Distribution of Grades", msg=msg)
            msg = self.make_feedback('{function} did not have the right xlabel ("Grades")\n')
            self.assertIsNotNone(plot['xlabel'], msg=msg)
            self.assertSimilarStrings(plot['xlabel'], "Grades", msg=msg)
            msg = self.make_feedback('{function} did not have the right ylabel ("Number of Assignments").\n')
            self.assertIsNotNone(plot['ylabel'], msg=msg)
            self.assertSimilarStrings(plot['ylabel'], "Number of Assignments", msg=msg)
                
    @_skip_unless_callable(student_main, 'plot_grade_trends')
    def test_plot_grade_trends(self):
        "plot_grade_trends"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("submissions = canvas_requests.get_submissions({user_id!r}, {course_id!r})",
                                        "plot_grade_trends(submissions)",
                                        user_id=user_id,
                                        course_id=course_id)
            submissions = canvas_requests.get_submissions(user_id, course_id)
            _, output, _, mpl = call_safely(student_main.plot_grade_trends, 
                                            submissions, matplotlib=True)
            # Did they forget to plot something?
            msg = self.make_feedback("{function} has an unshown plot\n"+
                                     "Make sure you call plt.show().")
            self.assertFalse(mpl.unshown_plots(), msg=msg)
            # Do they have no plots?
            msg = self.make_feedback("{function} is not plotting anything\n")
            self.assertTrue(mpl.plots, msg=msg)
            # Do they have too many plots?
            msg = self.make_feedback("{function} has more than one plot\n")
            self.assertEqual(len(mpl.plots), 1, msg=msg)
            # Do they have any data?
            plot = mpl.plots[0]
            plot_data = plot['data']
            msg = self.make_feedback("{function} is not plotting any data\n")
            self.assertTrue(plot_data, msg=msg)
            # Extract the reference data
            expecteds = reference[(user_id, course_id)]["plot_grade_trends"]
            expecteds = [e for e in expecteds if e]
            dates, highs, lows, maxes = map(ast.literal_eval, expecteds)
            dates = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S') for d in dates]
            expected_plots = {'highest': highs, 
                              'lowest': lows, 
                              'maximum': maxes}
            # Do they have the labels?
            plotted_labels = [l['label'] for l in plot_data if l['label']]
            msg = self.make_feedback("{function} has no labels on its plots\n")
            self.assertGreater(len(plotted_labels), 0, msg=msg)
            user_plots = {x['label'].lower(): x for x in plot_data
                          if x['label']}
            msg = self.make_feedback("{function} has an unexpected label\n")
            for label in user_plots:
                self.assertIn(label.lower(), expected_plots, msg=msg)
            # Chck each plot in turn
            all_plotted = True
            for label, data in expected_plots.items():
                if label not in user_plots:
                    all_plotted = False
                    continue
                actual = user_plots[label]
                msg = self.make_feedback("{function} did not produce a line plot for {label}\n",
                                         label=label)
                self.assertEqual(actual['type'], 'Line', msg=msg)
                # Assert y-axis length
                msg = self.make_feedback("{function} did not plot correctly\n"
                                     +"The {label} line plot had the wrong number of\n"
                                     +"elements on the Y-axis.\n"
                                     +"You should be plotting every single submission.",
                                     label=label)
                self.assertEqual(len(actual['y']), len(data), msg=msg)
                # Assert y-axis length
                msg = self.make_feedback("{function} did not plot correctly\n"
                                     +"The {label} line plot had the wrong number of\n"
                                     +"elements on the X-axis.\n"
                                     +"You should be plotting every single submission.",
                                     label=label)
                self.assertEqual(len(actual['x']), len(dates), msg=msg)
                # Assert x-axis values
                matched_xs = zip(sorted(actual['x']), sorted(dates))
                for i, (s, c) in enumerate(matched_xs):
                    msg = self.make_feedback("{function} has incorrect X axis values\n"
                                             +"You did not plot datetimes for the {label}.\n",
                                             label=label)
                    self.assertIsInstance(s, datetime, msg=msg)
                    msg = self.make_feedback("{function} did not plot correctly\n"
                                             +"You have plotted the wrong X data for the {label}\n"
                                             +"(position {i} in the list)",
                                             label=label, i=i)
                    self.assertAlmostEqual(s, c, delta=TIME_TOLERANCE, msg=msg)
                # Assert y-axis values
                student_ys = group_by_value(actual['x'], actual['y'])
                expected_ys = group_by_value(dates, data)
                for d in dates:
                    # Did they plot all the Y values for this date?
                    msg = self.make_feedback("{function} has incorrect Y axis values\n"
                                             +"The {label} line has no values for the date {date}.",
                                             label=label,date=d)
                    self.assertIn(d, student_ys, msg=msg)
                    # Did they get the right number of Y values?
                    s_ys = student_ys[d]
                    c_ys = expected_ys[d]
                    msg = self.make_feedback("{function} has incorrect Y axis values\n"
                                             +"The {label} line has the wrong number of values for date {date}.",
                                             label=label,date=d)
                    self.assertEqual(len(c_ys), len(s_ys), msg=msg)
                    msg = self.make_feedback("{function} has incorrect Y axis values\n"
                                             +"The {label} line has the wrong values for date {date}.",
                                             label=label,date=d)
                    self.assertAlmostEqual(c_ys[-1], s_ys[-1], TOLERANCE, msg=msg)
            # Did they actually plot everything?
            msg = self.make_feedback("{function} does not have 3 labelled line plots\n")
            self.assertTrue(all_plotted, msg=msg)
            # Did they have titles?
            msg = self.make_feedback("{function} did not have the right title\n")
            self.assertIsNotNone(plot['title'], msg=msg)
            self.assertSimilarStrings(plot['title'], "Grade Trend", msg=msg)
            msg = self.make_feedback("{function} did not have the right ylabel\n")
            self.assertIsNotNone(plot['ylabel'], msg=msg)
            self.assertSimilarStrings(plot['ylabel'], "Grade", msg=msg)
            
class TestMain(TestBase):
    @_skip_unless_callable(student_main, 'main')
    def test_main(self):
        "main"
        for (user_id, course_id), data in reference.items():
            self.example = _run_example("# User types 10000, -1, {course_id}",
                                        "main({user_id!r})",
                                        user_id=user_id,
                                        course_id=course_id)
            input_values= ["10000", "-1", course_id]
            inputs = _make_inputs(*input_values)
            _,output,i,mpl = call_safely(student_main.main, user_id, prompter=inputs, matplotlib=True)
            # Did they terminate?
            msg = self.make_feedback("{function} did not stop accepting valid inputs.")
            self.assertFalse(i, msg=msg)
            # Did they print?
            msg = self.make_feedback("{function} did not print anything.")
            self.assertNotEqual(output, "", msg=msg)
            # Did they print the essential components?
            msg = self.make_feedback("{function} did not print the correct value")
            expected = reference[(user_id, course_id)]
            printing_functions = ['print_user_info', 'print_courses', 
                                  'summarize_points', 'summarize_groups']
            printing_functions = [f for f in printing_functions
                                  if hasattr(student_main, f)]
            for function_name in printing_functions:
                expected_joined = '\n'.join(expected[function_name])
                msg = self.make_feedback("{function} did not print the correct value\n"
                                         "Expected to see the following lines:\n"
                                         "{expected}\n"
                                         "Instead only found:\n"
                                         "{output}\n"
                                         "Perhaps the {inner} function was not called?",
                                         expected=indent4(expected_joined),
                                         output=indent4(output),
                                         inner=function_name)
                norm_out = _normalize_string(output, numeric_endings=True)
                for line in _normalize_string(expected_joined, numeric_endings=True):
                    self.assertIn(line, norm_out, msg=msg)
            # Did they have plots?
            plotting_functions = ['plot_scores', 'plot_grade_trends']
            plotting_functions = [f for f in plotting_functions
                                  if hasattr(student_main, f)]
            msg = self.make_feedback("{function} did not create the right number of plots.\n",
                                     "You were supposed to only need {plots}",
                                     plots=len(plotting_functions))
            self.assertEqual(len(mpl.plots), len(plotting_functions), msg=msg)
            # Did they call all the functions they needed?
            all_functions = (printing_functions + plotting_functions
                             + ['filter_available_courses', 'get_course_ids', 
                                'choose_course', ])
            main_declaration = inspect.getsource(student_main.main)
            all_nodes = ast.walk(ast.parse(main_declaration))
            all_calls = [node.func.id for node in all_nodes
                          if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Name)]
            for function_name in all_functions:
                if hasattr(student_main, function_name):
                    msg = self.make_feedback("{function} did not seem to call {inner}.",
                                             inner=function_name)
                    self.assertIn(function_name, all_calls, msg=msg)

_TEST_PHASES = [("User Info and Course Filter", TestFunctions),
                ("Course Handling", TestCourseHandling),
                ("Course Input", TestCourseInput),
                ("Submissions", TestSubmissions),
                ("Main Function", TestMain)]

#%% Run unit tests
if __name__ == "__main__":
    _run_unit_tests(_TEST_PHASES)