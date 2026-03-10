from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TokenRule:
    regex: str
    action: str
    priority: int  # Lower number = higher priority (order in the rule section)

    def __repr__(self):
        return f"TokenRule(regex={self.regex!r}, action={self.action!r}, priority={self.priority})"


@dataclass
class YalexSpecification:
    header: str = ""
    macros: Dict[str, str] = field(default_factory=dict)
    rules: List[TokenRule] = field(default_factory=list)
    trailer: str = ""

    def __repr__(self):
        return (f"YalexSpecification(\n"
                f"  header={self.header!r},\n"
                f"  macros={self.macros},\n"
                f"  rules={self.rules},\n"
                f"  trailer={self.trailer!r}\n"
                f")")

    def display(self):
        print("=" * 60)
        print("YALEX SPECIFICATION")
        print("=" * 60)
        
        print("\n[HEADER]")
        print(self.header if self.header else "(empty)")
        
        print("\n[MACROS]")
        if self.macros:
            for name, pattern in self.macros.items():
                print(f"  {name} -> {pattern}")
        else:
            print("  (none)")
        
        print("\n[RULES]")
        if self.rules:
            for i, rule in enumerate(self.rules, 1):
                print(f"  Rule {i} (priority {rule.priority}):")
                print(f"    Regex:  {rule.regex}")
                print(f"    Action: {rule.action}")
        else:
            print("  (none)")
        
        print("\n[TRAILER]")
        print(self.trailer if self.trailer else "(empty)")
        
        print("=" * 60)
