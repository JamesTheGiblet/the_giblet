from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    is_active_member: bool