import sys
import serial
import time
import random

# Print tool's comamnd line syntax.
def usage():
	print("Usage:", tool_name, "[-v] [-d] [-p <comp port>] <EcoXiP TestBench script filename> [<argument list>]")
	exit()
	

# Returns an integer's sign (strangely Python doesn't have a builtin function).
def sign(n):
	if n > 0:
		return 1
	if n < 0:
		return -1
	return 0

# Keep reading from serial line until full prompt is seen
def check_prompt(ser_hnd):
	#ok = False
	s = ""
	while True:
		b = ser_hnd.read(1)
		if len(b) == 0:
			# We can only get here due to timeout
			#print("Could not find prompt; so far read:")
			#print(s)
			return ERR_SER_TIMEOUT

		c = b.decode('utf-8')
		s += c
		if s.endswith(tool_prompt):
			#ok = True
			print(s)
			global prev_output
			prev_output = s.lower()
			return STATUS_OK

# Extract all labels from script and populate label table.
# Label table is a dictionary. The key is the label and the value is the label's line number.
def build_label_tab(scr_lines):
	ltab = {}
	n = 0
	for line in scr_lines:
		#print(line)
		if line.startswith("$:"):
			label = line[2:].strip().lower()
			if label in ltab:
				print_error(ERR_MULT_DEF_LABEL, line, n)
			ltab[label] = n
		n += 1
	return ltab

# Parse SET command
# Inputs: command line token list; variable table.
# Note: if variable hasn't been seen so far it will be added to
# variable table right here.
def parse_set_cmd(tk, vt):
	if len(tk) != 3:
		return ERR_NUM_ARGS
	var = tk[1]
	try:
		val = int(tk[2], 16)
	except ValueError:
		return ERR_SYNTAX
	vt[var] = val
	return STATUS_OK

# Parse SETV command
# Inputs: command line token list; variable table.
# Note: if first variable hasn't been seen so far it will be added to
# variable table right here. Second variable must pre-exist.
def parse_setv_cmd(tk, vt):
	if len(tk) != 3:
		return ERR_NUM_ARGS
	var1 = tk[1]
	var2 = tk[2]
	if not (var2 in vt):
		return ERR_UNDEF_VAR
	vt[var1] = vt[var2]
	return STATUS_OK

# Parse PRINT command
# Inputs: command line token list; variable table.
# Note: if variable hasn't been seen so far - it's an error.
def parse_print_cmd(tk, vt):
	if len(tk) != 2:
		return ERR_NUM_ARGS
	var = tk[1]
	if not (var in vt):
		return ERR_UNDEF_VAR
	print(var, "=", format(vt[var], 'x'))
	return STATUS_OK	

# Parse ADD/SUB command
# Inputs: command line token list; variable table; sign (indicating ADD or SUB)
# Note: if variable hasn't been seen so far - it's an error.
def parse_add_cmd(tk, vt, sign):
	if len(tk) != 3:
		return ERR_NUM_ARGS
	var = tk[1]
	if not (var in vt):
		return ERR_UNDEF_VAR
	try:
		val = int(tk[2], 16)
	except ValueError:
		return ERR_SYNTAX
	vt[var] += sign * val
	return STATUS_OK

# Parse ADDV/SUBV command
# Inputs: command line token list; variable table; sign (indicating ADD or SUB)
# Note: if input variables have't been seen so far - it's an error. However if
# the output variable does not exists we'll create it.
def parse_addv_cmd(tk, vt, sign):
	if len(tk) != 4:
		return ERR_NUM_ARGS
	var1 = tk[1]
	var2 = tk[2]
	if not (var2 in vt):
		return ERR_UNDEF_VAR
	var3 = tk[3]
	if not (var3 in vt):
		return ERR_UNDEF_VAR
	vt[var1] = vt[var2] + (sign * vt[var3])
	return STATUS_OK

# Parse BR command
# Inputs: command line token list; label table.
# Note: if label is not in label table - it's an error.
def parse_br_cmd(tk, ltb):
	if len(tk) != 2:
		return (ERR_NUM_ARGS, -1)
	label = tk[1]
	if not(label in ltb):
		return (ERR_UNDEF_LABEL, -1)
	return (STATUS_OK, ltb[label])

