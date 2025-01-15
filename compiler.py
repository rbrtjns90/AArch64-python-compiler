from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Union
import os
import subprocess

# Token types for our Python subset
class TokenType(Enum):
    PRINT = auto()
    STRING = auto()
    INTEGER = auto()
    PLUS = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()
    IDENTIFIER = auto()  # For variable names
    EQUALS = auto()      # For assignment
    INPUT = auto()       # For input() function
    COMMENT = auto()     # For comments

@dataclass
class Token:
    type: TokenType
    value: Optional[str] = None

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.current_char = self.source[self.pos] if source else None
        
    def advance(self):
        self.pos += 1
        self.current_char = self.source[self.pos] if self.pos < len(self.source) else None
        
    def peek(self, n: int = 1) -> Optional[str]:
        peek_pos = self.pos + n
        return self.source[peek_pos] if peek_pos < len(self.source) else None
        
    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()
            
    def handle_multiline_comment(self):
        # Skip opening quotes
        self.advance()
        self.advance()
        self.advance()
        
        while self.current_char:
            if (self.current_char == '"' and 
                self.peek() == '"' and 
                self.peek(2) == '"'):
                # Skip closing quotes
                self.advance()
                self.advance()
                self.advance()
                return
            self.advance()
            
    def handle_single_line_comment(self):
        while self.current_char and self.current_char != '\n':
            self.advance()
            
    def get_string(self) -> str:
        self.advance()  # Skip opening quote
        result = []
        while self.current_char and self.current_char != '"':
            result.append(self.current_char)
            self.advance()
        self.advance()  # Skip closing quote
        return ''.join(result)
    
    def get_integer(self) -> str:
        result = []
        while self.current_char and self.current_char.isdigit():
            result.append(self.current_char)
            self.advance()
        return ''.join(result)
        
    def get_identifier(self) -> str:
        result = []
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result.append(self.current_char)
            self.advance()
        return ''.join(result)
    
    def tokenize(self) -> List[Token]:
        tokens = []
        
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            if self.current_char.isdigit():
                tokens.append(Token(TokenType.INTEGER, self.get_integer()))
                continue
                
            if self.current_char == '+':
                tokens.append(Token(TokenType.PLUS))
                self.advance()
                continue
                
            if self.current_char == '=':
                tokens.append(Token(TokenType.EQUALS))
                self.advance()
                continue
                
            if self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN))
                self.advance()
                continue
                
            if self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN))
                self.advance()
                continue
                
            if self.current_char == '"':
                string_value = self.get_string()
                tokens.append(Token(TokenType.STRING, string_value))
                continue
                
            if self.current_char.isalpha() or self.current_char == '_':
                identifier = self.get_identifier()
                if identifier == 'print':
                    tokens.append(Token(TokenType.PRINT))
                elif identifier == 'input':
                    tokens.append(Token(TokenType.INPUT))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, identifier))
                continue
                
            raise SyntaxError(f"Unexpected character: {self.current_char}")
                
        tokens.append(Token(TokenType.EOF))
        return tokens

# AST node types

@dataclass
class StringLiteral:
    value: str

@dataclass
class IntegerLiteral:
    value: int

@dataclass
class BinaryOp:
    left: Union[IntegerLiteral, 'BinaryOp']
    right: Union[IntegerLiteral, 'BinaryOp']
    op: str

@dataclass
class PrintStatement:
    expression: Union[StringLiteral, IntegerLiteral, BinaryOp]

@dataclass
class Variable:
    name: str

@dataclass
class Assignment:
    variable: Variable
    value: Union[StringLiteral, IntegerLiteral, BinaryOp, 'Input']

@dataclass
class Input:
    prompt: StringLiteral


@dataclass
class Program:
    statements: List[PrintStatement]

# Parser
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def consume(self, token_type: TokenType) -> Token:
        current_token = self.tokens[self.pos]
        if current_token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {current_token.type}")
        self.pos += 1
        return current_token

    def parse_expression(self):
        token = self.tokens[self.pos]
        
        if token.type == TokenType.INTEGER:
            self.pos += 1
            return IntegerLiteral(int(token.value))
            
        if token.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(token.value)
            
        if token.type == TokenType.IDENTIFIER:
            self.pos += 1
            return Variable(token.value)
            
        if token.type == TokenType.INPUT:
            self.pos += 1
            self.consume(TokenType.LPAREN)
            prompt = self.parse_expression()
            self.consume(TokenType.RPAREN)
            return Input(prompt)
            
        raise SyntaxError(f"Unexpected token: {token}")
    
    def parse_statement(self) -> Union[PrintStatement, Assignment]:
        token = self.tokens[self.pos]
        
        if token.type == TokenType.PRINT:
            self.pos += 1
            self.consume(TokenType.LPAREN)
            expr = self.parse_expression()  
            self.consume(TokenType.RPAREN)
            return PrintStatement(expr)
            
        elif token.type == TokenType.IDENTIFIER:
            var_name = token.value
            self.pos += 1
            self.consume(TokenType.EQUALS)
            value = self.parse_expression()  
            return Assignment(Variable(var_name), value)
            
        raise SyntaxError(f"Unexpected token: {token}")
    
    def parse(self) -> Program:
        statements = []
        while self.pos < len(self.tokens) - 1:  # -1 for EOF
            statements.append(self.parse_statement())
        self.consume(TokenType.EOF)
        return Program(statements)
    

