import re
import os
import sys
import subprocess
from typing import List, Dict, Optional

class MacOSAssemblyConverter:
    # ... [Previous converter code remains exactly the same] ...

    def compile_and_link(input_file: str, output_file: str = None) -> bool:
        """
        Compile ARM64 assembly to x86_64 executable
        
        Args:
            input_file: Path to input ARM64 assembly file
            output_file: Desired name for output executable (optional)
        
        Returns:
            bool: True if compilation successful, False otherwise
        """
        try:
            # Read input file
            with open(input_file, 'r') as f:
                arm64_code = f.read()

            # Get base filename without extension
            base_name = os.path.splitext(input_file)[0]
            
            # Use provided output name or default to base_name
            output_name = output_file or base_name

            # Convert assembly
            converter = MacOSAssemblyConverter()
            x86_code = converter.convert_assembly(arm64_code)

            # Write x86_64 assembly to temporary file
            x86_file = f"{base_name}_x86.s"
            with open(x86_file, 'w') as f:
                f.write(x86_code)

            # Assemble
            object_file = f"{base_name}_x86.o"
            assembly_result = subprocess.run(
                ['as', '-arch', 'x86_64', x86_file, '-o', object_file],
                capture_output=True,
                text=True
            )
            
            if assembly_result.returncode != 0:
                print("Assembly failed:")
                print(assembly_result.stderr)
                return False

            # Link
            sdk_path = "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib"
            link_result = subprocess.run(
                ['ld', '-o', output_name, object_file, 
                '-lSystem', '-arch', 'x86_64', 
                '-macos_version_min', '11.0', 
                '-L', sdk_path],
                capture_output=True,
                text=True
            )
            
            if link_result.returncode != 0:
                print("Linking failed:")
                print(link_result.stderr)
                return False

            # Clean up temporary files
            os.remove(x86_file)
            os.remove(object_file)
            
            print(f"Successfully created executable: {output_name}")
            return True

        except Exception as e:
            print(f"Error during compilation: {str(e)}")
            return False

def main():
    """Command line interface for the assembly converter"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert ARM64 assembly to x86_64 and compile for macOS'
    )
    parser.add_argument(
        'input_file',
        help='Input ARM64 assembly file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output executable name (optional)',
        default=None
    )
    parser.add_argument(
        '--keep-assembly',
        action='store_true',
        help='Keep the generated x86_64 assembly file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed conversion output'
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1

    try:
        # Read input file
        with open(args.input_file, 'r') as f:
            arm64_code = f.read()

        converter = MacOSAssemblyConverter()
        x86_code = converter.convert_assembly(arm64_code)

        # Generate output filenames
        base_name = os.path.splitext(args.input_file)[0]
        x86_file = f"{base_name}_x86.s"
        output_name = args.output or base_name

        # Save x86_64 assembly
        with open(x86_file, 'w') as f:
            f.write(x86_code)

        if args.verbose:
            print(f"Generated x86_64 assembly:\n{x86_code}\n")

        # Compile and link
        success = compile_and_link(args.input_file, output_name)

        # Clean up unless --keep-assembly is specified
        if not args.keep_assembly and os.path.exists(x86_file):
            os.remove(x86_file)

        return 0 if success else 1

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())