# Parse BR<cond> set of commands
# Inputs: command line token list; label table; variable table; two
# signs indicating the type of comparison (for example for LE, less
# than or equal, type of comparison the signs are -1 and 0.
# Note: if label is not in label table - it's an error.
# Note: if variable hasn't been seen so far - it's an error.
# Note: the sign of difference between the variable and the value
# to which it's compared must be equal to one of the pair of argument signs.
def parse_brcond_cmd(tk, ltb, vt, sign1, sign2):
	if len(tk) != 4: 
		return (ERR_NUM_ARGS, -1)
	var = tk[1]
	if not (var in vt):
		return (ERR_UNDEF_VAR, -1)
	varval = vt[var]
	try:
		val = int(tk[2], 16)
	except ValueError:
		return (ERR_SYNTAX, -1)
	label = tk[3]
	if not(label in ltb):
		return (ERR_UNDEF_LABEL, -1)
	diff = varval - val
	diff_sign = sign(diff)
	if diff_sign == sign1 or diff_sign == sign2:
		return (STATUS_OK, ltb[label])
	else:
		return (STATUS_OK, -1)

# Parse DELAY command
# Inputs: command line token list
def parse_delay_cmd(tk):
	if len(tk) != 2: 
		return (ERR_NUM_ARGS, -1)
	time.sleep(float(tk[1]))
	return STATUS_OK

# Parse RAND command
# Inputs: command line token list
def parse_rand_cmd(tk, vt):
	if len(tk) != 4: 
		return (ERR_NUM_ARGS, -1)
	var = tk[1]
	try:
		vt[var] = random.randint(int(tk[2], 16), int(tk[3], 16))
	except ValueError:
		return ERR_SYNTAX
	return STATUS_OK

# Parse RANDSEED command
# Inputs: command line token list
def parse_randseed_cmd(tk):
	if len(tk) != 2: 
		return (ERR_NUM_ARGS, -1)
	try:
		random.seed(a=int(tk[1], 16))
	except ValueError:
		return ERR_SYNTAX
	return STATUS_OK

# Parse ECHO command
# Inputs: command line token list
def parse_echo_cmd(tk):
	for s in tk[1:]:
		print(s, end=" ")
	print("")
	return STATUS_OK

# Parse FINDOUT command
# Inputs: command line token list; variable table
# Notes: string will be converted to lower case (it's a case-insesitive search)
# if variable hasn't been seen before - it will be created.
def parse_findout_cmd(tk, vt):
	if len(tk) != 3: 
		return (ERR_NUM_ARGS, -1)
	search_str = tk[1]
	flag_var = tk[2]
	#print(prev_output)
	#print(search_str)
	if prev_output.find(search_str) != -1:
		vt[flag_var] = 1
	else:
		vt[flag_var] = 0
	return STATUS_OK


# Print error message
# Inputs: error code; line string; line number.
# Note: this function also exits the program.
def print_error(errc, l, lnum):
	print("")
	print("ERROR:", errtab[errc - 1])
	print("Line", lnum + 1, ":")
	print(l)
	exit()

