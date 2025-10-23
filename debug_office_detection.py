#!/usr/bin/env python3
"""Debug office detection functionality"""

from app import detect_office_from_message, office_tags

test_messages = [
    'How do I apply to the college?',
    'I need to reset my password for the portal',
    'How can I request my transcript?',
    'I need counseling services',
    'What student organizations can I join?'
]

print("🔍 Testing Office Detection")
print("=" * 50)

for msg in test_messages:
    detected = detect_office_from_message(msg)
    office = office_tags.get(detected, 'General') if detected else 'General'
    print(f'Message: "{msg}"')
    print(f'Detected tag: {detected}')
    print(f'Office: {office}')
    print('---')
