from yalex_parser import YalexParser
import sys
import os


def main():
    # Check if a file was provided as argument
    if len(sys.argv) > 1:
        yal_file = sys.argv[1]
    else:
        # Use default example file
        yal_file = "java_lexer.yal"
    
    # Check if file exists
    if not os.path.exists(yal_file):
        print(f"Error: File '{yal_file}' not found.")
        print(f"\nUsage: python main.py [filename.yal]")
        return 1
    
    print(f"Parsing file: {yal_file}")
    print()
    
    try:
        # Create parser and parse file
        parser = YalexParser()
        spec = parser.parse_file(yal_file)
        
        # Display the parsed specification
        spec.display()
        
        print("\n[OK] Parsing completed successfully!")
        return 0
        
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