# Parse a directive line (a line which start with a '$')
# Inputs: line string; label table, variable table.
# Ignores labels (which have already been processed) and comments.
# Splits command line into tokens, checks for a valid command string (op code)
# and calls one of the parse functions accordingly.
def parse_directive(l, ltab, vtab):
	l = l.lower()
	if len(l) < 2:
		parse_status = ERR_SYNTAX # '$' followed by nothing
	elif l[1] == '#':
		 parse_status = STATUS_OK # it's a comment
	elif l[1] == ":":
		parse_status = STATUS_OK # it's a label (we've already built a label tab)
	else:
		dr = l[1:].strip()
		tokens = dr.split()
		if len(tokens) == 0:
			parse_status = ERR_SYNTAX  #'$' followed by nothing
		elif tokens[0] == "set":
			parse_status = parse_set_cmd(tokens, vtab)
		elif tokens[0] == "setv":
			parse_status = parse_setv_cmd(tokens, vtab)
		elif tokens[0] == "print":
			parse_status = parse_print_cmd(tokens, vtab)
		elif tokens[0] == "add":
			parse_status = parse_add_cmd(tokens, vtab, 1)
		elif tokens[0] == "sub":
			parse_status = parse_add_cmd(tokens, vtab, -1)
		elif tokens[0] == "addv":
			parse_status = parse_addv_cmd(tokens, vtab, 1)
		elif tokens[0] == "subv":
			parse_status = parse_addv_cmd(tokens, vtab, -1)		
		elif tokens[0].startswith("br"):
			if len(tokens[0]) == 2:
				return parse_br_cmd(tokens, ltab)
			elif len(tokens[0]) == 4 and tokens[0][2:] in brcond_tab:
				#print(tokens[0][2:], brcond_tab[tokens[0][2:]][0], brcond_tab[tokens[0][2:]][1])
				#print(ltab)
				#print(vtab)
				return parse_brcond_cmd(tokens, ltab, vtab, brcond_tab[tokens[0][2:]][0], brcond_tab[tokens[0][2:]][1])
			else:
				parse_status = ERR_UNDEF_CMD
		elif tokens[0] == "delay":
			parse_status = parse_delay_cmd(tokens)
		elif tokens[0] == "findout":
			parse_status = parse_findout_cmd(tokens, vtab)
		elif tokens[0] == "rand":
			parse_status = parse_rand_cmd(tokens, vtab)
		elif tokens[0] == "randseed":
			parse_status = parse_randseed_cmd(tokens)
		elif tokens[0] == "echo":
			parse_status = parse_echo_cmd(tokens)
		else:
			parse_status = ERR_UNDEF_CMD

	return (parse_status, -1)

# Perform variable substitution inside a test bench command line.
# Inputs: line string; variable table.
# Splits the test bench command line into tokens. If any of the token
# strings starts with a '@' the rest of the token string is assumed to
# be a variable identifier and a substitution is attempted. After all
# substitutions have been performed the command lines is re-assembled.
# Note: if variable hasn't been seen so far - it's an error.
def var_subst(l, vt):
	tokens = l.split()
	n = 0
	for t in tokens:
		if t[0] == "@":
			var = t[1:].lower()
			if not (var in vt):
				return (ERR_UNDEF_VAR, "")
			tokens[n] = format(vt[var], 'x')
		n += 1
	l1 = " ".join(tokens)
	return (STATUS_OK, l1)

# Main function

# Build a dictionary for BR<cond> type of commands. Per each <cond> string
# provides a pair of signs. See the BR<cond> parse function.
brcond_tab = {"eq": [0,0], "ne": [1,-1], "gt": [1,1], "ge": [0,1], "lt": [-1,-1], "le": [0,-1]}

# Error code constants
STATUS_OK = 0
ERR_SYNTAX = 1
ERR_UNDEF_CMD = 2
ERR_NUM_ARGS = 3
ERR_UNDEF_VAR = 4
ERR_UNDEF_LABEL = 5
ERR_MULT_DEF_LABEL = 6
ERR_SER_TIMEOUT = 7

# Error message table
errtab = [
"incorrect syntax",
"undefined command",
"wrong number of arguments",
"undefined variable",
"undefined label",
"multiply defined label",
"read timeout",
""
]

tool_name = sys.argv[0]
tool_name_break = tool_name.split("\\")
tool_name = tool_name_break[len(tool_name_break) - 1]
print(tool_name)

if tool_name.startswith("exip"):
	tool_prompt = "EcoXiP >>> "
if tool_name.startswith("cbram"):
	tool_prompt = "CBRAM >>> "
if tool_name.startswith("fhd"):
	tool_prompt = "FusionHD >>> "
if tool_name.startswith("fhd"):
	tool_prompt = ">>> "


# Set default values for the command line arguments.
verbose = False
dryrun = False
comport = "COM3"
script_name = ""

# Get number of arguments from command line.
num_args = len(sys.argv)

