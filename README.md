# AArch64 python compiler
 A Compiler for AArch64 Apple Silicon for a Subset of Python.
 Inspiration from -> https://github.com/tsoding/porth

Everything is pure python and depends on the standard library.

For compilation on your machine, you need Xcode installed. Open up a shell and type xcode-select --install and you're good to go.

Usage

python3 compiler.py python_test.txt 

The executable will be named "output" by default.

You can specify an executable name as the third argument

python3 compiler.py python_test.txt executable_file


python3 compiler.py
Currently implemented commands 
 - Single Line Comments
 - """ Multiline Comments """
 - Variable Declaration var = "Foo" or 2
 - User Input var = input("What the Foo?")
 - print("String") + print(1+2)

Immediate Goals
 - Mathematical operations beyond just addition (-, *, /)
 - Boolean expressions and conditional statements (if/else)
 - Loops (while and for)
 - Functions
 - Arrays or lists

End Goals
 - Turing Completion
 - Inline Assembly
 - Ability to utilize LibC
 - Probably Force Static typing and declaration of allocated space needed for variables to avoid buffer overflows
