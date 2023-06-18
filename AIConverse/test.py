import unittest
import os
import glob

# Create a test case class
class MyTestCase(unittest.TestCase):
    def test_something(self):
        # Test your code here
        self.assertEqual(2 + 2, 4)

# Get the list of all Python files in the current directory
python_files = glob.glob('*.py')

# Create a test suite
test_suite = unittest.TestSuite()

# Iterate over each Python file and add the test case to the test suite
for file in python_files:
    module_name = os.path.splitext(file)[0]
    module = __import__(module_name)
    tests = unittest.defaultTestLoader.loadTestsFromModule(module)
    test_suite.addTests(tests)

# Run the test suite
unittest.TextTestRunner().run(test_suite)