argn = 1
skiparg = False
script_cmd_line = []

# Parse command line, set variables accordingly.
for arg in sys.argv[1:]:
	if not skiparg:
		skiparg = False
		if arg[0] == '-':
			if arg[1:] == 'v':
				verbose = True
			elif arg[1:] == 'd':
				dryrun = True
			elif arg[1:] == 'p':
				if argn < num_args - 1:
					comport = sys.argv[argn + 1]
					skiparg = True
				else:
					usage()
			else:
				usage()
		else:
			script_cmd_line.append(arg)
	else:
		skiparg = False
	argn+=1

if len(script_cmd_line) == 0:
	usage()
script_name = script_cmd_line[0]


# Print current settings following command line parsing. 
print ("script is", script_name)
print ("com port is", comport)
print("verbose is", verbose)
print("dryrun is", dryrun)
print("")

if script_name == "":
	usage()

# If it's not a dry run open the serial connection.
if not dryrun:
	try:
		ser = serial.Serial(comport, 115200, timeout=1)
	except serial.SerialException:
		print("Error: cannot open", comport)
		exit()

# Open the script file.
try:
	script_file = open(script_name, 'r')
except FileNotFoundError:
	print("Error: file", script_name, "not found")
	exit()

# If it's not a dry run, wait for first prompt.
if not dryrun:
	while True:
		prompt_check_status = check_prompt(ser)
		if prompt_check_status == STATUS_OK:
			break
		else:
			# Not seeing a prompt -  send a RETURN to target (perhaps it's listening now)
			line = "\r"
			byteseq = line.encode('utf-8') #convert to ASCII/UTF-8
			ser.write(byteseq) #send to port
	# now change timeout to a couple of minutes to accommodate commands like 60 (Chip Erase)
	ser.timeout = 120 


# Get script lines into a string list.
script_lines = script_file.readlines()
# Get number of script lines.
script_len = len(script_lines)
# Init current line number to 0
lnum = 0

# First pass over the script: build label table
label_tab = build_label_tab(script_lines)

# Initialize variable table to an empty dictionary
var_tab = {}
# Now insert command line arguments to variable table as arg1, arg2, arg3...
arg_num = 0
for script_arg_val in script_cmd_line[1:]:
	arg_num += 1
	argi = "arg"+str(arg_num)
	var_tab[argi] = int(script_arg_val, 16)

# Initialize string holding previous output from Test Bench
prev_output = ""

# Main loop: continue while we haven't reached beyond the last script line
while(lnum < script_len):
	# Get Current line string
	line = script_lines[lnum].strip('\n')
	# Get rid of empty lines - just increment line number.
	if len(line) == 0: #empty line
		lnum += 1
		continue
	# Check type of line
	if line[0] == '$':
		# It's a directive line - call teh directive parsing function
		parse_status = parse_directive(line, label_tab, var_tab)
		if parse_status[0] != STATUS_OK :
			print_error(parse_status[0], line, lnum)
		else:
			if parse_status[1] == -1:
				# Parse status doesn't indicate a taken branch. We'll continue
				# execution sequentially so just increment line number.
				lnum += 1
			else:
				# Parse status indicates a taken branch. We'll break
				# sequential flow and change to a non-sequential line number.
				lnum = parse_status[1]
	else:
		# It's a test bench line - call the variable substitution function. 
		subst_status = var_subst(line, var_tab)
		if subst_status[0] != STATUS_OK:
			print_error(subst_status[0], line, lnum)
		else:
			line = subst_status[1]
		# For verbose or dry run print the test bench line to be sent.
		if(verbose or dryrun):
			print("")
			print(line)
		if not dryrun:
			# Unless it's a dry run prepare a byte stream and send to serial line
			line += '\r' # add RETURN char
			byteseq = line.encode('utf-8') #convert to ASCII/UTF-8
			#print(byteseq)
			ser.write(byteseq) #send to port
			read_stat = check_prompt(ser)
			if read_stat != STATUS_OK:
				print_error(read_stat, line, lnum)
		# Increment current line number
		lnum += 1
