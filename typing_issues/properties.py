import sidekick.api as sk


# It should infer the right properties for
class Foo:
    lst = sk.lazy(lambda _: [])
    set: sk.Prop[set] = sk.lazy(lambda _: set())


foo = Foo()
foo.lst.append(42)
foo.lst.add(42)
foo.set.append(42)
foo.set.add(42)
