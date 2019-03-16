from sidekick import eff
from sidekick.eff import io


class Shout:
    def write(self, data):
        eff.get_super(io.TermIO).write(data.upper())

    def readline(self):
        return eff.get_super(io.TermIO, self).readline()


def say_hello():
    name = io.input("Name: ")
    age = int(io.input("Age: "))
    io.print(f"Hello {name}! Congrats for your {age} years.")


write = io.TermIO.write
read = io.TermIO.readline

intents = [
    [write, "Name: "],
    [read, "John"],
    [write, "Age: "],
    [read, "42"],
    [write, "Hello John! Congrats for your 42 years.\n"],
]

with eff.assert_intents(intents):
    with eff.handle({io.TermIO: Shout()}):
        say_hello()

with io.with_inputs(["john", "42"], echo=True, handlers={io.TermIO: Shout()}):
    say_hello()
