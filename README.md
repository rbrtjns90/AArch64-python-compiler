# AArch64 python compiler
 A Compiler for AArch64 Apple Silicon for a Subset of Python.
 Inspiration from -> https://github.com/tsoding/porth

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
