#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
# This code is the responder an an will implement the
# reactions to the requests, in case of pmon some error-handling
# strategies.
#

from tkinter import *


def clicked():
    lbl.configure(text="Button was clicked !!")


window = Tk()
window.title("Ki-Wi events")
window.geometry('800x400')

lbl = Label(window, text="Hello")
lbl.grid(column=0, row=0)
btn = Button(window, text="Click Me", command=clicked)
btn.grid(column=1, row=0)

window.mainloop()