from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext

BUFFERSIZE = 1000
PROMPT = '>>> '


class Terminal(Frame):
    def __init__(self, parent=None):
        self.history = []
        self.historyIndex = 0
        self.txt = scrolledtext.ScrolledText(root, wrap=CHAR,
                                             width=60, height=20,
                                             font=("Consolas", 12))
        self.txt.grid(column=0, row=2, pady=10, padx=10)
        self.txt.insert(1.0, PROMPT)
        self.txt.focus()      # placing cursor in text area

        # Key bindings
        self.txt.bind('<Return>', self.onReturnKey)
        self.txt.bind('<BackSpace>', self.onBackSpace)
        self.txt.bind('<Delete>', self.onDelete)
        self.txt.bind('<Up>', self.onUpArrowKey)
        self.txt.bind('<Down>', self.onDownArrowKey)
        self.txt.bind('<Home>', self.onHomeKey)

    def onReturnKey(self, event):
        cmdstr = self.txt.get("end-1l linestart", "end-1l lineend")[
            len(PROMPT):].strip()
        print(cmdstr)
        if len(cmdstr) > 0:
            self.history.append(cmdstr)
        self.txt.insert(END, '\n' + PROMPT)
        self.txt.mark_set(INSERT, END)
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

    def replaceLineWithHistory(self):
        self.txt.delete('end-1l linestart+' +
                        str(len(PROMPT)) + 'c', 'end-1l lineend')

        newLine = ''
        if self.historyIndex < len(self.history):
            newLine = self.history[self.historyIndex]
        self.txt.insert(END, newLine)
        return 'break'

    def onHomeKey(self, event):
        self.txt.tag_add(SEL, '1.0', END+'-1c')   # select entire text
        self.txt.mark_set(INSERT, '1.0')          # move insert point to top
        self.txt.see(INSERT)                      # scroll to top


if __name__ == "__main__":
    root = Tk()
    root.title("ScrolledText Widget Example")
    term = Terminal(root)

    root.mainloop()
