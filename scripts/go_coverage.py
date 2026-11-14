"""Exhaustiveness ledger for the Go guide: spec sections, std packages and go subcommands.

Packages count as covered only when a checked program, answer, project file or expected
rejection imports them; commands only when a project check runs them. Spec sections are
claimed by lessons (a `spec` field on new lessons, SPEC below for the original ones).
"""
import json
from pathlib import Path
import re

INVENTORY = json.loads(Path(__file__).with_name('go_guide_inventory.json').read_text())

# Spec sections taught by lessons written before lessons carried a `spec` field.
SPEC = {
    'first-program': ['Program_execution', 'Package_clause', 'Import_declarations', 'Source_file_organization'],
    'gofmt-and-style': ['Comments', 'Semicolons', 'Tokens'],
    'variables-zero-values': ['Variables', 'Variable_declarations', 'Short_variable_declarations', 'The_zero_value', 'Assignment_statements'],
    'constants-iota': ['Constants', 'Constant_declarations', 'Iota', 'Constant_expressions'],
    'numeric-types': ['Numeric_types', 'Arithmetic_operators', 'Integer_operators', 'Integer_overflow', 'Floating_point_operators', 'Conversions'],
    'strings-bytes-runes': ['String_types', 'String_literals', 'Rune_literals', 'Conversions_to_and_from_a_string_type', 'String_concatenation'],
    'operators-precedence': ['Operators', 'Operator_precedence', 'Logical_operators', 'IncDec_statements', 'Operators_and_punctuation'],
    'type-definitions-aliases': ['Type_declarations', 'Alias_declarations', 'Type_definitions', 'Underlying_types'],
    'if-and-for': ['If_statements', 'For_statements', 'For_condition', 'For_clause', 'For_range'],
    'switch': ['Switch_statements', 'Expression_switches', 'Fallthrough_statements', 'Break_statements'],
    'labels-break-continue': ['Labeled_statements', 'Label_scopes', 'Continue_statements', 'Goto_statements'],
    'functions-multiple-results': ['Function_declarations', 'Function_types', 'Return_statements', 'Blank_identifier'],
    'variadic-and-function-values': ['Passing_arguments_to_..._parameters', 'Calls'],
    'closures-loop-variables': ['Function_literals', 'Go_1.22'],
    'defer-basics': ['Defer_statements'],
    'arrays': ['Array_types', 'Index_expressions'],
    'slices-len-cap': ['Slice_types', 'Slice_expressions', 'Appending_and_copying_slices', 'Making_slices_maps_and_channels'],
    'maps': ['Map_types', 'Deletion_of_map_elements'],
    'structs-embedding': ['Struct_types', 'Selectors', 'Composite_literals'],
    'pointers-new': ['Pointer_types', 'Address_operators', 'Allocation'],
    'struct-literal-selectors': ['Go_1.27'],
    'copy-clear-min-max': ['Built-in_functions', 'Clear', 'Min_and_max', 'Length_and_capacity'],
    'methods-receivers': ['Method_declarations'],
    'interfaces-implicit': ['Interface_types', 'Basic_interfaces', 'Implementing_an_interface', 'Method_sets'],
    'type-assertions-switches': ['Type_assertions', 'Type_switches'],
    'interface-composition': ['Embedded_interfaces'],
    'comparable-equality': ['Comparison_operators'],
    'error-values': ['Errors'],
    'panic-recover': ['Handling_panics', 'Run_time_panics'],
    'packages-visibility-init': ['Packages', 'Exported_identifiers', 'Package_initialization', 'Program_initialization'],
    'go-directive-toolchain': ['Language_versions'],
    'type-parameters': ['Type_parameter_declarations', 'Instantiations'],
    'constraints-type-sets': ['General_interfaces', 'Type_constraints', 'Satisfying_a_type_constraint'],
    'type-inference': ['Type_inference', 'Type_unification', 'Type_unification_rules'],
    'range-over-func': ['Go_1.23'],
    'channels-buffering': ['Channel_types', 'Send_statements', 'Receive_operator'],
    'close-and-range': ['Close'],
    'select-timeouts': ['Select_statements'],
    'goroutines': ['Go_statements'],
    'unsafe-pointer': ['Package_unsafe'],
    'memory-layout': ['Size_and_alignment_guarantees'],
}

# Subcommands that a validator must not run; each is still taught in a lesson.
COMMAND_EXEMPT = {
    'bug': 'opens a browser to file an issue on the user\'s behalf; taught from go help bug',
}


def imports(source):
    """Import paths from the import section only, so Go source quoted inside a lesson does not count."""
    header = re.split(r'^(?:func|type|var|const)\b', source, maxsplit=1, flags=re.M)[0]
    header = re.sub(r'//[^\n]*', '', header)
    found = set(re.findall(r'^import (?:[\w.]+ )?"([^"]+)"', header, re.M))
    for block in re.findall(r'^import \((.*?)^\)', header, re.S | re.M):
        found |= set(re.findall(r'"([^"]+)"', block))
    return found


def compiled_here(path, content):
    """True for project files the darwin/arm64 validator compiles in an ordinary build."""
    # shortcut: constrained, testdata and other-OS files never count, even if a cross-build check compiles them
    other_os = re.search(r'_(linux|windows|plan9|freebsd|js|wasip1)(_test)?\.go$', path)
    return not (other_os or path.startswith('testdata/') or '/testdata/' in path or re.search(r'^//go:build ', content, re.M))


def sources(lesson):
    files = (lesson['project'] or []) + (lesson.get('projectSolutionFiles') or [])
    yield from [lesson['code'], lesson['solution']] + [r['source'] for r in lesson.get('rejections', [])]
    yield from [f['content'] for f in files if f['path'].endswith('.go') and compiled_here(f['path'], f['content'])]


def report(lessons):
    keys = {l['key'] for l in lessons}
    spec = {}
    for l in lessons:
        for section in SPEC.get(l['key'], []) + l.get('spec', []):
            spec.setdefault(section, []).append(l['key'])
    used = set().union(*(imports(s) for l in lessons for s in sources(l)))
    ran = {c['args'][0] for l in lessons for c in l.get('projectChecks', []) if c.get('exit', 0) == 0}
    helped = {c['args'][1] for l in lessons for c in l.get('projectChecks', []) if c['args'][:1] == ['help'] and len(c['args']) > 1}
    sections, packages, commands = INVENTORY['spec']['sections'], INVENTORY['std']['packages'], INVENTORY['commands']['names']
    return dict(
        unknownLessonKeys=sorted(set(SPEC) - keys),
        unknownSections=sorted(set(spec) - set(sections)),
        missingSections=[s for s in sections if s not in spec],
        missingPackages=[p for p in packages if p not in used],
        missingCommands=[c for c in commands if c not in ran and not (c in COMMAND_EXEMPT and c in helped)],
        totals=dict(sections=len(sections), packages=len(packages), commands=len(commands)))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from go_guide import LESSONS
    r = report(LESSONS)
    print(json.dumps({k: (v if k == 'totals' else len(v)) for k, v in r.items()}))
    for k, v in r.items():
        if k != 'totals' and v: print(k, ' '.join(v))
