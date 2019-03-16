=======
Effects
=======


Say hello to a function that produces side effects:

.. code-block:: python

    def say_hello():
        name = input('Name: ')
        age = int(input('Age: '))
        print(f'Hello {name}! Congrats for your {age} years.')

This elusively simple code introduces a series of complications:

* It relies on side-effects that are not easily trackable.
* Testing requires mocks and other advanced tricks.
* Uses global state (users can modify sys.stdout).

say_hello() is not a proper function in a mathematical sense and we execute it
just for its side effects, not for its result value. Functional programming
teaches us to avoid effectful code since it cannot be expressed and composed as
simple function applications. Of course, an IO side-effect is required to display
at least the final result of a computation to the user, hence any minimally useful
program requires at least some side effects.

Many functional programming languages handle effects explicitly in the type
system. This is the case of Haskell, for instance, that creates a special type
to represent a computation that produces side-effects (instead of making those
effects "appear" magically with no indication in the input and output
parameters of a function).

This approach can make effectful functions behave like pure functions. However,
it is hard to translate those idioms to Python. Haskell syntax can handle
functional effectful code somewhat elegantly, while a direct Python displacement
would be both awkward and verbose.

Haskell version of ``say_hello`` is very similar to what we have in Python:

.. code-block:: haskell

    sayHello = do
        name <- input "Name: "
        age <- read <$> input "Age: "
        print ("Hello " <> name <> "!, Congrats for your " <> show age <> " years!")

(for the nitpickers: the "input" function does not exist, but it is trivial to
implement). Pretty simple, huh?

The similarity is very superficial. Semantically, the code above corresponds to
the following Python beast:


.. ignore-next-block
.. code-block:: python

    say_hello = execute(
        io.input('Name:')
            .bind(lambda name:
                io.input('Age: ').map(int).bind(lambda age:
                    io.print(f'Hello {name}! Congrats for your {age} years.'))))

The special ``io.input`` and ``io.print`` do not produce IO, but instead represents
the desired operations as data, which later can be executed by some sort of
runtime system represented by the function "execute".

The code above relies heavily on callbacks, in which the ".bind()" method register
an action that is executed after each effect is concluded.

No sane library writer should subject its users to this kind of API. We
could try to make this Haskell idiom a little more Pythonic, while keeping the
essential features, but there is so much that Python can do. The Effect_ library
takes this road, and did a great job of translating those concepts to
more idiomatic Python, but IMO the API still feel a little bit clumsy.

.. _Effect: https://effect.readthedocs.io/


Implementing effects
====================




@do
def say_hello():
    name = yield my_input('name')
    return my_print(f'Hello {name}!')



res = say_hello()

class ShoutIO(TermIO):
    def write(self, data):
        super().write(data.upper())

with eff.handle({TermIO: ShoutIO()}):
    res = say_hello()


effects = [
    [TermIO.write, 'Name: '],
    [TermIO.readline, 'John'],
    [TermIO.write, 'Age: '],
    [TermIO.readline, '42'],
    [TermIO.write, 'Hello John! Congrats for your 42 years.'],
]


with eff.check(effects):
    res = say_hello()


with eff.io.with_inputs(['John']):
    res = say_hello()



class TermIO(Effect):
    def readline(self):
        return builtins.input()

    def write(self, data):
        builtins.print(data, end='')


