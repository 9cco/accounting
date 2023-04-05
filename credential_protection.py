import base64
import argon2
import math
import sys
import os
import re
import getpass
from secrets import token_bytes
from cryptography.fernet import Fernet

from aux_functions import saveDictToJson, eprint, loadJsonFile

FERNET_KEY_LENGTH = 32

# This outputs the hash as a bytes object with len = hash_len. We assume password is a string, while salt is a
# bytes object.
def argon2Hash(password, salt, time_cost = 3, memory_cost = 102400, parallelism = 8, hash_len = 16,\
               type=argon2.low_level.Type.ID):
    return argon2.low_level.hash_secret_raw(password.encode(), salt, time_cost = time_cost, memory_cost = memory_cost,\
                                    parallelism = parallelism, hash_len = hash_len, type=type)

class EncryptionParameters:
    def __init__(self, time_cost = 3, memory_cost = 102400, parallelism = 8):
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism

    def __str__(self):
        return f"[time_cost: {self.time_cost}, memory_cost: {self.memory_cost}, parallelism: {self.parallelism}]"

    def makeDict(self):
        return {'time_cost' : self.time_cost, 'memory_cost' : self.memory_cost, 'parallelism' : self.parallelism}

def argon2Key(password, salt, hash_len, params):
    return argon2Hash(password, salt, time_cost = params.time_cost, memory_cost = params.memory_cost, parallelism = params.parallelism,\
            hash_len = hash_len, type = argon2.low_level.Type.ID)

# Takes a password and a key-length and generates a salt. Then derives a key based on the salt and password of the specified length
# using Argon2 PBKDF.
def argon2SaltAndKey(password, key_length = FERNET_KEY_LENGTH, params = EncryptionParameters()):

    # Want a salt length between 16 and 512
    salt_length = min(max(key_length, 16), 512)
    salt = token_bytes(salt_length)

    key = argon2Key(password, salt, key_length, params)
    return salt, key, params

# Encrypt a data string object using a password. This password generates a key using Argon2 which is
# used to encrypt the data using AES-256. The output is two b64 encoded strings as well as a EncryptionParameters object.
# The first string is the salt, used in
# the key derivation, while the other is the encrypted b64-encoded string of the data.
def encrypt(password, data, params = EncryptionParameters()):

    # Key derivation
    salt, key, _ = argon2SaltAndKey(password, key_length = FERNET_KEY_LENGTH, params = params)
    b64_key = base64.urlsafe_b64encode(key)

    # Encryption with AES
    f = Fernet(b64_key)
    ciphertext = f.encrypt(data.encode()).decode()

    # Externally to the encrypt/decrypt function, we want to use only strings, so we need to convert the salt to a
    # b64 encoded string
    salt_str = base64.urlsafe_b64encode(salt).decode()

    return salt_str, ciphertext, params

# Generates a Fernet object given a password, a salt string and a parameter object
def generateFernet(password, salt_str, params):

    # Decode the salt into a bytes object
    salt = base64.urlsafe_b64decode(salt_str.encode())

    # Re-generate / derive the key.
    key = argon2Key(password, salt, FERNET_KEY_LENGTH, params)
    b64_key = base64.urlsafe_b64encode(key)

    # Return AES object.
    return Fernet(b64_key)


# Does the reverse of 'encrypt' function.
def decrypt(password, salt_str, ciphertext, parms):
    
    # Get AES Fernet object
    f = generateFernet(password, salt_str, parms)
    cleartext = f.decrypt(ciphertext.encode()).decode()

    return cleartext

# Also need a similar function to encrypt, but where we specify the salt and parameters for encryption
def encryptWithParameters(password, salt_str, data, params):
    
    # Encryption with AES
    f = generateFernet(password, salt_str, params)
    ciphertext = f.encrypt(data.encode()).decode()
    
    return ciphertext

