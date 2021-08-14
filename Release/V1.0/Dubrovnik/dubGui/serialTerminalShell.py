from tkinter import *
# from tkinter import ttk
from tkinter import scrolledtext

# BUFFERSIZE = 1000
PROMPT = '>>> '
CLEAR_CMD = 'clear'


class Terminal(Frame):
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text='Terminal',
                            relief=GROOVE, padx=10, pady=10)
        self.history = []
        self.historyIndex = 0
        self.txt = scrolledtext.ScrolledText(
            self, wrap=CHAR, width=60, height=20, font=("Consolas", 11))
        self.txt.pack(expand=YES, fill=BOTH)
        # self.txt.grid(row=0, column=0, pady=10, padx=10)
        self.clear()
        self.txt.focus()      # placing cursor in text area

        # Key bindings
        self.txt.bind('<Return>', self.onReturnKey)
        self.txt.bind('<BackSpace>', self.onBackSpace)
        self.txt.bind('<Delete>', self.onDelete)
        self.txt.bind('<Up>', self.onUpArrowKey)
        self.txt.bind('<Down>', self.onDownArrowKey)
        self.txt.bind('<Left>', self.onLeftArrowKey)

    def onReturnKey(self, event):
        cmdstr = self.txt.get("end-1l linestart", "end-1l lineend")[
            len(PROMPT):].strip()
        print(cmdstr)
        if len(cmdstr) > 0:
            self.history.append(cmdstr)

        if cmdstr == CLEAR_CMD:
            self.clear()
            return 'break'
        # elif len(cmdstr) > 0:
            # try:
            #     comm.send(cmdstr)
            #     resp = comm.response(longResponse=False).strip()
            # except Exception as e:
            #     resp = f'error from boardcom: {e}'
            # self.txt.insert(END, '\n' + resp)

        self.txt.insert(END, '\n' + PROMPT)
        self.txt.mark_set(INSERT, END)
        self.txt.see(INSERT)
        self.historyIndex = len(self.history)
        # Returning 'break' prevents the native behavior, i.e. line break.
        return 'break'

    def onBackSpace(self, event):
        return self.allowDelete(5)

    def onDelete(self, event):
        return self.allowDelete(4)

    def allowDelete(self, charIndex):
        cur = self.txt.index(INSERT)
        charPos = int(cur.split('.')[1])
        if charPos < charIndex:
            return 'break'

    def onUpArrowKey(self, event):
        if self.historyIndex > 0:
            self.historyIndex -= 1
        return self.replaceLineWithHistory()

    def onDownArrowKey(self, event):
        if self.historyIndex < len(self.history):
            self.historyIndex += 1
        return self.replaceLineWithHistory()

    def onLeftArrowKey(self, event):
        return self.allowDelete(5)

    def replaceLineWithHistory(self):
        self.txt.delete('end-1l linestart+' +
                        str(len(PROMPT)) + 'c', 'end-1l lineend')

        newLine = ''
        if self.historyIndex < len(self.history):
            newLine = self.history[self.historyIndex]
        self.txt.insert(END, newLine)
        return 'break'

    def clear(self):
        self.txt.delete(1.0, END)
        self.txt.insert(1.0, PROMPT)

    def callCommand(self):
        pass


if __name__ == "__main__":
    root = Tk()
    root.title("ScrolledText Widget Example")
    term = Terminal(root)
    term.grid_propagate(0)
    term.pack(expand=YES, fill=BOTH)

    root.mainloop()
