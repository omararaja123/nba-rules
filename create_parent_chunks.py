"""
Step 1: Create Parent Chunks for Parent-Child Architecture
Maps all child chunks to parents and creates comprehensive parent chunks.
"""

import json

print("=" * 80)
print("CREATING PARENT CHUNKS FOR PARENT-CHILD ARCHITECTURE")
print("=" * 80)
print()

# Load child chunks (original 155)
with open('data/09_stable_chunks.json', 'r') as f:
    data = json.load(f)

child_chunks = data['chunks']

print(f"Loaded {len(child_chunks)} child chunks")
print()

# Group children by rule to create parents
rule_groups = {}
for chunk in child_chunks:
    rule = chunk['metadata']['rule_number']
    if rule not in rule_groups:
        rule_groups[rule] = []
    rule_groups[rule].append(chunk)

print(f"Grouped into {len(rule_groups)} rules")
print()

# Define parent chunk structure
parent_chunks = []

print("Creating parent chunks:")
print()

for rule_num in sorted(rule_groups.keys()):
    children = rule_groups[rule_num]

    # Combine all child texts for this rule
    combined_text = ""
    child_ids = []
    sections = []

    for child in children:
        combined_text += child['text'] + "\n\n"
        child_ids.append(child['id'])
        section = child['metadata']['section_title']
        if section not in sections:
            sections.append(section)

    # Create parent chunk
    rule_title = children[0]['metadata']['rule_title']

    parent_chunk = {
        "id": f"parent_rule_{rule_num:02d}",
        "text": combined_text,
        "metadata": {
            "rule_number": rule_num,
            "rule_title": rule_title,
            "chunk_type": "parent",
            "sections": sections,
            "child_chunk_ids": child_ids,
            "num_children": len(child_ids),
        }
    }

    parent_chunks.append(parent_chunk)

    print(f"✅ Rule {rule_num}: {rule_title}")
    print(f"   Sections: {', '.join([s[:30] for s in sections[:3]])}")
    print(f"   Children: {len(child_ids)}")
    print(f"   Size: {len(combined_text)} characters")
    print()

print()
print("=" * 80)
print(f"CREATED {len(parent_chunks)} PARENT CHUNKS")
print("=" * 80)
print()

# Save parent chunks
output_data = {
    "version": "2.0",
    "format": "parent-child",
    "type": "parent_chunks",
    "total_parents": len(parent_chunks),
    "total_children_referenced": len(child_chunks),
    "chunks": parent_chunks
}

with open('data/11_parent_chunks.json', 'w') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(parent_chunks)} parent chunks to: data/11_parent_chunks.json")
print()

# Create child-to-parent mapping
print("Creating child-to-parent mapping...")
print()

mapping = {}
for parent in parent_chunks:
    rule = parent['metadata']['rule_number']
    for child_id in parent['metadata']['child_chunk_ids']:
        mapping[child_id] = {
            'parent_id': parent['id'],
            'parent_rule': rule,
            'rule_title': parent['metadata']['rule_title'],
        }

with open('data/11_child_parent_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print(f"✅ Created mapping for {len(mapping)} child chunks")
print(f"✅ Saved to: data/11_child_parent_mapping.json")
print()

print("=" * 80)
print("PARENT CHUNKS SUMMARY")
print("=" * 80)
print()

for parent in parent_chunks:
    rule = parent['metadata']['rule_number']
    title = parent['metadata']['rule_title']
    children = parent['metadata']['num_children']
    size = len(parent['text'])
    print(f"Rule {rule:2d} ({title:30s}): {children:2d} children, {size:5d} chars")

print()