# Credential class which defines encryptable credential data. Consists of variables 'name' (str), 'check' (str),
# 'salt' (str), 'data' (str), and 'encrypted' (bool)
class Credential:
    def __init__(self, *args):
        # Constructor for a credential using a dictionary where we assume the dictionary has the structure
        # {'name', 'check', 'salt', 'data', 'encrypted'}
        if len(args) == 1 and isinstance(args[0], dict):
            dick = args[0]
            self.setVariables(dick['name'], dick['check'], dick['salt'], dick['data'], dick['encrypted'])
        elif len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
            name = args[0]
            data = args[1]
            self.setVariables(name, name, None, data, False)
        else:
            raise Exception("ERROR: argument list \n{args}\n not supported for constructor of Credential class")

    def __str__(self):
        return f"{{\n  name: {self.name},\n  check: {self.check},\n  salt: {self.salt},\n  data: {self.data},\n  encrypted: {self.encrypted}\n}}"

    def setVariables(self, name, check, salt, data, encrypted):
        self.name = name
        self.check = check
        self.salt = salt
        self.data = data
        self.encrypted = encrypted

    def makeDict(self):
        return {'name' : self.name, 'check' : self.check, 'salt' : self.salt, 'data' : self.data, 'encrypted' : self.encrypted}

    # Checks to see if the object is decrypted by checking if the name equals the check and the reported status of "encrypted" is False.
    def isDecrypted(self):
        checked = self.name == self.check
        if (not checked) and (not self.encrypted):
            raise Exception(f"Error in dictionary {self.name}. It says it is decrypted, but check is not equal to name.")
        elif checked and self.encrypted:
            raise Exception(f"Error in dictionary {self.name}. It says it is encrypted, but the name equals the check.")
        elif self.encrypted and (not checked):
            return False
        else:
            return True

    # Encrypts the data and check-value of the credential. Returns the parameters used for encryption.
    def encryptCredential(self, password, params):
        if self.isDecrypted():
            salt_str, data_cipher, _ = encrypt(password, self.data, params=params)
            check_cipher = encryptWithParameters(password, salt_str, self.check, params)

            self.check = check_cipher
            self.data = data_cipher
            self.salt = salt_str
            self.encrypted = True
        else:
            raise Exception(f"ERROR encryptionCredential: {self.name} is already encrypted.")

        return params

    def decryptCredential(self, password, params):
        # Check that the object can be decrypted.
        if (not self.isDecrypted()) and self.salt != None:
            # Decrypt data and decryption check.
            clear_data = decrypt(password, self.salt, self.data, params)
            clear_check = decrypt(password, self.salt, self.check, params)

            # Raise error if the decryption was unsuccessful.
            if not clear_check == self.name:
                raise Exception(f"Error decrypting credential {self.name}. Got decrypted check {clear_check}.")

            # Mutate object
            self.check = clear_check
            self.salt = None
            self.data = clear_data
            self.encrypted = False

        return

# Load files into Credentials objects in a list
# {'name', 'check', 'salt', 'data', 'encrypted'}
def loadCleartextCredentials(folder_name = 'credentials'):
    # Make a path starting at the script location.
    script_folder = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
    path = os.path.join(script_folder, folder_name)

    # Find files by listing the contents of folder_name and storing only paths to files.
    files = [fname for fname in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, fname))]

    credz = []
    for file in files:

        name = re.sub(r'\.[^\.]+$', '', file)
        path = os.path.join(folder_name, file)

        # Read content of file
        with open(path, 'r') as f:
            data = f.read().strip()

        cred = Credential(name, data)
        credz.append(cred)

    return credz

# Encrypt all credentials in list
def encryptCredentialList(password, credz, params):
    for cred in credz:
        cred.encryptCredential(password, params)
    return

# Decrypt all credentials in a list
def decryptCredentialList(password, credz, params):
    for cred in credz:
        cred.decryptCredential(password, params)
    return

# Function finds the size of the alphabeth used by assuming conventional forms like [A-Z], [a-z], [0-9], etc.
# and uses this to evaluate the bit complexity of the password. Uses this to give the password an adjective
# from the list: terribly weak, weak, ok, strong, very strong, insanely paranoid
def evaluatePassword(password):
    adjective = 'weak'
    bits = 10
    string_length = len(password)
    alpha_size = 0

    if re.search(r'[a-z]', password):
        alpha_size += 26
    if re.search(r'[A-Z]', password):
        alpha_size += 26
    if re.search(r'[0-9]', password):
        alpha_size += 10

    # Remove all characters of the above alphabets from password.
    aux_string = re.sub(r'[A-Za-z0-9]', "", password)
    # Count the number of distinct characters not in the above ranges.
    extra_chars = len(set(aux_string))
    alpha_size += extra_chars

    # Calculate bits
    bits = int(round(math.log2(alpha_size) * string_length, 0))

    if bits in range(0,40):
        adjective = 'terribly weak'
    elif bits in range(41, 68):
        adjective = 'weak'
    elif bits in range(69, 80):
        adjective = 'ok'
    elif bits in range(81, 100):
        adjective = 'strong'
    elif bits in range(101, 160):
        adjective = 'excellent'
    elif bits > 160:
        adjective = 'insanely paranoid'

    return adjective, bits

