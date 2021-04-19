from sli.tools import expandedHomePath
import os
import json
import getpass
from sli.encrypt import Encryptor

"""
SLI's context manager, load, manipulate, and store context objects
"""

class ContextManager():

    def __init__(self, options):
        self._setup_directory()
        self.options = options
        self.use_context = self.options.get('use_context')
        self.encrypt_context = self.options.get('use_context')
        self.context_dir = expandedHomePath('.sli/context')
        self.context_file = '' # Populated when loading context
        self.context_password = options.get('context_password', '')
    
    @staticmethod
    def _setup_directory():
        """Create initial directories required for context management in SLI"""
        directories = [expandedHomePath(d) for d in ['.sli', '.sli/skillets', '.sli/context']]
        for directory in directories:
            if not os.path.exists(directory):
                os.mkdir(directory)
    
    def _get_context_password(self):
        """Returns user supplied password for context"""
        if len(self.context_password) > 0:
            return self.context_password
        self.context_password = getpass.getpass('Context encryption password: ')
        return self.context_password


    def loadContext(self):
        """Load a context from disk"""
        context = {}

        # Unless a context name is specified, assume default context
        context_name = self.options.get('context_name', 'default')
        self.context_file = expandedHomePath(f'.sli/context/{context_name}.json')

        if not context_name == 'default':
            self.use_context = True

        # If not loading a context, return the blank context
        if not self.use_context:
            return context

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
            self.encrypt_context = True # Make sure we encrypt the written file at the end
            content = context_file_json.get('encrypted_context')
            if not content:
                raise ValueError(
                    'Context has encryption specified, but encrypted_context not found'
                    )
            password = self._get_context_password()
            decrypted = False
            while not decrypted:
                try:
                    encryptor = Encryptor(password)
                    decrypted_dict = encryptor.decrypt_dict(content)
                    decrypted = True
                except json.decoder.JSONDecodeError:
                    print('Invalid context decryption key\n')
                    self.context_password = ''
                    password = self._get_context_password()
            return decrypted_dict

        # Assume unencrypted context content, return context
        return context_file_json.get('context', context)

    
    def saveContext(self, context):
        """Save a context to disk"""

        # If not configured to use a context do nothing
        if not self.use_context:
            return
        
        # If required write encrypted context file
        if self.encrypt_context:

            if len(self.context_password) < 1:
                # We don't currently have a context password set, lets create one
                matches = False
                new_password = ''
                while not matches:
                    new_password = getpass.getpass('New context encryption password: ')
                    confirm_password = getpass.getpass('Confirm password: ')
                    matches = new_password == confirm_password and len(new_password) > 0
                    if not matches:
                        print('Passwords did not match.\n')
                self.context_password = new_password

            encryptor = Encryptor(self.context_password)
            encrypted_context = encryptor.encrypt_dict(context)
            with open(self.context_file, 'w') as f:
                write_dict = {
                    'encrypted': True,
                    'encrypted_context': encrypted_context
                }
                f.write(json.dumps(write_dict, indent=4))

        else:
            # Write unencrypted context
            with open(self.context_file, 'w') as f:
                write_dict = {
                    'encrypted': False,
                    'context': context
                }
                f.write(json.dumps(write_dict, indent=4))