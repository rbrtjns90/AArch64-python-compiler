#!/usr/bin/env python3

import re
import argparse
from typing import Dict, List, Tuple

class AsmConverterATT:
    def __init__(self):
        self.register_map = {
            'x0': '%rdi',
            'x1': '%rsi',
            'x2': '%rdx',
            'x3': '%rcx',
            'x4': '%r8',
            'x5': '%r9',
            'x16': '%rax',  # System call number
            'x29': '%rbp',  # Frame pointer
            'x30': '%rbx',  # Link register
            'sp': '%rsp',   # Stack pointer
            'w4': '%r8d'    # 32-bit registers
        }
        
        self.syscall_map = {
            '1': '0x2000001',  # exit
            '3': '0x2000003',  # read
            '4': '0x2000004'   # write
        }

    def convert_data_section(self, input_lines: List[str]) -> List[str]:
        output_lines = []
        current_section = None
        
        for line in input_lines:
            line = line.strip()
            
            if not line or line.startswith('//'):
                continue
                
            if '.data' in line:
                output_lines.append('.section __DATA,__data')
                current_section = 'data'
            elif '.text' in line:
                output_lines.append('.section __TEXT,__text')
                current_section = 'text'
            elif '.global' in line:
                output_lines.append(line.replace('.global', '.globl'))
            elif '.align' in line:
                output_lines.append(line)
            elif current_section == 'data':
                if ':' in line:
                    output_lines.append(line)
                elif '.ascii' in line:
                    output_lines.append(line)
                elif '.space' in line:
                    output_lines.append(line)
                elif '.set' in line:
                    # Convert .set len_label, . - label to .set len_label, . - label
                    if '. -' in line:
                        output_lines.append(line)
                    else:
                        output_lines.append(line)
                elif '.fill' in line:
                    # Convert .fill size, width, value
                    output_lines.append(line)
        
        return output_lines

    def convert_instruction(self, line: str) -> str:
        # Remove comments and trim
        line = re.sub(r'//.*$', '', line)
        line = line.strip()
        
        if not line:
            return ''
            
        # Handle labels
        if line.endswith(':'):
            return line
            
        # Handle branching
        if line.startswith('b.'):
            condition = line.split()[0][2:]  # get condition code
            target = line.split()[1]
            return f"    j{self.convert_condition(condition)} {target}"
            
        if line.startswith('b '):
            target = line.split()[1]
            return f"    jmp {target}"
            
        # Handle immediate moves
        if line.startswith('mov'):
            parts = line.split()
            if len(parts) >= 3:
                dest = self.convert_register(parts[1].rstrip(','))
                source = parts[2]
                
                if source.startswith('#'):
                    # Handle immediate value
                    value = source[1:]
                    if value.startswith("'") and value.endswith("'"):  # character constant
                        value = ord(value[1:-1])
                    return f"    movq ${value}, {dest}"
                else:
                    source = self.convert_register(source)
                    return f"    movq {source}, {dest}"
                    
        # Handle stack operations
        if line.startswith('stp'):
            parts = line.split()
            reg1 = self.convert_register(parts[1].rstrip(','))
            reg2 = self.convert_register(parts[2].rstrip(','))
            return f"    pushq {reg1}\n    pushq {reg2}"
            
        if line.startswith('ldp'):
            parts = line.split()
            reg1 = self.convert_register(parts[1].rstrip(','))
            reg2 = self.convert_register(parts[2].rstrip(','))
            return f"    popq {reg2}\n    popq {reg1}"
            
        # Handle system calls
        if line.startswith('svc'):
            return "    syscall"
            
        # Handle adrp and add pair for addressing
        if line.startswith('adrp'):
            parts = line.split()
            dest = self.convert_register(parts[1].rstrip(','))
            symbol = parts[2].split('@')[0]
            return f"    leaq {symbol}(%rip), {dest}"
            
        if line.startswith('add') and '@PAGEOFF' in line:
            # We can skip these as we handled the address in the adrp conversion
            return ""
            
        # Handle string operations
        if line.startswith('strb'):
            parts = line.split()
            source = self.convert_register(parts[1].rstrip(','))
            dest = self.convert_memory_operand(parts[2])
            return f"    movb {source}, {dest}"
            
        # Handle comparisons
        if line.startswith('cmp'):
            parts = line.split()
            reg1 = self.convert_register(parts[1].rstrip(','))
            reg2 = self.convert_operand(parts[2])
            return f"    cmpq {reg2}, {reg1}"
            
        # Handle cbz (compare and branch if zero)
        if line.startswith('cbz'):
            parts = line.split()
            reg = self.convert_register(parts[1].rstrip(','))
            label = parts[2]
            return f"    testq {reg}, {reg}\n    jz {label}"
            
        # Handle string store
        if line.startswith('str'):
            parts = line.split()
            source = self.convert_register(parts[1].rstrip(','))
            dest = self.convert_memory_operand(parts[2])
            return f"    movq {source}, {dest}"
            
        # Handle arithmetic
        if line.startswith('udiv'):
            parts = line.split()
            dest = self.convert_register(parts[1].rstrip(','))
            source1 = self.convert_register(parts[2].rstrip(','))
            source2 = self.convert_register(parts[3])
            return f"    movq {source1}, %rax\n    xorq %rdx, %rdx\n    divq {source2}\n    movq %rax, {dest}"
            
        if line.startswith('msub'):
            parts = line.split()
            dest = self.convert_register(parts[1].rstrip(','))
            source1 = self.convert_register(parts[2].rstrip(','))
            source2 = self.convert_register(parts[3].rstrip(','))
            source3 = self.convert_register(parts[4])
            return f"    movq {source1}, %rax\n    imulq {source2}\n    subq {source3}, %rax\n    movq %rax, {dest}"
            
        # Handle procedure return
        if line.startswith('ret'):
            return "    ret"
            
        return f"    # Unconverted: {line}"

    def convert_condition(self, arm_cond: str) -> str:
        # Convert ARM condition codes to x86
        cond_map = {
            'eq': 'e',   # Equal
            'ne': 'ne',  # Not equal
            'gt': 'g',   # Greater than
            'lt': 'l',   # Less than
            'ge': 'ge',  # Greater than or equal
            'le': 'le'   # Less than or equal
        }
        return cond_map.get(arm_cond, 'mp')  # Default to unconditional jump if unknown

    def convert_register(self, reg: str) -> str:
        reg = reg.strip(' ,[]')
        return self.register_map.get(reg, f"%{reg}")

    def convert_operand(self, operand: str) -> str:
        operand = operand.strip()
        if operand.startswith('#'):
            return f"${operand[1:]}"
        return self.convert_register(operand)

    def convert_memory_operand(self, operand: str) -> str:
        # Handle memory operands like [x1, x2] or [x1, #8]
        operand = operand.strip('[]')
        parts = operand.split(',')
        
        if len(parts) == 1:
            return f"({self.convert_register(parts[0])})"
        
        base = self.convert_register(parts[0])
        offset = parts[1].strip()
        
        if offset.startswith('#'):
            return f"{offset[1:]}({base})"
        return f"({base},{self.convert_register(offset)})"

    def convert_file(self, input_filename: str, output_filename: str):
        try:
            with open(input_filename, 'r') as f:
                input_lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file '{input_filename}' not found")
            
        output_lines = [
            '# Converted from AArch64 to x86_64 assembly (AT&T Syntax)',
            '.section __TEXT,__text'
        ]
        
        # Add data section
        data_lines = self.convert_data_section(input_lines)
        output_lines.extend(data_lines)
        
        # Process text section
        in_text = False
        for line in input_lines:
            if '.text' in line:
                in_text = True
                output_lines.append('.section __TEXT,__text')
                continue
                
            if in_text and line.strip():
                converted = self.convert_instruction(line)
                if converted:
                    output_lines.append(converted)
        
        # Write output
        try:
            with open(output_filename, 'w') as f:
                f.write('\n'.join(output_lines))
        except PermissionError:
            raise PermissionError(f"Permission denied when writing to '{output_filename}'")

def main():
    parser = argparse.ArgumentParser(
        description='Convert AArch64 assembly to x86_64 assembly in AT&T syntax'
    )
    parser.add_argument('input_file', help='Input AArch64 assembly file')
    parser.add_argument('output_file', help='Output x86_64 assembly file')
    
    args = parser.parse_args()
    
    converter = AsmConverterATT()
    try:
        converter.convert_file(args.input_file, args.output_file)
        print(f"Conversion complete. Output written to {args.output_file}")
        print("Please review the output file for any necessary manual adjustments.")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main()