# IR instructions
@dataclass
class IRStringConstant:
    value: str
    label: str

@dataclass
class IRInteger:
    value: int

@dataclass
class IRVariable:
    name: str

@dataclass
class IRAdd:
    left: Union['IRAdd', IRInteger, IRVariable]
    right: Union['IRAdd', IRInteger, IRVariable]

@dataclass
class IRInput:
    prompt: IRStringConstant
    result: str  # Label for where to store the result

@dataclass
class IRAssignment:
    variable_name: str
    value: Union[IRStringConstant, IRInteger, IRAdd, IRInput, IRVariable]

@dataclass
class IRPrintCall:
    string_ref: str

@dataclass
class IRPrintInt:
    expression: Union[IRAdd, IRInteger, IRVariable]


class IRGenerator:
    def __init__(self):
        self.string_constants = []
        self.instructions = []
        self.string_count = 0
        self.variables = {}  # Track variables and their types/values
        
    def generate_expression(self, expr):
        if isinstance(expr, IntegerLiteral):
            return IRInteger(expr.value)
        elif isinstance(expr, StringLiteral):
            string_label = f"string_{self.string_count}"
            self.string_count += 1
            self.string_constants.append(IRStringConstant(expr.value, string_label))
            return IRStringConstant(expr.value, string_label)
        elif isinstance(expr, BinaryOp):
            if expr.op == '+':
                return IRAdd(
                    self.generate_expression(expr.left),
                    self.generate_expression(expr.right)
                )
        elif isinstance(expr, Variable):
            if expr.name not in self.variables:
                raise NameError(f"Variable '{expr.name}' is not defined")
            return self.variables[expr.name]
        elif isinstance(expr, Input):
            # Generate IR for input operation
            prompt_ir = self.generate_expression(expr.prompt)
            return IRInput(prompt_ir, f"input_result_{self.string_count}")
            
        raise ValueError(f"Unsupported expression: {expr}")
    
    def generate(self, program: Program) -> None:
        for statement in program.statements:
            print(f"Processing statement: {type(statement)}")  # Debug output
            
            if isinstance(statement, PrintStatement):
                if isinstance(statement.expression, Variable):
                    if statement.expression.name not in self.variables:
                        raise NameError(f"Variable '{statement.expression.name}' is not defined")
                    value = self.variables[statement.expression.name]
                    if isinstance(value, IRStringConstant):
                        self.instructions.append(IRPrintCall(value.label))
                    elif isinstance(value, (IRInteger, IRAdd)):
                        self.instructions.append(IRPrintInt(value))
                    elif isinstance(value, IRInput):
                        # Handle printing of input result
                        self.instructions.append(IRPrintCall(value.result))
                else:
                    ir_expr = self.generate_expression(statement.expression)
                    if isinstance(ir_expr, IRStringConstant):
                        self.instructions.append(IRPrintCall(ir_expr.label))
                    else:
                        self.instructions.append(IRPrintInt(ir_expr))
            
            elif isinstance(statement, Assignment):
                print(f"Processing assignment to variable: {statement.variable.name}")  # Debug output
                value = self.generate_expression(statement.value)
                if isinstance(statement.value, Input):
                    print("Found input operation!")  # Debug output
                    # Add the input instruction to get user input
                    self.instructions.append(value)
                self.variables[statement.variable.name] = value




