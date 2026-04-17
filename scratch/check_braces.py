import sys

def check_braces_smart(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    depth = 0
    in_string = False
    string_char = None
    in_template = False
    in_comment_single = False
    in_comment_multi = False
    
    line_no = 1
    i = 0
    while i < len(content):
        char = content[i]
        
        if in_comment_single:
            if char == '\n':
                in_comment_single = False
        elif in_comment_multi:
            if char == '*' and i+1 < len(content) and content[i+1] == '/':
                in_comment_multi = False
                i += 1
        elif in_string:
            if char == string_char and content[i-1] != '\\':
                in_string = False
        elif in_template:
            if char == '`' and content[i-1] != '\\':
                in_template = False
            elif char == '$' and i+1 < len(content) and content[i+1] == '{':
                # Nested expression in template literal
                # This is tricky because it adds depth
                # We'll just treat it as a normal { for now
                pass
        else:
            if char == '/' and i+1 < len(content) and content[i+1] == '/':
                in_comment_single = True
                i += 1
            elif char == '/' and i+1 < len(content) and content[i+1] == '*':
                in_comment_multi = True
                i += 1
            elif char in ["'", '"']:
                in_string = True
                string_char = char
            elif char == '`':
                in_template = True
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth < 0:
                    print(f"Extra closing brace at line {line_no}")
                    return
        
        if char == '\n':
            line_no += 1
        i += 1
    
    if depth > 0:
        print(f"Unclosed opening brace. Final depth: {depth}")
    elif depth == 0:
        print("Braces are balanced.")
    else:
        print(f"Braces are unbalanced. Final depth: {depth}")

if __name__ == "__main__":
    check_braces_smart(sys.argv[1])
