# State transition solver - solves "river problems" where the problem can be expressed
# as a series of states with transitions between them and rules governing the allowed transitions
# The "state" is the complete picture of all information in the system. It is an aggregation of
# substates (ex. east bank, specifying what is on the east side, and west bank, specifying what is
# on the west side)
import itertools
import json
from dataclasses import dataclass
import copy
import re
import collections


# Data structure for a single search step in a search tree
class SearchTreeNode:
    def __init__(self, parent: 'SearchTreeNode' or None, state: dict):
        self.parent = parent
        self.children = []
        # System state associated with this step
        self.system_state = state

    # Return True if the provided state is a child
    def is_child(self, state: dict):
        for child in self.children:
            if child.system_state == state:
                return True
        return False

    # Return True if the provided state is the same as that represented by this node or any of its parents' states
    # This finds loops where a search path doubles back on itself
    def detect_loop(self, new_state: dict):
        node = self
        while node:
            if new_state == node.system_state:
                return True
            node = node.parent
        return False

    def add_children(self, child_states: list[dict]) -> list['SearchTreeNode']:
        added = []
        for new_state in child_states:
            if not self.detect_loop(new_state) and not self.is_child(new_state):
                new_node = SearchTreeNode(self, new_state)
                self.children.append(new_node)
                added.append(new_node)
        return added


# Wrap search algorithm management into class. Construct with "breadth-first" or "depth-first" (default)
class SearchAlgorithm:
    def __init__(self, algorithm_to_use: str):
        if algorithm_to_use != "breadth-first" and algorithm_to_use != "depth-first":
            raise ValueError(f"Algorithm {algorithm_to_use} is not supported")
        else:
            self._algorithm = "depth-first"
        self._visited = set()
        self._to_visit = collections.deque()
        # Pointer to current active node in the tree
        self._current_node: SearchTreeNode

    @staticmethod
    def get_state_path(node) -> list[dict]:
        path = []
        _node = node
        while node:
            path.append(node.system_state)
            node = node.parent
        return path

    # Perform the search
    def search(self, start_state: dict, target_state: dict, transition_facilitator: str, max_transition_capacity: int,
               disallowed_transition_rules: list[str]):
        # Reset the tracking collections
        self._visited = set()
        self._to_visit = collections.deque()
        # Start the tree
        root = SearchTreeNode(None, start_state)
        current_node = root
        self._to_visit.append(root)
        while current_node.system_state != target_state:
            self._visited.add(current_node)
            _new_states = form_new_states(current_node.system_state, transition_facilitator, max_transition_capacity,
                                          disallowed_transition_rules)
            self.add_states_as_children(current_node, _new_states)
            if self._to_visit.count == 0:
                break  # No more nodes to search
            else:
                current_node = self._to_visit.popleft()

        # Build the path of state transitions
        if current_node.system_state == target_state:
            return self.get_state_path(current_node)
        else:
            return None

    def add_states_as_children(self, node: SearchTreeNode, children: list[dict]):
        added = node.add_children(children)  # Add them as nodes in the tree
        # Depth-first adds discovered children to the top of the queue
        if self._algorithm != "breadth-first":
            self._to_visit.extendleft(added)
        else:
            # Breadth-first adds discovered children to the end of the queue
            self._to_visit.extend(added)


def load_initial_state():
    s = json.loads('{ "bank1": ["beans", "boat", "fox", "goose"], "bank2": [] }')
    return s


def load_terminal_state():
    s = json.loads('{ "bank1": [], "bank2": ["beans", "boat", "fox", "goose"] }')
    return s


def load_invalid_state_rules():
    s = ["(fox AND goose) AND NOT boat",
         "(goose AND beans) AND NOT boat"]
    for _ in range(0, len(s)):
        s[_] = s[_].replace("NOT ", "!")
    return s


@dataclass
class Config:
    transition_facilitator: str
    transition_max_capacity: int


def load_config():
    return Config("boat", 1)


def get_source_sub_state(current, transition_facilitator):
    for sub_state in current:
        if transition_facilitator in current[sub_state]:
            return sub_state
    raise LookupError(f"No state contains transition facilitator {transition_facilitator} ")


