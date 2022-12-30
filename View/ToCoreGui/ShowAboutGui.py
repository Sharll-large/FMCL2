import platform
import tkinter as tk
import tkinter.messagebox

import Const
import Core.Launch.CoreLaunchTaskSub


def show_license():
    tk.messagebox.showinfo("License",
'''
MIT License
                           
Copyright (c) 2022 Sharll-large
                           
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
                           
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
                           
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')

def show_about():
    tk.messagebox.showinfo("About software",
f'''
FMCL Preview Version
Software version:\t{Const.software_version}
Tkinter version:\t{tk.TkVersion}
Python version:\t{platform.python_version()}
System name(raw):\t{platform.system()}
System name:\t{Core.Launch.CoreLaunchTaskSub.system()}
System arch(raw):\t{platform.machine()}
System arch:\t{Core.Launch.CoreLaunchTaskSub.arch()}
''')