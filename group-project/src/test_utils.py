import unittest
import sys
import os

# Add the parent directory to the path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from utils import calculate_statistics, validate_username


class TestCalculateStatistics(unittest.TestCase):
    """Test cases for calculate_statistics function"""
    
    def test_valid_integer_list(self):
        """Test with a list of valid integers"""
        numbers = [1, 2, 3, 4, 5]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 15)
        self.assertEqual(result["average"], 3.0)
        self.assertEqual(result["max"], 5)
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["count"], 5)
    
    def test_valid_float_list(self):
        """Test with a list of valid floats"""
        numbers = [1.5, 2.5, 3.5, 4.5]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 12.0)
        self.assertEqual(result["average"], 3.0)
        self.assertEqual(result["max"], 4.5)
        self.assertEqual(result["min"], 1.5)
        self.assertEqual(result["count"], 4)
    
    def test_mixed_number_list(self):
        """Test with a list of mixed integers and floats"""
        numbers = [1, 2.5, 3, 4.5, 5]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 16.0)
        self.assertEqual(result["average"], 3.2)
        self.assertEqual(result["max"], 5)
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["count"], 5)
    
    def test_single_element_list(self):
        """Test with a list containing only one element"""
        numbers = [42]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 42)
        self.assertEqual(result["average"], 42.0)
        self.assertEqual(result["max"], 42)
        self.assertEqual(result["min"], 42)
        self.assertEqual(result["count"], 1)
    
    def test_list_with_non_numeric_elements(self):
        """Test with a list containing non-numeric elements"""
        numbers = [1, 2, "three", 4, 5, None]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 12)
        self.assertEqual(result["average"], 3.0)
        self.assertEqual(result["max"], 5)
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["count"], 4)
    
    def test_empty_list(self):
        """Test with an empty list"""
        result = calculate_statistics([])
        self.assertIsNone(result)
    
    def test_list_with_only_non_numeric_elements(self):
        """Test with a list containing only non-numeric elements"""
        numbers = ["one", "two", "three", None, []]
        result = calculate_statistics(numbers)
        self.assertIsNone(result)
    
    def test_invalid_input_type(self):
        """Test with invalid input type (not a list)"""
        with self.assertRaises(TypeError):
            calculate_statistics("not a list")
        
        with self.assertRaises(TypeError):
            calculate_statistics(123)
        
        with self.assertRaises(TypeError):
            calculate_statistics(None)
    
    def test_negative_numbers(self):
        """Test with negative numbers"""
        numbers = [-5, -2, 0, 3, 7]
        result = calculate_statistics(numbers)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["sum"], 3)
        self.assertEqual(result["average"], 0.6)
        self.assertEqual(result["max"], 7)
        self.assertEqual(result["min"], -5)
        self.assertEqual(result["count"], 5)


class TestValidateUsername(unittest.TestCase):
    """Test cases for validate_username function"""
    
    def test_valid_usernames(self):
        """Test various valid usernames"""
        valid_usernames = [
            "user",      # minimum length
            "john123",   # alphanumeric
            "AliceSmith", # mixed case
            "test_user_123", # with underscores
            "a" * 20,    # maximum length
            "abc123",    # typical username
        ]
        
        for username in valid_usernames:
            with self.subTest(username=username):
                self.assertTrue(validate_username(username))
    
    def test_too_short_username(self):
        """Test usernames that are too short"""
        short_usernames = ["", "a", "ab"]
        
        for username in short_usernames:
            with self.subTest(username=username):
                self.assertFalse(validate_username(username))
    
    def test_too_long_username(self):
        """Test usernames that are too long"""
        long_username = "a" * 21
        self.assertFalse(validate_username(long_username))
    
    def test_usernames_with_special_characters(self):
        """Test usernames containing special characters"""
        invalid_usernames = [
            "user@name",
            "user-name",
            "user name",
            "user.name",
            "user#name",
            "user$name",
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                self.assertFalse(validate_username(username))
    
    def test_usernames_starting_with_number(self):
        """Test usernames that start with a number"""
        invalid_usernames = [
            "1user",
            "123abc",
            "9test",
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                self.assertFalse(validate_username(username))
    
    def test_non_string_inputs(self):
        """Test with non-string inputs"""
        invalid_inputs = [123, None, [], {}, 45.6]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input=invalid_input):
                self.assertFalse(validate_username(invalid_input))
    
    def test_boundary_lengths(self):
        """Test usernames at boundary lengths"""
        # Minimum valid length (3 characters)
        self.assertTrue(validate_username("abc"))
        
        # Maximum valid length (20 characters)
        self.assertTrue(validate_username("a" * 20))
        
        # Just below minimum (2 characters)
        self.assertFalse(validate_username("ab"))
        
        # Just above maximum (21 characters)
        self.assertFalse(validate_username("a" * 21))


if __name__ == "__main__":
    unittest.main()