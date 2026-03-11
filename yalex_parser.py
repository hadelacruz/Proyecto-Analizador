from models import YalexSpecification, TokenRule
import re


class YalexParser:
    """Parser for .yal lexical specification files following yalex syntax."""
    
    def __init__(self):
        self.spec = YalexSpecification()
        self.content = ""
        self.pos = 0
        self.line = 1
        self.col = 1
    
    def parse_file(self, filepath: str) -> YalexSpecification:
        with open(filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        self.pos = 0
        self.line = 1
        self.col = 1
        self.spec = YalexSpecification()
        
        # Parse in order: header, macros, rules, trailer
        self._skip_whitespace_and_comments()
        self._parse_header()
        self._skip_whitespace_and_comments()
        self._parse_macros()
        self._skip_whitespace_and_comments()
        self._parse_rules()
        self._skip_whitespace_and_comments()
        self._parse_trailer()
        
        return self.spec
    
    def _current_char(self) -> str:
        if self.pos >= len(self.content):
            return ''
        return self.content[self.pos]
    
    def _peek_char(self, offset: int = 1) -> str:
        pos = self.pos + offset
        if pos >= len(self.content):
            return ''
        return self.content[pos]
    
    def _advance(self):
        if self.pos < len(self.content):
            if self.content[self.pos] == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1
    
    def _skip_whitespace_and_comments(self):
        """Skip whitespace and block comments (* ... *)"""
        while self.pos < len(self.content):
            ch = self._current_char()
            
            # Skip whitespace
            if ch in ' \t\n\r':
                self._advance()
                continue
            
            # Skip block comments (* ... *)
            if ch == '(' and self._peek_char() == '*':
                self._advance()  # skip (
                self._advance()  # skip *
                # Skip until we find *)
                while self.pos < len(self.content):
                    if self._current_char() == '*' and self._peek_char() == ')':
                        self._advance()  # skip *
                        self._advance()  # skip )
                        break
                    self._advance()
                continue
            
            break
    
    def _parse_header(self):
        if self._current_char() != '{':
            return  # No header
        
        self._advance()  # skip opening {
        
        # Find matching closing brace, handling nested braces
        brace_count = 1
        start_pos = self.pos
        
        while self.pos < len(self.content) and brace_count > 0:
            ch = self._current_char()
            if ch == '{':
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
            
            if brace_count > 0:
                self._advance()
        
        # Extract header content
        header_content = self.content[start_pos:self.pos].strip()
        self.spec.header = header_content
        
        if self._current_char() == '}':
            self._advance()  # skip closing }
    
    def _parse_macros(self):
        while True:
            self._skip_whitespace_and_comments()
            
            # Check if this is a macro definition
            if not self._match_keyword('let'):
                break
            
            # Skip 'let'
            self.pos += 3
            self._skip_whitespace_and_comments()
            
            # Parse macro name
            name = self._parse_identifier()
            if not name:
                raise SyntaxError(f"Expected macro name at line {self.line}")
            
            self._skip_whitespace_and_comments()
            
            # Expect '='
            if self._current_char() != '=':
                raise SyntaxError(f"Expected '=' after macro name at line {self.line}")
            self._advance()
            self._skip_whitespace_and_comments()
            
            # Parse macro value (regex pattern until end of line or next 'let'/'rule')
            value = self._parse_macro_value()
            
            self.spec.macros[name] = value
    
    def _parse_identifier(self) -> str:
        start_pos = self.pos
        
        # First character must be letter or underscore
        ch = self._current_char()
        if not (ch.isalpha() or ch == '_'):
            return ''
        
        while self._current_char() and (self._current_char().isalnum() or self._current_char() == '_'):
            self._advance()
        
        return self.content[start_pos:self.pos]
    
    def _parse_macro_value(self) -> str:
        start_pos = self.pos
        
        # Read until newline or end of file
        while self._current_char() and self._current_char() != '\n':
            self._advance()
        
        return self.content[start_pos:self.pos].strip()
    
    def _parse_rules(self):
        self._skip_whitespace_and_comments()
        
        # Check for 'rule' keyword
        if not self._match_keyword('rule'):
            return  # No rules section
        
        # Skip 'rule'
        self.pos += 4
        self._skip_whitespace_and_comments()
        
        # Parse rule name
        rule_name = self._parse_identifier()
        if not rule_name:
            raise SyntaxError(f"Expected rule name at line {self.line}")
        
        self._skip_whitespace_and_comments()
        
        # Expect '='
        if self._current_char() != '=':
            raise SyntaxError(f"Expected '=' after rule name at line {self.line}")
        self._advance()
        self._skip_whitespace_and_comments()
        
        # Parse rule alternatives separated by |
        priority = 0
        while True:
            # Parse regex pattern
            pattern = self._parse_pattern()
            if not pattern:
                break
            
            self._skip_whitespace_and_comments()
            
            # Parse action code inside { ... }
            action = self._parse_action()
            
            # Add rule
            self.spec.rules.append(TokenRule(
                regex=pattern.strip(),
                action=action.strip(),
                priority=priority
            ))
            priority += 1
            
            self._skip_whitespace_and_comments()
            
            # Check for | to continue with next alternative
            if self._current_char() == '|':
                self._advance()
                self._skip_whitespace_and_comments()
            else:
                break
    
    def _parse_pattern(self) -> str:
        """
        Parse a regex pattern until we hit { for the action.
        Handles character classes, quotes, and parentheses.
        """
        start_pos = self.pos
        in_char_class = False
        in_string = False
        string_char = None
        paren_depth = 0  # Track parentheses depth
        
        while self.pos < len(self.content):
            ch = self._current_char()
            
            # Handle character classes [...]
            if ch == '[' and not in_string:
                in_char_class = True
                self._advance()
                continue
            
            if ch == ']' and in_char_class and not in_string:
                in_char_class = False
                self._advance()
                continue
            
            # Handle parentheses (for grouping in regex)
            if ch == '(' and not in_char_class and not in_string:
                paren_depth += 1
                self._advance()
                continue
            
            if ch == ')' and not in_char_class and not in_string and paren_depth > 0:
                paren_depth -= 1
                self._advance()
                continue
            
            # Handle string literals
            if ch in ('"', "'") and not in_char_class:
                if not in_string:
                    in_string = True
                    string_char = ch
                    self._advance()
                    continue
                elif ch == string_char:
                    in_string = False
                    string_char = None
                    self._advance()
                    continue
            
            # If we hit { and we're not inside a character class or string, we're done
            if ch == '{' and not in_char_class and not in_string and paren_depth == 0:
                break
            
            # If we hit | and we're not inside a character class, string, or parentheses, we're done
            if ch == '|' and not in_char_class and not in_string and paren_depth == 0:
                break
            
            # Stop at newline if not in special context (for macro references, etc)
            if ch == '\n' and not in_char_class and not in_string and paren_depth == 0:
                # Check if this looks like end of pattern
                if self.pos > start_pos:
                    # Peek ahead to see if there's a {
                    saved_pos = self.pos
                    self._skip_whitespace_and_comments()
                    if self._current_char() == '{':
                        # This is the end of the pattern
                        break
                    else:
                        # Not the end, restore position
                        self.pos = saved_pos
            
            self._advance()
        
        pattern = self.content[start_pos:self.pos].strip()
        return pattern
    
    def _parse_action(self) -> str:
        """Parse action code inside { ... }, handling nested braces and comments"""
        if self._current_char() != '{':
            return ''
        
        self._advance()  # skip opening {
        
        # Find matching closing brace
        brace_count = 1
        start_pos = self.pos
        
        while self.pos < len(self.content) and brace_count > 0:
            ch = self._current_char()
            
            # Handle yalex block comments (* ... *)
            if ch == '(' and self._peek_char() == '*':
                self._advance()  # skip (
                self._advance()  # skip *
                while self.pos < len(self.content):
                    if self._current_char() == '*' and self._peek_char() == ')':
                        self._advance()  # skip *
                        self._advance()  # skip )
                        break
                    self._advance()
                continue
            
            # Handle string literals to avoid counting braces inside strings
            if ch in ('"', "'"):
                quote = ch
                self._advance()
                while self.pos < len(self.content):
                    ch = self._current_char()
                    if ch == '\\':
                        self._advance()  # skip escape
                        if self.pos < len(self.content):
                            self._advance()  # skip escaped char
                    elif ch == quote:
                        self._advance()
                        break
                    else:
                        self._advance()
                continue
            
            if ch == '{':
                brace_count += 1
            elif ch == '}':
                brace_count -= 1
            
            if brace_count > 0:
                self._advance()
        
        action_content = self.content[start_pos:self.pos].strip()
        
        if self._current_char() == '}':
            self._advance()  # skip closing }
        
        return action_content
    
    def _parse_trailer(self):
        """Parse trailer code (optional, can be inside { ... })"""
        self._skip_whitespace_and_comments()
        
        # Check if trailer is enclosed in braces
        if self._current_char() == '{':
            self._advance()  # skip opening {
            
            # Find matching closing brace
            brace_count = 1
            start_pos = self.pos
            
            while self.pos < len(self.content) and brace_count > 0:
                ch = self._current_char()
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                
                if brace_count > 0:
                    self._advance()
            
            trailer_content = self.content[start_pos:self.pos].strip()
            self.spec.trailer = trailer_content
            
            if self._current_char() == '}':
                self._advance()  # skip closing }
        else:
            # No braces, read everything remaining as trailer
            start_pos = self.pos
            
            while self.pos < len(self.content):
                self._advance()
            
            trailer = self.content[start_pos:].strip()
            if trailer:
                self.spec.trailer = trailer
    
    def _match_keyword(self, keyword: str) -> bool:
        end_pos = self.pos + len(keyword)
        if end_pos > len(self.content):
            return False
        
        # Check if the keyword matches
        if self.content[self.pos:end_pos] != keyword:
            return False
        
        # Check that it's followed by whitespace or special char (not part of identifier)
        if end_pos < len(self.content):
            next_char = self.content[end_pos]
            if next_char.isalnum() or next_char == '_':
                return False
        
        return True