# Gets a password from the user for settings a password. Makes sure that they wrote correctly
# by asking two times.
def getPassword():
    while True:
        password = getpass.getpass("Enter password for encrypting credentials: ")
        password2 = getpass.getpass("Please repeat the password: ")
        if password == password2:
            break
        else:
            print("ERROR: The passwords did not match. Please try again.\n")

    adjective, bits = evaluatePassword(password)
    print(f"Passwords match and is {adjective} ({bits} bits). Please remember to save it in your password manager.")
    return password

# Takes a list of Credential objects,
# asks the user for a password, uses the password to encrypt the credentials,
# writes a dictionary with encrypted credentials as well as encryption information
# to a json file in the folder the script is located in.
def encryptCredentialsToFile(credz, output_fn = 'api_credentials.json'):

    # Check if output file exists already
    # Get current script folder path
    script_folder = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
    path = os.path.join(script_folder, output_fn)

    if os.path.exists(path):
        # Ask the user if overwriting is ok.
        choice = input(f"Warning: '{path}' already exists. Overwrite? (y/n): ")
        if not 'y' in choice.lower():
            raise Exception("File already exists!")

    # Get a password from the user.
    password = getPassword()

    # Set encryption parameters to default values.
    parameters = EncryptionParameters()
    # Encrypt data in the credentials.
    encryptCredentialList(password, credz, parameters)

    # Create final dictionary
    final_dictionary = {'parameters' : parameters.makeDict(), 'credentials' : [cred.makeDict() for cred in credz]}

    # Write this dictionary to file
    saveDictToJson(final_dictionary, path)
    print("Credentials successfully encrypted. You can now delete the cleartext copy.")
    return output_fn

# Combine function checks if the credential in import_list exists in source
# list before adding it to it. Warn the user if such a conflict occurs. Only add credentials
# that are unique.
def combineCredentials(source_list, import_list):
    # Make shallow copy of list.
    combined_list = source_list[:]
    source_names = [cred.name for cred in source_list]
    for cred in import_list:
        if cred.name in source_names:
            eprint(f"Warning: {cred.name} exists in both lists. Skipping import of duplicate.")
        else:
            combined_list.append(cred)

    return combined_list

# Takes the folder where cleartext credentials are stored, as well as the filename where encrypted
# credentials are stored. First loads the cleartext credentials if they exist, then attempts to
# decrypt any encrypted credentials in the output_fn. Exits if no credentials are found. Finally
# adds all credentials together in a list of dictionaries and outputs this.
def loadCredentials(folder_name = 'credentials', output_fn = 'api_credentials.json'):
    
    # Load cleartext credentials.
    try:
        cleartext_credz = loadCleartextCredentials(folder_name = folder_name)
    except:
        cleartext_credz = []
    
    # Load encrypted credentials to objects
    try:
        encrypted_dict = loadJsonFile(output_fn)
    except:
        eprint(f"Warning: File {output_fn} not found.")
        return cleartext_credz
    enc_credz = [Credential(dick) for dick in encrypted_dict['credentials']]
    params_dict = encrypted_dict['parameters']
    parameters = EncryptionParameters(time_cost = params_dict['time_cost'], memory_cost = \
                                     params_dict['memory_cost'], parallelism = params_dict['parallelism'])
    
    # Decrypt encrypted data
    while True:
        password = getpass.getpass("Enter password for decrypting credentials: ")
        try:
            decryptCredentialList(password, enc_credz, parameters)
            break
        except Exception as e:
            choice = input("ERROR during decryption process. Perhaps you entered the wrong password. Try again? (y/n): ")
            if not 'y' in choice.lower():
                raise e
                exit(-1)
    
    # Check if data was correctly decrypted
    for cred in enc_credz:
        if not cred.isDecrypted():
            raise Exception(f"ERROR: The credential {cred.name} was not correctly decrypted")
        
    return combineCredentials(enc_credz, cleartext_credz)

def main(argv):

    password = "Password123"
    salt, key, _ = argon2SaltAndKey(password, key_length = FERNET_KEY_LENGTH)
    print(key)
    print(salt)
    data = "my selcret romance"
    salt_str, ciphertext, parms = encrypt(password, data)
    print(salt_str)
    print(f"\n{data} => {ciphertext}")
    cleartext = decrypt(password, salt_str, ciphertext, parms)
    print(f"\n{ciphertext} => {cleartext}")

    credz = loadCleartextCredentials()
    for cred in credz:
        print(cred)

    encryptCredentialsToFile(credz, output_fn = "encrypted_credz.json")
    print("File saved successfully.\n")

    print("Loading credentials from cleartext and encrypted.")
    cred_list = loadCredentials()
    print("Loaded credentials:")
    for cred in cred_list:
        print(cred.name)
    print()

    return

if __name__ == "__main__":
   main(sys.argv[1:])
 
