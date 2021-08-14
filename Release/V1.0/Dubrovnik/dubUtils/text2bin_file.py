import os

os.chdir(r'C:\MyLibs\Dubrovnik\dubScripts')
os.getcwd()

# Create a text file in Notepad
# Copy and paste text content and save it as "a_textfile.txt"

# ***************************
#  Read text file
# ***************************
datafile = 'a_textfile.txt'
with open(datafile, 'r') as fh:
    data_array = fh.read()
# print(data_array)

# ********************************
#  Convert text into binary format
# ********************************
# bindata = bytearray(b'abcdefgh')
bindata = bytes(data_array, 'utf-8')
# bindata = data_array.encode()

# ****************************************
#  Create binary file and write data to it
# ****************************************
binfile = 'a_binary_file.bin'
with open(binfile, 'wb') as fh:
    fh.write(bindata)

# ******************************************
#  Read back binary file and print to verify
# ******************************************
with open(binfile, 'rb') as fh:
    df = fh.read()
print(df)
