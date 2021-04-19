from sli.tools import expandedHomePath
import os
import json

"""
SLI's context manager, load, manipulate, and store context objects
"""

class ContextManager():

    def __init__(self, options):
        self._setup_directory()
        self.options = options
        self.use_context = self.options.get('use_context')
        self.context_dir = expandedHomePath('.sli/context')
        self.context_file = '' # Populated when loading context
    
    @staticmethod
    def _setup_directory():
        """Create initial directories required for context management in SLI"""
        directories = [expandedHomePath(d) for d in ['.sli', '.sli/skillets', '.sli/context']]
        for directory in directories:
            if not os.path.exists(directory):
                os.mkdir(directory)

    def loadContext(self):
        """Load a context from disk"""
        context = {}

        # If not loading a context, return the blank context
        if not self.use_context:
            return context
        
        # Unless a context name is specified, assume default context
        context_name = self.options.get('context_name', 'default')
        self.context_file = expandedHomePath(f'.sli/context/{context_name}.json')

        # If specified context file not found, return blank context
        if not os.path.exists(self.context_file):
            return context
        
        try:
            with open(self.context_file, 'r') as f:
                context_file_json = json.loads(f.read())
        except Exception as e:
            print(f"Error loading context file {self.context_file} - {e}")
            return context

        # Check for encryption and decrypt stored value if found
        if context_file_json.get('encrypted'):
            pass

        # Assume unencrypted context content, return context
        return context_file_json.get('context', context)

    
    def saveContext(self, context):
        """Save a context to disk"""

        # If not configured to use a context do nothing
        if not self.use_context:
            return

        # Write unencrypted context
        with open(self.context_file, 'w') as f:
            write_dict = {
                'encrypted': False,
                'context': context
            }
            f.write(json.dumps(write_dict, indent=4))