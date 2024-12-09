import argparse
import os
import re
import sys
from pathlib import Path


def format_comment_spaces(text):
    """
    Ensure there is a space after "(*" and before "*)".
    """
    # Replace "(*" with "(* " if not followed by a space
    text = re.sub(r'\(\*(?!\s)', r'(* ', text)
    # Replace "*)" with " *)" if not preceded by a space
    text = re.sub(r'(?<!\s)\*\)', r' *)', text)
    return text

def ensure_newline_before_keywords(text):
    """
    Ensure that certain keywords start on a new line.
    """
    keywords = [
        "Lemma", "Theorem", "Definition", "Fixpoint", 
        "Proof", "Qed", "Admitted", "Admit", 
        "Corollary", "Remark", "Proposition", "Example"
    ]
    # Create a regex pattern that matches any of the keywords not at the start of a line
    # Using word boundaries to match whole words
    pattern = r'(?<!\n)(?<!^)\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
    # Replace matched keywords with a newline followed by the keyword
    replacement = r'\n\1'
    text = re.sub(pattern, replacement, text)
    return text

def format_coq_code(text):
    """
    Format the Coq code by processing the entire text.
    """
    # First, format comment spacing
    text = format_comment_spaces(text)
    # Then, ensure newline before certain keywords
    text = ensure_newline_before_keywords(text)
    
    # Normalize line endings to Unix style
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text

def format_file(file_path, in_place=False, backup=False):
    """
    Format a single Coq file.
    
    Args:
        file_path (Path): Path object representing the file to format.
        in_place (bool): If True, overwrite the original file.
        backup (bool): If True and in_place is True, create a backup of the original file.
    """
    try:
        with file_path.open('r', encoding='utf-8') as f:
            original_text = f.read()
        
        formatted_text = format_coq_code(original_text)
        
        if in_place:
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                with backup_path.open('w', encoding='utf-8') as f_backup:
                    f_backup.write(original_text)
                print(f"Backup created: {backup_path}")
            
            with file_path.open('w', encoding='utf-8') as f:
                f.write(formatted_text)
            print(f"Formatted (in-place): {file_path}")
        else:
            print(f"--- {file_path} ---")
            print(formatted_text)
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)

def find_coq_files(directory, exclude_dirs=None):
    """
    Recursively find all .v files in the given directory, excluding specified subdirectories.
    
    Args:
        directory (Path): Path object representing the directory to search.
        exclude_dirs (List[Path] or None): List of directories to exclude.
        
    Returns:
        List[Path]: List of Path objects for each .v file found.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    coq_files = []
    for path in directory.rglob('*.v'):
        if not any(excluded in path.parents for excluded in exclude_dirs):
            coq_files.append(path)
    return coq_files

def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Coq Code Formatter: Formats Coq (.v) files by ensuring proper comment spacing and inserting newlines before specified keywords."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-f', '--file', 
        type=Path, 
        help="Path to a single Coq (.v) file to format."
    )
    group.add_argument(
        '-d', '--directory', 
        type=Path, 
        help="Path to a directory containing Coq (.v) files to format recursively."
    )
    parser.add_argument(
        '-i', '--in-place', 
        action='store_true', 
        help="Modify the files in place. If not set, the formatted code will be printed to stdout."
    )
    parser.add_argument(
        '-b', '--backup', 
        action='store_true', 
        help="Create a backup of the original file before formatting (only applicable with --in-place)."
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Default behavior: format all .v files in current directory in-place
    if not args.file and not args.directory:
        args.directory = Path('.')
        args.in_place = True
        # Optionally, set backup to True if desired by default
        # args.backup = True
    
    if args.file:
        if not args.file.is_file():
            print(f"Error: {args.file} is not a valid file.", file=sys.stderr)
            sys.exit(1)
        format_file(args.file, in_place=args.in_place, backup=args.backup)
    
    elif args.directory:
        if not args.directory.is_dir():
            print(f"Error: {args.directory} is not a valid directory.", file=sys.stderr)
            sys.exit(1)
        coq_files = find_coq_files(args.directory)
        if not coq_files:
            print(f"No .v files found in directory {args.directory}.", file=sys.stderr)
            sys.exit(1)
        for coq_file in coq_files:
            format_file(coq_file, in_place=args.in_place, backup=args.backup)

if __name__ == "__main__":
    main()