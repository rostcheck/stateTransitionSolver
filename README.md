# stateTransitionSolver
> A general solver (in Python) for problems that can be expressed as state transitions, such as
> river crossing problems.

## General Information
Many kinds of problems can be expressed as state transitions. This highly general approach can solve problems in 
quantum mechanics, chemistry, computer science, artificial intelligence, and many other 
disciplines. To express and solve a problem as state transitions, we first view problem can be viewed as a 
series of states, where the state is a complete picture of the system, with all the elements within
it and their individual states. The system starts in an initial state, and we seek to get it into
a target state. In a maze problem, the starting state might begin with the mouse at the maze entrance 
and the cheese at the center, and the target state would be the mouse having reached the cheese.

Besides the initial and final state, the solver allows us to define transitions by identifying a
transition facilitator that must be present to enable state transition, a capacity that the 
facilitator can accommodate, and a series of rules defining which transitions are disallowed. To 
illustrate these, we consider a river crossing problem.

## River problem example
For example, consider river crossing problems, such as how to cross a river with a fox, goat, and 
beans using a boat with only room for one animal or plant, where the fox will eat the goat if 
they are left unattended and the goat will eat the beans if left unattended. This problem has many
variations, such as the 'jealous husbands' problem where several couples must cross but certain
people cannot be left unattended together in the boat.

The initial state begins with the fox, goat, beans, and boat on one bank and nothing on the other. 
Our target state has the fox, goat, beans, and boat on the opposite bank and nothing remaining on 
the original bank. The boat is the transition facilitator; it must be present for an object to
change location. The boat's cargo capacity is the transition facilitator's max capacity. Finally, a
series of rules defines the disallowed transition - for example, `(fox AND goose) AND NOT boat` is 
not allowed.

## Configuration

The solver expects the initial and final state to be defined as JSON.
For example, initial state:

    { "bank1": ["beans", "boat", "fox", "goose"], "bank2": [] }

with target state

    { "bank1": [], "bank2": ["beans", "boat", "fox", "goose"] }

Rules are defined as a list of conditions for disallowed transitions:

    ["(fox AND goose) AND NOT boat",
    "(goose AND beans) AND NOT boat"]

The rule parser is a simple built-in parser that allows parenthesis for 
order of operations, with the operators AND, OR, and NOT. 

Other configuration includes the name of the transition facilitator (here 
"boat") and its max capacity (ex. 1). Note that transitions may use less
capacity than the max defined threshold - for example, a facilitator with
a max capacity of 3 could move 0, 1, 2, or 3 items in a transition.

## Constructing transition pathways via search
To find a solution, the solver constructs possible transitions from the 
initial state, rules out those that result in loops, and discards those that
result in a state that violate the disallowed transition rules. It then 
conducts a search, using a selectable search algorithm (currently depth-first
and breath-first are supported) through the unfolding graph of branching 
states, stopping when it has found a path to the desired state or no more
search options remain.

## Technologies Used
Originally written in Python 3.11.5

## Author
Initial version written by [David Rostcheck](https://www.davidrostcheck.com), November 2023

## License
This project is open source and available under the MIT license.