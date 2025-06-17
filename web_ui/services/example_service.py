"""Example management service"""

import os

class ExampleService:
    """Service for managing MDP examples"""
    
    def __init__(self):
        self.example_descriptions = {
            'input0.txt': 'Simple 3-node example',
            'input1.txt': 'Maze navigation problem',
            'input2.txt': 'Publisher decision tree',
            'input3.txt': 'Restaurant choice problem',
            'input4.txt': 'Student Markov process (chance nodes)',
            'input5.txt': 'Student MDP (decision nodes)',
            'input6.txt': 'Academic career progression'
        }
    
    def get_examples_directory(self):
        """Get the path to the examples directory"""
        current_dir = os.path.dirname(os.path.abspath(__file__))  # services directory
        web_ui_dir = os.path.dirname(current_dir)  # web_ui directory
        parent_dir = os.path.dirname(web_ui_dir)  # MDP_Solver directory
        return os.path.join(parent_dir, 'tests', 'input_files')
    
    def load_examples(self):
        """Load all available examples"""
        examples = []
        test_dir = self.get_examples_directory()
        
        if not os.path.exists(test_dir):
            print(f"Test directory does not exist: {test_dir}")
            return []
        
        for filename in sorted(os.listdir(test_dir)):
            if filename.endswith('.txt') and filename != 'test.txt':
                filepath = os.path.join(test_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    examples.append({
                        'name': filename.replace('.txt', '').replace('input', 'Example '),
                        'description': self.example_descriptions.get(filename, 'MDP example'),
                        'content': content,
                        'filename': filename
                    })
                except Exception as e:
                    print(f"Error loading example {filename}: {e}")
                    continue
        
        return examples
    
    def get_example_by_filename(self, filename):
        """Get a specific example by filename"""
        test_dir = self.get_examples_directory()
        filepath = os.path.join(test_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            return {
                'name': filename.replace('.txt', '').replace('input', 'Example '),
                'description': self.example_descriptions.get(filename, 'MDP example'),
                'content': content,
                'filename': filename
            }
        except Exception as e:
            print(f"Error loading example {filename}: {e}")
            return None