# Assembly Generator
class AssemblyGenerator:
    def __init__(self, ir_generator: IRGenerator):
        self.ir = ir_generator
        self.input_buffer_size = 100  # Size for input buffer
        
    def generate(self) -> str:
        assembly = []
        
        # Global directive and alignment
        assembly.append(".global _main")
        assembly.append(".align 4")
        
        # Data section
        assembly.append("\n.data")
        
        # Add input buffers for each input operation
        for instr in self.ir.instructions:
            if isinstance(instr, IRInput):
                assembly.append(f"{instr.result}:")
                assembly.append(f"    .space {self.input_buffer_size}")
                assembly.append(f"    .set len_{instr.result}, {self.input_buffer_size}")
        
        # Add string constants
        for string_const in self.ir.string_constants:
            assembly.append(f"{string_const.label}:")
            assembly.append(f'    .ascii "{string_const.value}"')
            assembly.append(f"    .set len_{string_const.label}, . - {string_const.label}")
        
        # Add number format if needed
        if any(isinstance(instr, IRPrintInt) for instr in self.ir.instructions):
            assembly.append("number_str:")
            assembly.append("    .ascii \"0123456789\\n\"")
            assembly.append("buffer:")
            assembly.append("    .fill 20, 1, 0  // Buffer for number conversion")
        
        # Text section
        assembly.append("\n.text")
        assembly.append("_main:")
        
        # Function prologue
        assembly.append("    // Save frame pointer")
        assembly.append("    stp x29, x30, [sp, #-16]!")
        assembly.append("    mov x29, sp")
        
        # Generate code for each instruction
        for instr in self.ir.instructions:
            if isinstance(instr, IRPrintCall):
                # String printing
                assembly.append("\n    // Write string to stdout")
                assembly.append("    mov     x0, #1              // stdout")
                assembly.append(f"    adrp    x1, {instr.string_ref}@PAGE")
                assembly.append(f"    add     x1, x1, {instr.string_ref}@PAGEOFF")
                assembly.append(f"    mov     x2, #len_{instr.string_ref}")
                assembly.append("    mov     x16, #4            // macOS write syscall")
                assembly.append("    svc     #0x80             // invoke syscall")
            
            elif isinstance(instr, IRPrintInt):
                # Number printing code...
                assembly.append("\n    // Print integer")
                self.generate_expression(assembly, instr.expression)
                assembly.extend([
                    "    adrp    x1, buffer@PAGE",
                    "    add     x1, x1, buffer@PAGEOFF",
                    "    mov     x2, #0          // String length counter",
                    "    mov     x3, #10         // For division by 10",
                    # Convert number to string...
                    "    cmp     x0, #0",
                    "    b.ne    1f",
                    "    mov     x4, #'0'",
                    "    strb    w4, [x1]",
                    "    mov     x2, #1",
                    "    b       3f",
                    "1:  // Start conversion loop",
                    "    cbz     x0, 2f",
                    "    udiv    x4, x0, x3",
                    "    msub    x5, x4, x3, x0",
                    "    add     x5, x5, #'0'",
                    "    strb    w5, [x1, x2]",
                    "    add     x2, x2, #1",
                    "    mov     x0, x4",
                    "    b       1b",
                    "2:  // Reverse the string",
                    "    mov     x3, #0",
                    "    sub     x4, x2, #1",
                    "3:  // Add newline",
                    "    mov     w4, #'\\n'",
                    "    strb    w4, [x1, x2]",
                    "    add     x2, x2, #1",
                    # Print the number
                    "    mov     x0, #1",
                    "    mov     x16, #4",
                    "    svc     #0x80"
                ])
            
            elif isinstance(instr, IRInput):
                # First print the prompt
                assembly.append("\n    // Print input prompt")
                assembly.append("    mov     x0, #1              // stdout")
                assembly.append(f"    adrp    x1, {instr.prompt.label}@PAGE")
                assembly.append(f"    add     x1, x1, {instr.prompt.label}@PAGEOFF")
                assembly.append(f"    mov     x2, #len_{instr.prompt.label}")
                assembly.append("    mov     x16, #4            // macOS write syscall")
                assembly.append("    svc     #0x80             // invoke syscall")
                
                # Then read input from stdin into the specific input buffer
                assembly.append("\n    // Read input from stdin")
                assembly.append("    mov     x0, #0              // stdin")
                assembly.append(f"    adrp    x1, {instr.result}@PAGE")
                assembly.append(f"    add     x1, x1, {instr.result}@PAGEOFF")
                assembly.append(f"    mov     x2, #len_{instr.result}  // buffer size")
                assembly.append("    mov     x16, #3            // macOS read syscall")
                assembly.append("    svc     #0x80             // invoke syscall")
                
                # Store the actual length of input
                assembly.append("    str     x0, [sp, #-16]!    // Save input length")
        
        # Exit cleanly
        assembly.append("\n    // Exit")
        assembly.append("    mov     x0, #0")
        assembly.append("    mov     x16, #1")
        assembly.append("    svc     #0x80")
        
        # Function epilogue
        assembly.append("\n    // Restore frame pointer")
        assembly.append("    ldp x29, x30, [sp], #16")
        assembly.append("    ret")
        
        return '\n'.join(assembly)
        
    def generate_expression(self, assembly: list, expr) -> None:
        if isinstance(expr, IRInteger):
            assembly.append(f"    mov x0, #{expr.value}")
        elif isinstance(expr, IRAdd):
            # Generate left operand
            self.generate_expression(assembly, expr.left)
            assembly.append("    str x0, [sp, #-16]!")
            # Generate right operand
            self.generate_expression(assembly, expr.right)
            assembly.append("    mov x1, x0")
            assembly.append("    ldr x0, [sp], #16")
            assembly.append("    add x0, x0, x1")