def get_target_sub_state(current, transition_facilitator):
    count = 0
    return_state = {}
    for sub_state in current:
        if transition_facilitator not in current[sub_state]:
            count += 1
            return_state = sub_state
    if count == 0:
        raise LookupError(f"All substates contain facilitator {transition_facilitator}, can't identify target")
    if count > 1:
        raise LookupError(f"More than one target sub-state was found, behavior undefined")
    else:
        return return_state


def get_new_state(source_state, source_tag, target_tag, targets):
    new_state = copy.deepcopy(source_state)
    for target in targets:
        new_state[target_tag].append(target)
        new_state[source_tag].remove(target)
    new_state[target_tag] = sorted(new_state[target_tag])
    new_state[source_tag] = sorted(new_state[source_tag])
    return new_state


def get_sub_rules(s):
    results = set()
    for start in range(len(s)):
        string = s[start:]
        results.update(re.findall('\(.*?\)', string))
    return results


# Get the value from a rule section, where the value is either the strings "True", "False", or a
# string representing a lookup key in the dictionary
def get_value(s, string_list):
    reverse = False
    return_val = False
    if s == "True":
        return True
    if s == "False":
        return False
    if s[0] == '!':
        reverse = True
        s = s[1:]
    if s in string_list:
        return_val = True
    if reverse:
        return not return_val
    else:
        return return_val


# Super basic rules evaluator
def evaluate_rule(rule: str, testlist):
    # If any substrings contain parenthesis, recursively evaluate them first
    sub_rules = get_sub_rules(rule)
    if sub_rules:
        for sub_rule in sub_rules:
            result = evaluate_rule(sub_rule[1:-1], testlist)
            rule = rule.replace(sub_rule, str(result))
    # Process AND clauses
    match = re.search('([\w!]+) AND ([\w!]+)', rule)
    if match:
        lhs = get_value(match.group(1), testlist)
        rhs = get_value(match.group(2), testlist)
        return lhs and rhs

    # Process OR clauses
    match = re.search('(\s+) OR (\s+)', rule)
    if match:
        lhs = get_value(match.group(1), testlist)
        rhs = get_value(match.group(2), testlist)
        return lhs or rhs
    return False


def state_is_allowed(trial_state, transition_rules):
    for sub_state in trial_state:
        for rule in transition_rules:
            if evaluate_rule(rule, trial_state[sub_state]):
                return False
    return True


def form_transitions(current: dict, source_tag: str, target_tag: str, transition_facilitator: str, capacity: int,
                     transition_rules: list[str]):
    return_states = []
    # Transition facilitator must move between substates (ex. move boat between banks)
    base_new_state = get_new_state(current, source_tag, target_tag, [transition_facilitator])

    transition_candidates = list(itertools.combinations(base_new_state[source_tag], capacity))
    for candidate in transition_candidates:
        trial_state = get_new_state(base_new_state, source_tag, target_tag, candidate)
        if state_is_allowed(trial_state, transition_rules):
            return_states.append(trial_state)
    return return_states


def form_new_states(this_state: dict, transition_facilitator: str, max_capacity: int, transition_rules: list[str]):
    new_states = []
    source = get_source_sub_state(this_state, transition_facilitator)
    target = get_target_sub_state(this_state, transition_facilitator)

    # Form all the permutations for each allowable capacity of the transition facilitator
    for step in range(0, max_capacity + 1):
        found_states = form_transitions(this_state, source, target, transition_facilitator, step, transition_rules)
        if len(found_states) > 0:
            new_states.extend(found_states)

    return new_states


if __name__ == '__main__':
    current_state = load_initial_state()
    end_state = load_terminal_state()
    config = load_config()
    rules = load_invalid_state_rules()

    algorithm = SearchAlgorithm('depth-first')
    solution = algorithm.search(current_state, end_state, config.transition_facilitator, config.transition_max_capacity,
                                rules)

    if solution:
        print('Solution path found:')
        solution.reverse()
        for i in range(0, len(solution)):
            print(f"State {i}: {solution[i]}")
    else:
        print('No solution path found')