# Modified compilation pipeline
def compile_to_assembly(source_code: str) -> str:
    # Split the source code into lines and filter out empty lines
    source_lines = [line.strip() for line in source_code.split('\n') if line.strip()]
    
    # Process each line through the lexer
    all_tokens = []
    in_multiline_comment = False
    
    for line in source_lines:
        # Handle multiline comments
        if '"""' in line:
            if in_multiline_comment:
                in_multiline_comment = False
            else:
                in_multiline_comment = True
            continue
            
        if in_multiline_comment:
            continue
            
        # Handle single line comments and actual code
        code_part = line.split('#')[0].strip()
        if code_part:
            lexer = Lexer(code_part)
            line_tokens = lexer.tokenize()
            all_tokens.extend(line_tokens[:-1])
    
    # Add final EOF token
    all_tokens.append(Token(TokenType.EOF))
    
    print("\nTokens after processing:")
    for token in all_tokens:
        print(f"Type: {token.type}, Value: {token.value}")
    
    # Parse tokens
    parser = Parser(all_tokens)
    program = parser.parse()
    
    print("\nGenerating IR...")
    ir_gen = IRGenerator()
    ir_gen.generate(program)
    
    print("\nIR Instructions:")
    for instr in ir_gen.instructions:
        print(f"  {type(instr)}: {instr}")
    
    print("\nGenerating assembly...")
    asm_gen = AssemblyGenerator(ir_gen)
    return asm_gen.generate()

# Test function to help debug
def debug_tokens(source_code: str) -> List[Token]:
    source_lines = source_code.split('\n')
    all_tokens = []
    in_multiline_comment = False
    
    for line in source_lines:
        if not line.strip():
            continue
            
        if '"""' in line:
            if in_multiline_comment:
                in_multiline_comment = False
            else:
                in_multiline_comment = True
            continue
            
        if in_multiline_comment:
            continue
            
        code_part = line.split('#')[0].strip()
        if code_part:
            lexer = Lexer(code_part)
            line_tokens = lexer.tokenize()
            all_tokens.extend(line_tokens[:-1])
    
    all_tokens.append(Token(TokenType.EOF))
    return all_tokens

def compile_and_link(source_code: str, output_name: str = "output") -> None:
    """
    Compiles the source code to assembly, writes it to a file,
    and then assembles and links it into an executable.
    
    Args:
        source_code: The source code to compile
        output_name: The name of the output executable (default: "output")
    """
    # Generate assembly
    assembly_code = compile_to_assembly(source_code)
    
    # Write assembly to file
    asm_file = f"{output_name}.s"
    with open(asm_file, "w") as f:
        f.write(assembly_code)
    
    try:
        # Assemble the file (creates object file)
        subprocess.run(["as", "-o", f"{output_name}.o", asm_file], check=True)
        
        # Link the object file into an executable
        subprocess.run(["ld", "-o", output_name, f"{output_name}.o", "-lSystem", "-syslibroot", 
                       "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk", "-e", "_main"], 
                      check=True)
        
        # Make the output file executable
        os.chmod(output_name, 0o755)
        
        # Clean up intermediate files
        #os.remove(f"{output_name}.o")
        #os.remove(asm_file)
        
        print(f"Successfully compiled to '{output_name}'")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {e}")
        # Keep the assembly file for debugging if compilation fails
        print(f"Assembly file '{asm_file}' has been preserved for debugging")



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        source_file = sys.argv[1]
        output_name = os.path.splitext(source_file)[0]  # Use source filename without extension
        
        with open(source_file, 'r') as file:
            source = file.read()
        
        # Debug: Print tokens
        print("Tokens:")
        tokens = debug_tokens(source)
        for token in tokens:
            print(f"Type: {token.type}, Value: {token.value}")
        
        # Compile and link
        try:
            compile_and_link(source, output_name)
            print(f"\nYou can now run the program with: ./{output_name}")
        except Exception as e:
            print(f"Error during compilation: {str(e)}")
    else:
        print("Please provide a source file as argument")

